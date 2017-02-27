# pinybot

[![Join the chat at https://gitter.im/pinybot/Lobby](https://badges.gitter.im/pinybot/Lobby.svg)](https://gitter.im/pinybot/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
> "The true base for your Tinychat bot needs."

![Github code](https://img.shields.io/badge/Code-Python-green.svg) [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/GoelBiju/pinybot/master/LICENSE) [![GitHub issues](https://img.shields.io/github/issues/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/issues) [![GitHub stars](https://img.shields.io/github/stars/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/stargazers) [![GitHub forks](https://img.shields.io/github/forks/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/network) ![Github downloads](https://img.shields.io/github/downloads/GoelBiju/pinybot/total.svg)


A Tinychat room helper forked and extended from [nortxort's pinylib](https://github.com/nortxort/pinylib), featuring all the essential features to help kickstart a room on [Tinychat](https://tinychat.com/).

If you like or found this useful i.e. practically or contextually, please do star the repository. We also happily accept any new features or interesting pull requests you would like to be included in the project.

If there is a bug you want to highlight or if you are plagued by any other aspect of the project, be sure to post an issue in the [issues section](https://github.com/GoelBiju/pinybot/issues).

Visit our **[homepage](https://GoelBiju.github.io/pinybot/)** for general information.

All our releases can be found in the [release section](https://github.com/GoelBiju/pinybot/releases) with the source code. Release information/order is within the release procedures file, found in the project folder.

*Windows users also can optionally download an executable version of the program.*

---

## Requirements

* [Python 2.7 (sub-version 10+)](https://www.python.org/downloads/)


### Dependencies

* [Requests](http://docs.python-requests.org/en/master/)
* [PyAMF](https://github.com/hydralabs/pyamf)
* [PySocks](https://github.com/Anorov/PySocks) (*Provided*)
* [colorama](https://github.com/tartley/colorama)
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/)

**Linux**

Run this on a linux terminal:
```sh
pip2 install bs4 requests pysocks colorama pyamf
OR
pip install [module name]
```
**Windows**

*Note:* Windows users are encouraged to add Python to their environment paths; more information [here](https://superuser.com/questions/143119/how-to-add-python-to-the-windows-path).

The following Windows instructions assume you *do not* have Python27 set in your environment/system variables.

In order to install on windows, be sure to use command prompt:
```
C:\Python27\Scripts\pip2.exe install bs4 requests pysocks colorama pyamf
```

Modules and requirements information is stored within **requirements.txt**, found in the project folder.

### Optional Dependencies

* [Wikipedia](https://github.com/goldsmith/Wikipedia) (for use with wikipedia searches)

**Linux**
```sh
pip2 install wikipedia
```
**Windows**
```
C:\Python27\Scripts\pip2 install wikipedia
```

### Automatic dependencies via update script

An alternative to installing all the dependencies one by one or downloading the latest version of the bot from GitHub, is to simply start pinybot.py. Upon starting the file, the update script will commence and determine if you have the latest version of the bot and/or if you have the latest versions of the modules needed to run it. 

If there were any modifications made to a new version of the bot, then the latest version will be downloaded to a new directory which will be placed in the project folder, where you can easily extract it and overwrite your local copy.

You can always disable this feature in the **config.ini** in the project folder.

---

## File information

* **api** *(directory)* - Contains scripts related to external features e.g. communicating with the Tinychat API. 
* **files** *(directory)* - Here resides all the bot generated files and the file handling script(s).
* **rtmp** *(directory)* - The basic communications scripts reside here, and all other various low level functions to interact with the remote server.
* **config.ini** *(file)* - All the pertinent configurations and settings for both the bot and core can be set in here.
* **pinybot.py** *(file)* - The **MAIN** bot script itself. Running this will intiate a console connection to the room.
* **pinylib.py** *(file)* - The **CORE** bot script which is a store for all the essential functions in order for a normal connection to be made to the server and allowing for low-level communications to be executed.
* **requirements.txt** *(file)* - Contains the modules which are required in order for the bot to run wholly.
* **update.py** *(file)* - Hosts the module updating (based on the requirements file) and bot version checking script to allow for you stay updated with any new changes made.

* Other files:
	* ChangeLog.html (*file*) - Contains all the recent changes made to the project.
	* CREDITS (*file*) - The acknowledgements and credits to all those who helped with the bot.
	* CONTRIBUTING (*file*) - Simple introduction to contributing to this project in any shape or form.
	* RELEASE-PROCEDURE (*file*) - Outline as to how releases/updates to the repository will work.
	* LICENSE (*file*) - The MIT license for the project.
	* README.md (*file*) - This file.


### Detailed information

All further information in regards to the functions/features of the bot can be found in the GitHub repository [Wiki](https://github.com/GoelBiju/pinybot/Wiki).

---

## Run the bot!

There is very little you need to follow to run the bot normally, i.e. downloading and extracting the files and opening **pinybot.py** will start the bot.

*However*, if you would like to configure the various other settings, then feel free to. All custom settings/options are found in the default **config.ini** file.

**Linux**
```sh
python2 pinybot.py
OR
python pinybot.py
```
*Create a Linux executable* (**optional**)
```sh
chmod +x pinybot.py
./pinybot.py
```
Windows (assumes you are in the ***pinybot-master*** directory)
```
C:\Python27\python pinybot.py
```

If you have any trouble navigating command prompt within Windows, please refer to this [beginner's guide to command prompt](http://www.online-tech-tips.com/computer-tips/how-to-use-dos-command-prompt/).

## *"How can I help?"*

You can easily leave a comment or an issue regarding help to fix a bug, sort a pending issue, a suggestion or even joining the team to help with the project.

## Interested running it remotely?

If you are interested in running the bot online (instead of locally), why not try the OpenShift dedicated [pinybot repository](https://github.com/GoelBiju/pinybot-OpenShift).

It's almost configured to a 'click to setup and run' standard to save you time and effort in setting up the bot. 

Please do tell us if you have issues with this, either by posting an issue here or on the dedicated repository.
