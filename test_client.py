from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

import os

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

point = TCP4ClientEndpoint(reactor, "localhost", 8420)
d = connectProtocol(point, TestServ())
reactor.run()
