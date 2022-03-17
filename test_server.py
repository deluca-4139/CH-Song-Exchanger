from twisted.internet.protocol import Factory, Protocol
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor

import sys
import os
import configparser

class Test(Protocol):
    def connectionMade(self):
        print("Connection made")
        self.transport.write(self.factory.file_to_send)
        #self.transport.loseConnection()
    def dataReceived(self, data):
        print("Data received")
        print(data)

class TestFactory(Factory):
    protocol = Test

    def __init__(self, f):
        self.file_to_send = f

'''
send_file = open("test.txt", "rb").read()
endpoint = TCP4ServerEndpoint(reactor, 8420)
endpoint.listen(TestFactory(send_file))
reactor.run()
'''

def parseINI(f=None):
    # Strict might end up causing problems in the future, but
    # it's needed to deal with duplicate keys in .ini files
    # Interpolation raises issues when dealing with special
    # characters within the .ini files, which we can't control
    iniReader = configparser.ConfigParser(strict=False, interpolation=None)
    try:
        iniReader.read(f, encoding='utf-8-sig') # account for BOM
    except UnicodeDecodeError:
        iniReader.read(f, encoding="utf-16") # if UTF-8 fails, use 16
    except configparser.ParsingError:
        print("Error parsing {}; maybe there's a blank key?".format(f))
        return None

    songDict = {}

    # Have to do this bullshit because
    # people aren't consistent
    items = []
    for x in iniReader:
        items.append(x)

    for entry in iniReader[items[1]]:
        songDict[entry] = iniReader[items[1]][entry]
    return songDict

songs_found = 0
songs = {}
for root, dirs, files, in os.walk(sys.argv[1]):
    for name in files:
        song_entry = root.split("\\")[-1]
        if name == "song.ini":
            song_parse = parseINI((root + "\\" + name))
            if song_parse is not None:
                songs[song_entry] = song_parse # Should probably double check to make sure this isn't overwriting existing dictionary entries
                songs_found += 1

print("Found {} total songs.".format(songs_found))
