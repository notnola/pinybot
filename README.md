<!-- GoelBiju (2016) -->
<!-- Page header - originally in Markdown, replaced with HTML for convenience. -->

<h1>
	<center>
		<strong><i>pinybot</i></strong>
	</center>
</h1>

<center>
[![GitHub code](https://img.shields.io/badge/Code-Python-green.svg)](https://www.python.org/) [![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/GoelBiju/pinybot/master/LICENSE) [![GitHub issues](https://img.shields.io/github/issues/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/issues) [![GitHub stars](https://img.shields.io/github/stars/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/stargazers) [![GitHub forks](https://img.shields.io/github/forks/GoelBiju/pinybot.svg)](https://github.com/GoelBiju/pinybot/network) [![GitHub downloads](https://img.shields.io/github/downloads/GoelBiju/pinybot/total.svg)](https://github.com/GoelBiju/pinybot/releases) [![GitHub IRC](https://img.shields.io/badge/IRC-%23pinybot-green.svg)](http://webchat.freenode.net/?channels=pinybot) 
</center>

---

A Tinychat room helper forked and extended from [nortxort's pinylib](https://github.com/nortxort/pinylib), featuring all the essential features to help kickstart a room on [Tinychat](https://tinychat.com/).

If you like or found this useful, I would be grateful if you star the repository. I also happily accept any new features or interesting pull requests you would like to be included in the project.

If there is a bug you want to highlight or if you are perplexed by any other aspect of the project, be sure to post an issue in the [issues section](https://github.com/GoelBiju/pinybot/issues).

All the releases can be found in the [releases section](https://github.com/GoelBiju/pinybot/releases) with the source code. Release information/order to which the project adheres to is within the release procedures file, found in the project folder.

*Windows users have the option to download a compiled, executable version of the program which is provided alongside the release source code.*

Visit our **[homepage](https://goelbiju.github.io/pinybot/)** for general information.

---

## Requirements

[Python 2.7](https://www.python.org/downloads/)

### Dependencies

* [Requests](http://docs.python-requests.org/en/master/)
* [PyAMF](https://github.com/hydralabs/pyamf)
* [PySocks](https://github.com/Anorov/PySocks) (*Provided*)
* [colorama](https://github.com/tartley/colorama)
* [BeautifulSoup4](http://www.crummy.com/software/BeautifulSoup/)


***NOTE:*** The compilation of PyAMF may require the installation of a Visual C++ compiler. You can *optionally* download and install this from [Microsoft's page](https://www.microsoft.com/en-gb/download/details.aspx?id=44266) (Windows only). This being said, you **do not** need PyAMF compiled in order to use it, simply copy the [pyamf folder](https://github.com/hydralabs/pyamf/tree/master/pyamf) and place it in the root of the project directory and make sure you have all the other dependencies installed via *pip* or *easy_install*.

**Linux**

Run this within a linux terminal:
```sh
pip2 install [module name]
OR
pip2 install requests pyamf colorama bs4
```

**optionally**, to install pysocks locally (despite being provided):
```sh
pip2 install pysocks
```

**Windows**

*Note:* Windows users are encouraged to add Python to their environment path. More information is available [here](https://superuser.com/questions/143119/how-to-add-python-to-the-windows-path) regarding adding environmental variables.

The following Windows instructions assume you *do not* have Python version 2.7 set as an environmental (user/system) variable.

In order **to install on Windows**, be sure to use command prompt:
```sh
C:\Python27\Scripts\pip.exe install bs4 requests pysocks colorama pyamf

C:\Python27\Scripts\pip2.exe install bs4 requests pysocks colorama pyamf
```

---

## File information

Listed below are the files within this project and notes regarding their purpose. Please be sure you have these files and also do not have any other unrelated files in the project directory.

* Key files/directories:
	* **apis** *(directory)* - Contains scripts related to external APIs e.g. communicating with the Tinychat API, YouTube API, SoundCloud API etc.
	* **files** *(directory)* - Here resides all the bot generated files and the file handling script(s).
	* **rtmp** *(directory)* - The basic communications scripts reside here, and all other various low level functions to interact with the remote server via sockets and the RTMP protocol.
	* **utilities** *(directory)* -
	* **config.ini** *(file)* - All the pertinent configurations and settings for both the bot and core can be set in here.
	* **pinybot.py** *(file)* - The **MAIN** bot script itself. Running this will initiate a console connection to the room.
	* **pinylib.py** *(file)* - The **CORE** bot script which is a store for all the essential functions in order for a normal connection to be made to the server and allowing for low-level communications to be executed.

* Other files:
	* about.py *(file)* - 
	* \__init__.py *(file)* - Allows all the files within the project folder to be available as a python package.
	The changelog has now moved to the GitHub Pages - add reference to this change.
	* changelog.html *(file)* - Contains all the recent changes made to the project.
	* CREDITS *(file)* - The acknowledgements and credits to all those who helped with the bot.
	*  LICENSE *(file)* - The MIT license for the project.
	* CONTRIBUTING *(file)* - Simple introduction to contributing in this project, in any shape or form.
	* RELEASE-PROCEDURE *(file)* - Outline as to how releases/updates to the repository work.
	* README.md *(file)* - This file which contains pertinent information regarding all the other files.


### Detailed information

All further information in regards to the background of the project and the functions/features of the program can be found in the GitHub repository [Wiki](https://github.com/GoelBiju/pinybot/wiki).

---

## Run the bot!

There is very little you need to follow to run the bot normally. The downloading and extraction of the files within the GitHub repository folder (and the dependencies which you should have installed as stated above) should prepare you for the initial run of the application.

Opening **pinybot.py** by double-clicking will start the *CLI* (Command Line Interface) with the application running via python.

You can also start the bot via command line/terminal, as follows:

**Linux**

```sh
python pinybot.py
OR
python2 pinybot.py
```

*Create a Linux executable* (**optional**):
```sh
chmod +x pinybot.py
./pinybot.py
```

**Windows**
 
Assumes you are in the default *pinybot-master* directory:
```
C:\Python27\python pinybot.py
```

If you have any trouble navigating command prompt within Windows, please refer to this [beginner's guide to command prompt](http://www.online-tech-tips.com/computer-tips/how-to-use-dos-command-prompt/).

In the event that you do **not** feel **satisfied with the configuration** and you would like to configure the multitude of settings at your disposable, then feel free to. All custom settings/options can be found in the default **config.ini** file. The specifics of these options are highlighted in the [wiki](https://github.com/GoelBiju/pinybot/wiki/Configure-it!).

In the case that there is an aspect of the bot that should be worth adding as a confiigurable option, then feel free to flag an issue and we can easily deploy a patch to rectify this.


## *"How can **I** help?"*

You can easily leave a comment or an issue regarding help to fix a bug, with the assurance that someone will repond and help sort out your issue. It can even be a suggestion or simply asking to join in to develop a bigger and better application.

## Running remotely

If you are interested in running the bot remotely (instead of locally on your computer or server), why not try the OpenShift dedicated [pinybot repository](https://github.com/GoelBiju/pinybot-OpenShift) platform as a solution.

It is almost configured to a 'click to setup and start' standard to save you time and effort in setting up the application online.

Please do enquire into issues you may face when using this, either by posting an issue here or on the dedicated repository.

## Contact Us

If there are any personal suggestions or queries you would like to ask us, please be sure to visit the **#pinybot** *IRC* (Internet Relay Chat) channel on the [Freenode](http://webchat.freenode.net/?channels=pinybot) network, where we will happily help you!

You can visit the irc directly by clicking on the link above or on the GitHub shield at the top of the README.

---

## License

The MIT License (MIT)

Copyright (c) 2016 Goel Biju

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

---

<!-- Page footer -->
<footer>
	<center><a href="http://goelbiju.github.io/pinybot/" target="_blank">Visit Git Pages</a></center>
</footer>
