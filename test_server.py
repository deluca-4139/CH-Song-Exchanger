from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import sys
import json
import os

import library

class Test(Protocol):
    def connectionMade(self):
        print("Connection made")
        self.transport.write(self.factory.file_to_send)
        self.transport.write("\r\n\r\n".encode("utf-8"))
        #self.transport.loseConnection()
    def dataReceived(self, data):
        print("Data received")
        print(data)
    def connectionLost(self, reason):
        print("Connection to client terminated.")

class TestFactory(Factory):
    protocol = Test

    def __init__(self, f):
        self.file_to_send = f

############################################################

if not os.path.exists("library.json"):
    print("Parsing song library...")
    songs = library.parse_library(sys.argv[1])

    json_file = open("library.json", "w")
    json.dump(songs, json_file)
    json_file.close()

    print("Parsing complete.")
    print()
else:
    print("library.json already exists. Continuing with pre-existing parsed library...")
    print()

print("Opening TCP server...")
send_file = open("library.json", "rb").read()
endpoint = TCP4ServerEndpoint(reactor, 8420)
endpoint.listen(TestFactory(send_file))
reactor.run()
