""" Functions to do various console operations with. """
import os


def clear_console():
    """ Allows the console screen to be cleared. """
    if os.name == 'nt':
        type_clear = 'cls'
    else:
        type_clear = 'clear'
    os.system(type_clear)
