# pinybot

A Tinychat room helper forked and extended from [nortxort's pinylib](https://github.com/nortxort/pinylib). Featuring all the essential features to help kickstart a room.
If you like or found this useful i.e. practically or contextually, please do star the repository. We also happily accept any new features or interesting pull requests!

Be sure to post an issue if there is a bug you want to highlight or if you are plagued by anything else. 

Visit our **[homepage](https://oddballz.github.io/pinybot/)** for general information and what we (as a group) are.

---

## Requires

* [Python 2.7 (sub-version 10+)](https://www.python.org/downloads/)

Windows users are encouraged to add Python to their environment paths; more information [here](https://superuser.com/questions/143119/how-to-add-python-to-the-windows-path).
The following Windows instructions assume you *do not* have Python27 set in your environment/system variables.

### Dependencies

* [PyAMF](https://github.com/hydralabs/pyamf)
* [Requests](http://docs.python-requests.org/en/master/)
* [PySocks](https://github.com/Anorov/PySocks) (*Provided*)
* [colorama](https://github.com/tartley/colorama)
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/)

Linux

```sh
pip2 install bs4 requests pysocks colorama pyamf
```
Windows
```
C:\Python27\Scripts\pip2 install bs4 requests pysocks colorama pyamf
```

(All module requirements information is stored within **requirements.txt**)

### Optional Dependencies

* [Wikipedia](https://github.com/goldsmith/Wikipedia) (for use with wikipedia searches)

Linux
```sh
pip2 install wikipedia
```
Windows
```
C:\Python27\Scripts\pip2 install wikipedia
```

### Automatic bot/dependencies via update script

An alternative to installing all the dependencies one by one or downloading the latest version of the bot, is to simply start pinybot.py. Upon startup, the update script will commence and determine
if you have the current version of the bot and/or if you have the latest versions of the modules needed to run it. If there was any modifications made to a new version of the bot, then the latest 
version will be downloaded to a new directory, where you can easily extract it and overwrite your local copy.

---

## File information

* **api** *(directory)* - Contains scripts related to external features e.g. communicating with the Tinychat API. 
* **files** *(directory)* - Here resides all the bot created files and the file handling script(s) files.
* **rtmp** *(directory)* - The basic communcation scripts reside here, and all other various low level functions to interact with the server.
* **config.ini** *(file)* - All the pertinent configurations/settings for the bot and the core can be set in here. **NOTE: If the bot is placed on a webserver, the config.ini file must be setup with respect to that (more information regarding this below).**
* **pinybot.py** *(file)* - The MAIN bot script itself. Running this will intiate a console connection to the room.
* **requirements.txt** *(file)* - Contains the modules which are required in order for the bot to run wholly.
* **tinychat.py** *(file)* - The CORE bot script which is a store for all the essential functions in order for a normal connection to be made to the server and allowing for low-level communications to be executed.
* **update.py** *(file)* - Hosts the module updating (based on the requirements file) and bot version checking script to allow for you stay updated with any new changes made.


### Detailed information

All further information in regards to the functions/features of the bot can be found in the GitHub Repository [Wiki](https://github.com/oddballz/pinybot/wiki). 

---

## Run the bot!

There is very little you need to follow to run the bot normally, i.e. downloading and extracting the files and opening **pinybot.py** will start the bot.
However, if you would like to configure the various other settings, then feel free to. All custom setting options are available in the default **config.ini** file.

Linux
```sh
python2 pinybot.py
```
Create a Linux executable (optional)
```sh
chmod +x pinybot.py
./pinybot.py
```
Windows (assumes you are in the pinybot-master directory)
```
C:\Python27\python pinybot.py
```

### "How can I help?"

You can easily leave a comment, or an issue asking to help us fix a bug, sort a pending issue, or even join the team.

### Interested in a webserver?

If you are interested in running the bot online (instead of locally) why not try the OpenShift dedicated [pinybot repository](https://github.com/oddballz/pinybot-OpenShift).
It's almost configured to a 'click to setup and run' standard, to save you time and effort in setting up the bot. Please do tell us if you have issues with this, either by posting an issue here or on that repository.