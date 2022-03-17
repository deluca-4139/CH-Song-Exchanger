from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

class TestServ(Protocol):
    def connectionMade(self):
        self.transport.write("Hello, this is a client!\r\n".encode('utf-8'))
        #self.transport.loseConnection()
    def dataReceived(self, data):
        print("Data received.")
        save_file = open("test.txt", "wb")
        save_file.write(data)
        save_file.close()

point = TCP4ClientEndpoint(reactor, "localhost", 8420)
d = connectProtocol(point, TestServ())
reactor.run()
