from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

import os
import sys
import json

import library

class TestServ(Protocol):
    def connectionMade(self):
        self.transport.write("Hello, this is a client!\r\n".encode('utf-8'))
        #self.transport.loseConnection()
    def dataReceived(self, data):
        print("Data received.")
        if data.decode('utf-8')[-4:] == '\r\n\r\n':
            print("End of file received.")
            save_file = open("compare_lib.json", "a")
            save_file.write(data.decode('utf-8')[:-4]) # Write the last received data batch minus EOF
            save_file.close()
            self.transport.loseConnection()
            reactor.stop() # Close server connection to move on
        else:
            save_file = open("compare_lib.json", "ab")
            save_file.write(data)
            save_file.close()

############################################################

if os.path.exists("compare_lib.json"):
    print("Pre-existing compare_lib.json found. Removing...")
    os.remove("compare_lib.json")

point = TCP4ClientEndpoint(reactor, sys.argv[1], 8420)
d = connectProtocol(point, TestServ())
reactor.run()

############################################################

loc_lib = library.parse_library(sys.argv[2])
ext_lib = json.loads(open("compare_lib.json", "r", encoding="utf-8").read())
compare = library.compare_libs(loc_lib, ext_lib)

if (len(compare[1]) == 0) and (len(compare[2]) == 0):
    print("Your libraries are completely identical!")
else:
    print("There are a total of {} songs in common between the two libraries.".format(len(compare[1])))
    print("There are {0} songs in your library that are not in theirs, and {1} songs in their library that are not in yours.".format(len(compare[1]), len(compare[2])))
