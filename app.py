from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.Qt import Qt
import sys, json

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


class Form(QtWidgets.QDialog):
    def buttonPushed(self):
        print("Buttons that are selected:")
        for widget in self.buttons_list:
            if widget.checkState(0) == 2:
                print(widget.text(0))

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
        super(Form, self).__init__(parent)

        self.tree = QtWidgets.QTreeWidget()
        self.headerItem = QtWidgets.QTreeWidgetItem()
        self.item = QtWidgets.QTreeWidgetItem()
        self.button = QtWidgets.QPushButton("Click Me")
        self.button.clicked.connect(self.buttonPushed)

        self.root = Node("root")
        ext_lib = json.loads(open("ext_lib.json", "r").read())
        for key in ext_lib:
            self.root.insert(ext_lib[key])

        self.buttons_list = []

        for item in self.root.children:
            self.createNode(item, self.tree)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tree)
        layout.addWidget(self.button)
        self.setLayout(layout)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    form = Form()
    form.show()
    sys.exit(app.exec())
