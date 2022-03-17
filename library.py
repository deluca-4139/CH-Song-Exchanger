import os
import configparser

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

def parse_library(path):
    songs_found = 0
    songs = {}
    for root, dirs, files, in os.walk(path):
        for name in files:
            song_entry = root.split("\\")[-1]
            if name == "song.ini":
                song_parse = parseINI((root + "\\" + name))
                if song_parse is not None:
                    # TODO: change dictionary entry formatting to
                    # allow for multiple versions of the same song
                    if song_entry in songs:
                        print("Duplicate song entry found for {}.".format(song_entry))
                    songs[song_entry] = song_parse
                    songs_found += 1

    print("Found {} total songs.".format(songs_found))
    return songs
