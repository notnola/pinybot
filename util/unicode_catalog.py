""" A file to store various unicode symbol's and their pythonic representations. """

# Catalog formatting:
# UNICODE_NAME = unicode representation  # Additional comment on what this unicode symbol is assigned to.

# NOTE: It seems that most unicode symbols up to Unicode Version 3.0.0 work, we cannot be sure if newer versions
#       work with the online flash client.

TIME = u'\u231A'  # up-time

MUSICAL_NOTE = u'\u266B'  # playlist entries

MUSICAL_NOTE_SIXTEENTH = u'\u266C'  # radio notification

NUMERO = u'\u2116'  # stating the position of a track added to or in the playlist

STATE = u'\u21DB'  # success message from internal operation

INDICATE = u'\u261B'  # error message from internal operation

INDICATE_UPWARDS = u'\u261D'  # alerting of a greenroom broadcast approval required

RELOAD = u'\u21BA'  # reconnecting to the room

BLACK_STAR = u'\u2605'  # added as a temporary moderator

WHITE_STAR = u'\u2606'  # removed as a temporary moderator

CHECKBOX_TICK = u'\u2611'  # do advice function reply

TICK_MARK = u'\u2713'  # adding a camera block

CROSS_MARK = u'\u2717'  # removing a camera block

CIRCLED_WHITE_STAR = u'\u272A'  # stating media request playing

BLACK_HEART = u'\u2764'  # added to auto-forgive

WHITE_HEART = u'\u2661'  # removed from auto-forgive

TOXIC = u'\u2620'  # bad word found

PENCIL = u'\u270E'  # adding a media to playlist

SCISSORS = u'\u2704'  # removing a media from playlist

VICTORY_HAND = u'\u270C'  # waking up CleverBot

# FLOWER = u'\u2740'  # NOTE: not yet assigned

ARROW_STREAK = u'\u27A0'  # accepting media requests

# ARROW_RIGHT = u'\u2400'  # playlist countdowns

ITALIC_CROSS = u'\u2718'  # declining media requests

FLORAL_HEART = u'\u2766'  # NOTE: not yet assigned

NOTIFICATION = u'\u2709'  # NOTE: not yet assigned

ARROW_SIDEWAYS = u'\u27AB'  # adding/playing a media request to/from playlist

NO_WIDTH = u'\u200B'  # applying bold styling to small words which would otherwise not be parsed accurately

WRITING_HAND = u'\u270D'  # displaying any additions to lists/files

DAGGER_FOOTNOTE = u'\u2020'  #

# NOTE (regarding NO_WIDTH):
# 'Zero Width Space' character; the addition of the zero width character before and after
# text to allow bold printing. This avoids [two letter bold] parsing errors in the client.
