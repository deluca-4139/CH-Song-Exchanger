from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

import os
import sys
import json

import library

class TestServ(Protocol):
    def validateLibs(self, c):
        self.transport.write("{}\r\n\r\n".format(len(c[0])).encode("utf-8"))
        local_lib = open("library.json", "rb").read()
        self.transport.write(local_lib)
        self.transport.write("\r\n\r\n".encode("utf-8"))

    def compareLibs(self):
        #loc_lib = library.parse_library_hash(sys.argv[2])
        #lib_file = open("library.json", "w")
        #json.dump(loc_lib, lib_file)
        #lib_file.close()
        loc_lib = json.loads(open("library.json", "r", encoding="utf-8").read())

        ext_lib = json.loads(open("compare_lib.json", "r", encoding="utf-8").read())
        compare = library.compare_hash_libs(loc_lib, ext_lib)

        self.state = "validating"
        if (len(compare[1]) == 0) and (len(compare[2]) == 0):
            print("Your libraries are completely identical!")
        else:
            print("There are a total of {} songs in common between the two libraries.".format(len(compare[0])))
            print("There are {0} songs in your library that are not in theirs, and {1} songs in their library that are not in yours.".format(len(compare[1]), len(compare[2])))

        self.validateLibs(compare)

    def connectionMade(self):
        print("Connection to server established.")
        self.state = "downloading"
        #self.transport.loseConnection()

    def dataReceived(self, data):
        print("Data received.")
        if self.state == "downloading":
            if data.decode('utf-8')[-4:] == '\r\n\r\n':
                print("End of file received.")
                save_file = open("compare_lib.json", "a")
                save_file.write(data.decode('utf-8')[:-4]) # Write the last received data batch minus EOF
                save_file.close()
                self.state = "comparing"
                self.compareLibs()
                #self.transport.loseConnection()
                #reactor.stop() # Close server connection to move on
            else:
                save_file = open("compare_lib.json", "ab")
                save_file.write(data)
                save_file.close()
        elif self.state == "validating":
            print() # TODO: complete

############################################################

def main():
    if os.path.exists("compare_lib.json"):
        print("Pre-existing compare_lib.json found. Removing...")
        os.remove("compare_lib.json")

    if os.path.exists("local_lib.json"):
        print("Pre-existing local_lib.json found. Removing...")
        os.remove("local_lib.json")

    point = TCP4ClientEndpoint(reactor, sys.argv[1], 8420)
    d = connectProtocol(point, TestServ())
    reactor.run()

############################################################
