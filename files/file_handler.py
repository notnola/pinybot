# -*- coding: utf-8 -*-

""" Handles operation related to files. """

import os
import codecs
import ConfigParser
import ast


def file_reader(file_path, file_name):
    """
    Reads from a file.
    :param file_path: str the path to the file.
    :param file_name: str the name of the file.
    :return: list of lines or None if no file exists.
    """
    file_content = []
    try:
        with open(file_path + file_name, mode='r') as f:
            for line in f:
                file_content.append(line.rstrip('\n'))
            return file_content
    except IOError:
        return None


def file_writer(file_path, file_name, write_this):
    """
    Write to file line by line.
    :param file_path: str the path to the file.
    :param file_name: str the name of the file.
    :param write_this: str the content to write.
    :return:
    """
    if not os.path.exists(file_path):
        os.makedirs(file_path)
    with open(file_path + file_name, mode='a') as f:
        f.write(write_this + '\n')


def delete_file_content(file_path, file_name):
    """
    Deletes all content from a file.
    :param file_path: str the path to the file.
    :param file_name: str the name of the file.
    """
    open(file_path + file_name, mode='w').close()


def remove_from_file(file_path, file_name, remove):
    """
    Removes a line from a file.
    :param file_path: str the path to the file.
    :param file_name: str the name of the file.
    :param remove: str the line to remove.
    :return: True on success else False
    """
    file_list = file_reader(file_path, file_name)
    if file_list is not None:
        if remove in file_list:
            file_list.remove(remove)
            delete_file_content(file_path, file_name)
            for line in file_list:
                file_writer(file_path, file_name, line)
            return True
        return False
    return False


def configuration_loader(file_location):
    """
    Loads the necessary settings required for the bot to run from the given path with a '.ini' file.
    The settings are then returned as a dictionary which can then be used in the bot.
    :param file_location: str The location including the name and extension of the file.
    :return: CONFIG: dict configurations given in the '.ini' file.
    """
    if not os.path.exists(file_location):
        return None

    # Setup Configuration module and read the configuration
    config = ConfigParser.ConfigParser()
    config.read(file_location)

    CONFIG = {}

    for section in config.sections():
        options = config.options(section)
        for option in options:

            value = config.get(section, option).strip()

            # Handle Boolean/Null values/types
            if value == 'true':
                value = True
            elif value == 'false':
                value = False
            elif value == 'none':
                value = None

            # Handle integers/floats
            try:
                int(value)
                value = int(value)
            except Exception:
                try:
                    float(value)
                    value = float(value)
                except Exception:
                    pass

            # Handle lists
            try:
                value = value[:]
            except Exception:
                pass

            # Handle dictionaries
            try:
                value = ast.literal_eval(value)
            except Exception:
                pass

            CONFIG[option.strip()] = value
    return CONFIG


# TODO: Possibly use configuration parser instead?
def ascii_loader(file_location):
    """
    Loads (one line) ASCII objects into a dictionary, provided a file is stated.
    :param file_location: str the path to the file and the file (with extension).
    :return: ASCII_dict: dict of all the formatted ascii objects.
    NOTE: ASCII in specified file must be in the format: [name of ascii] [ASCII object],
          the name must be one word followed by a space and then the ASCII object.
    """
    if os.path.exists(file_location):
        ascii_file = codecs.open(file_location, encoding='utf-8')
        ascii_raw_data = ascii_file.readlines()

        ascii_data = {}
        for x in xrange(len(ascii_raw_data)):
            ascii_object = ascii_raw_data[x].split(' ')
            ascii_id = u'' + ascii_object[0]
            ascii_byte_data = u'' + ' '.join(ascii_object[1:])
            ascii_data[ascii_id] = ascii_byte_data

        return ascii_data
    else:
        return None
