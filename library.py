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
        try:
            iniReader.read(f, encoding="utf-16") # if UTF-8 fails, use 16
        except UnicodeDecodeError:
            print("Error parsing {}; I was unable to decode using UTF-8 or 16. Maybe corrupted?".format(f))
            return None
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
    for root, dirs, files in os.walk(path):
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

def compare_libs(lib1, lib2):
    songs_in_common = []
    in1not2 = []
    in2not1 = []

    for song in lib1:
        if song in lib2:
            song_identical = True
            # Check each .ini field to confirm
            # song versions are the same.
            for item in lib1[song]:
                try:
                    if lib1[song][item] != lib2[song][item]:
                        song_identical = False
                except KeyError:
                    print("Key error when searching for {0} and {1}.".format(song, item))
                    song_identical = False # TODO: figure out a more elegant solution to this
            if song_identical:
                songs_in_common.append(song)
            else:
                print("Songs not identical.") # TODO: complete
        else:
            in1not2.append(song)

    for song in lib2:
        if song not in songs_in_common:
            in2not1.append(song)

    return (songs_in_common, in1not2, in2not1)
