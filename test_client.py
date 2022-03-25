from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from PyQt5.QtCore import QObject, pyqtSignal

import os, sys, json

import library

class Signaler(QObject):
    signal = pyqtSignal(str)

    def run(self, string):
        self.signal.emit(string)

class TestServ(Protocol):
    def __init__(self):
        self.emitter = Signaler()

    def validateLibs(self, c):
        self.transport.write("{}\r\n\r\n".format(len(c[0])).encode("utf-8"))
        local_lib = open("library.json", "rb").read()
        self.transport.write(local_lib)
        self.transport.write("\r\n\r\n".encode("utf-8"))

    def compareLibs(self):
        self.emitter.run("comparing")
        loc_lib = json.loads(open("library.json", "r", encoding="utf-8").read())

        ext_lib = json.loads(open("ext_lib.json", "r", encoding="utf-8").read())
        compare = library.compare_hash_libs(loc_lib, ext_lib)

        self.state = "validating"
        if (len(compare[1]) == 0) and (len(compare[2]) == 0):
            self.emitter.run("identical")
            print("Your libraries are completely identical!")
        else:
            self.emitter.run("compare-success") # TODO: will need to move this when server validates amount with client in future
            print("There are a total of {} songs in common between the two libraries.".format(len(compare[0])))
            print("There are {0} songs in your library that are not in theirs, and {1} songs in their library that are not in yours.".format(len(compare[1]), len(compare[2])))

        self.validateLibs(compare)

    def connectionMade(self):
        self.emitter.run("connected-client")
        print("Connection to server established.")
        self.state = "downloading"
        #self.transport.loseConnection()

    def dataReceived(self, data):
        print("Data received.")
        self.emitter.run("data-received")
        if self.state == "downloading":
            if data.decode('utf-8')[-4:] == '\r\n\r\n':
                print("End of file received.")
                save_file = open("ext_lib.json", "a")
                save_file.write(data.decode('utf-8')[:-4]) # Write the last received data batch minus EOF
                save_file.close()
                self.state = "comparing"
                self.compareLibs()
                #self.transport.loseConnection()
                #reactor.stop() # Close server connection to move on
            else:
                save_file = open("ext_lib.json", "ab")
                save_file.write(data)
                save_file.close()
        elif self.state == "validating":
            print() # TODO: complete

############################################################

def main():
    if os.path.exists("ext_lib.json"):
        print("Pre-existing ext_lib.json found. Removing...")
        os.remove("ext_lib.json")

    if os.path.exists("local_lib.json"):
        print("Pre-existing local_lib.json found. Removing...")
        os.remove("local_lib.json")

    point = TCP4ClientEndpoint(reactor, sys.argv[1], 8420)
    d = connectProtocol(point, TestServ())
    reactor.run()

############################################################
