from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
import sys, json, os, platform

from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint, TCP4ClientEndpoint, connectProtocol
from twisted.internet import reactor

import library, server, client

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
    communicator = QtCore.pyqtSignal(str)

    def sendDownload(self, song_list):
        reactor.callFromThread(server.Server.sendSongList, self.server_factory.connectedProtocol, song_list)

    def run(self):
        send_file = open("library.json", "rb").read()
        endpoint = TCP4ServerEndpoint(reactor, 8420)
        self.server_factory = server.ServerFactory(send_file)
        endpoint.listen(self.server_factory)
        self.server_factory.emitter.signal.connect(lambda x: self.communicator.emit(x))
        reactor.run(installSignalHandlers=False)

class ClientWorker(QtCore.QObject):
    communicator = QtCore.pyqtSignal(str)

    def __init__(self, i):
        super(QtCore.QObject, self).__init__()
        self.ip = i

    def sendDownload(self, song_list):
        reactor.callFromThread(client.Client.sendSongList, self.client, song_list)

    def run(self):
        point = TCP4ClientEndpoint(reactor, self.ip, 8420)
        self.client = client.Client()
        self.client.emitter.signal.connect(lambda x: self.communicator.emit(x))
        d = connectProtocol(point, self.client)
        reactor.run(installSignalHandlers=False)

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
        path_split = path.split("\\" if platform.system() == "Windows" else "/") # TODO: allow Unix paths
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
    download_signal = QtCore.pyqtSignal()

    def displaySongs(self):
        loc_lib = json.loads(open("library.json", "r").read())
        ext_lib = json.loads(open("ext_lib.json", "r").read())

        common_path = library.find_library_path([ext_lib[key] for key in ext_lib])

        compare = library.compare_hash_libs(loc_lib, ext_lib)
        for key in compare[2]:
            self.root.insert(compare[2][key][len(common_path)+1:])

        for item in self.root.children:
            self.createNode(item, self.tree)

        self.download_button.setEnabled(True)

    def handleEmit(self, emit):
        if emit == "connected-server":
            self.status_message.setText("Connected to client.")
        elif emit == "connected-client":
            self.status_message.setText("Connected to server.")
        elif emit == "data-received":
            self.status_message.setText("Receiving data...")
        elif emit == "comparing":
            self.status_message.setText("Validating libraries...")
        elif emit == "compare-success":
            self.status_message.setText("Library validation successful!")
            self.displaySongs()
        elif emit == "compare-failure":
            self.status_message.setText("Library validation unsuccessful.")
        elif emit == "identical":
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Library Message")
            popup.setText("You have identical libraries!")
            popup.exec()
        elif emit == "terminated":
            self.status_message.setText("Connection terminated.")
            self.download_button.setEnabled(False) # TODO: also turn on/off connect/start server buttons as needed
        elif emit == "server-received-list":
            self.hasReceivedFileList = True
            self.download_signal.emit()
        elif emit == "create-archive":
            self.status_message.setText("Creating archive...")
        elif emit == "sending-archive":
            self.status_message.setText("Uploading songs...")
        elif emit == "receiving-archive":
            self.status_message.setText("Receiving songs...")
        elif emit == "extracting":
            self.status_message.setText("Extracting to library...")
        elif emit == "extraction-complete":
            self.status_message.setText("Complete!")
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("{} Message".format("Server" if self.runningServer else "Client"))
            popup.setText("Download Complete!")
            popup.setInformativeText("You may now scan your library in Clone Hero. Rock on!")
            popup.exec()

    def downloadButtonPushed(self):
        ext_lib = json.loads(open("ext_lib.json", "r").read())
        self.button_paths = []
        for widget in self.buttons_list:
            if widget.checkState(0) == 2:
                for key in ext_lib:
                    if widget.text(0) in ext_lib[key]:
                        self.button_paths.append(ext_lib[key])
        self.download_button.setEnabled(False)
        self.download_button.setText("Waiting...")

        if self.runningClient:
            self.client_worker.sendDownload({"list": self.button_paths})
        elif self.runningServer:
            if self.hasReceivedFileList:
                self.server_worker.sendDownload({"list": self.button_paths})
            self.download_signal.connect(lambda: self.server_worker.sendDownload({"list": self.button_paths})) # Might need to be moved?

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
            self.status_message.setText("Server idle.")
            self.server_thread = QtCore.QThread()
            self.server_worker = ServerWorker()
            self.server_worker.moveToThread(self.server_thread)

            self.server_worker.communicator.connect(lambda x: self.handleEmit(x))
            self.server_thread.started.connect(self.server_worker.run)
            self.server_thread.start()

            self.runningServer = True

    def clientButtonPushed(self):
        canStart = True
        for c in self.ip_text_box.text():
            if not c.isdigit() and c != ".":
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

                self.client_worker.communicator.connect(lambda x: self.handleEmit(x))
                self.client_thread.started.connect(self.client_worker.run)
                self.client_thread.start()

                self.runningClient = True
        else:
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Client Message")
            popup.setText("You must enter a valid IP.")
            popup.exec()

    def parseButtonPushed(self):
        parseLib = True

        if not os.path.exists(self.library_path_box.text()):
            popup = QtWidgets.QMessageBox()
            popup.setWindowTitle("Library Parse")
            popup.setText("Invalid Path")
            popup.setInformativeText("I was unable to find the path you specified. Please enter a valid path.")
            popup.setIcon(QtWidgets.QMessageBox.Warning)
            popup.exec()
            return False

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

        self.runningServer = False
        self.runningClient = False

        self.hasReceivedFileList = False

        if os.path.exists("ext_lib.json"):
            print("Pre-existing ext_lib.json found. Removing...")
            os.remove("ext_lib.json")
        if os.path.exists("compare_lib.json"):
            print("Pre-existing compare_lib.json found. Removing...")
            os.remove("compare_lib.json")
        if os.path.exists("song_list_dic.json"):
            print("Pre-existing song_list_dic.json found. Removing...")
            os.remove("song_list_dic.json")
        if os.path.exists("send_songs.7z"):
            print("Pre-existing send_songs.7z found. Removing...")
            os.remove("send_songs.7z")
        if os.path.exists("receive_songs.7z"):
            print("Pre-existing receive_songs.7z found. Removing...")
            os.remove("receive_songs.7z")

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
        self.buttons_list = []

        treeLayout = QtWidgets.QVBoxLayout(self)
        treeLayout.addWidget(self.tree)

        self.download_button = QtWidgets.QPushButton("Download")
        self.download_button.clicked.connect(self.downloadButtonPushed)
        self.download_button.setEnabled(False)
        middleLayout = QtWidgets.QHBoxLayout(self)
        middleLayout.addWidget(self.download_button)

        self.ip_text_box = QtWidgets.QLineEdit()
        self.ip_text_box.setPlaceholderText("Enter IP here...")
        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setEnabled(False)
        self.connect_button.clicked.connect(self.clientButtonPushed)
        self.ip_text_box.textChanged.connect(lambda: self.connect_button.setEnabled(True) if (self.ip_text_box.text() != "") else (self.connect_button.setEnabled(False)))
        self.server_button = QtWidgets.QPushButton("Start Server")
        self.server_button.clicked.connect(self.serverButtonPushed)
        self.status_message = QtWidgets.QLabel("")
        self.status_message.setFixedSize(150, 20)
        lowerLayout = QtWidgets.QHBoxLayout(self)
        lowerLayout.addWidget(self.ip_text_box)
        lowerLayout.addWidget(self.connect_button)
        lowerLayout.addWidget(self.server_button)
        lowerLayout.addWidget(self.connect_button)
        lowerLayout.addWidget(self.status_message)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(treeLayout)
        mainLayout.addLayout(middleLayout)
        mainLayout.addLayout(lowerLayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
