from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import sys
import json
import os

import library

class Test(Protocol):
    def compareLibs(self):
        print("Comparing libraries and validating data...")
        loc_lib = json.loads(open("library.json", "r", encoding='utf-8').read())
        ext_lib = json.loads(open("ext_lib.json", "r", encoding='utf-8').read())
        compare = library.compare_hash_libs(loc_lib, ext_lib)

        if len(compare[0]) == int(self.shared_songs):
            print("Success! I agree with the client that you share {} songs in common.".format(self.shared_songs))
        else:
            print("Something went wrong; I calculated {} shared songs in common, while the client calculated {} songs.".format(len(compare[0]), self.shared_songs))

    def connectionMade(self):
        print("Connection made")
        self.transport.write(self.factory.file_to_send)
        self.transport.write("\r\n\r\n".encode("utf-8"))
        self.state = "validating"
        #self.transport.loseConnection()

    def dataReceived(self, data):
        print("Data received")
        if self.state == "validating":
            index = 0
            while data.decode("utf-8")[index:(index+4)] != "\r\n\r\n":
                index += 1
            self.shared_songs = data.decode('utf-8')[0:index]
            ext_lib = open("ext_lib.json", "a")
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

    def connectionLost(self, reason):
        print("Connection to client terminated.")

class TestFactory(Factory):
    protocol = Test

    def __init__(self, f):
        self.file_to_send = f

############################################################

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
