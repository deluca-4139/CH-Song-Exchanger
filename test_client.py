from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from PyQt5.QtCore import QObject, pyqtSignal

import os, sys, json, py7zr

import library

class Signaler(QObject):
    signal = pyqtSignal(str)

    def run(self, string):
        self.signal.emit(string)

class TestServ(Protocol):
    def __init__(self):
        self.emitter = Signaler()

    def sendSongList(self, song_list):
        self.transport.write("{}\r\n\r\n".format(json.dumps(song_list)).encode("utf-8"))
        self.state = "receiving-songs"

    def sendSongs(self):
        print("Reached client.sendSongs().")

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
            print("There are a total of {} songs in common between the two libraries.".format(len(compare[0])))
            print("There are {0} songs in your library that are not in theirs, and {1} songs in their library that are not in yours.".format(len(compare[1]), len(compare[2])))

        self.validateLibs(compare)

    def connectionMade(self):
        self.emitter.run("connected-client")
        print("Connection to server established.")
        self.state = "downloading"
        #self.transport.loseConnection()

    def connectionLost(self, reason):
        self.emitter.run("terminated")
        print("Connection to server terminated.")

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
            if data.decode("utf-8") == "success\r\n\r\n":
                self.emitter.run("compare-success")
                print("Success! The server agrees with my assessment of our libraries.")
                self.state = "wait-user-1" # TODO: edit depending on workflow
            elif data.decode("utf-8") == "failure\r\n\r\n":
                self.emitter.run("compare-failure")
                print("The server's assessment of our libraries did not match my own.")
                self.state = "compare-fail" # Might need to flesh out in the future
        elif self.state == "receiving-songs":
            if data.decode('utf-8')[-4:] == '\r\n\r\n':
                print("End of file received.")
                save_file = open("receive_songs.7z", "a")
                save_file.write(data.decode('utf-8')[:-4])
                save_file.close()
                self.state = "sending-songs" # ?
                self.sendSongs()
            else:
                save_file = open("receive_songs.7z", "ab")
                save_file.write(data)
                save_file.close()


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
