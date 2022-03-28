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

class Client(Protocol):
    def __init__(self):
        self.emitter = Signaler()

    def unzipLibrary(self):
        lib = json.loads(open("library.json", "r").read())
        library_path = library.find_library_path([lib[key] for key in lib])
        if not os.path.isdir(library_path + "\\CH-X"): # TODO: allow for Unix paths
            os.mkdir(library_path + "\\CH-X")
        with py7zr.SevenZipFile("receive_songs.7z", "r") as archive:
            archive.extractall(library_path + "\\CH-X")
        os.remove("ext_lib.json")
        os.remove("song_list_dic.json")
        os.remove("send_songs.7z")
        os.remove("receive_songs.7z")
        print("Extraction complete.")
        self.emitter.run("extraction-complete")

    def sendSongList(self, song_list):
        self.transport.write("{}\r\n\r\n".format(json.dumps(song_list)).encode("utf-8"))
        self.finishedReceiving = False
        self.state = "receiving-songs-list"

    def sendSongs(self):
        songs_list = json.loads(open("song_list_dic.json", "r", encoding="utf-8").read())

        print("Creating archive...")
        with py7zr.SevenZipFile("send_songs.7z", "w") as archive:
            for song_path in songs_list["list"]:
                index = len(song_path) - 1
                while song_path[index] != "\\": # TODO: allow for Unix paths
                    index -= 1
                archive.writeall(song_path, song_path[index+1:])

        send_file = open("send_songs.7z", "rb").read()
        self.transport.write(send_file)
        self.transport.write("\r\n\r\n".encode("utf-8"))
        self.state = "receiving-songs"

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
        elif self.state == "receiving-songs-list":
            if data.decode("utf-8")[-4:] == '\r\n\r\n':
                song_list_dic = open("song_list_dic.json", "a")
                song_list_dic.write(data.decode("utf-8")[:-4])
                song_list_dic.close()
                #self.state = "" # TODO: change
                #self.factory.emitter.run("client-received-list")
                self.sendSongs()
            else:
                song_list_dic = open("song_list_dic.json", "ab")
                song_list_dic.write(data)
                song_list_dic.close()
        elif self.state == "receiving-songs":
            save_file = open("receive_songs.7z", "ab")
            save_file.write(data)
            save_file.close()
            try:
                test_file = py7zr.SevenZipFile("receive_songs.7z", "r")
                test_file.close()
            except py7zr.exceptions.Bad7zFile:
                print("Receiving song archive...")
            else:
                self.finishedReceiving = True
            finally:
                if self.finishedReceiving:
                    self.unzipLibrary()



############################################################

def main():
    if os.path.exists("ext_lib.json"):
        print("Pre-existing ext_lib.json found. Removing...")
        os.remove("ext_lib.json")

    if os.path.exists("local_lib.json"):
        print("Pre-existing local_lib.json found. Removing...")
        os.remove("local_lib.json")

    point = TCP4ClientEndpoint(reactor, sys.argv[1], 8420)
    d = connectProtocol(point, Client())
    reactor.run()

############################################################
