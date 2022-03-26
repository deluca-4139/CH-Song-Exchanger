from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

from PyQt5.QtCore import QObject, pyqtSignal

import os, sys, json, py7zr

import library

class Signaler(QObject):
    signal = pyqtSignal(str)

    def run(self, string):
        self.signal.emit(string)

class Test(Protocol):
    def sendSongs(self):
        songs_list = json.loads(open("song_list_dic.json", "r", encoding="utf-8").read())
        print(songs_list["list"])

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

    def compareLibs(self):
        self.factory.emitter.run("comparing")
        print("Comparing libraries and validating data...")
        loc_lib = json.loads(open("library.json", "r", encoding='utf-8').read())
        ext_lib = json.loads(open("ext_lib.json", "r", encoding='utf-8').read())
        compare = library.compare_hash_libs(loc_lib, ext_lib)

        if (len(compare[1]) == 0) and (len(compare[2]) == 0):
            self.factory.emitter.run("identical")
        if len(compare[0]) == int(self.shared_songs):
            print("Success! I agree with the client that you share {} songs in common.".format(self.shared_songs))
            self.factory.emitter.run("compare-success")
            self.transport.write("success\r\n\r\n".encode("utf-8"))
            self.state = "wait-user-1" # TODO: edit depending on workflow
        else:
            print("Something went wrong; I calculated {} shared songs in common, while the client calculated {} songs.".format(len(compare[0]), self.shared_songs))
            self.factory.emitter.run("compare-failure")

    def connectionMade(self):
        self.factory.emitter.run("connected")
        print("Connection made")
        self.transport.write(self.factory.file_to_send)
        self.transport.write("\r\n\r\n".encode("utf-8"))
        self.state = "validating"
        #self.transport.loseConnection()

    def dataReceived(self, data):
        self.factory.emitter.run("data-received")
        print("Data received")
        if self.state == "validating":
            index = 0
            while data.decode("utf-8")[index:(index+4)] != "\r\n\r\n":
                index += 1
            self.shared_songs = data.decode('utf-8')[0:index]
            ext_lib = open("ext_lib.json", "a")
            if data.decode('utf-8')[-4:] == '\r\n\r\n':
                ext_lib = open("ext_lib.json", "a")
                ext_lib.write(data.decode('utf-8')[index+4:-4])
                ext_lib.close()
                self.state = "comparing"
                self.compareLibs()
            else:
                ext_lib.write(data.decode('utf-8')[(index+4):])
                ext_lib.close()
                self.state = "receiving"
        elif self.state == "receiving":
            if data.decode('utf-8')[-4:] == '\r\n\r\n':
                ext_lib = open("ext_lib.json", "a")
                ext_lib.write(data.decode('utf-8')[:-4])
                ext_lib.close()
                self.state = "comparing"
                self.compareLibs()
            else:
                ext_lib = open("ext_lib.json", "ab")
                ext_lib.write(data)
                ext_lib.close()
        elif self.state == "wait-user-1":
            if data.decode("utf-8")[-4:] == '\r\n\r\n':
                song_list_dic = open("song_list_dic.json", "a")
                song_list_dic.write(data.decode("utf-8")[:-4])
                song_list_dic.close()
                #self.state = "" # TODO: change
                self.factory.emitter.run("server-received-list")
                self.sendSongs()
            else:
                song_list_dic = open("song_list_dic.json", "ab")
                song_list_dic.write(data)
                song_list_dic.close()

    def connectionLost(self, reason):
        self.factory.emitter.run("terminated")
        print("Connection to client terminated.")

class TestFactory(Factory):
    protocol = Test

    def __init__(self, f):
        self.emitter = Signaler()
        self.file_to_send = f

############################################################

def main():
    parseLib = True

    if os.path.exists("ext_lib.json"):
        print("Pre-existing ext_lib.json found. Removing...")
        os.remove("ext_lib.json")

    if os.path.exists("library.json"):
        answer = input("library.json already exists. Re-parse? (Y/N)")
        if answer.lower() == "n":
            parseLib = False
        elif answer.lower() == "y":
            print("Removing existing library...")
            os.remove("library.json")
    if parseLib:
        print("Parsing song library...")
        songs = library.parse_library_hash(sys.argv[1])

        json_file = open("library.json", "w")
        json.dump(songs, json_file)
        json_file.close()

        print("Parsing complete.")
        print()
    else:
        print("Continuing with pre-existing parsed library...")
        print()

    print("Opening TCP server...")
    send_file = open("library.json", "rb").read()
    endpoint = TCP4ServerEndpoint(reactor, 8420)
    endpoint.listen(TestFactory(send_file))
    reactor.run()
