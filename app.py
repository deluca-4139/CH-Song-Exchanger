from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
import sys, json
from time import sleep # TODO: remove

import library

class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()

    def __init__(self, path):
        super(QtCore.QObject, self).__init__()
        self.library_path = path

    def run(self):
        parsed_library = library.parse_library_hash(self.library_path)
        self.finished.emit()

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

    def parseButtonPushed(self):
        print("Parsing given path...")
        self.parse_status_text.setText("Parsing...")

        self.thread = QtCore.QThread()
        self.worker = Worker(self.library_path_box.text())
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(lambda: print("Finished parsing!"))
        self.worker.finished.connect(lambda: self.parse_status_text.setText("Finished!"))
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

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

        self.library_path_box = QtWidgets.QLineEdit("Enter song library path here...")
        self.parse_library_button = QtWidgets.QPushButton("Parse Library")
        self.parse_library_button.clicked.connect(self.parseButtonPushed)
        self.parse_status_text = QtWidgets.QLabel("Enter path and click parse.")
        self.parse_status_text.setFixedSize(150, 20)

        topLayout = QtWidgets.QHBoxLayout(self)
        topLayout.addWidget(self.library_path_box)
        topLayout.addWidget(self.parse_library_button)
        topLayout.addWidget(self.parse_status_text)

        self.tree = QtWidgets.QTreeWidget()
        self.button = QtWidgets.QPushButton("Click Me")
        self.button.clicked.connect(self.buttonPushed)

        self.root = Node("root")
        ext_lib = json.loads(open("library.json", "r").read()) # rename
        for key in ext_lib:
            self.root.insert(ext_lib[key])

        self.buttons_list = []

        for item in self.root.children:
            self.createNode(item, self.tree)

        treeLayout = QtWidgets.QVBoxLayout(self)
        treeLayout.addWidget(self.tree)
        treeLayout.addWidget(self.button)

        mainLayout = QtWidgets.QVBoxLayout(self)
        mainLayout.addLayout(topLayout)
        mainLayout.addLayout(treeLayout)

        widget = QtWidgets.QWidget()
        widget.setLayout(mainLayout)
        self.setCentralWidget(widget)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = Window()
    window.show()
    sys.exit(app.exec())
