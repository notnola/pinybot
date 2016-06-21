# -*- coding: utf-8 -*-

""" Handles operations related to updating of modules/bot """

import os
import time
import zipfile
from files import file_handler as fh

# Try to see if PIP is available otherwise use the standard easy install module.
try:
    # PIP to install
    import pip
    on_pip = True
except ImportError:
    from setuptools.command import easy_install  # easy_install to install
    on_easy_install = True

# Update variables:
new_changes = False

# Try to see if requests is already present for bot updates.
try:
    import requests
    requests_present = True
except ImportError:
    requests_present = False


# TODO: Real commit updating; line by line checking on each file.
def module_installer(package):
    """
    Install a package given via PIP or easy_install.
    :param package: str the name of the package.
    """
    global on_pip
    global on_easy_install

    print('Setting up: ' + package)
    if on_pip:
        pip.main(['install', package])  # PIP command
    elif on_easy_install:
        easy_install.main(['-U', package])  # easy_install command
    else:
        return None


# Module handler; processes the required versions of modules in order to run it.
def module_updater(CONFIG):
    """
    Installs modules based on the configuration found by the bot.
    :param CONFIG: dict the configuration settings for the bot.
    """
    global new_changes

    if CONFIG['module_updater']:
        print('--> Now checking module updates...')
        time.sleep(2.5)
        requirements_file = open(CONFIG['requirements_file'], 'r')

        # Parse requirements file
        requirements = requirements_file.readlines()
        dependencies = []

        for x in range(len(requirements)):
            dependencies.append(requirements[x].strip())

        if len(dependencies) is 0:
            return new_changes
        else:
            # Install the dependencies depending on the most convenient module available.
            if on_pip or on_easy_install:
                for x in range(len(dependencies)):
                    module_installer(dependencies[x])
                print('--> Module checking complete.')
            else:
                print('*We were unable to install the modules required. Please install PIP or easy_install.*')
                print('*You can run the get-pip.py module at: https://bootstrap.pypa.io/get-pip.py*')

            time.sleep(2.5)
            new_changes = True
            return new_changes
    else:
        return new_changes


# Update handler; processes updates if the latest version of the bot is not present on the client computer.
def bot_updater(CONFIG):
    """
    Allows for the retrieval of new bot updates.
    :param CONFIG: dict the configuration settings for the bot.
    """
    global new_changes

    if CONFIG['bot_updater']:
        print('--> Now checking bot updates...')
        time.sleep(1.5)
        if not requests_present:
            print('*No requests module present. Please install requests to receive bot updates.*')
            time.sleep(5)
            return new_changes
        else:
            repo_url = CONFIG['repository']
            print('--> Fetching from repository: ' + repo_url)
            time.sleep(1)

            # Fetch the latest configuration file from the repository
            temp_config = requests.get(CONFIG['temporary_configuration'])
            temp_config_file = open('temp_config.ini', 'w+')
            temp_config_file.write(temp_config.content)
            temp_config_file.close()

            print('--> Detecting version data.')
            time.sleep(1)
            temp_config_data = fh.configuration_loader('temp_config.ini')

            # Try to see if any version data exists or not.
            try:
                latest_version = temp_config_data['version']
            except KeyError:
                latest_version = None

            os.remove('temp_config.ini')

            if latest_version is None:
                print('--> No version data was found, skipped bot updating.')
                time.sleep(2)
                return new_changes
            else:
                # Version comparison
                present_version = CONFIG['version']
                present_version_parts = present_version.split('.')
                present_version_float = float(present_version_parts[0] + '.' + ''.join(present_version_parts[1:]))
                latest_version_parts = latest_version.split('.')
                latest_version_float = float(latest_version_parts[0] + '.' + ''.join(latest_version_parts[1:]))

                print ('--> Your version: ' + str(present_version_float) + ' Repository version: ' + str(latest_version_float))

                if latest_version_float > present_version_float:
                    choice = raw_input('--> New version found! Download now? (y/n)')
                    if choice.lower() is 'y':
                        latest_version = requests.get(CONFIG['repository_zip'], stream=True)
                        latest = open('latest_version.zip', 'wb')
                        latest.write(latest_version.content)
                        latest.close()
                        to_extract = zipfile.ZipFile('latest_version.zip', 'r')
                        os.remove('latest_version.zip')

                        for file_name in to_extract.namelist():
                            to_extract.extract(file_name, os.path.abspath(str(os.path.join(os.path.dirname(__file__)))))
                            print('--> Extracted: ' + str(file_name))
                        time.sleep(2)

                        print('--> All files have been extracted into ' + str(to_extract.namelist()[0]))
                        print('*Please copy and overwrite all files in the downloaded folder into your bot folder, then run pinybot.*')
                        print('This console will close in 20 seconds.')

                        time.sleep(20)
                        new_changes = True
                        return new_changes
                    else:
                        print('--> Download skipped.')
                        time.sleep(2)
                        return new_changes
                else:
                    print('You are running the latest version.')
                    time.sleep(2)
                    return new_changes
