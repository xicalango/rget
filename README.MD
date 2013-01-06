rGet
====

A textual user interface for wget, written in python with cmd and subprocess, supporting the management of multiple downloads at the same time.

Basic Usage
===========
Paste the URLs you'd like to download into the commandline then start downloading by typing `startAll`.

Typing `ls` will show you the information about all downloads.
Remove finished downloads from the list with `removeFinished`.

As this programm uses python's cmd, command autocompletion works.

Exit by sending EOF or typing `exit`. All pending downloads are closed.

Commands
========

* **dl <url>** Add and start downloading *<url>*
* **add <url>** Add *<url>* to list but don't start downloading
* **ls** List downloads in list with their id.
* **start <id|url>** Start an idle download given by id or url
* **startAll** Stars all idle downloads
* **stop <id|url>** Stops download given by id or url
* **remove <id|url>** Removes a download from the list, stopping it when needed
* **removeFinished** Removes all finished downloads from the list.
* **exit** or **EOF** Exits the program, interrupting all downloads.

TODO
====

* Configuration stuff like setting the output directory
* A curses based ui
* Suspending/Continuing downloads

Vision
======

The vision is to recreate a tool like rTorrent for managing normal http/ftp downloads. 

