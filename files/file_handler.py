# -*- coding: utf-8 -*-
""" Handles operation related to files. """

import os

# Additional modules to handle configurations & unicode.
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
        f.writelines(write_this + '\n')
        return True


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


def delete_file(file_path, file_name):
    """
    Deletes a file entirely.
    :param file_path: str the path to the file.
    :param file_name: str the file name.
    :return: True if deleted, else False
    """
    if os.path.isfile(file_path + file_name):
        os.remove(file_path + file_name)
        return True
    return False


def delete_file_content(file_path, file_name):
    """
    Deletes all content from a file.
    :param file_path: str the path to the file.
    :param file_name: str the name of the file.
    """
    open(file_path + file_name, mode='w').close()


# TODO: Manual section parameter added to handle individual sections.
def configuration_loader(file_location, manual_section=None):
    """
    Loads the necessary settings required for the bot to run from the given path with a '.ini' file.
    The settings are then returned as a dictionary which can then be used in the bot.
    :param file_location: str The location including the name and extension of the file.
    :param manual_section: str default None, a specific section in the configuration to read from.
    :return: CONFIG: dict configurations given in the '.ini' file.
    """
    try:
        # Setup Configuration module and read the configuration.
        config_file = ConfigParser.ConfigParser()
        config_file.read(file_location)

        # This is the dictionary in which all our options parsed from the configuration file will
        # be stored and finally returned to the main application.
        config_options = {}

        # Parse the sections we only need if it specified manually as a section, otherwise parse all sections
        # within the configuration file.
        parse_sections = []
        if manual_section is not None:
            parse_sections.append(manual_section)
        else:
            for section in config_file.sections():
                parse_sections.append(section)

        # Iterate over the sections to parse and derive the options to parse it.
        for section in parse_sections:
            options = config_file.options(section)

            for option in options:
                value = config_file.get(section, option).strip()

                # Handle Boolean/Null values/types.
                if value == 'true':
                    value = True
                elif value == 'false':
                    value = False
                elif value == 'none':
                    value = None

                # Handle integers/floats.
                try:
                    value = int(value)
                except ValueError:  # Exception
                    try:
                        value = float(value)
                    except ValueError:  # Exception
                        pass

                # Handle lists.
                try:
                    value = value[:]
                except TypeError:  # Exception
                    pass

                # Handle dictionaries
                try:
                    value = ast.literal_eval(value)
                except (SyntaxError, ValueError):  # Exception
                    pass

                # Strip the option values to remove any whitespace characters.
                config_options[option.strip()] = value
        return config_options
    except IOError:
        # If the configuration file doesn't exist in the path given, then return the null type.
        return None


# TODO: Possibly use configuration parser instead?
def unicode_loader(file_location):
    """
    Loads (one line) unicode objects into a dictionary, provided a file is stated.

    NOTE: Unicode in the specified file must be in the format: [name of unicode object] [unicode object body],
          the name must be one word followed by a space and then the unicode object body.

    :param file_location: str the path to the file and the file (with extension).
    :return: unicode_data: dict{all the formatted unicode objects}.
    """
    try:
        # Open the file with the appropriate codec.
        # TODO: codec read encoding switched from 'utf-8' to 'utf-8-sig' to make sure the Byte Order Mark (BOM)
        #       characters are removed when reading from the file.
        unicode_file = codecs.open(file_location, encoding='utf-8-sig')
        unicode_raw_data = unicode_file.readlines()

        # Add the parsed unicode data to the dictionary.
        unicode_data = {}
        for x in xrange(len(unicode_raw_data)):
            unicode_object = unicode_raw_data[x].split(' ')
            unicode_id = u'' + unicode_object[0]
            unicode_byte_data = u'' + ' '.join(unicode_object[1:])
            unicode_data[unicode_id] = unicode_byte_data
        return unicode_data
    except IOError:
        return None
