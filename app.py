from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
import sys, json, os

from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor

import library, test_server, test_client

class ParseWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, path):
        super(QtCore.QObject, self).__init__()
        self.library_path = path

    def run(self):
        parsed_library = library.parse_library_hash(self.library_path)
        json_file = open("library.json", "w")
        json.dump(parsed_library, json_file)
        json_file.close()
        self.finished.emit()

class ServerWorker(QtCore.QObject):
    def run(self):
        send_file = open("library.json", "rb").read()
        endpoint = TCP4ServerEndpoint(reactor, 8420)
        endpoint.listen(test_server.TestFactory(send_file))
        reactor.run()

class ClientWorker(QtCore.QObject):
    def __init__(self, i):
        super(QtCore.QObject, self).__init__()
        self.ip = i
    def run(self):
        point = TCP4ClientEndpoint(reactor, self.ip, 8420)
        d = connectProtocol(point, test_client.TestServ())
        reactor.run()

class Node:
    def __init__(self, d):
        self.children = []
        self.data = d

    def __str__(self):
        return self.data

    def isLeaf(self):
        return len(self.children) == 0

    def hasChild(self, name):
        if self.isLeaf():
            return (False, None)
        for item in self.children:
            if item.data == name:
                return (True, item)
        return (False, None)

    def insert(self, path):
        path_split = path.split("\\") # TODO: allow Unix paths
        if len(path_split) == 1:
            self.children.append(Node(path_split[0]))
        else:
            hasChildCheck = self.hasChild(path_split[0])
            if hasChildCheck[0]:
                hasChildCheck[1].insert(path[(len(path_split[0])+1):])
            else:
                newNode = Node(path_split[0])
                newNode.insert(path[(len(path_split[0])+1):])
                self.children.append(newNode)


class Window(QtWidgets.QMainWindow):
    def buttonPushed(self):
        print("Buttons that are selected:")
        for widget in self.buttons_list:
            if widget.checkState(0) == 2:
                print(widget.text(0))

    def serverButtonPushed(self):
        if not os.path.exists("library.json"):
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Server Message")
            popup.setText("library.json not found.")
            popup.setInformativeText("You must parse your library before continuing.")
            popup.exec()
        else:
            print("Opening TCP server...")
            self.server_button.setEnabled(False)
            self.connect_button.setEnabled(False)
            self.server_thread = QtCore.QThread()
            self.server_worker = ServerWorker()
            self.server_worker.moveToThread(self.server_thread)

            self.server_thread.started.connect(self.server_worker.run)
            self.server_thread.start()

    def clientButtonPushed(self):
        canStart = True
        for c in self.ip_text_box.text():
            if not c.isdigit() or c != ".":
                canStart = False

        if self.ip_text_box.text() == "localhost":
            canStart = True

        if canStart:
            if not os.path.exists("library.json"):
                popup = QtWidgets.QMessageBox()
                popup.setWindowTitle("Client Message")
                popup.setText("library.json not found.")
                popup.setInformativeText("You must parse your library before continuing.")
                popup.exec()
            else:
                print("Connecting to server...")
                self.server_button.setEnabled(False)
                self.connect_button.setEnabled(False)
                self.client_thread = QtCore.QThread()
                self.client_worker = ClientWorker(self.ip_text_box.text())
                self.client_worker.moveToThread(self.client_thread)

                self.client_thread.started.connect(self.client_worker.run)
                self.client_thread.start()
        else:
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Client Message")
            popup.setText("You must enter a valid IP.")
            popup.exec()

    def parseButtonPushed(self):
        parseLib = True

        if os.path.exists("library.json"):
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Library Parse")
            popup.setText("Your library has already been parsed.")
            popup.setInformativeText("Would you like to re-parse?")
            popup.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            popup.setDefaultButton(QtWidgets.QMessageBox.Yes)
            popup.setIcon(QtWidgets.QMessageBox.Question)
            ret = popup.exec()
            if ret == QtWidgets.QMessageBox.No:
                parseLib = False
            elif ret == QtWidgets.QMessageBox.Yes:
                print("Removing existing library...")
                os.remove("library.json")

        if parseLib:
            print("Parsing given path...")
            self.parse_status_text.setText("Parsing...")

            self.parse_thread = QtCore.QThread()
            self.parse_worker = ParseWorker(self.library_path_box.text())
            self.parse_worker.moveToThread(self.parse_thread)

            self.parse_thread.started.connect(self.parse_worker.run)
            self.parse_worker.finished.connect(self.parse_thread.quit)
            self.parse_worker.finished.connect(lambda: print("Finished parsing!"))
            self.parse_worker.finished.connect(lambda: self.parse_status_text.setText("Finished!"))
            self.parse_worker.finished.connect(self.parse_worker.deleteLater)
            self.parse_thread.finished.connect(self.parse_thread.deleteLater)

            self.parse_thread.start()

    def createNode(self, item, parent):
        if not item.isLeaf():
            parentNode = QtWidgets.QTreeWidgetItem(parent)
            parentNode.setText(0, str(item))
            parentNode.setFlags(parentNode.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
            for child in item.children:
                self.createNode(child, parentNode)
        else:
            childNode = QtWidgets.QTreeWidgetItem(parent)
            childNode.setFlags(childNode.flags() | Qt.ItemIsUserCheckable)
            childNode.setText(0, str(item))
            childNode.setCheckState(0, Qt.Unchecked)
            self.buttons_list.append(childNode)

    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.setWindowTitle("Song Exchanger")
        self.setMinimumSize(800, 600)

        # These might need to be relocated?
        if os.path.exists("ext_lib.json"):
            print("Pre-existing ext_lib.json found. Removing...")
            os.remove("ext_lib.json")
        if os.path.exists("compare_lib.json"):
            print("Pre-existing compare_lib.json found. Removing...")
            os.remove("compare_lib.json")

        self.library_path_box = QtWidgets.QLineEdit()
        self.library_path_box.setPlaceholderText("Enter song library path here...")
        self.parse_library_button = QtWidgets.QPushButton("Parse Library")
        self.parse_library_button.clicked.connect(self.parseButtonPushed)
        self.parse_library_button.setEnabled(False)
        self.library_path_box.textChanged.connect(lambda: self.parse_library_button.setEnabled(True) if (self.library_path_box.text() != "") else (self.parse_library_button.setEnabled(False)))
        self.parse_status_text = QtWidgets.QLabel("Enter path and click parse.")
        self.parse_status_text.setFixedSize(150, 20)

        topLayout = QtWidgets.QHBoxLayout(self)
        topLayout.addWidget(self.library_path_box)
        topLayout.addWidget(self.parse_library_button)
        topLayout.addWidget(self.parse_status_text)

        self.tree = QtWidgets.QTreeWidget()

        self.root = Node("root")

        #ext_lib = json.loads(open("library.json", "r").read())
        #for key in ext_lib:
        #    self.root.insert(ext_lib[key])

        self.buttons_list = []

        for item in self.root.children:
            self.createNode(item, self.tree)

        treeLayout = QtWidgets.QVBoxLayout(self)
        treeLayout.addWidget(self.tree)

        self.ip_text_box = QtWidgets.QLineEdit()
        self.ip_text_box.setPlaceholderText("Enter IP here...")
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(self.clientButtonPushed)
        self.ip_text_box.textChanged.connect(lambda: self.connect_button.setEnabled(True) if (self.ip_text_box.text() != "") else (self.connect_button.setEnabled(False)))
        self.server_button = QtWidgets.QPushButton("Start Server")
        self.server_button.clicked.connect(self.serverButtonPushed)
        lowerLayout = QtWidgets.QHBoxLayout(self)
        lowerLayout.addWidget(self.ip_text_box)
        lowerLayout.addWidget(self.connect_button)
        lowerLayout.addWidget(self.server_button)
        lowerLayout.addWidget(self.connect_button)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(treeLayout)
        mainLayout.addLayout(lowerLayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
