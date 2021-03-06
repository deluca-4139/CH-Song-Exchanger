import os
import hashlib

# TODO: allow for both Unix and Win paths
def parse_library_hash(path):
    songs_found = 0
    songs = {}
    for root, dirs, files in os.walk(path):
        for name in files:
            song_entry = root[(len(path)+1):] # Unix path might need edit?
            if name == "notes.chart" or name == "notes.mid":
                chart_file = open((root + "\\" + name), "rb").read()
                chart_hash = hashlib.md5(chart_file).hexdigest()
                if chart_hash in songs:
                    print("Duplicate hash found for {}.".format(song_entry))
                songs[chart_hash] = root
                songs_found += 1
    print("Found {} total songs.".format(songs_found))
    return songs

def compare_hash_libs(lib1, lib2):
    songs_in_common = []
    in1not2 = {}
    in2not1 = {}

    for song in lib1:
        if song in lib2:
            songs_in_common.append(song)
        else:
            in1not2[song] = lib1[song]
    for song in lib2:
        if song not in lib1:
            in2not1[song] = lib2[song]

    return (songs_in_common, in1not2, in2not1)

# This function might assume that a user has
# at least one song in their library...
def find_library_path(song_list):
    pathFound = False
    index = 0
    test_path = song_list[0]
    while not pathFound:
        index += 1
        try:
            while test_path[index] != "\\": # TODO: allow for Unix paths
                index += 1
        except IndexError:
            pathFound = True
        for song in song_list:
            if test_path[:index] not in song:
                pathFound = True
    index -= 1
    while test_path[index] != "\\": # TODO: allow for Unix paths
        index -=1
    return test_path[:index]
