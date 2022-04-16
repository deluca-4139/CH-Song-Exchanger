# Clone Hero Song Exchanger

Everyone who's played Clone Hero Online knows this struggle:

> A: "Hey, do you have {insert song here}? It's one of my favorites."
>
> B: "Oh shoot, I don't think I have that one..."
>
> A: "Darn... how about {insert other song here}?"
>
> B: "Nope, not that one..."

With the way that CH Online works, you must both have access to a song's chart if you want to play it; but trying to have your friend download a bunch of songs that you want to play can be annoying, and take up a lot of time trying to figure out where you got all of those charts from. That's where **Clone Hero Song Exchanger** comes in!

*CH-X* allows you to connect directly with your friend, sync your libraries, and determine which songs you are both missing from the other's library. You can then select which songs you want to download from an easy to navigate display, and then download them straight from your friend! No more endless scrolling through Chorus or zipping up songs to send through Discord; *CH-X* handles it all for you.  

## Disclaimer

CH-X currently operates on an entirely peer-to-peer (P2P) basis. This means that the client connects directly to the server through a TCP connection facilitated by the Python networking library Twisted. There are two major things to note about this:

1. The __security__ of this application is entirely based upon the users. I can make no guarantee that you will not send or receive malicious data. Since this is an open-source project, you can look through the code to make sure that I (the programmer) have not included anything malicious within it, but it is up to the user to stay safe when connecting to others and opening up their network for connecting. If you're curious, read on for more information about how specifically CH-X handles song libraries.

2. The __speed__ of this application *also* depends on the users. As the connection you are making is P2P - and everyone has differently capable computer setups - the speed at which the archives are created and downloaded could be very slow. I will try my best to improve the speed of the program on the backend as much as possible, but of course I cannot provide a magic bullet that will cause users' computers and networks to perform faster.

With that out of the way, let's get to rockin'!

## Installation

If you have Python installed, running CH-X is as simple as `clone`ing or downloading/extracting this repository and running

```
py .\app.py
```

if you're on a Windows system, or

```
python app.py
```

if you're on a Unix system (Mac/Linux). **(Support for Mac/Linux systems is currently in testing. For those on those systems, download the executables from the latest pre-release!)** Make sure you've installed all of the dependencies listed below, either with `pip install` or `py -m pip install`.

You can also download the latest build from the sidebar of the repository, which should contain an executable built with `pyinstaller`. Just download and run the executable/binary for your relevant system.

### Dependencies:
* `twisted`
* `json`
* `PyQt5`
* `py7zr`

## Usage

Using CH-X is also very simple:

0. One person must be the server, and the other the client. The server must port forward to allow the client to connect; at the moment, CH-X uses port 8420, but I plan to have it be customizable in the future. In theory, tunneling applications like Hamachi *should* work, but I have not tested them myself. Please let me know if you give them a shot!

1. Start up CH-X either from the command line as detailed above, or by launching the executable.

2. If this is your first time running CH-X, you should enter the path to your song library in the top text box and hit the "Parse Library" button. CH-X will go through your song library in the background, taking note of all of the songs in it, and let you know when it's done. If you've changed your song library since the last time you used CH-X, you can re-parse by following the same instructions, and clicking "Yes" on the pop-up window that prompts if you'd like to re-parse. Please note that **you must parse your library before starting a server or attempting to connect to one.** CH-X *will not* allow you to do either of these things if it does not detect a parsed library.

3. Once you've parsed your library, the server should click the "Start Server" button. Once the server has been started, the client can enter the public IP address of the server and click the "Connect" button. CH-X will exchange song libraries in the background, and update its display when it has finished.

4. After a connection has been established, CH-X will show you a tree display containing all of the songs in the other person's library that are not in yours. You can click on the checkbox next to any of the songs/folders you would like to mark them for download. Once you have finished deciding which songs you would like to receive, click the "Download" button.

5. Once both the server and the client have clicked the "Download" button, exchanging of the songs will begin in the background. Please be patient as this process continues; closing the application or breaking the network connection will cause the transfer to fail.

6. Once all songs have been exchanged, CH-X will extract them directly to your song library and create a popup notifying you of its completion. You are now free to close the application, re-scan your songs in Clone Hero, and rock on!

## Questions/Notes/Etc

#### "How does CH-X exchange songs over the internet? I want to know what's going on before I use it."

Sure, I totally get it.

CH-X uses the Python networking library [Twisted](https://github.com/twisted/twisted) to create and manage TCP connections. The server and the client are both spawned in a separate thread from the main thread, as the main thread is running the PyQt5 GUI. Signals within the server/client running in the thread are used to update the UI based on the status of the process(es) going on behind the scenes.

When CH-X parses your song library, it takes the path that you give it and loops recursively through all of the subdirectories within that path, just as Clone Hero itself would. It's looking for any folder containing a `notes.chart` or `notes.mid` file; if it finds one, it takes the MD5 hash of the chart file and adds it to a *dictionary* containing your entire song library, along with the path it found the song in. This dictionary is then saved in a JSON file called `library.json`, which you can look at in the directory that CH-X is in.

When CH-X compares song libraries, it first sends across its connection the `library.json` files of the two user's respective libraries. Those libraries are compared locally on each end by going through each dictionary and checking each hash to see if it exists in the other dictionary. If it does, it's logged as a common song, and if it doesn't, it's logged depending on whether it was in your library or the other user's library. The *client* then sends the amount of songs that it found in common between the two libraries to the server, which the *server* validates and responds to depending on whether it agrees with the client's assessment. This validation process makes sure that both the server and the client are on the same page with regards to which songs the two share.

After both users have chosen their songs (and the server and client have confirmed this), the exchange of songs can begin. First, the server and client exchange lists of songs that the users selected (i.e. the checkboxes in the UI they had checked). After that's happened, the *client* creates a 7-Zip archive containing all of the songs that the *server* had checked, and sends it over. Once the server has finished receiving this file, it follows suit by creating an archive containing all of the songs that the *client* had checked, and sending that over as well. After both the server and the client have finished sending and receiving the archives containing their desired songs, they extract them directly to the user's song directory (within a sub-folder called CH-X, just to keep things clean). After completing the extraction, CH-X cleans up all of the extra `.json` and `.7z` files it created, and lets you know it's done.

#### "I've found a bug! What should I do?"

Either open an issue within GitHub, or message me on Discord. Please try to be as clear and detailed in your description of the bug as possible, including steps to reproduce it, if at all possible.

#### TODOs

* ~~Implement Unix path support. At the moment, CH-X only uses Windows pathing (i.e. backslashes instead of forward), so only Windows systems are supported.~~ **Support for Mac/Linux systems has been implemented and is currently in alpha testing. Please download the latest pre-release if you want to help test it!**
* Allow for custom port usage.
* Allow for archive-only usage; this would make it so that if you didn't have a super stable internet connection, you could tick a box and have CH-X zip up all the songs your friend wanted, and then upload the archive yourself to an external file storage service.
* Continue to revamp UI.

## Contact

The easiest way to reach me is on Discord at `Nicole 🌼#4092`. I change my username somewhat frequently though, so if I haven't updated this page with my new username, you should be able to find me through the Clone Hero Discord server. You're welcome to contact me with bug reports, questions about usage or functionality, suggestions for new features, or just to let me know what you think of the program!


Thanks for reading, and long live rhythm gaming! 🤘🏻
