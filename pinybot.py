#!/usr/bin/env python2
# -*- coding: utf-8 -*-

""" A Tinychat bot (based on the pinylib library) with additional features/commands.
         _           __        __
   ___  (_)__  __ __/ /  ___  / /_
  / _ \/ / _ \/ // / _ \/ _ \/ __/
 / .__/_/_//_/\_, /_.__/\___/\__/
/_/          /___/

"""

# Supplementary Information:
# Description: Tinychat Python bot,
# Repository homepage: https://goelbiju.github.io/pinybot/,
# Repository: https://github.com/GoelBiju/pinybot/

# Acknowledgements to Nortxort (https://github.com/nortxort/) and Autotonic (https://github.com/autotonic/).
# Many others including: @notnola, @technetium1 have helped with this project and I would like to say thanks to them.

# Core imports
import os
import sys
import re
import random
import threading
import logging

# Standard imports
# TODO: Implement updating properly at a later stage.
# TODO: Module updater does not work due to pinylib call being first.
import pinylib
from apis import auto_url, clever_client_bot, soundcloud, youtube, lastfm, privacy_settings, other_apis

# Information variables
author = '*Goel* (https://github.com/GoelBiju/ )' + \
        ' [acknowledgements/general information can be found in the repository]'
repository = 'https://goelbiju.github.io/pinybot/'

__version__ = '1.4.2'
build_name = '"Waves"'

log = logging.getLogger(__name__)

# Loads CONFIG in the configuration file from the root directory:
CONFIG_FILE_NAME = '/config.ini'  # State the name of the '.ini' file here.
CURRENT_PATH = sys.path[0]
CONFIG_PATH = CURRENT_PATH + CONFIG_FILE_NAME
CONFIG = pinylib.fh.configuration_loader(CONFIG_PATH)


def clear_console():
    """ Allows the clearance of the console. """
    if os.name == 'nt':
        type_clear = 'cls'
    else:
        type_clear = 'clear'
    os.system(type_clear)

# Make sure we clear the console before proceeding.
clear_console()

if CONFIG is None:
    print('No file named ' + CONFIG_FILE_NAME + ' found in: ' + CONFIG_PATH)
    sys.exit(1)  # Exit to system safely whilst returning exit code 1


# Loads the 'ascii.txt' file with ASCII/unicode text into a dictionary.
if CONFIG['ascii_chars']:
    ascii_dict = pinylib.fh.unicode_loader(CONFIG['path'] + CONFIG['ascii_file'])
    ascii_chars = True
    if ascii_dict is None:
        ascii_chars = False
        print('No ' + CONFIG['ascii_file'] + ' was not found at: ' + CONFIG['path'])
        print('As a result the ASCII/unicode was not loaded. Please check your settings.\n')


# Any special unicode character used within the bot is stored in this dictionary
special_unicode = {               # Assigned to:
    'time': u"\u231A",            # - uptime
    'musical_note': u"\u266B",    # - playlist entries
    'indicate': u"\u261B",        # - error messages
    'state': u"\u21DB",           # - successful messages
    'black_star': u"\u2605",      # - added as botter
    'white_star': u"\u2606",      # - removed as botter
    'check_mark': u"\u2713",      # - adding a camblock
    'cross_mark': u"\u2717",      # - removing a camblock
    'black_heart': u"\u2764",     # - added to autoforgive
    'white_heart': u"\u2661",     # - removed from autoforgive
    'toxic': u"\u2620",           # - bad word found
    'pencil': u"\u270E",          # - adding a media to playlist
    'scissors': u"\u2704",        # - deleting a media from playlist
    'victory_hand': u"\u270C",    # - waking up CleverBot
    'flower': u"\u2740",          # - NOTE: not yet assigned
    'arrow_streak': u"\u27A0",    # - accepting media requests
    'italic_cross': u"\u2718",    # - declining media requests
    'floral_heart': u"\u2766",    # - NOTE: not yet assigned
    'notification': u"\u2709",    # - NOTE: not yet assigned
    'arrow_sideways': u"\u27AB",  # - adding/playing a media request [to playlist]
    'no_width': u"\u200B",        # - applying bold styling to small words which would otherwise not
                                  # be parsed accurately ('Zero Width Space' character). The Addition of the zero
                                  # width character before and after text to allow bold printing. This avoids
                                  # [two letter bold] parsing errors in the client.
}


# External commands procedures
def eightball():
    """
    Magic eight ball.
    :return: str random answer from the list.
    """
    answers = ['It is certain.', 'It is decidedly so.', 'without a doubt', 'Yes - definitely.',
               'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.',
               'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.',
               'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'My reply is no',
               'My sources say no.', 'Outlook not so good.', 'Very doubtful.', 'I\'m pretty sure it\'s right.',
               'You can count on it.', 'Yes, in due time.', 'My sources say no.', 'Definitely not.',
               'You will have to wait.', 'I have my doubts.', 'Outlook so so.', 'Looks good to me!', 'Who knows?',
               'Looking good!', 'Probably.', 'Are you kidding me?', 'Go for it!', 'Don\'t bet on it.',
               'Forget about it.']
    return random.choice(answers)


class TinychatBot(pinylib.TinychatRTMPClient):
    """ Overrides event methods in TinychatRTMPClient that the client should to react to. """

    # Initial settings:
    init_time = int(pinylib.time.time())
    key = CONFIG['key']

    # - Privilege settings:
    botters = []  # Botters will only be temporarily stored until the next bot restart.

    # - Loads/creates permanent botter accounts files:
    if not os.path.exists(CONFIG['path'] + CONFIG['botteraccounts']):
        open(CONFIG['path'] + CONFIG['botteraccounts'], mode='w')
    botteraccounts = pinylib.fh.file_reader(CONFIG['path'], CONFIG['botteraccounts'])

    # - Loads/creates autoforgive files:
    if not os.path.exists(CONFIG['path'] + CONFIG['autoforgive']):
        open(CONFIG['path'] + CONFIG['autoforgive'], mode='w')
    autoforgive = pinylib.fh.file_reader(CONFIG['path'], CONFIG['autoforgive'])

    # - Media events/variables settings:
    yt_type = 'youTube'
    sc_type = 'soundCloud'
    is_mod_playing = False
    media_timer_thread = None
    media_request = None
    media_start_time = 0
    inowplay = 0
    media_delay = 2.5
    playlist_mode = CONFIG['playlist_mode']
    public_media = CONFIG['public_media']
    playlist = []
    search_play_lists = []
    search_list = []
    last_played_media = {}

    # - Module settings:
    privacy_settings = object
    clever_bot_enable = CONFIG['clever_bot_enable']
    clever_bot_session = None
    clever_bot_instant = CONFIG['clever_bot_instant']
    clever_bot_msg_time = int(pinylib.time.time())

    # - Method settings:
    auto_url_mode = CONFIG['auto_url_mode']
    cam_blocked = []
    bot_listen = True
    forgive_all = False
    syncing = False
    pmming_all = False

    # - Spam prevention settings:
    spam_potential = False
    spam_prevention = CONFIG['spam_prevention']
    check_bad_string = CONFIG['check_bad_string']
    snapshot_spam = CONFIG['snapshot_spam']
    snap_line = 'I just took a video snapshot of this chatroom. Check it out here:'
    unicode_spam = CONFIG['unicode_spam']
    message_caps_limit = CONFIG['message_caps_limit']
    room_link_spam = CONFIG['room_link_spam']
    caps_char_limit = CONFIG['caps_char_limit']
    bot_report_kick = CONFIG['bot_report_kick']

    # - Join settings:
    is_broadcasting_allowed = CONFIG['broadcasting_allowed']
    is_guest_entry_allowed = CONFIG['guests_allowed']
    is_newusers_allowed = CONFIG['new_users_allowed']
    is_guest_nicks_allowed = CONFIG['guest_nicks_allowed']
    auto_pm = CONFIG['auto_pm']
    pm_msg = CONFIG['pm_msg']
    welcome_user = CONFIG['welcome_user']
    welcome_broadcast_msg = CONFIG['welcome_broadcast_msg']
    auto_close = CONFIG['auto_close']
    ban_mobiles = CONFIG['ban_mobiles']

    # Set restricted terms here for Urban-dictionary this will prevent users requesting replies which may potentially
    # cause a crash or damage to the program.
    restricted_terms = CONFIG['urbandictionary_restricted']

    # Allow playlist mode to be enforced upon setting public media to True.
    if public_media:
        playlist_mode = True

    def on_join(self, join_info_dict):
        log.info('User join info: %s' % join_info_dict)
        user = self.add_user_info(join_info_dict['nick'])
        user.nick = join_info_dict['nick']
        user.user_account = join_info_dict['account']
        user.id = join_info_dict['id']
        user.is_mod = join_info_dict['mod']
        user.is_owner = join_info_dict['own']

        if join_info_dict['account']:
            tc_info = pinylib.tinychat_api.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']
            if join_info_dict['own']:
                self.console_write(pinylib.COLOR['red'], 'Room Owner %s:%d:%s' % (join_info_dict['nick'],
                                   join_info_dict['id'], join_info_dict['account']))
            elif join_info_dict['mod']:
                self.console_write(pinylib.COLOR['bright_red'], 'Moderator %s:%d:%s' % (join_info_dict['nick'],
                                   join_info_dict['id'], join_info_dict['account']))
            else:
                self.console_write(pinylib.COLOR['bright_yellow'], '%s:%d has account: %s' % (join_info_dict['nick'],
                                   join_info_dict['id'], join_info_dict['account']))

                # TODO: Test to see if this works.
                ba = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badaccounts'])
                if ba is not None:
                    if join_info_dict['account'] in ba:
                        if self.is_client_mod:
                            self.send_ban_msg(join_info_dict['nick'], join_info_dict['id'])
                            if CONFIG['baforgive']:
                                self.send_forgive_msg(join_info_dict['id'])
                            self.send_bot_msg(special_unicode['toxic'] + ' *Auto-Banned:* %s (bad account)'
                                              % join_info_dict['account'], self.is_client_mod)

                # Assign botteraccounts if they were in the locally stored file.
                if join_info_dict['account'] in self.botteraccounts:
                    user.has_power = True
        else:
            if join_info_dict['id'] is not self.client_id:
                if not self.is_guest_entry_allowed:
                    self.send_ban_msg(join_info_dict['nick'], join_info_dict['id'])
                    # Remove next line to keep ban.
                    self.send_forgive_msg(join_info_dict['id'])
                    self.send_bot_msg(special_unicode['toxic'] + ' *Auto-Banned:* (guests not allowed)',
                                      self.is_client_mod)
                else:
                    self.console_write(pinylib.COLOR['bright_cyan'], '%s:%d joined the room.' %
                                       (join_info_dict['nick'], join_info_dict['id']))

    def on_joinsdone(self):
        if not self.is_reconnected:
            if CONFIG['auto_message_enabled']:
                self.start_auto_msg_timer()
        if self.is_client_mod:
            self.send_banlist_msg()
        if self.is_client_owner and self._roomtype != 'default':
            threading.Thread(target=self.get_privacy_settings).start()

    def on_avon(self, uid, name):
        if not self.is_broadcasting_allowed or name in self.cam_blocked:
            self.send_close_user_msg(name)
        else:
            user = self.find_user_info(name)

            if not user.is_owner or not user.is_mod or not user.has_power:
                uid_parts = str(uid).split(':')
                if len(uid_parts) is 2:
                    clean_uid = uid_parts[0]
                    user_device = u'' + uid_parts[1]
                    if user_device not in ['android', 'ios']:
                        user_device = 'unknown'
                    user.device_type = user_device
                    self.console_write(pinylib.COLOR['cyan'], '%s:%s is broadcasting from an %s.' %
                                       (name, clean_uid, user_device))

                if self.auto_close:
                    if name.startswith('newuser'):
                        self.send_close_user_msg(name)

                    elif name.startswith('guest-'):
                        self.send_close_user_msg(name)

                    elif user.device_type in ['android', 'ios']:
                        if self.ban_mobiles:
                            self.send_ban_msg(name, uid)
                            # Remove next line to keep ban.
                            self.send_forgive_msg(uid)
                        else:
                            self.send_close_user_msg(name)
                    return

            if len(self.welcome_broadcast_msg) is not 0:
                if len(name) is 2:
                    name = special_unicode['no_width'] + name + special_unicode['no_width']
                self.send_bot_msg('%s *%s*' % (self.welcome_broadcast_msg, name), self.is_client_mod)

            self.console_write(pinylib.COLOR['cyan'], '%s:%s is broadcasting.' % (name, uid))

    def send_auto_pm(self, nickname):
        room = self.roomname.upper()
        new_pm_msg = self.replace_content(self.pm_msg, nickname, room)

        if '|' in new_pm_msg:
            message_parts = new_pm_msg.split('|')
            for x in range(len(message_parts)):
                self.send_private_msg(message_parts[x], nickname)
        else:
            self.send_private_msg(new_pm_msg, nickname)

    def on_nick(self, old, new, uid):
        if uid != self.client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self.room_users.keys():
                del self.room_users[old]
                self.room_users[new] = old_info

            # Fetch latest information regarding the user.
            user = self.find_user_info(new)

            # Transfer temporary botter privileges on a nick change.
            if old in self.botters:
                self.botters.remove(old)
                self.botters.append(new)

            if not user.is_owner or user.is_mod or user.has_power:
                if new.startswith('guest-') and not self.is_guest_nicks_allowed:
                    if self.is_client_mod:
                        self.send_ban_msg(new, uid)
                        # Remove next line to keep ban.
                        self.send_forgive_msg(uid)
                        self.send_bot_msg(special_unicode['toxic'] + ' *Auto-Banned:* (bot nick detected)',
                                          self.is_client_mod)
                        return

                elif new.startswith('newuser') and not self.is_newusers_allowed:
                    if self.is_client_mod:
                            self.send_ban_msg(new, uid)
                            self.send_bot_msg(special_unicode['toxic'] + ' *Auto-Banned:* (new-user nick detected)',
                                              self.is_client_mod)
                            return

            if old.startswith('guest-'):
                bn = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badnicks'])

                if bn is not None and new in bn:
                    if self.is_client_mod:
                        self.send_ban_msg(new, uid)
                        if CONFIG['bnforgive']:
                            self.send_forgive_msg(uid)
                        self.send_bot_msg(special_unicode['toxic'] + ' *Auto-Banned:* (bad nick)', self.is_client_mod)
                else:
                    if user is not None:
                        if self.welcome_user:
                            if user.user_account:
                                self.send_bot_msg(special_unicode['heavy_arrow'] + ' Welcome to %s: *%s*' %
                                                  (self.roomname, user.user_account), self.is_client_mod)
                            else:
                                self.send_bot_msg(special_unicode['heavy_arrow'] + ' Welcome to ' + self.roomname +
                                                  ': *' + special_unicode['no_width'] + new +
                                                  special_unicode['no_width'] + '*', self.is_client_mod)

                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                        if not self.is_mod_playing:
                            # Play the media at the correct start time when the user has set their nick name.
                            self.send_media_broadcast_start(self.last_played_media['type'],
                                                            self.last_played_media['video_id'],
                                                            time_point=self.current_media_time_point(),
                                                            private_nick=new)

                    # Send any private messages set to be sent once their nickname has been set.
                    if self.auto_pm and len(self.pm_msg) is not 0:
                        self.send_auto_pm(new)

            self.console_write(pinylib.COLOR['bright_cyan'], '%s:%s changed nick to: %s' % (old, uid, new))

    def on_kick(self, uid, name):
        if uid != self.client_id:
            user = self.find_user_info(name)
            if user.user_account in self.autoforgive:
                self.send_forgive_msg(user.id)
                self.console_write(pinylib.COLOR['bright_red'], '%s:%s was kicked and has been automatically forgiven.'
                                   % (name, uid))
            else:
                self.console_write(pinylib.COLOR['bright_red'], '%s:%s was banned.' % (name, uid))
                self.send_banlist_msg()

    def on_quit(self, uid, name):
        if uid is not self.client_id:
            if name in self.room_users.keys():
                # Execute the tidying method before deleting the user from our records.
                self.tidy_exit(name)
                del self.room_users[name]
                self.console_write(pinylib.COLOR['cyan'], '%s:%s left the room.' % (name, uid))

    def tidy_exit(self, name):
        user = self.find_user_info(name)
        # Delete user from botters/botteraccounts if they were instated.
        if user.nick in self.botters:
            self.botters.remove(user.nick)
        if user.user_account:
            if user.user_account in self.botteraccounts:
                self.botteraccounts.remove(user.user_account)
        # Delete the nickname from the cam blocked list if the user was in it.
        if user.nick in self.cam_blocked:
            self.cam_blocked.remove(user.nick)

    def on_reported(self, uid, nick):
        self.console_write(pinylib.COLOR['bright_red'], 'The bot was reported by %s:%s.' % (nick, uid))
        if self.bot_report_kick:
            self.send_ban_msg(nick, uid)
            self.send_bot_msg('*Auto-Banned:* (reporting the bot)', self.is_client_mod)
            # Remove next line to keep ban.
            self.send_forgive_msg(uid)

    # Media Events.
    def on_media_broadcast_start(self, media_type, video_id, time_point, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media, youTube or soundCloud.
        :param time_point: int the time point at which the media was begun.
        :param video_id: str the YouTube ID or SoundCloud track ID.
        :param usr_nick: str the user name of the user playing media.
        """
        if self.user_obj.is_mod:
            self.is_mod_playing = True
            self.cancel_media_event_timer()

            # are we in pause state?
            if 'pause' in self.last_played_media:
                # Delete pause time point.
                del self.last_played_media['pause']

            video_time = 0

            if media_type == 'youTube':
                _youtube = youtube.youtube_time(video_id, check=False)
                if _youtube is not None:
                    self.last_played_media = _youtube
                    video_time = _youtube['video_time']

            elif media_type == 'soundCloud':
                _soundcloud = soundcloud.soundcloud_track_info(video_id)
                if _soundcloud is not None:
                    self.last_played_media = _soundcloud
                    video_time = _soundcloud['video_time']

            self.media_event_timer(video_time)
            self.console_write(pinylib.COLOR['bright_magenta'], '%s is playing %s %s (%s)'
                               % (usr_nick, media_type, video_id, time_point))

    def on_media_broadcast_close(self, media_type, usr_nick):
        """
        A user closed a media broadcast.
        :param media_type: str the type of media, youTube or soundCloud.
        :param usr_nick: str the user name of the user closing the media.
        """
        if self.user_obj.is_mod:
            self.cancel_media_event_timer()
            # Are we in pause state?
            if 'pause' in self.last_played_media:
                # Delete pause time point.
                del self.last_played_media['pause']
            self.console_write(pinylib.COLOR['bright_magenta'], '%s closed the %s' % (usr_nick, media_type))

    def on_media_broadcast_play(self, media_type, time_point, usr_nick):
        """
        A user resumed playing a media broadcast.
        :param media_type: str the media type, youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user resuming the tune.
        """
        if self.user_obj.is_mod:
            self.cancel_media_event_timer()
            new_media_time = float(self.last_played_media['video_time']) - time_point
            self.media_start_time = new_media_time

            # Are we in pause state?
            if 'pause' in self.last_played_media:
                # Delete pause time point.
                del self.last_played_media['pause']

            self.media_event_timer(new_media_time)
            self.console_write(pinylib.COLOR['bright_magenta'], '%s resumed the %s at: %s'
                               % (usr_nick, media_type, self.to_human_time(time_point)))

    def on_media_broadcast_paused(self, media_type, usr_nick):
        """
        A user paused the media broadcast.
        :param media_type: str the type of media being paused, youTube or soundCloud.
        :param usr_nick: str the user name of the user pausing the media.
        """
        if self.user_obj.is_mod:
            self.cancel_media_event_timer()
            # Are we in pause state already?
            if 'pause' in self.last_played_media:
                # If so delete old pause time point.
                del self.last_played_media['pause']
            # Make a new pause time point.
            ts_now = int(pinylib.time.time() * 1000)
            self.last_played_media['pause'] = ts_now - self.media_start_time

            self.console_write(pinylib.COLOR['bright_magenta'], '%s paused the %s' % (usr_nick, media_type))

    def on_media_broadcast_skip(self, media_type, time_point, usr_nick):
        """
        A user time searched a tune.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user time searching the tune.
        """
        if self.user_obj.is_mod:
            self.cancel_media_event_timer()
            new_media_time = self.last_played_media['video_time'] - time_point
            self.media_start_time = new_media_time

            if 'pause' in self.last_played_media:
                self.last_played_media['pause'] = new_media_time

            self.media_event_timer(new_media_time)
            self.console_write(pinylib.COLOR['bright_magenta'], '%s time searched the %s at: %s'
                               % (usr_nick, media_type, self.to_human_time(time_point)))

    # Media Message Method.
    def send_media_broadcast_start(self, media_type, video_id, time_point=0, private_nick=None):
        """
        Starts a media broadcast.
        NOTE: This method replaces play_youtube and play_soundcloud.
        :param media_type: str 'youTube' or 'soundCloud'
        :param video_id: str the media video ID.
        :param time_point: int where to start the media from in milliseconds.
        :param private_nick: str if not None, start the media broadcast for this username only.
        """
        mbs_msg = '/mbs %s %s %s' % (media_type, video_id, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbs_msg)
        else:
            self.is_mod_playing = False
            self.send_chat_msg(mbs_msg)

    # TODO: msg_raw implemented here in prevent spam?
    def prevent_spam(self, msg, msg_sender):
        """
        Spam checks to ensure chat box is rid any potential further spam.
        :param msg: str the message the user sent.
        :param msg_sender: str the nick name of the message sender.
        """
        # Reset the spam check at each message check, this allows us to know if the message should be passed onto
        # any further procedures.
        self.spam_potential = False
        user = self.find_user_info(msg_sender)

        # Always check to see if the user's message has any bad strings initially.
        if self.check_bad_string:
            check = self.check_msg_for_bad_string(msg)
            if check:
                self.spam_potential = True
                return

        # Check these unicode characters to see if they are present.
        unicode_spam_chars = [u'\u25b2', u'\x85']

        # Ban those who post messages with special unicode characters which is considered spam.
        if self.unicode_spam:
            for x in xrange(len(unicode_spam_chars)):
                if msg.find(unicode_spam_chars[x]) >= 0:
                    if self.is_client_mod:
                        self.send_ban_msg(user.nick, user.id)
                        self.spam_potential = True
                    return

        # Ban those who post excessive messages in both uppercase and exceeding a specified character limit.
        if self.message_caps_limit:
            if len(msg) >= self.caps_char_limit:
                # Search for all caps and numbers in the message which exceed the length of the characters stated in
                # the character limit.
                over_limit = re.search(r'[A-Z0-9]', msg)
                if over_limit:
                    if self.is_client_mod:
                        self.send_ban_msg(user.nick, user.id)
                        if CONFIG['caps_char_forgive']:
                            self.send_forgive_msg(user.id)
                    self.spam_potential = True
                    return

        # Kick/ban those who post links to other rooms.
        if self.room_link_spam:
            if 'tinychat.com/' + self.roomname not in msg:
                text_search = re.search(r'tinychat.com\/\w+($| |\/+ |\/+$)', msg, re.I)
                if text_search:
                    if self.is_client_mod:
                        self.send_ban_msg(user.nick, user.id)
                    self.spam_potential = True
                    return

        # If snapshot prevention is on, make sure we kick/ban the user.
        if self.snapshot_spam:
            if self.snap_line in msg:
                if self.is_client_mod:
                    self.send_ban_msg(user.nick, user.id)
                    # Remove next line to keep ban.
                    self.send_forgive_msg(user.id)
                self.spam_potential = True
                return

    # Message Method.
    def send_bot_msg(self, msg, is_mod=False):
        """
        Send a chat message to the room.
        :param msg: str the message to send.
        :param is_mod: boolean True send a owner run message, False send a normal chat message.
        """
        if is_mod:
            self.send_owner_run_msg(msg)
        else:
            self.send_chat_msg(msg)

    def message_handler(self, msg_sender, msg):
        """
        Custom message/command handler.

        NOTE: Any method using an API will start in a new thread along with
        methods that require more CPU attention. Otherwise, these can be intrusive
        to the processes running within the bot.
        :param msg_sender: str the user sending a message.
        :param msg: str the message.
        """
        # Spam checks to prevent any text from spamming the room chat and being parsed by the bot.
        if self.spam_prevention:
            if not self.user_obj.is_owner and not self.user_obj.is_super and not self.user_obj.is_mod \
                    and not self.user_obj.has_power:
                # Start the spam check.
                spam_check = threading.Thread(target=self.prevent_spam, args=(msg, msg_sender,))
                spam_check.start()

                # Wait until the spam check has finished then continue like normal. This avoids breaking any
                # particular handling of messages if the message was spam and proceeds into functions; this can
                # potentially bear many undesired effects.
                spam_check.join()
                # TODO: See spam potential without being a moderator, to reduce spam in console(?)
                if self.spam_potential:
                    self.console_write(pinylib.COLOR['bright_red'], 'Spam inbound, returning back.')
                    return

            # If auto URL has been switched on, run, in a new the thread, the automatic URL header retrieval.
            if self.auto_url_mode:
                threading.Thread(target=self.do_auto_url, args=(msg, )).start()

        # TODO: Added CleverBot instant call.
        # if the message begins with the client nickname and CleverBot Instant is turned on, send the message to
        # to the active session.
        if self.clever_bot_enable:
            if self.clever_bot_instant:
                if self.client_nick in msg.lower():
                    # if msg.lower().startswith('%s ' % self.client_nick): (only first method)
                    # There are two ways of going about sending a reply.
                    # One is to take the message after the nickname, meaning the nickname has to be first in
                    # the message.
                    # This is more safe to use and usually yields a more accurate response.
                    # The second is replacing the nickname with a blank space and taking the resulting message, this may
                    # result is an abnormal response, though covers a variety of responses.
                    # Only first method.
                    # query = msg.split('%s ' % self.client_nick)[1]
                    # The second method.
                    query = msg.lower().replace(self.client_nick, '')
                    threading.Thread(target=self.do_clever_bot, args=(query, True, )).start()
                    self.console_write(pinylib.COLOR['yellow'], '%s [CleverBot]:%s' %
                                       (self.user_obj.nick, query.strip()))
                    return

        # Is this a custom command?
        if msg.startswith(CONFIG['prefix']):
            # Split the message in to parts.
            parts = msg.split(' ')
            # parts[0] is the command.
            cmd = parts[0].lower().strip()
            # The rest is a command argument.
            cmd_arg = ' '.join(parts[1:]).strip()

            # Waive handling messages to normal users if the bot listening is set to False and the user
            # is not owner/super mod/mod/botter.
            if not self.bot_listen:
                if cmd == CONFIG['prefix'] + 'pmme':
                    self.do_pmme()
                else:
                    self.console_write(pinylib.COLOR['bright_red'], self.user_obj.nick + ':' + msg + ' [Not handled]')
                return

            # Super mod commands:
            if cmd == CONFIG['prefix'] + 'mod':
                threading.Thread(target=self.do_make_mod, args=(cmd_arg,)).start()

            elif cmd == CONFIG['prefix'] + 'rmod':
                threading.Thread(target=self.do_remove_mod, args=(cmd_arg,)).start()

            elif cmd == CONFIG['prefix'] + 'dir':
                threading.Thread(target=self.do_directory).start()

            elif cmd == CONFIG['prefix'] + 'p2t':
                threading.Thread(target=self.do_push2talk).start()

            elif cmd == CONFIG['prefix'] + 'gr':
                threading.Thread(target=self.do_green_room).start()

            elif cmd == CONFIG['prefix'] + 'crb':
                threading.Thread(target=self.do_clear_room_bans).start()

            # Owner and super mod commands:
            elif cmd == CONFIG['prefix'] + 'kill':
                self.do_kill()

            # Mod and bot controller commands:
            # - Lower-level commands (toggles):
            elif cmd == CONFIG['prefix'] + 'sleep':
                self.do_sleep()

            elif cmd == CONFIG['prefix'] + 'reboot':
                self.do_reboot()

            elif cmd == CONFIG['prefix'] + 'spam':
                self.do_spam()

            elif cmd == CONFIG['prefix'] + 'snap':
                self.do_snapshot()

            elif cmd == CONFIG['prefix'] + 'camblock':
                self.do_camblock(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'autoclose':
                self.do_autoclose()

            elif cmd == CONFIG['prefix'] + 'mobiles':
                self.do_ban_mobiles()

            elif cmd == CONFIG['prefix'] + 'autourl':
                self.do_auto_url_mode()

            elif cmd == CONFIG['prefix'] + 'playlist':
                self.do_playlist_mode()

            elif cmd == CONFIG['prefix'] + 'publicmedia':
                self.do_public_media()

            elif cmd == CONFIG['prefix'] + 'guests':
                self.do_guest_nick_ban()

            elif cmd == CONFIG['prefix'] + 'newuser':
                self.do_newuser_user_ban()

            elif cmd == CONFIG['prefix'] + 'mute':
                threading.Thread(target=self.do_mute).start()

            elif cmd == CONFIG['prefix'] + 'p2tnow':
                self.do_instant_push2talk()

            elif cmd == CONFIG['prefix'] + 'autopm':
                self.do_auto_pm()

            elif cmd == CONFIG['prefix'] + 'privateroom':
                self.do_private_room()

            # TODO: Add in cleverbot enable toggles.
            elif cmd == CONFIG['prefix'] + 'cleverbot':
                self.do_clever_bot_state()

            # - Higher-level commands:
            elif cmd == CONFIG['prefix'] + 'botter':
                threading.Thread(target=self.do_botter, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'protect':
                threading.Thread(target=self.do_autoforgive, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'close':
                self.do_close_broadcast(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'clr':
                self.do_clear()

            elif cmd == CONFIG['prefix'] + 'media':
                self.do_media_info()

            elif cmd == CONFIG['prefix'] + 'topicis':
                threading.Thread(target=self.do_current_topic).start()

            elif cmd == CONFIG['prefix'] + 'topic':
                self.do_topic(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'kick':
                self.do_kick(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'ban':
                self.do_kick(cmd_arg, True)

            elif cmd == CONFIG['prefix'] + 'forgive':
                threading.Thread(target=self.do_forgive, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'bn':
                threading.Thread(target=self.do_bad_nick, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'rmbn':
                self.do_remove_bad_nick(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'bs':
                threading.Thread(target=self.do_bad_string, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'rmbs':
                self.do_remove_bad_string(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'ba':
                threading.Thread(target=self.do_bad_account, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'rmba':
                self.do_remove_bad_account(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'list':
                self.do_list_info(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'uinfo':
                threading.Thread(target=self.do_user_info, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'rs':
                threading.Thread(target=self.do_room_settings).start()

            # Standard media commands:
            elif cmd == CONFIG['prefix'] + 'yt':
                threading.Thread(target=self.do_play_media, args=(self.yt_type, cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'sc':
                threading.Thread(target=self.do_play_media, args=(self.sc_type, cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'syncall':
                threading.Thread(target=self.do_sync_media, args=(True, )).start()

            elif cmd == CONFIG['prefix'] + 'syt':
                threading.Thread(target=self.do_youtube_search, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'psyt':
                self.do_play_youtube_search(cmd_arg)

            # Specific media control commands:
            # TODO: Requires new media handling class.

            elif cmd == CONFIG['prefix'] + 'replay':
                self.do_media_replay()

            elif cmd == CONFIG['prefix'] + 'skip':
                self.do_skip()

            elif cmd == CONFIG['prefix'] + 'stop':
                self.do_close_media()

            # TODO: Awaiting a media handling class, otherwise works properly.
            # elif cmd == CONFIG['prefix'] + 'pause':
            #     self.do_pause_media()

            # TODO: The media timer distorts the true value of the final media time, so it does not resume at
            #       the real paused time point (most likely since we deducted the wrong media time away from the pause
            #       time. So we are just awaiting a media handling class to handle all these activities.
            # elif cmd == CONFIG['prefix'] + 'resume':
            #     self.do_resume_media()

            # TODO: Make sure the time is correctly updated in the background media timer,
            #       so newly joined users receive the correct time.
            # elif cmd == CONFIG['prefix'] + 'seek':
            #     self.do_seek_media(cmd_arg)

            # Playlist media commands:
            elif cmd == CONFIG['prefix'] + 'pl':
                threading.Thread(target=self.do_youtube_playlist_videos, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'plsh':
                threading.Thread(target=self.do_youtube_playlist_search, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'pladd':
                threading.Thread(target=self.do_youtube_playlist_search_choice, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'top40':
                threading.Thread(target=self.do_charts).start()

            elif cmd == CONFIG['prefix'] + 'top':
                threading.Thread(target=self.do_lastfm_chart, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'ran':
                threading.Thread(target=self.do_lastfm_random_tunes, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'tag':
                threading.Thread(target=self.search_lastfm_by_tag, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'rm':
                self.do_delete_playlist_item(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'cpl':
                self.do_clear_playlist()

            elif cmd == CONFIG['prefix'] + 'a':
                threading.Thread(target=self.do_media_request_choice, args=(True,)).start()

            elif cmd == CONFIG['prefix'] + 'd':
                threading.Thread(target=self.do_media_request_choice, args=(False,)).start()

            # Public commands:
            elif cmd == CONFIG['prefix'] + 'v':
                threading.Thread(target=self.do_version).start()

            elif cmd == CONFIG['prefix'] + 'help':
                threading.Thread(target=self.do_help).start()

            elif cmd == CONFIG['prefix'] + 'now':
                threading.Thread(target=self.do_now_playing).start()

            elif cmd == CONFIG['prefix'] + 'next':
                threading.Thread(target=self.do_next_tune_in_playlist).start()

            elif cmd == CONFIG['prefix'] + 'pls':
                threading.Thread(target=self.do_playlist_status).start()

            elif cmd == CONFIG['prefix'] + 'uptime':
                self.do_uptime()

            elif cmd == CONFIG['prefix'] + 'pmme':
                self.do_pmme()

            elif cmd == CONFIG['prefix'] + 'reqyt':
                threading.Thread(target=self.do_media_request, args=(self.yt_type, cmd_arg)).start()

            elif cmd == CONFIG['prefix'] + 'reqsc':
                threading.Thread(target=self.do_media_request, args=(self.sc_type, cmd_arg)).start()

            # - Private media commands:
            elif cmd == CONFIG['prefix'] + 'ytme':
                threading.Thread(target=self.do_play_private_media, args=(self.yt_type, cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'scme':
                threading.Thread(target=self.do_play_private_media, args=(self.sc_type, cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'sync':
                threading.Thread(target=self.do_sync_media).start()

            elif cmd == CONFIG['prefix'] + 'stopme':
                threading.Thread(target=self.do_stop_private_media).start()

            # TODO: Private media methods maybe required, though only implemened after media class.
            # [Private pause/rewind/seek procedures here]

            # API commands:
            # - Tinychat API commands:
            elif cmd == CONFIG['prefix'] + 'spy':
                threading.Thread(target=self.do_spy, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'acspy':
                threading.Thread(target=self.do_account_spy, args=(cmd_arg, )).start()

            # - External API commands:
            elif cmd == CONFIG['prefix'] + 'urb':
                threading.Thread(target=self.do_search_urban_dictionary, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'wea':
                threading.Thread(target=self.do_weather_search, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'ip':
                threading.Thread(target=self.do_whois_ip, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'ddg':
                threading.Thread(target=self.do_duckduckgo_search, args=(cmd_arg, )).start()

            # TODO: Fix bug in Wikipedia parsing.
            elif cmd == CONFIG['prefix'] + 'wiki':
                threading.Thread(target=self.do_wiki_search, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'imdb':
                threading.Thread(target=self.do_omdb_search, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'ety':
                threading.Thread(target=self.do_etymonline_search, args=(cmd_arg, )).start()

            # Entertainment/alternative media commands:
            elif cmd == CONFIG['prefix'] + 'cb':
                threading.Thread(target=self.do_clever_bot, args=(cmd_arg, )).start()

            elif cmd == CONFIG['prefix'] + 'cn':
                threading.Thread(target=self.do_chuck_norris).start()

            elif cmd == CONFIG['prefix'] + '8ball':
                self.do_8ball(cmd_arg)

            elif cmd == CONFIG['prefix'] + 'yomama':
                threading.Thread(target=self.do_yo_mama_joke).start()

            elif cmd == CONFIG['prefix'] + 'advice':
                threading.Thread(target=self.do_advice).start()

            elif cmd == CONFIG['prefix'] + 'joke':
                threading.Thread(target=self.do_one_liner, args=(cmd_arg, )).start()

            # TODO: Place these two function into one and provide variable to determine the use of one.
            elif cmd == CONFIG['prefix'] + 'time':
                threading.Thread(target=self.do_time, args=(cmd_arg, )).start()

            # TODO: Allow non-military time conversion (24 hr --> 12 hr with AM/PM) via argument(?)
            elif cmd == CONFIG['prefix'] + 'time+':
                threading.Thread(target=self.do_time, args=(cmd_arg, True)).start()

            elif cmd == CONFIG['prefix'] + 'time12':
                threading.Thread(target=self.do_time, args=(cmd_arg, True, True)).start()

            else:
                # Main call to check if the command is an ASCII command.
                if ascii_chars:
                    ascii_result = self.do_ascii(cmd)
                    if ascii_result:
                        return

            #  Print command to console.
            self.console_write(pinylib.COLOR['yellow'], self.user_obj.nick + ':' + cmd + ' ' + cmd_arg)

        else:
            # Print chat message to console.
            self.console_write(pinylib.COLOR['green'], self.user_obj.nick + ':' + msg)

        # Add msg to user object last_msg attribute.
        self.user_obj.last_msg = msg

    # == Super Mod Commands Methods. ==
    def do_make_mod(self, account):
        """
        Make a tinychat account a room moderator.
        :param account str the account to make a moderator.
        """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if len(account) is 0:
                    self.send_bot_msg('*Missing account name.*', self.is_client_mod)
                else:
                    tc_user = self.privacy_settings.make_moderator(account)
                    if tc_user is None:
                        self.send_bot_msg('*The account is invalid.*', self.is_client_mod)
                    elif tc_user:
                        self.send_bot_msg('*' + account + ' was made a room moderator.*', self.is_client_mod)
                    elif not tc_user:
                        self.send_bot_msg('*The account is already a moderator.*', self.is_client_mod)

    def do_remove_mod(self, account):
        """
        Removes a tinychat account from the moderator list.
        :param account str the account to remove from the moderator list.
        """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if len(account) is 0:
                    self.send_bot_msg('*Missing account name.*', self.is_client_mod)
                else:
                    tc_user = self.privacy_settings.remove_moderator(account)
                    if tc_user:
                        self.send_bot_msg('*' + account + ' is no longer a room moderator.*', self.is_client_mod)
                    elif not tc_user:
                        self.send_bot_msg('*' + account + ' is not a room moderator.*', self.is_client_mod)

    def do_directory(self):
        """ Toggles if the room should be shown on the directory. """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if self.privacy_settings.show_on_directory():
                    self.send_bot_msg('*Room IS shown on the directory.*', self.is_client_mod)
                else:
                    self.send_bot_msg('*Room is NOT shown on the directory.*', self.is_client_mod)

    def do_push2talk(self):
        """ Toggles if the room should be in push2talk mode. """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if self.privacy_settings.set_push2talk():
                    self.send_bot_msg('*Push2Talk is enabled.*', self.is_client_mod)
                else:
                    self.send_bot_msg('*Push2Talk is disabled.*', self.is_client_mod)

    def do_green_room(self):
        """ Toggles if the room should be in greenroom mode. """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if self.privacy_settings.set_greenroom():
                    self.send_bot_msg('*Green room is enabled.*', self.is_client_mod)
                else:
                    self.send_bot_msg('*Green room is disabled.*', self.is_client_mod)

    def do_clear_room_bans(self):
        """ Clear all room bans. """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if self.privacy_settings.clear_bans():
                    self.send_bot_msg('*All room bans was cleared.*', self.is_client_mod)

    # == Owner And Super Mod Command Methods. ==
    def do_kill(self):
        """ Kills the bot. """
        if self.user_obj.is_owner or self.user_obj.is_super:
            threading.Thread(target=self.disconnect).start()
            # Exit normally.
            sys.exit(0)

    # == Owner And Mod Command Methods. ==
    def do_reboot(self):
        """ Reboots the bot. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod:
            self.reconnect()

    # == Owner/ Super Mod/ Mod/ Power users Command Methods. ==
    def do_media_info(self):
        """ Shows basic media info. """
        # This method was used while debugging the media player.
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                self.send_owner_run_msg('Playlist: *I Now Play*: %s' % str(self.inowplay))
                self.send_owner_run_msg('Playlist: *Length*: %s' % len(self.playlist))
                self.send_owner_run_msg('Media: *Current Time Point:* %s' %
                                        self.to_human_time(self.current_media_time_point()))
                self.send_owner_run_msg('Media: *Active Threads:* %s' % threading.active_count())

    # TODO: Possible sleep mode/night/inactive/low-power mode; allow hibernation activities/features.
    def do_sleep(self):
        """ Sets the bot to sleep so commands from everyone will be ignored until it is woken up by a PM. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.bot_listen = False
            self.send_bot_msg('*Bot listening set to*: *%s*' % self.bot_listen, self.is_client_mod)

    def do_spam(self):
        """ Toggles spam prevention """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.spam_prevention = not self.spam_prevention
            self.send_bot_msg('*Text Spam Prevention*: *%s*' % self.spam_prevention, self.is_client_mod)

    def do_snapshot(self):
        """ Toggles 'snapshot' prevention. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.snapshot_spam = not self.snapshot_spam
            self.send_bot_msg('*Snapshot Prevention*: *%s*' % self.snapshot_spam, self.is_client_mod)

    def do_autoclose(self):
        """ Toggles autoclose. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.auto_close = not self.auto_close
            self.send_bot_msg('*Auto closing mobiles/guests/newusers*: *%s*' % self.auto_close, self.is_client_mod)

    def do_ban_mobiles(self):
        """ Toggles ban on all recognised, broadcasting mobile devices. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.ban_mobiles = not self.ban_mobiles
            self.send_bot_msg('*Banning mobile users on cam*: *%s*' % self.ban_mobiles, self.is_client_mod)

    def do_auto_url_mode(self):
        """ Toggles auto url mode. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.auto_url_mode = not self.auto_url_mode
            self.send_bot_msg('*Auto-Url Mode*: *%s*' % self.auto_url_mode, self.is_client_mod)

    def do_playlist_mode(self):
        """ Toggles playlist mode. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.playlist_mode = not self.playlist_mode
            self.send_bot_msg('*Playlist Mode*: *%s*' % self.playlist_mode, self.is_client_mod)

    def do_public_media(self):
        """
        Toggles public media mode which allows the public to add media to the playlist or play media.
        NOTE: Playlist mode will be automatically enforced when public media is turned on. This is to prevent the
              spamming of media plays in the room. Playlist mode will have to be turned off manually if it is not
              going to be used if public media is going to be disabled.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.public_media = not self.public_media
            if self.public_media:
                self.playlist_mode = True
            self.send_bot_msg('*Public Media Mode*: *%s*' % self.public_media, self.is_client_mod)

    def do_guest_nick_ban(self):
        """ Toggles guest nickname banning. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.is_guest_nicks_allowed = not self.is_guest_nicks_allowed
            self.send_bot_msg('*Banning "guests-"*: *%s*' % self.is_guest_nicks_allowed, self.is_client_mod)

    def do_newuser_user_ban(self):
        """ Toggles new user banning. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.is_newusers_allowed = not self.is_newusers_allowed
            self.send_bot_msg('*New-user banning*: *%s*' % self.is_newusers_allowed, self.is_client_mod)

    def do_camblock(self, on_block):
        """
        Adds a user to the cam-blocked list to prevent them from camming up temporarily.
        :param: on_block: str the nick name of the user who may or may not be in the blocked list.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(on_block) is 0:
                self.send_bot_msg(special_unicode['indicate'] + ' Please state a user to cam block.',
                                  self.is_client_mod)
            else:
                user = self.find_user_info(on_block)
                if user is not None:
                    if user.nick not in self.cam_blocked:
                        self.cam_blocked.append(user.nick)
                        self.send_close_user_msg(user.nick)
                        self.send_bot_msg(special_unicode['check_mark'] + ' *' + special_unicode['no_width'] +
                                          user.nick + special_unicode['no_width'] + '* is now cam blocked.',
                                          self.is_client_mod)
                    else:
                        self.cam_blocked.remove(user.nick)
                        self.send_bot_msg(special_unicode['cross_mark'] + ' *' + special_unicode['no_width'] +
                                          user.nick + special_unicode['no_width'] + '* is no longer cam blocked.',
                                          self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] + ' The user you stated does not exist.',
                                      self.is_client_mod)

    def do_mute(self):
        """ Sends a room mute microphone message to all broadcasting users. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.send_mute_msg()

    def do_instant_push2talk(self):
        """ Sets microphones broadcasts to 'push2talk'. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.send_push2talk_msg()

    def do_auto_pm(self):
        """ Toggles on the automatic room private message. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(self.pm_msg) is not 0:
                self.auto_pm = not self.auto_pm
                self.send_bot_msg('*Auto PM*: *%s*' % self.auto_pm, self.is_client_mod)
            else:
                self.send_bot_msg('There is no PM message set    in the configuration file.', self.is_client_mod)

    def do_private_room(self):
        """" Sets room to private room. """
        if self.is_client_mod:
            if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                self.send_private_room_msg()
                self.private_room = not self.private_room
                self.send_bot_msg('Private Room is now set to: *%s*' % self.private_room, self.is_client_mod)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_clever_bot_state(self):
        """ Sets CleverBot to function in the room (as an instant call or via command). """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.clever_bot_enable = not self.clever_bot_enable
            self.send_bot_msg('*CleverBot* enabled: *%s*' % self.clever_bot_enable, self.is_client_mod)

    # TODO: Levels of botters - maybe just media users.
    def do_botter(self, new_botter):
        """
        Adds a new botter to allow control over the bot and appends the user to the list
        of botters, and IF they are signed, in to the botter accounts list and save their
        account to file as well.
        :param new_botter: str the nick name of the user to bot.
        """

        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod:
            if len(new_botter) is 0:
                self.send_bot_msg(special_unicode['indicate'] + ' Please state a nickname to bot.', self.is_client_mod)
            else:
                bot_user = self.find_user_info(new_botter)
                if not bot_user.is_owner or not bot_user.is_mod:
                    if bot_user is not None:
                        # Adding new botters
                        if bot_user.user_account and bot_user.user_account not in self.botteraccounts:
                            self.botteraccounts.append(bot_user.user_account)
                            writer = pinylib.fh.file_writer(CONFIG['path'], CONFIG['botteraccounts'],
                                                            bot_user.user_account)
                            if writer:
                                bot_user.has_power = True
                                self.send_bot_msg(special_unicode['black_star'] + ' *' + new_botter + '*' +
                                                  ' was added as a verified botter.', self.is_client_mod)

                        elif not bot_user.user_account and bot_user.nick not in self.botters:
                            self.botters.append(bot_user.nick)
                            bot_user.has_power = True
                            self.send_bot_msg(special_unicode['black_star'] + ' *' + new_botter + '*' +
                                              ' was added as a temporary botter.', self.is_client_mod)

                        else:
                            # Removing existing botters or verified botters.
                            remove = False

                            if bot_user.user_account:
                                for x in range(len(self.botteraccounts)):
                                    if self.botteraccounts[x] == bot_user.user_account:
                                        del self.botteraccounts[x]
                                        remove = pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['botteraccounts'],
                                                                             bot_user.user_account)
                                        break
                            else:
                                for x in range(len(self.botters)):
                                    if self.botters[x] == bot_user.nick:
                                        del self.botters[x]
                                        remove = True
                                        break

                            if remove:
                                bot_user.has_power = False
                                self.send_bot_msg(special_unicode['white_star'] + ' *' + new_botter +
                                                  '* was removed from botting.', self.is_client_mod)
                    else:
                        self.send_bot_msg(special_unicode['indicate'] + ' No user named: ' + new_botter,
                                          self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' This user already has privileges. No need to bot.', self.is_client_mod)

    def do_autoforgive(self, new_autoforgive):
        """
        Adds a new autoforgive user, IF user is logged in, to the autoforgive file;
        all users in this file be automatically forgiven if they are banned.
        :param new_autoforgive: str the nick name of the user to add to autoforgive.
        """

        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod:
            if len(new_autoforgive) is not 0:
                autoforgive_user = self.find_user_info(new_autoforgive)
                if autoforgive_user is not None:
                    if autoforgive_user.user_account and autoforgive_user.user_account not in self.autoforgive:
                        self.autoforgive.append(autoforgive_user.user_account)
                        self.send_bot_msg(special_unicode['black_heart'] + ' *' + special_unicode['no_width'] +
                                          new_autoforgive + special_unicode['no_width'] + '*' +
                                          ' is now protected.', self.is_client_mod)
                        pinylib.fh.file_writer(CONFIG['path'], CONFIG['autoforgive'], autoforgive_user.user_account)
                    elif not autoforgive_user.user_account:
                        self.send_bot_msg(
                            special_unicode['indicate'] + ' Protection is only available to users with accounts.',
                            self.is_client_mod)
                    else:
                        for x in range(len(self.autoforgive)):
                            if self.autoforgive[x] == autoforgive_user.user_account:
                                del self.autoforgive[x]
                                pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['autoforgive'],
                                                            autoforgive_user.user_account)
                                self.send_bot_msg(special_unicode['white_heart'] + ' *' + special_unicode['no_width'] +
                                                  new_autoforgive + special_unicode['no_width'] +
                                                  '* is no longer protected.', self.is_client_mod)
                                break
                else:
                    self.send_bot_msg(special_unicode['indicate'] + ' No user named: ' + new_autoforgive,
                                      self.is_client_mod)
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Please state a nickname to protect.',
                                  self.is_client_mod)

    def do_close_broadcast(self, nick_name):
        """
        Close a user broadcasting.
        :param nick_name: str the nickname to close.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(nick_name) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing nickname.', self.is_client_mod)
                else:
                    user = self.find_user_info(nick_name)
                    if user is not None:
                        self.send_close_user_msg(nick_name)
                    else:
                        self.send_bot_msg(special_unicode['indicate'] + ' No nickname called: ' +
                                          nick_name, self.is_client_mod)

    def do_clear(self):
        """ Clears the chat-box. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                for x in range(0, 25):
                    self.send_owner_run_msg(' ')
            else:
                clear = '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133' \
                        '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133'
                self._send_command('privmsg', [clear, u'#262626,en'])
            self.send_bot_msg(special_unicode['state'] + ' *The chat was cleared by ' + str(self.user_obj.nick) + '*',
                              self.is_client_mod)

    def do_nick(self, new_nick):
        """
        Set a new nick for the bot.
        :param new_nick: str the new nick.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(new_nick) is 0:
                self.client_nick = pinylib.create_random_string(5, 25)
                self.set_nick()
            else:
                if re.match('^[][\{\}a-zA-Z0-9_-]{1,25}$', new_nick):
                    self.client_nick = new_nick
                    self.set_nick()

    def do_topic(self, topic):
        """
        Sets the room topic.
        :param topic: str the new topic.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(topic) is 0:
                    self.send_topic_msg('')
                    self.send_bot_msg('Topic was *cleared&.', self.is_client_mod)
                else:
                    self.send_topic_msg(topic)
                    self.send_bot_msg(special_unicode['state'] + ' The *room topic* was set to: ' + topic,
                                      self.is_client_mod)
            else:
                self.send_bot_msg('Command not enabled.')

    def do_current_topic(self):
        """ Replies to the user what the current room topic is. """
        self.send_undercover_msg(self.user_obj.nick, 'The *current topic* is: %s' % self.topic_msg)

    def do_kick(self, nick_name, ban=False, discrete=False):
        """
        Kick/ban a user in the room.
        :param nick_name: str the nickname to kick or ban.
        :param ban: boolean True/False respectively if the user should be banned or not.
        :param discrete: boolean True/False respectively if the user to ban should be banned discretely.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(nick_name) is 0:
                    if not discrete:
                        self.send_bot_msg(special_unicode['indicate'] + ' Missing nickname.', self.is_client_mod)
                elif nick_name == self.client_nick:
                    if not discrete:
                        self.send_bot_msg(special_unicode['indicate'] + ' Action not allowed.', self.is_client_mod)
                else:
                    user = self.find_user_info(nick_name)
                    if user is not None:
                        if user.is_owner or user.is_super or user.is_mod and not self.user_obj.is_owner:
                            if not discrete:
                                self.send_bot_msg(special_unicode['indicate'] +
                                                  ' You cannot kick/ban a user with privileges.', self.is_client_mod)
                            return

                        if not self.user_obj.is_owner or not self.user_obj.is_super or not self.user_obj.is_mod:
                            if user.nick in self.botters:
                                if not discrete:
                                    self.send_bot_msg(special_unicode['indicate'] +
                                                      ' You cannot kick/ban another botter.', self.is_client_mod)
                                return
                            elif user.user_account:
                                if user.user_account in self.botteraccounts:
                                    if not discrete:
                                        self.send_bot_msg(special_unicode['indicate'] +
                                                          ' You cannot kick/ban another verified botter.',
                                                          self.is_client_mod)
                                    return

                        self.send_ban_msg(user.nick, user.id)
                        if not ban:
                            self.send_forgive_msg(user.id)

                    else:
                        if not discrete:
                            self.send_bot_msg(special_unicode['indicate'] + ' No user named: *' +
                                              special_unicode['no_width'] + nick_name + special_unicode['no_width'] +
                                              '*', self.is_client_mod)
            else:
                if not discrete:
                    self.send_bot_msg('Command not enabled.')

    # TODO: Allow un-ban of users who were not banned by the bot; this will mean the bot will have to read bans from
    #       moderators and request the new ban list accordingly. Maybe we can get initial ban list and store temporary
    #       one and work from there.
    def do_forgive(self, nick_name):
        """
        Forgive a user based on if their user id (uid) is found in the room's ban list.
        :param nick_name: str the nick name of the user that was banned.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(self.room_banlist) > 0:
                if len(nick_name) is not 0:
                    if nick_name in self.room_banlist:
                        uid = self.room_banlist[nick_name]
                        self.send_forgive_msg(str(uid))
                        self.send_bot_msg('*' + special_unicode['no_width'] + nick_name + special_unicode['no_width'] +
                                          '* has been forgiven.', self.is_client_mod)
                    else:
                        self.send_bot_msg(special_unicode['indicate'] + ' The user was not found in the banlist.',
                                          self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' Please state a nick to forgive from the ban list.', self.is_client_mod)
            else:
                self.send_bot_msg('The *banlist is empty*. No one to forgive.', self.is_client_mod)

    def do_forgive_all(self):
        """ Forgive all the user in the banlist. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if not self.forgive_all:
                self.send_undercover_msg(self.user_obj.nick, 'Now *forgiving all* users in the banlist...')
                self.forgive_all = True
                for uid in self.room_banlist.values():
                    self.send_forgive_msg(str(uid))
                    pinylib.time.sleep(1)
                self.forgive_all = False
            else:
                self.send_bot_msg('We have not finished forgiving everyone in the banlist. Try again later.',
                                  self.is_client_mod)

    def do_bad_nick(self, bad_nick):
        """
        Adds a bad username to the bad nicks file.
        :param bad_nick: str the bad nick to write to file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_nick) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing nickname.', self.is_client_mod)
                else:
                    badnicks = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badnicks'])
                    if badnicks is None:
                        pinylib.fh.file_writer(CONFIG['path'], CONFIG['badnicks'], bad_nick)
                    else:
                        if bad_nick in badnicks:
                            self.send_bot_msg(bad_nick + ' is already in list.', self.is_client_mod)
                        else:
                            pinylib.fh.file_writer(CONFIG['path'], CONFIG['badnicks'], bad_nick)
                            self.send_bot_msg('*' + bad_nick + '* was added to *bad nicknames*.', self.is_client_mod)
                            if bad_nick in self.room_users.keys():
                                bn_user = self.find_user_info(bad_nick)
                                self.send_ban_msg(bn_user.nick, bn_user.id)

    def do_remove_bad_nick(self, bad_nick):
        """
        Removes a bad nick from bad nicks file.
        :param bad_nick: str the bad nick to remove from file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_nick) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing nickname', self.is_client_mod)
                else:
                    rem = pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['badnicks'], bad_nick)
                    if rem:
                        self.send_bot_msg(bad_nick + ' was removed.', self.is_client_mod)

    def do_bad_string(self, bad_string):
        """
        Adds a bad string to the bad strings file.
        :param bad_string: str the bad string to add to file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_string) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Bad string can\'t be blank.', self.is_client_mod)
                elif len(bad_string) < 3:
                    self.send_bot_msg(special_unicode['indicate'] + ' Bad string to short: ' + str(len(bad_string)),
                                      self.is_client_mod)
                else:
                    bad_strings = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badstrings'])
                    if bad_strings is None:
                        pinylib.fh.file_writer(CONFIG['path'], CONFIG['badstrings'], bad_string)
                    else:
                        if bad_string in bad_strings:
                            self.send_bot_msg(bad_string + ' is already in list.', self.is_client_mod)
                        else:
                            pinylib.fh.file_writer(CONFIG['path'], CONFIG['badstrings'], bad_string)
                            self.send_bot_msg('*' + bad_string + '* was added to *bad strings*.', self.is_client_mod)

    def do_remove_bad_string(self, bad_string):
        """
        Removes a bad string from the bad strings file.
        :param bad_string: str the bad string to remove from file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_string) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing word string.', self.is_client_mod)
                else:
                    rem = pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['badstrings'], bad_string)
                    if rem:
                        self.send_bot_msg(bad_string + ' was removed.', self.is_client_mod)

    def do_bad_account(self, bad_account_name):
        """
        Adds a bad account name to the bad accounts file.
        :param bad_account_name: str the bad account name to file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_account_name) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Account can\'t be blank.', self.is_client_mod)
                elif len(bad_account_name) < 3:
                    self.send_bot_msg(special_unicode['indicate'] + ' Account to short: ' + str(len(bad_account_name)),
                                      self.is_client_mod)
                else:
                    bad_accounts = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badaccounts'])
                    if bad_accounts is None:
                        pinylib.fh.file_writer(CONFIG['path'], CONFIG['badaccounts'], bad_account_name)
                    else:
                        if bad_account_name in bad_accounts:
                            self.send_bot_msg(bad_account_name + ' is already in list.', self.is_client_mod)
                        else:
                            pinylib.fh.file_writer(CONFIG['path'], CONFIG['badaccounts'], bad_account_name)
                            self.send_bot_msg('*' + bad_account_name + '* was added to *bad accounts*.', self.is_client_mod)
                            for key in self.room_users.keys():
                                user = self.find_user_info(key)
                                if user.user_account == bad_account_name:
                                    self.send_ban_msg(user.nick, user.id)
                                    break

    def do_remove_bad_account(self, bad_account):
        """
        Removes a bad account from the bad accounts file.
        :param bad_account: str the bad account name to remove from file.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(bad_account) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing account.', self.is_client_mod)
                else:
                    rem = pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['badaccounts'], bad_account)
                    if rem:
                        self.send_bot_msg(bad_account + ' was removed.', self.is_client_mod)

    def do_list_info(self, list_type):
        """
        Shows info of different lists/files.
        :param list_type: str the type of list to find info for.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(list_type) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing list type.', self.is_client_mod)
                else:
                    if list_type.lower() == 'bn':
                        bad_nicks = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badnicks'])
                        if bad_nicks is None:
                            self.send_bot_msg(special_unicode['indicate'] + ' No items in this list.',
                                              self.is_client_mod)
                        else:
                            self.send_bot_msg(str(len(bad_nicks)) + ' bad nicks in list.', self.is_client_mod)

                    elif list_type.lower() == 'bs':
                        bad_strings = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badstrings'])
                        if bad_strings is None:
                            self.send_bot_msg(special_unicode['indicate'] + ' No items in this list.',
                                              self.is_client_mod)
                        else:
                            self.send_bot_msg(str(len(bad_strings)) + ' bad strings in list.', self.is_client_mod)

                    elif list_type.lower() == 'ba':
                        bad_accounts = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badaccounts'])
                        if bad_accounts is None:
                            self.send_bot_msg(special_unicode['indicate'] + ' No items in this list.',
                                              self.is_client_mod)
                        else:
                            self.send_bot_msg(str(len(bad_accounts)) + ' bad accounts in list.', self.is_client_mod)

                    elif list_type.lower() == 'pl':
                        if len(self.playlist) is not 0:
                            i_count = 0
                            for i in range(self.inowplay, len(self.playlist)):
                                v_time = self.to_human_time(self.playlist[i]['video_time'])
                                v_title = self.playlist[i]['video_title']
                                if i_count <= 4:
                                    if i_count == 0:
                                        self.send_owner_run_msg(
                                            special_unicode['state'] + ' (%s) *Next tune:*  *%s* %s' % (
                                                i, v_title, v_time))
                                    else:
                                        self.send_owner_run_msg('(%s) *%s* %s' % (i, v_title, v_time))
                                    i_count += 1
                        else:
                            self.send_owner_run_msg(special_unicode['indicate'] + ' No items in the playlist.')

                    elif list_type.lower() == 'mods':
                        if self.is_client_owner and self.user_obj.is_super:
                            if len(self.privacy_settings.room_moderators) is 0:
                                self.send_bot_msg('*There is currently no moderators for this room.*',
                                                  self.is_client_mod)
                            elif len(self.privacy_settings.room_moderators) is not 0:
                                mods = ', '.join(self.privacy_settings.room_moderators)
                                self.send_bot_msg('*Moderators:* ' + mods, self.is_client_mod)

    def do_user_info(self, nick_name):
        """
        Shows user object info for a given user name.
        :param nick_name: str the nick name of the user to show the info for.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(nick_name) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing nickname.', self.is_client_mod)
                else:
                    user = self.find_user_info(nick_name)
                    if user is None:
                        self.send_bot_msg(special_unicode['indicate'] + ' No user named: ' + nick_name,
                                          self.is_client_mod)
                    else:
                        self.send_owner_run_msg('*ID:* %s' % user.id)
                        self.send_owner_run_msg('*Owner:* %s' % user.is_owner)
                        self.send_owner_run_msg('*Is Mod:* %s' % user.is_mod)
                        self.send_owner_run_msg('*Device Type:* %s' % user.device_type)
                        if not user.is_owner and not user.is_mod:
                            if user.nick or user.user_account in self.botters or self.botteraccounts:
                                self.send_owner_run_msg('*Sudo:* %s' % user.is_super)
                                self.send_owner_run_msg('*Bot Privileges:* %s' % user.has_power)

                        if user.tinychat_id is None and user.user_account is not None:
                            tc_info = pinylib.tinychat_api.tinychat_user_info(user.user_account)
                            if tc_info is not None:
                                user.tinychat_id = tc_info['tinychat_id']
                                user.last_login = tc_info['last_active']
                        if user.tinychat_id is not None:
                            self.send_undercover_msg(self.user_obj.nick, '*User Account Type:* %s'
                                                     % user.user_account_type)
                            self.send_undercover_msg(self.user_obj.nick, '*User Account Gift Points:* %s'
                                                     % str(user.user_account_gift_points))
                            self.send_undercover_msg(self.user_obj.nick, '*Account:* %s' % user.user_account)
                            self.send_undercover_msg(self.user_obj.nick, '*Tinychat ID:* %s' % user.tinychat_id)
                            self.send_undercover_msg(self.user_obj.nick, '*Last login:* %s' % user.last_login)
                        self.send_owner_run_msg('*Last message:* %s' % str(user.last_msg))

    def do_room_settings(self):
        """ Shows current room settings. """
        if self.is_client_owner:
            if self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                settings = self.privacy_settings.current_settings()
                # self.send_owner_run_msg('*Broadcast Password:* ' + settings['broadcast_pass'])
                # self.send_owner_run_msg('*Room Password:* ' + settings['room_pass'])
                self.send_undercover_msg(self.user_obj.nick, '*Broadcast Password:* ' + settings['broadcast_pass'])
                self.send_undercover_msg(self.user_obj.nick, '*Room Password:* ' + settings['room_pass'])
                self.send_owner_run_msg('*Login Type:* ' + settings['allow_guests'])
                self.send_owner_run_msg('*Directory:* ' + settings['show_on_directory'])
                self.send_owner_run_msg('*Push2Talk:* ' + settings['push2talk'])
                self.send_owner_run_msg('*Greenroom:* ' + settings['greenroom'])

    def do_youtube_search(self, search_str):
        """
        Searches youtube for a given search term, and adds the results to a list.
        :param search_str: str the search term to search for.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(search_str) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Missing search term.', self.is_client_mod)
                else:
                    self.search_list = youtube.youtube_search_list(search_str, results=5)
                    if len(self.search_list) is not 0:
                        for i in range(0, len(self.search_list)):
                            v_time = self.to_human_time(self.search_list[i]['video_time'])
                            v_title = self.search_list[i]['video_title']
                            self.send_owner_run_msg('(%s) *%s* %s' % (i, v_title, v_time))
                    else:
                        self.send_bot_msg(special_unicode['indicate'] + ' Could not find: ' + search_str,
                                          self.is_client_mod)

    def do_play_youtube_search(self, int_choice):
        """
        Plays a youtube from the search list.
        :param int_choice: int the index in the search list to play.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if len(self.search_list) > 0:
                    try:
                        index_choice = int(int_choice)
                        if 0 <= index_choice <= 4:
                            if self.media_timer_thread is not None and self.media_timer_thread.is_alive()\
                                    and self.playlist_mode:
                                self.playlist.append(self.search_list[index_choice])
                                v_time = self.to_human_time(self.search_list[index_choice]['video_time'])
                                v_title = self.search_list[index_choice]['video_title']
                                self.send_bot_msg('*(' + str(len(self.playlist) - 1) + ') Added:* ' +
                                                  v_title + ' *to playlist.* ' + v_time)
                            else:
                                self.last_played_media = self.search_list[index_choice]
                                self.send_media_broadcast_start(self.search_list[index_choice]['type'],
                                                                self.search_list[index_choice]['video_id'])
                                self.media_event_timer(self.search_list[index_choice]['video_time'])
                        else:
                            self.send_bot_msg(special_unicode['indicate'] + ' Please make a choice between 0-4',
                                              self.is_client_mod)
                    except ValueError:
                        self.send_bot_msg(special_unicode['indicate'] + ' Only numbers allowed.', self.is_client_mod)

    def do_clear_playlist(self):
        """ Clear all media in the playlist. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(self.playlist) is not 0:
                pl_length = str(len(self.playlist))
                self.playlist[:] = []
                self.inowplay = 0
                self.send_bot_msg(special_unicode['scissors'] + ' *Deleted* ' + pl_length + ' *items* in the playlist.',
                                  self.is_client_mod)
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' The playlist is empty, *nothing to clear*.',
                                  self.is_client_mod)

    def do_media_replay(self):
        """ Replays the last played media. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.media_timer_thread is not None:
                self.cancel_media_event_timer()
            self.send_media_broadcast_start(self.last_played_media['type'], self.last_played_media['video_id'])
            self.media_event_timer(self.last_played_media['video_time'])

    def do_skip(self):
        """ Play the next item in the playlist. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(self.playlist) is not 0:
                if self.inowplay >= len(self.playlist):
                    self.send_bot_msg(special_unicode['state'] + ' This is the *last tune* in the playlist.',
                                      self.is_client_mod)
                else:
                    self.cancel_media_event_timer()
                    self.last_played_media = self.playlist[self.inowplay]
                    self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                    self.playlist[self.inowplay]['video_id'])
                    self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                    self.inowplay += 1  # Prepare the next tune in the playlist.
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' *No tunes to skip. The playlist is empty.*',
                                  self.is_client_mod)

    # TODO: When two media is playing, only the most recent is monitored and stopped.
    def do_close_media(self):
        """
        Stops any media playing in the room.
        NOTE: The default stop is from whichever type of media is playing in the playlist.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                self.cancel_media_event_timer()
                self.send_media_broadcast_close(self.last_played_media['type'])
                self.console_write(pinylib.COLOR['bright_magenta'], 'Closed the ' + self.last_played_media['type'])

    # TODO: These need to be integrated into a media handling class.
    # def do_pause_media(self):
    #     """ Pause media that is playing in the room. """
    #     if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
    #         if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
    #             # Send pause message.
    #             self.send_media_broadcast_pause(self.last_played_media['type'])
    #
    #             # Are we in pause state already?
    #             if 'pause' in self.last_played_media:
    #                 # If so delete old pause time point.
    #                 del self.last_played_media['pause']
    #
    #             # Make a new pause time point.
    #             # ts_now = int(pinylib.time.time() * 1000)
    #             # print "time now:", ts_now
    #             # print "media start time", self.media_start_time
    #             self.last_played_media['pause'] = self.current_media_time_point()  # ts_now - self.media_start_time
    #             print "new pause time", self.last_played_media['pause']
    #             # Adjust the media timer settings to handle the pause event.
    #             self.cancel_media_event_timer()
    #
    #              self.console_write(pinylib.COLOR['bright_magenta'], '%s paused the %s at %s' %
    #                             (self.client_nick, self.last_played_media['type'], self.last_played_media['pause']))
    #         else:
    #             self.send_bot_msg(special_unicode['indicate'] + ' No media playing to pause.', self.is_client_mod)

    # def do_resume_media(self):
    #     """ Resume media that was paused in the room. """
    #     if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
    #         # Are we in pause state?
    #         if 'pause' in self.last_played_media:
    #             # Send resume message.
    #             resume_time = self.last_played_media['pause']
    #             self.send_media_broadcast_play(self.last_played_media['type'], resume_time)
    #             # The current media timer is cancelled, if there was a pause.
    #             self.cancel_media_event_timer()
    #             # Make a new time point.
    #             new_media_time = float(self.last_played_media['video_time'] - self.last_played_media['pause'])
    #             # Delete pause time point already present.
    #             del self.last_played_media['pause']
    #             self.media_start_time = new_media_time
    #
    #             self.media_event_timer(new_media_time)
    #             self.console_write(pinylib.COLOR['bright_magenta'], '%s resumed the %s at: %s'
    #                                % (self.client_nick, self.last_played_media['type'], resume_time))
    #         else:
    #             self.send_bot_msg(special_unicode['indicate'] + ' No previously paused media was found.',
    #                               self.is_client_mod)

    # def do_seek_media(self, new_time_point):
    #    """
    #    Forward/rewind (seek) any media that is playing in the room.
    #    :param new_time_point: new time_point passed on in these possible formats: hh/mm/ss, mm/ss or ss.
    #    """
    #    if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
    #        # Handle any given time points, with appropriate formatting
    #        if len(new_time_point) is 0:
    #            self.send_bot_msg(
    #                special_unicode['indicate'] + ' Please enter time to scroll to *(hh:mm:ss/mm:ss/ss)*.',
    #                self.is_client_mod)
    #        else:
    #            # Handle skip locally.
    #            self.cancel_media_event_timer()

    #            time_point = self.format_time_point(str(new_time_point))
    #            print 'new time_point', time_point

    #            if self.last_played_media['video_time'] <= time_point:
    #                self.send_bot_msg(special_unicode['indicate'] + ' The seek time is longer than the media time.' +
    #                                  'Please choose between 0 - '
    #                                   + self.to_human_time(self.last_played_media['video_time']) + '.')
    #            else:
    #                new_media_time = self.last_played_media['video_time'] - time_point
    #                self.media_start_time = new_media_time

    #                if 'pause' in self.last_played_media:
    #                    self.last_played_media['pause'] = new_media_time

    #                Send skip message.
    #                self.send_media_broadcast_skip(self.last_played_media['type'], time_point)

    #                self.media_event_timer(new_media_time)
    #                self.console_write(pinylib.COLOR['bright_magenta'], 'Time searched the ' +
    #                                   self.last_played_media['type'] + ' at: ' + self.to_human_time(time_point))

    # TODO: Possibly add tags to show who request the media as a room message.
    def do_media_request_choice(self, request_choice):
        """
        Allows owners/super mods/moderators/botters to accept/decline any temporarily stored media requests.
        :param request_choice: bool True/False if the media request was accepted or declined by the privileged user.
        """
        if self.is_client_mod:
            if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                if self.media_request is not None:
                    if request_choice is True:
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive() \
                                and self.playlist_mode:
                            self.playlist.append(self.media_request)
                            self.send_bot_msg(special_unicode['arrow_streak'] +
                                              ' The media request was *accepted*. Added media to the playlist.',
                                              self.is_client_mod)
                        else:
                            self.last_played_media = self.media_request
                            self.send_media_broadcast_start(self.media_request['type'], self.media_request['video_id'])
                            self.media_event_timer(self.media_request['video_time'])
                            self.send_bot_msg(special_unicode['arrow_streak'] + ' *Playing* media request.',
                                              self.is_client_mod)
                        self.media_request = None
                    else:
                        self.send_bot_msg(special_unicode['italic_cross'] +
                                          ' The media request was *declined*. New media requests can be made.',
                                          self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] + ' *No media was requested* by any users.',
                                      self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    # == Public Command Methods. ==
    def do_version(self):
        """ Replies with relevant version information concerning the bot. """
        self.send_undercover_msg(self.user_obj.nick, '*pinybot* ' + str(__version__) + ' *Build:* ' + build_name)
        self.send_undercover_msg(self.user_obj.nick, '*Author:* ' + str(author))
        self.send_undercover_msg(self.user_obj.nick, '*Repository:* ' + str(CONFIG['repository']))

    def do_help(self):
        """ Posts a link to a GitHub README/Wiki about the bot commands. """
        self.send_undercover_msg(self.user_obj.nick,
                                 '*Commands:* https://github.com/GoelBiju/pinybot/wiki/Features/')

    def do_uptime(self):
        """ Shows the bots uptime. """
        self.send_bot_msg(special_unicode['time'] + ' *Uptime:* ' +
                          self.to_human_time(self.get_uptime()), self.is_client_mod)

    def do_pmme(self):
        """ Opens a PM session with the bot. """
        self.send_private_msg('How can I help you *' + special_unicode['no_width'] + self.user_obj.nick +
                              special_unicode['no_width'] + '*?', self.user_obj.nick)

    #  == Media Related Command Methods. ==
    def do_playlist_status(self):
        """ Shows info about the playlist. """
        if self.is_client_mod:
            if len(self.playlist) is 0:
                self.send_bot_msg(special_unicode['indicate'] + ' The playlist is *empty*.', self.is_client_mod)
            else:
                inquee = len(self.playlist) - self.inowplay
                self.send_bot_msg(str(len(self.playlist)) + ' *item(s) in the playlist.* ' + str(inquee) +
                                  ' *Still in queue.*', self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_now_playing(self):
        """ Shows the currently playing media title to the user. """
        if self.is_client_mod:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                self.send_undercover_msg(self.user_obj.nick, '*' + special_unicode['no_width'] + self.user_obj.nick +
                                         special_unicode['no_width'] + '*, the media being played is: *' +
                                         str(self.last_played_media['video_title']) + '* (%s)' %
                                         self.to_human_time(self.last_played_media['video_time']))
            else:
                self.send_undercover_msg(self.user_obj.nick, '*No track is playing.*')

    def do_next_tune_in_playlist(self):
        """ Shows next item in the playlist. """
        if self.is_client_mod:
            if len(self.playlist) is 0:
                self.send_bot_msg(special_unicode['indicate'] + ' *No tunes* in the playlist.', self.is_client_mod)
            elif self.inowplay < len(self.playlist):
                play_time = self.to_human_time(self.playlist[self.inowplay]['video_time'])
                play_title = self.playlist[self.inowplay]['video_title']
                self.send_bot_msg(special_unicode['state'] + ' (' + str(self.inowplay) + ') *' + play_title + '* ' +
                                  play_time, self.is_client_mod)
            elif self.inowplay >= len(self.playlist):
                self.send_bot_msg(special_unicode['indicate'] + ' This is the *last tune* in the playlist.',
                                  self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    # NEW: Added public media and playlist mode.
    # TODO: Make sure we can utilise this elsewhere or remove this from the code.
    # def do_add_media_to_playlist(self, media_type, search_str):
    #     """
    #     Searches for and adds a media to the playlist.
    #     :param media_type: str the type of media i.e. search medium.
    #     :param search_str: str the search term.
    #     """
    #     log.info('User: %s:%s is searching %s: %s' % (self.user_obj.nick, self.user_obj.id, media_type, search_str))
    #     if self.is_client_mod:
    #         if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power \
    #                 or self.public_media:
    #
    #             type_str = str
    #             if media_type == self.yt_type:
    #                 type_str = 'YouTube'
    #             elif media_type == self.sc_type:
    #                 type_str = 'SoundCloud'
    #
    #             if len(search_str) is 0:
    #                 self.send_bot_msg(
    #                     special_unicode['indicate'] + ' Please specify *' + type_str + '* title, id or link.',
    #                     self.is_client_mod)
    #             else:
    #                 _media = None
    #                 if media_type == self.yt_type:
    #                     _media = youtube.youtube_search(search_str)
    #                 elif media_type == self.sc_type:
    #                     _media = soundcloud.soundcloud_search(search_str)
    #
    #                 if _media is None:
    #                     log.warning('%s request returned: %s' % (media_type, _media))
    #                     self.send_bot_msg(special_unicode['indicate'] + ' Could not find media: ' + search_str,
    #                                       self.is_client_mod)
    #                 else:
    #                     log.info('%s found: %s' % (media_type, _media))
    #                     if self.media_timer_thread is not None and self.media_timer_thread.is_alive()\
    #                             and self.playlist_mode:
    #                         self.playlist.append(_media)
    #                         self.send_bot_msg(special_unicode['pencil'] + ' *Added:* ' + _media['video_title'] +
    #                                           ' *to playlist.* ' + self.to_human_time(_media['video_time']),
    #                                           self.is_client_mod)
    #                     else:
    #                         self.last_played_media = _media
    #                         self.send_media_broadcast_start(_media['type'], _media['video_id'])
    #                         self.media_event_timer(_media['video_time'])
    #                         self.inowplay += 1  # Prepare the next tune in the playlist.
    #         else:
    #             self.send_bot_msg('Not enabled right now.')

    def do_play_media(self, media_type, search_str):
        """
        Plays a youTube or soundCloud video matching the search term.
        :param media_type: str youTube or soundCloud depending on the type of media to play.
        :param search_str: str the search term.
        """
        if self.is_client_mod:
            if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power \
                    or self.public_media:
                # Set up the type of media to be added to the playlist/played.
                type_str = str
                if media_type == self.yt_type:
                    type_str = 'YouTube'
                elif media_type == self.sc_type:
                    type_str = 'SoundCloud'

                if len(search_str) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Please specify *' + type_str +
                                      ' title, id or link.*', self.is_client_mod)
                else:
                    # Set up media search variable.
                    _media = None

                    # Search for the specified media.
                    if media_type == self.yt_type:
                        media_search_type = youtube.youtube_search
                    elif media_type == self.sc_type:
                        media_search_type = soundcloud.soundcloud_search

                    # Search for multiple video/track requests and search them independently.
                    if '&&' in search_str:
                        if self.playlist_mode:
                            multi_search = search_str.split('&&')
                            searched = 0

                            # Search each media entry independently.
                            for search in multi_search:
                                _media = media_search_type(search)

                                if _media is not None:
                                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                        self.playlist.append(_media)
                                    else:
                                        self.last_played_media = _media
                                        self.send_media_broadcast_start(_media['type'], _media['video_id'])
                                        self.media_event_timer(_media['video_time'])
                                    searched += 1

                            self.send_bot_msg(special_unicode['state'] + ' Added %s video/track(s) to the playlist.' %
                                              searched, self.is_client_mod)
                        else:
                            self.send_bot_msg(special_unicode['indicate'] +
                                              ' Playlist mode is not enabled. Turn it on to add multiple songs.')

                    # Search for a media entry.
                    _media = media_search_type(search_str)

                    # Handle starting media playback.
                    if _media is None:
                        self.send_bot_msg(special_unicode['indicate'] + ' Could not find media: ' + search_str,
                                          self.is_client_mod)
                    else:
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive() \
                                and self.playlist_mode:
                            self.playlist.append(_media)
                            self.send_bot_msg(special_unicode['pencil'] + ' ' + special_unicode['musical_note'] + ' *' +
                                              str(_media['video_title']) + ' ' + special_unicode['musical_note'] +
                                              ' at #' + str(len(self.playlist)) + '*', self.is_client_mod)
                        else:
                            self.last_played_media = _media
                            self.send_media_broadcast_start(_media['type'], _media['video_id'])
                            self.media_event_timer(_media['video_time'])
        else:
            self.send_bot_msg('Not enabled right now.')

    # TODO: Private media handling(?)
    def do_play_private_media(self, media_type, search_str):
        """
        Plays a youTube or soundCloud matching the search term privately.
        :param media_type: str youTube or soundCloud depending on the type of media to play privately.
        :param search_str: str the search term.
        NOTE: The video will only be visible for the message sender.
        """
        if self.is_client_mod:
            type_str = str
            if media_type == self.yt_type:
                type_str = 'YouTube'
            elif media_type == self.sc_type:
                type_str = 'SoundCloud'

            if len(search_str) is 0:
                self.send_undercover_msg(self.user_obj.nick, self.user_obj.nick + ', please specify *' +
                                         type_str + ' title, id or link.*')
            else:
                _media = None
                if media_type == self.yt_type:
                    _media = youtube.youtube_search(search_str)
                elif media_type == self.sc_type:
                    _media = soundcloud.soundcloud_search(search_str)

                if _media is None:
                    self.send_undercover_msg(self.user_obj.nick, 'Could not find video: ' + search_str)
                else:
                    self.user_obj.private_media = media_type
                    self.send_media_broadcast_start(media_type, _media['video_id'], private_nick=self.user_obj.nick)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_stop_private_media(self):
        """
        Stops a users private media (youTube or soundCloud) using a user attribute.
        If the attribute is not available, then both media are forcibly stopped.
        """
        # Close the private media depending if either attribute exists.
        if hasattr(self.user_obj, 'yt_type'):
            self.send_media_broadcast_close(self.yt_type, self.user_obj.nick)
        elif hasattr(self.user_obj, 'sc_type'):
            self.send_media_broadcast_close(self.sc_type, self.user_obj.nick)
        else:
            # If none/both do then issue a close for both types of media.
            self.send_media_broadcast_close(self.yt_type, self.user_obj.nick)
            self.send_media_broadcast_close(self.sc_type, self.user_obj.nick)

    def do_media_request(self, request_type, request_item):
        """
        Allows user's to make media requests for both YouTube and SoundCloud and requests the media to
        be accepted/declined by a owner/super mod/moderator/botter.
        :param request_type: str the type of media it is YouTube/SoundCloud.
        :param request_item: str the item to request for link/id/title.
        """
        if self.is_client_mod:
            if self.media_request is None:
                # Set up the type of media to be added to the playlist/played.
                type_str = str
                if request_type == self.yt_type:
                    type_str = 'YouTube'
                elif request_type == self.sc_type:
                    type_str = 'SoundCloud'

                if len(request_item) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' Please specify *' +
                                      type_str + ' title, id or link to make a media request.*', self.is_client_mod)
                else:
                    # Search for the specified media.
                    _media = None
                    if request_type == self.yt_type:
                        _media = youtube.youtube_search(request_item)
                    elif request_type == self.sc_type:
                        _media = soundcloud.soundcloud_search(request_item)

                    # Handle starting media playback.
                    if _media is None:
                        self.send_bot_msg(special_unicode['indicate'] + ' Could not find media: ' + request_item,
                                          self.is_client_mod)
                    else:
                        self.media_request = _media
                        self.send_bot_msg(special_unicode['arrow_sideways'] + ' Media request has been *submitted*. ' +
                                          'Please wait until the request is accepted/declined.', self.is_client_mod)
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Please wait until a privileged user ' +
                                  'decides on the current media request.', self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_sync_media(self, sync_all=False, sync_name=False):
        """
        Syncs the media that is currently being playing to you, all or a specific user(s) within the room.
        :param sync_all: bool True/False if we should sync all the users in the room.
        :param sync_name: str/bool to False if none present.
        """
        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
            if not sync_all and not sync_name:
                self.send_media_broadcast_start(self.last_played_media['type'], self.last_played_media['video_id'],
                                                self.current_media_time_point(), private_nick=self.user_obj.nick)
            else:
                if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                    if sync_all and not sync_name:
                        if not self.syncing:
                            self.syncing = True
                            for user in self.room_users.keys():
                                # Send the media at the correct start time from the playlist to the user.
                                if user != self.client_nick:
                                    self.send_media_broadcast_start(self.last_played_media['type'],
                                                                    self.last_played_media['video_id'],
                                                                    self.current_media_time_point(), private_nick=user)
                            pinylib.time.sleep(1)
                            self.syncing = False
                        else:
                            self.send_bot_msg(special_unicode['indicate'] +
                                              ' A room sync request is currently being processed.', self.is_client_mod)
                    elif not sync_all and sync_name:
                        self.send_undercover_msg(str(sync_name), 'Your media was just synced by %s.' %
                                                 self.user_obj.nick)
                        self.send_media_broadcast_start(self.last_played_media['type'],
                                                        self.last_played_media['video_id'],
                                                        self.current_media_time_point(),
                                                        private_nick=sync_name)
        else:
            self.send_undercover_msg(self.user_obj.nick, 'No media playing to *sync* at the moment.')

    def do_youtube_playlist_videos(self, playlist):
        """
        Retrieves and adds video IDs of songs from a playlist.
        Add all the videos from the given playlist.
        :param: playlist: str the playlist or playlist ID.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.playlist_mode:
                if len(playlist) is 0:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' Please enter a playlist url or playlist ID.', self.is_client_mod)
                else:
                    # Get only the playlist ID from the provided link.
                    playlist_id = ''
                    if '=' in playlist:
                        location_equal = playlist.index('=')
                        playlist_id = playlist[location_equal + 1:len(playlist)]
                    else:
                        if 'http' or 'www' or 'youtube' not in playlist:
                            playlist_id = playlist

                    self.send_bot_msg(special_unicode['state'] +
                                      ' *Just a minute* while we fetch the videos in the playlist...',
                                      self.is_client_mod)

                    video_list, non_public = youtube.youtube_playlist_videos(playlist_id)
                    if len(video_list) is 0:
                        self.send_bot_msg(special_unicode['indicate'] +
                                          ' No videos in playlist or none were found.', self.is_client_mod)
                    else:
                        if non_public > 0:
                            playlist_message = special_unicode['pencil'] + \
                                               ' Added *' + str(len(video_list)) + ' videos* to the playlist. ' + \
                                               'There were *' + special_unicode['no_width'] + str(non_public) + \
                                               special_unicode['no_width'] + '* non-public videos.'
                        else:
                            playlist_message = special_unicode['pencil'] + \
                                               ' Added *' + str(len(video_list)) + ' videos* to the playlist.'

                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.playlist.extend(video_list)
                            self.send_bot_msg(playlist_message, self.is_client_mod)
                        else:
                            self.playlist.extend(video_list)
                            self.last_played_media = self.playlist[self.inowplay]
                            self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                            self.playlist[self.inowplay]['video_id'])
                            self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                            self.inowplay += 1  # Prepare the next tune in the playlist.
                            self.send_bot_msg(playlist_message, self.is_client_mod)
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                  self.is_client_mod)

    def do_youtube_playlist_search(self, playlist_search):
        """
        Retrieves search results for a youtube playlist search.
        :param playlist_search: str the name of the playlist you want to search.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            log.info('User %s:%s is searching a YouTube playlist: %s' % (self.user_obj.nick, self.user_obj.id,
                                                                         playlist_search))
            if self.playlist_mode:
                if len(playlist_search) is 0:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' Please enter a playlist search query.', self.is_client_mod)
                else:
                    self.search_play_lists = youtube.youtube_playlist_search(playlist_search, results=4)
                    if self.search_play_lists is None:
                        log.warning('The search returned an error.')
                        self.send_bot_msg(special_unicode['indicate'] +
                                          '  There was an error while fetching the results.', self.is_client_mod)
                    elif len(self.search_play_lists) is 0:
                        self.send_bot_msg(special_unicode['indicate'] +
                                          ' The search returned no results.', self.is_client_mod)
                    else:
                        log.info('YouTube playlist were found: %s' % self.search_play_lists)
                        for x in range(len(self.search_play_lists)):
                            self.send_undercover_msg(self.user_obj.nick, '*' + str(x + 1) + '. ' +
                                                     self.search_play_lists[x]['playlist_title'] + ' - ' +
                                                     self.search_play_lists[x]['playlist_id'] + '*')
                            pinylib.time.sleep(0.2)
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                  self.is_client_mod)

    def do_youtube_playlist_search_choice(self, index_choice):
        """
        Starts a playlist from the search list.
        :param index_choice: int the index in the play lists to start.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.playlist_mode:
                if len(self.search_play_lists) is 0:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' No previous playlist search committed to confirm ID. Please do *!plsh*.',
                                      self.is_client_mod)
                elif len(index_choice) is 0:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' Please choose your selection from the playlist IDs,  e.g. *!pladd 2*',
                                      self.is_client_mod)
                else:
                    if 0 <= int(index_choice) <= 4:
                        threading.Thread(target=self.do_youtube_playlist_videos,
                                         args=(self.search_play_lists[int(index_choice) - 1]['playlist_id'],)).start()
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                  self.is_client_mod)

    def do_charts(self):
        """ Retrieves the Top40 songs list and adds the songs to the playlist. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.playlist_mode:
                self.send_bot_msg(special_unicode['state'] +
                                  ' *Hang on* while we retrieve the Top40 songs...', self.is_client_mod)

                songs_list = other_apis.top40()
                top40_list = list(reversed(songs_list))
                if songs_list is None:
                    self.send_bot_msg(special_unicode['indicate'] +
                                      ' We could not fetch the Top40 songs list.', self.is_client_mod)
                elif len(songs_list) is 0:
                    self.send_bot_msg(special_unicode['indicate'] + ' No songs were found.', self.is_client_mod)
                else:
                    video_list = []
                    for x in range(len(top40_list)):
                        search_str = top40_list[x][0] + ' - ' + top40_list[x][1]
                        _youtube = youtube.youtube_search(search_str)
                        if _youtube is not None:
                            video_list.append(_youtube)

                    if len(video_list) > 0:
                        self.send_bot_msg(special_unicode['pencil'] + ' *Added Top40* songs (40 --> 1) to playlist.',
                                          self.is_client_mod)

                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.playlist.extend(video_list)
                        else:
                            self.playlist.extend(video_list)
                            self.last_played_media = self.playlist[self.inowplay]
                            self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                            self.playlist[self.inowplay]['video_id'])
                            self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                            self.inowplay += 1  # Prepare the next tune in the playlist.
            else:
                self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                  self.is_client_mod)

    def do_lastfm_chart(self, chart_items):
        """
        Makes a playlist from the currently most played tunes on Last.fm.
        :param chart_items: int the amount of tunes we want.
        """
        if self.is_client_mod:
            if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                if self.playlist_mode:
                    if chart_items is 0 or chart_items is None:
                        self.send_bot_msg(special_unicode['indicate'] + ' Please specify the amount of tunes you want.',
                                          self.is_client_mod)
                    else:
                        try:
                            _items = int(chart_items)
                        except ValueError:
                            self.send_bot_msg(special_unicode['indicate'] + ' Only numbers allowed.',
                                              self.is_client_mod)
                        else:
                            if _items > 0:
                                if _items > 30:
                                    self.send_bot_msg(special_unicode['indicate'] + ' No more than 30 tunes.',
                                                      self.is_client_mod)
                                else:
                                    self.send_bot_msg(
                                        special_unicode['state'] + ' *Please wait* while creating a playlist...',
                                        self.is_client_mod)
                                    last = lastfm.get_lastfm_chart(_items)

                                    if last is not None:
                                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                            self.playlist.extend(last)
                                            self.send_bot_msg(special_unicode['pencil'] +
                                                              ' *Added: *%s* tunes from last.fm chart.*'
                                                              % str(len(last)), self.is_client_mod)
                                        else:
                                            self.playlist.extend(last)
                                            self.send_bot_msg(special_unicode['pencil'] + '*Added:* ' + str(len(last)) +
                                                              ' *tunes from last.fm chart.*', self.is_client_mod)
                                            self.last_played_media = self.playlist[self.inowplay]
                                            self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                                            self.playlist[self.inowplay]['video_id'])
                                            self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                                            self.inowplay += 1  # Prepare the next tune in the playlist.
                                    else:
                                        self.send_bot_msg(special_unicode['indicate'] +
                                                          ' Failed to retrieve a result from last.fm.',
                                                          self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                      self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_lastfm_random_tunes(self, max_tunes):
        """
        Creates a playlist from what other people are listening to on Last.fm.
        :param max_tunes: int the max amount of tunes.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if self.is_client_mod:
                if max_tunes is 0 or max_tunes is None:
                    self.send_bot_msg(special_unicode['indicate'] + ' Please specify the max amount of tunes you want.',
                                      self.is_client_mod)
                else:
                    try:
                        _items = int(max_tunes)
                    except ValueError:
                        self.send_bot_msg(special_unicode['indicate'] + ' Only numbers allowed.', self.is_client_mod)
                    else:
                        if _items > 0:
                            if _items > 25:
                                self.send_bot_msg(special_unicode['indicate'] + ' No more than 25 tunes.',
                                                  self.is_client_mod)
                            else:
                                self.send_bot_msg(
                                    special_unicode['state'] + ' *Please wait* while creating a playlist...',
                                    self.is_client_mod)
                                last = lastfm.lastfm_listening_now(max_tunes)

                                if last is not None:
                                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                        self.playlist.extend(last)
                                        self.send_bot_msg(special_unicode['pencil'] + ' Added *' + str(
                                            len(last)) + '* tunes from *last.fm*',
                                                          self.is_client_mod)
                                    else:
                                        self.playlist.extend(last)
                                        self.send_bot_msg(special_unicode['pencil'] + ' Added *' + str(len(last)) +
                                                          ' * tunes from *last.fm*', self.is_client_mod)
                                        self.last_played_media = self.playlist[self.inowplay]
                                        self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                                        self.playlist[self.inowplay]['video_id'])
                                        self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                                        self.inowplay += 1  # Prepare the next tune in the playlist.
                                else:
                                    self.send_bot_msg(
                                        special_unicode['indicate'] + ' Failed to retrieve a result from last.fm.',
                                        self.is_client_mod)
            else:
                self.send_bot_msg('Not enabled right now.')

    def search_lastfm_by_tag(self, search_str):
        """
        Searches last.fm for tunes matching the search term and creates a playlist from them.
        :param search_str: str the search term to search for.
        """
        if self.is_client_mod:
            if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
                if self.playlist_mode:
                    if len(search_str) is 0:
                        self.send_bot_msg(special_unicode['indicate'] + ' Missing search tag.', self.is_client_mod)
                    else:
                        self.send_bot_msg(special_unicode['state'] + ' *Please wait* while creating playlist...',
                                          self.is_client_mod)
                        last = lastfm.search_lastfm_by_tag(search_str)

                        if last is not None:
                            if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                self.playlist.extend(last)
                                self.send_bot_msg(
                                    special_unicode['pencil'] + ' Added *' + str(len(last)) + '* tunes from *last.fm*',
                                    self.is_client_mod)
                            else:
                                self.playlist.extend(last)
                                self.send_bot_msg(
                                    special_unicode['pencil'] + ' Added *' + str(len(last)) + '* tunes from *last.fm*',
                                    self.is_client_mod)
                                self.last_played_media = self.playlist[self.inowplay]
                                self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                                self.playlist[self.inowplay]['video_id'])
                                self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                                self.inowplay += 1  # Prepare the next tune in the playlist.
                        else:
                            self.send_bot_msg(special_unicode['indicate'] +
                                              ' Failed to retrieve a result from last.fm.', self.is_client_mod)
                else:
                    self.send_bot_msg(special_unicode['indicate'] + ' Turn on *playlist mode* to use this feature.',
                                      self.is_client_mod)
            else:
                self.send_bot_msg('Not enabled right now.')

    def do_delete_playlist_item(self, to_delete):
        """
        Delete item(s) from the playlist by index.
        :param to_delete: str index(es) to delete.
        """
        usage = '*' + CONFIG['prefix'] + 'del 1* or *' + CONFIG['prefix'] + 'del 1,2,4* or *' \
                + CONFIG['prefix'] + 'del 2:8*'
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(self.playlist) is 0:
                self.send_undercover_msg(self.user_obj.nick, 'The playlist is empty.')
            if len(to_delete) is 0:
                self.send_undercover_msg(self.user_obj.nick, usage)
            else:
                indexes = None
                deleted_by_range = False
                playlist_copy = list(self.playlist)
                # using : as a separator.
                if ':' in to_delete:
                    try:
                        range_indexes = map(int, to_delete.split(':'))
                        temp_indexes = range(range_indexes[0], range_indexes[1])
                    except ValueError:
                        self.send_undercover_msg(self.user_obj.nick, usage)
                    else:
                        indexes = []
                        for i in temp_indexes:
                            if i < len(self.playlist):
                                if i not in indexes:
                                    indexes.append(i)
                        if len(indexes) > 1:
                            deleted_by_range = True
                else:
                    try:
                        temp_indexes = map(int, to_delete.split(','))
                    except ValueError:
                        self.send_undercover_msg(self.user_obj.nick, usage)
                    else:
                        indexes = []
                        for i in temp_indexes:
                            if i < len(self.playlist):
                                if i not in indexes:
                                    indexes.append(i)
                deleted_indexes = []
                if indexes is not None and len(indexes) is not 0:
                    if len(self.playlist) is not 0:
                        for i in sorted(indexes, reverse=True):
                            if self.inowplay <= i < len(self.playlist):
                                del self.playlist[i]
                                deleted_indexes.append(str(i))
                        deleted_indexes.reverse()
                        if len(deleted_indexes) > 0:
                            if deleted_by_range:
                                self.send_bot_msg('*deleted: index range from (and including)* ' +
                                                  str(deleted_indexes[0]) + ' to ' + str(deleted_indexes[-1]),
                                                  self.is_client_mod)
                            elif len(deleted_indexes) is 1:
                                self.send_bot_msg('Deleted: *' + playlist_copy[int(deleted_indexes[0])]['video_title'] +
                                                  '*', self.is_client_mod)
                            else:
                                self.send_bot_msg('*Deleted tracks at index:* ' + ', '.join(deleted_indexes),
                                                  self.is_client_mod)
                        else:
                            self.send_bot_msg('Nothing was deleted.', self.is_client_mod)
                    else:
                        self.send_bot_msg('The playlist is empty, no tracks to delete.', self.is_client_mod)

    # == Tinychat API Command Methods. ==
    def do_spy(self, room_name):
        """
        Shows info for a given room.
        :param room_name: str the room name to find info for.
        """
        if self.is_client_mod:
            if len(room_name) is 0:
                self.send_undercover_msg(self.user_obj.nick, 'Missing room name.')
            else:
                spy_info = pinylib.tinychat_api.spy_info(room_name)
                if spy_info is None:
                    self.send_undercover_msg(self.user_obj.nick, 'The room is empty.')
                elif spy_info == 'PW':
                    self.send_undercover_msg(self.user_obj.nick, 'The room is password protected.')
                else:
                    self.send_undercover_msg(self.user_obj.nick,
                                             '*mods:* ' + spy_info['mod_count'] +
                                             ' *Broadcasters:* ' + spy_info['broadcaster_count'] +
                                             ' *Users:* ' + spy_info['total_count'])
                    if self.user_obj.is_owner or self.user_obj.is_mod or self.user_obj.has_power:
                        users = ', '.join(spy_info['users'])
                        self.send_undercover_msg(self.user_obj.nick, '*' + users + '*')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_account_spy(self, account):
        """
        Shows info about a Tinychat account.
        :param account: str Tinychat account.
        """
        if self.is_client_mod:
            if len(account) is 0:
                self.send_undercover_msg(self.user_obj.nick, 'Missing username to search for.')
            else:
                tc_usr = pinylib.tinychat_api.tinychat_user_info(account)
                if tc_usr is None:
                    self.send_undercover_msg(self.user_obj.nick, 'Could not find Tinychat info for: %s' % account)
                else:
                    self.send_undercover_msg(self.user_obj.nick, 'ID: %s, Last login: %s, Location: %s' %
                                             (tc_usr['tinychat_id'], tc_usr['last_active'], tc_usr['location']))
        else:
            self.send_bot_msg('Not enabled right now.')

    # == Other API Command Methods. ==
    def do_search_urban_dictionary(self, search_str):
        """
        Shows "Urban Dictionary" definition of search string.
        :param search_str: str the search string to look up a definition for.
        """
        if self.is_client_mod:
            if len(search_str) is 0:
                self.send_bot_msg(special_unicode['indicate'] +
                                  ' Please specify something to look up on *Urban-Dictionary*.', self.is_client_mod)
            elif search_str in self.restricted_terms:
                self.send_bot_msg(special_unicode['indicate'] + ' This is a restricted term.', self.is_client_mod)
            else:
                urban_definition = other_apis.urbandictionary_search(search_str)
                if urban_definition is None:
                    self.send_bot_msg(special_unicode['indicate'] + ' Could not find a definition for: ' + search_str,
                                      self.is_client_mod)
                else:
                    self.send_bot_msg(urban_definition, self.is_client_mod)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_weather_search(self, search_str):
        """
        Shows weather info for a given search string.
        :param search_str: str the search string to find weather data for.
        """
        if len(search_str) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please specify a city to search for.', self.is_client_mod)
        else:
            weather = other_apis.weather_search(search_str)
            if weather is None:
                self.send_bot_msg(special_unicode['indicate'] + ' Could not find weather data for: ' + search_str,
                                  self.is_client_mod)
            elif not weather:
                self.send_bot_msg(special_unicode['indicate'] + ' Missing API key.', self.is_client_mod)
            else:
                self.send_bot_msg(weather, self.is_client_mod)

    def do_whois_ip(self, ip_str):
        """
        Shows whois info for a given ip address.
        :param ip_str: str the ip address to find info for.
        """
        if len(ip_str) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please provide an IP address.', self.is_client_mod)
        else:
            whois = other_apis.whois(ip_str)
            if whois is None:
                self.send_bot_msg(special_unicode['indicate'] + ' No info found for: ' + ip_str, self.is_client_mod)
            else:
                self.send_bot_msg(whois)

    def do_duckduckgo_search(self, search):
        """
        Shows definitions/information relating to a particular DuckDuckGo search query.
        :param search: str the search query.
        """
        if len(search) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please enter a *DuckDuckGo* search term.',
                              self.is_client_mod)
        else:
            definitions = other_apis.duckduckgo_search(search)
            if definitions is not None:
                for x in range(len(definitions)):
                    if len(definitions[x]) > 160:
                        sentence = definitions[x][0:159] + '\n ' + definitions[x][159:]
                    else:
                        sentence = definitions[x]
                    self.send_bot_msg(str(x + 1) + ' *' + sentence + '*', self.is_client_mod)

    # TODO: Fix Wikipedia module integration.
    def do_wiki_search(self, search_str=None):
        """
        Grab first sentence from a Wikipedia article.
        :param search_str: str Wikipedia search.
        """
        if len(search_str) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please specify something to look up on *Wikipedia*.',
                              self.is_client_mod)
        else:
            wiki = other_apis.wiki_search()  # search_str
            # This bit probably isn't needed since we are only pulling two sentences from the searched article.
            if wiki is None:
                self.send_bot_msg(special_unicode['indicate'] + ' There was an error with the *Wikipedia* search.',
                                  self.is_client_mod)
            elif wiki is False:
                self.send_bot_msg(special_unicode['indicate'] +
                                  ' *No Wikipedia module installed!* -- "pip install wikipedia"', self.is_client_mod)
            else:
                if len(wiki) > 70:
                    if '.' in str(wiki):
                        wiki_parts = str(wiki).split('.')
                        self.send_bot_msg(u'' + wiki_parts[0].strip(), self.is_client_mod)
                else:
                    self.send_bot_msg(u'' + wiki.strip(), self.is_client_mod)

    def do_omdb_search(self, search):
        """
        Post information retrieved from OMDb (serving IMDB data) API.
        :param search: str the IMDB entertainment search.
        """
        if len(search) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please specify a *movie or television* show.',
                              self.is_client_mod)
        else:
            omdb = other_apis.omdb_search(search)
            if omdb is None:
                self.send_bot_msg(special_unicode['indicate'] + ' *Error or title does not exist.*', self.is_client_mod)
            else:
                self.send_bot_msg(omdb, self.is_client_mod)

    def do_etymonline_search(self, search):
        """
        Search http://etymonline.com/ to reply with etymology for particular search term.
        :param search: str the term you want its etymology for.
        """
        if len(search) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please enter a *search term* to lookup on *Etymonline*.',
                              self.is_client_mod)
        else:
            etymology = other_apis.etymonline(search)
            if etymology is None:
                self.send_bot_msg(special_unicode['indicate'] + ' We could not retrieve the etymology for your term.',
                                  self.is_client_mod)
            else:
                if len(etymology) > 295:
                    etymology = etymology[:294] + ' ...'
                self.send_bot_msg(etymology, self.is_client_mod)

    # == Just For Fun Command Methods. ==
    # When instant is used initially without using !cb to initialise the session, the instant message is not printed.
    def do_clever_bot(self, query, instant=False):
        """
        Shows the reply from the online self-learning A.I. CleverBot.
        :param query: str the statement/question to ask CleverBot.
        :param instant: bool True/False whether the request was from when a user typed in the client's nickname or
                       manually requested a response.
        """
        if self.clever_bot_enable:
            if len(query) is not 0:
                if self.clever_bot_session is None:
                    # Open a new connection to CleverBot in the event we do not already have one set up.
                    self.clever_bot_session = clever_client_bot.CleverBot()
                    # Start CleverBot message timer.
                    threading.Thread(target=self.clever_bot_timer).start()
                    if not instant:
                        self.send_bot_msg(special_unicode['victory_hand'] + ' *Waking up* %s' % self.client_nick,
                                          self.is_client_mod)
                    self.do_clever_bot(query, instant)
                else:
                    # Request the response from the server and send it as a normal user message.
                    response = self.clever_bot_session.converse(query)
                    if not instant and self.is_client_mod:
                        self.send_bot_msg('*CleverBot* %s: %s' % (special_unicode['state'], response),
                                          self.is_client_mod)
                    else:
                        self.send_bot_msg(response)

                # Record the time at which the response was sent.
                self.clever_bot_msg_time = int(pinylib.time.time())
            else:
                if not instant:
                    self.send_bot_msg(special_unicode['indicate'] + ' Please enter a statement/question.',
                                      self.is_client_mod)
        else:
            self.send_bot_msg(special_unicode['indicate'] + ' Please enable CleverBot to use this function.',
                              self.is_client_mod)

    def do_chuck_norris(self):
        """ Shows a Chuck Norris joke/quote. """
        chuck = other_apis.chuck_norris()
        if chuck is not None:
            self.send_bot_msg(chuck, self.is_client_mod)
        else:
            self.send_bot_msg('Unable to retrieve from server.', self.is_client_mod)

    def do_8ball(self, question):
        """
        Shows magic eight ball answer to a yes/no question.
        :param question: str the yes/no question.
        """
        if len(question) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Provide a *yes/no* question.', self.is_client_mod)
        else:
            self.send_bot_msg('*8Ball:* ' + eightball(), self.is_client_mod)

    def do_auto_url(self, msg):
        """
        Retrieve header information for a given link.
        :param msg: str complete message by the user.
        """
        if 'http' in msg or 'https' in msg:
            if '!' not in msg and 'tinychat.com' not in msg:
                url = None
                if msg.startswith('http://'):
                    url = msg.split('http://')[1]
                    msgs = url.split(' ')[0]
                    url = auto_url.auto_url('http://' + msgs)
                elif msg.startswith('https://'):
                    url = msg.split('https://')[1]
                    msgs = url.split(' ')[0]
                    url = auto_url.auto_url('https://' + msgs)
                if url is not None:
                    self.send_bot_msg('*[ ' + url + ' ]*', self.is_client_mod)
                    self.console_write(pinylib.COLOR['cyan'], self.user_obj.nick + ' posted a URL: ' + url)

    def do_yo_mama_joke(self):
        """ Shows the reply from a 'Yo Mama' joke API. """
        yo_mama = str(other_apis.yo_mama_joke())
        if yo_mama is not None:
            self.send_bot_msg('*' + special_unicode['no_width'] + self.user_obj.nick + special_unicode['no_width'] +
                              '* says ' + yo_mama.lower(), self.is_client_mod)
        else:
            self.send_bot_msg(special_unicode['indicate'] + ' Unable to retrieve from server.', self.is_client_mod)

    def do_advice(self):
        """ Shows the reply from an advice API. """
        advice = other_apis.online_advice()
        if advice is not None:
            self.send_bot_msg('*' + special_unicode['no_width'] + self.user_obj.nick + special_unicode['no_width'] +
                              '*, ' + advice.lower(), self.is_client_mod)
        else:
            self.send_bot_msg(special_unicode['indicate'] + ' Unable to retrieve from server.', self.is_client_mod)

    def do_one_liner(self, tag):
        """
        Shows a random "one-liner" joke.
        :param tag: str a specific category to pick a random joke from OR state '?' to list categories.
        """
        if tag:
            if tag == '?':
                all_tags = ', '.join(other_apis.tags) + '.'
                self.send_undercover_msg(self.user_obj.nick, '*Possible tags*: ' + str(all_tags))
                return
            elif tag in other_apis.tags:
                one_liner = other_apis.one_liners(tag)
            else:
                self.send_bot_msg('The tag you specified is not available. Enter *!joke ?* to get a list of tags.',
                                  self.is_client_mod)
                return
        else:
            one_liner = other_apis.one_liners()

        if one_liner is not None:
            self.send_bot_msg('*' + one_liner + '*', self.is_client_mod)
        else:
            self.send_bot_msg('Unable to retrieve from server.', self.is_client_mod)

    def do_time(self, location, additional, twelve_hour):
        """
        Shows the time in a location via Google (or time.is if specified otherwise).
        :param location: str location name.
        :param additional: bool True/False whether the time.is API should be used to fetch the time.
        :param twelve_hour: bool True/False (if additional is True) whether the time returned should be displayed in
                            analogue with AM/PM.
        """
        if len(location) is 0:
            self.send_bot_msg(special_unicode['indicate'] + ' Please enter a location to fetch the time.',
                              self.is_client_mod)
        else:
            if not additional:
                time_list = other_apis.google_time(location)
                if time_list is None:
                    self.send_bot_msg(special_unicode['indicate'] + ' We could not fetch the time in *"%s"*.' %
                                      str(location), self.is_client_mod)
                else:
                    self.send_bot_msg('%s: *%s*' % (time_list[0], time_list[1]), self.is_client_mod)
            else:
                time = other_apis.time_is(location)
                if time is None:
                    self.send_bot_msg(
                        special_unicode['indicate'] + ' We could not fetch the time in "%s".' % str(location),
                        self.is_client_mod)
                else:
                    if twelve_hour:
                        time_status = 'AM'
                        raw_time = int(time[0:1])
                        if raw_time > 12:
                            time_status = 'PM'
                        time = str(raw_time - 12) + time[2:len(time) - 1] + ' ' + time_status
                    self.send_bot_msg('The time in *%s* is: *%s*.' % (str(location), str(time)), self.is_client_mod)

    # TODO: ASCII needs to be re-done properly - "None" reply.
    def do_ascii(self, ascii_id):
        """
        Shows the appropriate ASCII message in relation to the ASCII dictionary.
        :param ascii_id: str the ASCII keyword/command.
        """
        if '!' in ascii_id:
            parts = ascii_id.split('!')
            if len(parts) > 1:
                key = parts[1]
                if key in ascii_dict:
                    ascii_message = ascii_dict[key]
                    # Allow for custom replacement variables in the ASCII message.
                    new_ascii_message = self.replace_content(ascii_message)
                    self.send_bot_msg('*%s*' % new_ascii_message, self.is_client_mod)
                    return True
                else:
                    return False
        else:
            return False

    def private_message_handler(self, msg_sender, private_msg):
        """
        Custom private message commands.
        :param msg_sender: str the user sending the private message.
        :param private_msg: str the private message.
        """
        # Check ban words/strings on the private message.
        check = False
        if self.check_bad_string:
            check = self.check_msg_for_bad_string(private_msg, True)

        if not check:
            # Is this a custom PM command?
            if private_msg.startswith(CONFIG['prefix']):
                # Split the message in to parts.
                pm_parts = private_msg.split(' ')
                # pm_parts[0] is the command.
                pm_cmd = pm_parts[0].lower().strip()
                # The rest is a command argument.
                pm_arg = ' '.join(pm_parts[1:]).strip()

                # Super mod commands.
                if pm_cmd == CONFIG['prefix'] + 'rp':
                    threading.Thread(target=self.do_set_room_pass, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'bp':
                    threading.Thread(target=self.do_set_broadcast_pass, args=(pm_arg, )).start()

                # Owner and super mod commands.
                elif pm_cmd == CONFIG['prefix'] + 'key':
                    threading.Thread(target=self.do_key, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'clrbn':
                    threading.Thread(target=self.do_clear_bad_nicks).start()

                elif pm_cmd == CONFIG['prefix'] + 'clrbs':
                    threading.Thread(target=self.do_clear_bad_strings).start()

                elif pm_cmd == CONFIG['prefix'] + 'clrba':
                    threading.Thread(target=self.do_clear_bad_accounts).start()

                # Mod and bot controller commands.
                elif pm_cmd == CONFIG['prefix'] + 'disconnect':
                    self.do_pm_disconnect(pm_arg)

                elif pm_cmd == CONFIG['prefix'] + 'wakeup':
                    self.do_pm_wake()

                elif pm_cmd == CONFIG['prefix'] + 'op':
                    threading.Thread(target=self.do_op_user, args=(pm_parts, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'deop':
                    threading.Thread(target=self.do_deop_user, args=(pm_parts, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'up':
                    threading.Thread(target=self.do_cam_up, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'upvideo':
                    threading.Thread(target=self.do_cam_video_up, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'down':
                    threading.Thread(target=self.do_cam_down, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'nick':
                    self.do_nick(pm_arg)

                elif pm_cmd == CONFIG['prefix'] + 'ban':
                    threading.Thread(target=self.do_kick, args=(pm_arg, True, True, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'nocam':
                    threading.Thread(target=self.do_nocam, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'noguest':
                    threading.Thread(target=self.do_no_guest, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'notice':
                    if self.is_client_mod:
                        threading.Thread(target=self.send_owner_run_msg, args=(pm_arg, )).start()
                    else:
                        threading.Thread(target=self.send_private_msg, args=('Not enabled.', msg_sender)).start()

                elif pm_cmd == CONFIG['prefix'] + 'say':
                    threading.Thread(target=self.send_chat_msg, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'setpm':
                    threading.Thread(target=self.do_set_auto_pm, args=(pm_arg, )).start()

                # Public commands.
                elif pm_cmd == CONFIG['prefix'] + 'sudo':
                    threading.Thread(target=self.do_super_user, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'opme':
                    threading.Thread(target=self.do_opme, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'pm':
                    threading.Thread(target=self.do_pm_bridge, args=(pm_parts, )).start()

            # Print to console.
            self.console_write(pinylib.COLOR['white'], 'Private message from ' + msg_sender + ': ' + str(private_msg)
                               .replace(self.key, '***KEY***').replace(CONFIG['super_key'], '***SUPER KEY***'))

    # == Super Mod Command Methods. ==
    def do_set_room_pass(self, password):
        """
        Set a room password for the room.
        :param password: str the room password
        """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if not password:
                    self.privacy_settings.set_room_password()
                    self.send_bot_msg('*The room password was removed.*', self.is_client_mod)
                    pinylib.time.sleep(1)
                    self.send_private_msg('The room password was removed.', self.user_obj.nick)
                elif len(password) > 1:
                    self.privacy_settings.set_room_password(password)
                    self.send_private_msg('*The room password is now:* ' + password, self.user_obj.nick)
                    pinylib.time.sleep(1)
                    self.send_bot_msg('*The room is now password protected.*', self.is_client_mod)

    def do_set_broadcast_pass(self, password):
        """
        Set a broadcast password for the room.
        :param password: str the password
        """
        if self.is_client_owner:
            if self.user_obj.is_super:
                if not password:
                    self.privacy_settings.set_broadcast_password()
                    self.send_bot_msg('*The broadcast password was removed.*', self.is_client_mod)
                    pinylib.time.sleep(1)
                    self.send_private_msg('The broadcast password was removed.', self.user_obj.nick)
                elif len(password) > 1:
                    self.privacy_settings.set_broadcast_password(password)
                    self.send_private_msg('*The broadcast password is now:* ' + password, self.user_obj.nick)
                    pinylib.time.sleep(1)
                    self.send_bot_msg('*Broadcast password is enabled.*', self.is_client_mod)

    # == Owner And Super Mod Command Methods. ==
    def do_key(self, new_key):
        """
        Shows or sets a new secret key.
        :param new_key: str the new secret key.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            if len(new_key) is 0:
                self.send_private_msg('The current key is: *' + self.key + '*', self.user_obj.nick)
            elif len(new_key) < 6:
                self.send_private_msg('Key must be at least 6 characters long: ' + str(len(self.key)),
                                      self.user_obj.nick)
            elif len(new_key) >= 6:
                self.key = new_key
                self.send_private_msg('The key was changed to: *' + self.key + '*', self.user_obj.nick)

    def do_clear_bad_nicks(self):
        """ Clears the bad nicks file. """
        if self.user_obj.is_owner or self.user_obj.is_super:
            pinylib.fh.delete_file_content(CONFIG['path'], CONFIG['badnicks'])

    def do_clear_bad_strings(self):
        """ Clears the bad strings file. """
        if self.user_obj.is_owner or self.user_obj.is_super:
            pinylib.fh.delete_file_content(CONFIG['path'], CONFIG['badstrings'])

    def do_clear_bad_accounts(self):
        """ Clears the bad accounts file. """
        if self.user_obj.is_owner or self.user_obj.is_super:
            pinylib.fh.delete_file_content(CONFIG['path'], CONFIG['badaccounts'])

    # == Mod And Bot Controller Command Methods. ==
    def do_pm_disconnect(self, key):
        """
        Disconnects the bot via PM.
        :param key: str the key to access the command.
        """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            else:
                if key == self.key:
                    log.info('User %s:%s commenced remote disconnect.' % (self.user_obj.nick, self.user_obj.id))
                    self.send_private_msg('The bot will disconnect from the room.', self.user_obj.nick)
                    self.console_write(pinylib.COLOR['red'], 'Disconnected by %s.' % self.user_obj.nick)
                    threading.Thread(target=self.disconnect).start()
                    # Exit with a normal status code.
                    sys.exit(1)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)

    # TODO: Show hibernation statistics when awoken.
    def do_pm_wake(self):
        """ Lets the bot resume normal activities from when it was set to sleep. """
        if self.user_obj.is_owner or self.user_obj.is_super or self.user_obj.is_mod or self.user_obj.has_power:
            self.bot_listen = True
            self.send_private_msg('The bot has now *woken up* from sleep, normal activities may now be resumed.',
                                  self.user_obj.nick)

    def do_op_user(self, msg_parts):
        """
        Lets the room owner, a mod or a bot controller make another user a bot controller.
        NOTE: Mods or bot controllers will have to provide a key, the owner does not.
        :param msg_parts: list the pm message as a list.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user_obj.nick)
            elif len(msg_parts) == 2:
                user = self.find_user_info(msg_parts[1])
                if user is not None:
                    if user.has_power:
                        self.send_private_msg('This user already has privileges. No need to re-instate.',
                                              self.user_obj.nick)
                    else:
                        user.has_power = True
                        self.send_private_msg(user.nick + ' is now a bot controller.', self.user_obj.nick)
                        self.send_private_msg('You are now a bot controller.', user.nick)
                else:
                    self.send_private_msg('No user named: ' + msg_parts[1], self.user_obj.nick)

        elif self.user_obj.is_mod or self.user_obj.has_power:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user_obj.nick)
            elif len(msg_parts) == 2:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif len(msg_parts) == 3:
                if msg_parts[2] == self.key:
                    user = self.find_user_info(msg_parts[1])
                    if user is not None:
                        if user.has_power:
                            self.send_private_msg('This user already has privileges. No need to re-instate.',
                                                  self.user_obj.nick)
                        else:
                            user.has_power = True
                            self.send_private_msg(user.nick + ' is now a bot controller.', self.user_obj.nick)
                            self.send_private_msg('You are now a bot controller.', user.nick)
                    else:
                        self.send_private_msg('No user named: ' + msg_parts[1], self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_deop_user(self, msg_parts):
        """
        Lets the room owner, a mod or a bot controller remove a user from being a bot controller.
        NOTE: Mods or bot controllers will have to provide a key, owner does not.
        :param msg_parts: list the pm message as a list.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user_obj.nick)
            elif len(msg_parts) == 2:
                user = self.find_user_info(msg_parts[1])
                if user is not None:
                    if not user.has_power:
                        self.send_private_msg('This user was never instated as a bot controller. No need to DE-OP.',
                                              self.user_obj.nick)
                    else:
                        user.has_power = False
                        self.send_private_msg(user.nick + ' is not a bot controller anymore.', self.user_obj.nick)
                else:
                    self.send_private_msg('No user named: ' + msg_parts[1], self.user_obj.nick)

        elif self.user_obj.is_mod or self.user_obj.has_power:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user_obj.nick)
            elif len(msg_parts) == 2:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif len(msg_parts) == 3:
                if msg_parts[2] == self.key:
                    user = self.find_user_info(msg_parts[1])
                    if user is not None:
                        if not user.has_power:
                            self.send_private_msg(
                                'This user was never instated as a bot controller. No need to DE-OP.',
                                self.user_obj.nick)
                        else:
                            user.has_power = False
                            self.send_private_msg(user.nick + ' is not a bot controller anymore.',
                                                  self.user_obj.nick)
                    else:
                        self.send_private_msg('No user named: ' + msg_parts[1], self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_cam_up(self, key):
        """
        Makes the bot cam up.
        :param key str the key needed for moderators/bot controllers.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            self._set_stream()
        elif self.user_obj.is_mod or self.user_obj.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif key == self.key:
                self._set_stream()
            else:
                self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_cam_video_up(self, key):
        """
        Makes the bot cam up with a default video.
        :param key str the key needed for moderators/bot controllers.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            self._set_stream(video=True)
        elif self.user_obj.is_mod or self.user_obj.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif key == self.key:
                self._set_stream(video=True)
            else:
                self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_cam_down(self, key):
        """
        Makes the bot cam down.
        :param key: str the key needed for moderators/bot controllers.
        """
        if self.user_obj.is_owner or self.user_obj.is_super:
            self._set_stream(stream=False)
        elif self.user_obj.is_mod or self.user_obj.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif key == self.key:
                self._set_stream(stream=False)
            else:
                self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_nocam(self, key):
        """
        Toggles if broadcasting is allowed or not.
        NOTE: Mods or bot controllers will have to provide a key, owner does not.
        :param key: str secret key.
        """
        if self.is_broadcasting_allowed:
            if self.user_obj.is_owner or self.user_obj.is_super:
                self.is_broadcasting_allowed = False
                self.send_private_msg('*Broadcasting is NOT allowed.*', self.user_obj.nick)
            elif self.user_obj.is_mod or self.user_obj.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user_obj.nick)
                elif key == self.key:
                    self.is_broadcasting_allowed = False
                    self.send_private_msg('*Broadcasting is NOT allowed.*', self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)
        else:
            if self.user_obj.is_owner or self.user_obj.is_super:
                self.is_broadcasting_allowed = True
                self.send_private_msg('*Broadcasting is allowed.*', self.user_obj.nick)
            elif self.user_obj.is_mod or self.user_obj.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user_obj.nick)
                elif key == self.key:
                    self.is_broadcasting_allowed = True
                    self.send_private_msg('*Broadcasting is allowed.*', self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)

    # TODO: no_normal users mode - only account mode (maybe a toggle for this here?)
    def do_no_guest(self, key):
        """
        Toggles if guests are allowed to join the room or not.
        NOTE: This will kick all guests that join the room, only turn it on if you are sure.
              Mods or bot controllers will have to provide a key, the owner does not.
        :param key: str secret key.
        """
        if self.is_guest_entry_allowed:
            if self.user_obj.is_owner or self.user_obj.is_super:
                self.is_guest_entry_allowed = False
                self.send_private_msg('*Guests are NOT allowed to join the room.*', self.user_obj.nick)
            elif self.user_obj.is_mod or self.user_obj.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user_obj.nick)
                elif key == self.key:
                    self.is_guest_entry_allowed = False
                    self.send_private_msg('*Guests are NOT allowed to join the room.*', self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)
        else:
            if self.user_obj.is_owner or self.user_obj.is_super:
                self.is_guest_entry_allowed = True
                self.send_private_msg('*Guests ARE allowed to join the room.*', self.user_obj.nick)
            elif self.user_obj.is_mod or self.user_obj.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user_obj.nick)
                elif key == self.key:
                    self.is_guest_entry_allowed = True
                    self.send_private_msg('*Guests ARE allowed to join the room.*', self.user_obj.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_set_auto_pm(self, message):
        """
        Allows for owners/moderators/botters to change the room private message.
        :param message: str the new private message to be sent automatically to everyone upon entering the room.
        """
        if self.user_obj.is_mod or self.user_obj.has_power or self.user_obj.is_owner:
            if self.auto_pm:
                if len(message) is 0:
                    self.send_private_msg('Please enter a new Room Private Message.', self.user_obj.nick)
                else:
                    self.pm_msg = message
                    self.send_private_msg('Room private message now set to: %s' % self.pm_msg, self.user_obj.nick)
            else:
                self.send_private_msg('Automatic private message feature is not enabled in the configuration.',
                                      self.user_obj.nick)

    # == Public PM Command Methods. ==
    def do_super_user(self, super_key):
        """
        Makes a user super mod, the highest level of mod.
        It is only possible to be a super mod if the client is owner.
        :param super_key: str the super key.
        """
        if self.is_client_owner:
            if len(super_key) is 0:
                self.send_private_msg('Missing super key.', self.user_obj.nick)
            elif super_key == CONFIG['super_key']:
                self.user_obj.is_super = True
                self.send_private_msg('*You are now a super mod.*', self.user_obj.nick)
            else:
                self.send_private_msg('Wrong super key.', self.user_obj.nick)
        else:
            self.send_private_msg('Client is owner: *' + str(self.is_client_owner) + '*', self.user_obj.nick)

    def do_opme(self, key):
        """
        Makes a user a bot controller if user provides the right key.
        :param key: str the secret key.
        """
        if self.user_obj.has_power:
            self.send_private_msg('You already have privileges. No need to OP again.', self.user_obj.nick)
        else:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user_obj.nick)
            elif key == self.key:
                self.user_obj.has_power = True
                self.send_private_msg('You are now a bot controller.', self.user_obj.nick)
            else:
                self.send_private_msg('Wrong key.', self.user_obj.nick)

    def do_pm_bridge(self, pm_parts):
        """
        Makes the bot work as a PM message bridge between two users who are not signed in.
        :param pm_parts: list the pm message as a list.
        """
        if len(pm_parts) == 1:
            self.send_private_msg('Missing username.', self.user_obj.nick)
        elif len(pm_parts) == 2:
            self.send_private_msg('The command is: ' + CONFIG['prefix'] + 'pm username message', self.user_obj.nick)
        elif len(pm_parts) >= 3:
            pm_to = pm_parts[1]
            msg = ' '.join(pm_parts[2:])
            is_user = self.find_user_info(pm_to)
            if is_user is not None:
                if is_user.id == self.client_id:
                    self.send_private_msg('Action not allowed.', self.user_obj.nick)
                else:
                    self.send_private_msg('*<' + self.user_obj.nick + '>* ' + msg, pm_to)
            else:
                self.send_private_msg('No user named: ' + pm_to, self.user_obj.nick)

    # Media functions.
    def media_event_handler(self):
        """ This method gets called whenever a media is done playing. """
        if len(self.playlist) is not 0:
            if self.inowplay >= len(self.playlist):
                self.inowplay = 0
                self.playlist[:] = []
            else:
                pinylib.time.sleep(self.media_delay)
                if self.is_connected:
                    self.last_played_media = self.playlist[self.inowplay]
                    self.send_media_broadcast_start(self.playlist[self.inowplay]['type'],
                                                    self.playlist[self.inowplay]['video_id'])
                self.media_event_timer(self.playlist[self.inowplay]['video_time'])
                self.inowplay += 1

    def media_event_timer(self, video_time):
        """
        Set of a timed event thread.
        :param video_time: int the time in milliseconds.
        """
        video_time_in_seconds = video_time / 1000
        # The next line should be where ever send_media_broadcast_start is called.
        # For now ill leave it here as it doesn't seem to cause any problems.
        # However if a tune gets paused, then current_media_time_point will return a wrong time
        # this could affect user joining the room and therefor it should be fixed.
        self.media_start_time = int(pinylib.time.time() * 1000)
        self.media_timer_thread = threading.Timer(video_time_in_seconds, self.media_event_handler)
        self.media_timer_thread.start()

    def current_media_time_point(self):
        """
        Returns the currently playing medias time point.
        :return: int the currently playing medias time point in milliseconds.
        """
        if 'pause' in self.last_played_media:
            return self.last_played_media['pause']
        else:
            if self.media_timer_thread is not None:
                if self.media_timer_thread.is_alive():
                    ts_now = int(pinylib.time.time() * 1000)
                    elapsed_track_time = ts_now - self.media_start_time
                    return elapsed_track_time
                return 0
            return 0

    def cancel_media_event_timer(self):
        """
        Cancel the media event timer if it is running.
        :return: True if canceled, else False
        """
        if self.media_timer_thread is not None:
            if self.media_timer_thread.is_alive():
                self.media_timer_thread.cancel()
                self.media_timer_thread = None
                return True
            return False
        return False

    def random_msg(self):
        """
        Pick a random message from a list of messages.
        :return: str random message.
        """
        upnext = None
        if len(self.playlist) is not 0:
            if self.inowplay + 1 < len(self.playlist):
                next_video_title = self.playlist[self.inowplay]['video_title']
                next_video_time = self.to_human_time(self.playlist[self.inowplay]['video_time'])
                upnext = '*Next is:* (' + str(self.inowplay) + ') *' + next_video_title + '* ' + next_video_time
            inquee = len(self.playlist) - self.inowplay
            plstat = str(len(self.playlist)) + ' *items in the playlist.* ' + str(inquee) + ' *Still in queue.*'
        else:
            upnext = CONFIG['prefix'] + 'yt *(YouTube title, link or id) to add a YouTube to the playlist.'
            plstat = CONFIG['prefix'] + 'sc *(SoundCloud title or id)* to add a SoundCloud to the playlist.'

        messages = ['Reporting for duty..', 'Hello, is anyone here?', 'Awaiting command..', 'Observing behavior..',
                    upnext, plstat, '*I have been connected for:* ' + self.to_human_time(self.get_uptime()),
                    'Everyone alright?', 'What\'s everyone up to?',
                    'How is the weather where everyone is?', 'Why is everyone so quiet?',
                    'Anything in particular going on?',
                    'Type: *' + CONFIG['prefix'] + 'help* for a list of commands',
                    'Anything interesting in the news lately?']
        return random.choice(messages)

    # Timed auto functions.
    def auto_msg_handler(self):
        """ The event handler for auto_msg_timer. """
        if self.is_connected:
            self.send_bot_msg(self.random_msg())
        self.start_auto_msg_timer()

    def start_auto_msg_timer(self):
        """
        In rooms with less activity, it can be useful to have the client send auto messages to keep the client alive.
        This method can be disabled by setting CONFIG['auto_message_sender'] to False.
        The interval for when a message should be sent, is set in CONFIG['auto_message_interval']
        """
        threading.Timer(CONFIG['auto_message_interval'], self.auto_msg_handler).start()

    # TODO: Added in a timer to monitor CleverBot session & reset messages periodically.
    def clever_bot_timer(self):
        """
        Start clearing POST data by checking if messages are sent to CleverBot within
        every 5 minutes (300 seconds), otherwise clear all the data that was previously recorded.
        NOTE: Anything as a result asked before that to CleverBot may reply with an inaccurate reply.
        """
        while self.clever_bot_session is not None:
            # Reset the POST log in CleverBot to an empty list to clear the previous
            # POST message history if the time is 5 minutes or over and messages have been sent in the log.
            if int(pinylib.time.time()) - self.clever_bot_msg_time >= 300 and \
                            len(self.clever_bot_session.post_log) is not 0:
                self.clever_bot_session.post_log = []
                self.clever_bot_msg_time = int(pinylib.time.time())
            pinylib.time.sleep(1)

    # Helper Methods.
    def get_privacy_settings(self):
        """ Parse the privacy settings page. """
        log.info('Parsing %s\'s privacy page. Proxy %s' % (self.account, self.proxy))
        self.privacy_settings = privacy_settings.TinychatPrivacyPage(self.proxy)
        self.privacy_settings.parse_privacy_settings()

    def get_uptime(self):
        """
        Gets the bots uptime.
        NOTE: This will not get reset after a reconnect.
        :return: int milliseconds.
        """
        up = int(pinylib.time.time() - self.init_time)
        return up * 1000

    @staticmethod
    def format_time_point(raw_time_point):
        """
        Formats a given time point by the user in the format hh:mm:ss, mm:ss or ss.
        :param raw_time_point: str the type of time point given, varying in style (as described above).
        :return: int milliseconds of the time that was given.
        """
        if ':' in raw_time_point:
            time_point_components = raw_time_point.split(':')
        else:
            time_point_components = [raw_time_point]

        # h/m/s pre-sets.
        hour = 3600000
        minute = 60000
        second = 1000

        # Append in blank hour/minute values if they are missing.
        if len(time_point_components) < 3:
            if len(time_point_components) is 2:
                time_point_components.insert(0, '0')
            else:
                time_point_components.insert(0, '0')
                time_point_components.insert(0, '0')

        # Total milliseconds.
        milliseconds = int(time_point_components[0]) * hour + int(time_point_components[1]) * minute + \
                       int(time_point_components[2]) * second
        return milliseconds

    @staticmethod
    def to_human_time(milliseconds):
        """
        Converts milliseconds or seconds to (day(s)) hours minutes seconds.
        :param milliseconds: int the milliseconds or seconds to convert.
        :return: str in the format (days) hh:mm:ss
        """
        seconds = milliseconds / 1000

        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if d == 0 and h == 0:
            human_time = '%02d:%02d' % (m, s)
        elif d == 0:
            human_time = '%d:%02d:%02d' % (h, m, s)
        else:
            human_time = '%d Day(s) %d:%02d:%02d' % (d, h, m, s)
        return human_time

    def check_msg_for_bad_string(self, msg, pm=False):
        """
        Checks the chat message for bad string.
        :param msg: str the chat message.
        :param pm: boolean true/false if the check is for a pm or not.
        """
        msg_words = msg.split(' ')
        bad_strings = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badstrings'])
        if bad_strings is not None:
            for word in msg_words:
                if word in bad_strings:
                    if self.is_client_mod:
                        self.send_ban_msg(self.user_obj.nick, self.user_obj.id)
                        if CONFIG['bsforgive']:
                            self.send_forgive_msg(self.user_obj.id)
                        if not pm:
                            self.send_bot_msg(special_unicode['toxic'] + ' *Auto-banned*: (bad string in message)',
                                              self.is_client_mod)
                    return True

    def connection_info(self):
        """ Prints connection information regarding the bot into the console. """
        print('\nRoom location: %s, Room name: %s' % (self._embed_url, self.roomname))
        print('RTMP Info.:')
        print('IP: %s, PORT: %s, Proxy: %s, RTMP Url: %s, Playpath: %s' % (self._ip, self._port, self.proxy,
                                                                           self._tc_url, self._app))
        print('SWF (Desktop) Version: %s, SWF Url: %s' % (self._desktop_version, self._swf_url))
        print ('Tinychat Room Info.:')
        print('Nickname: %s, ID: %s, Account: %s' % (self.client_nick, self.client_id, self.account))
        print('SWF (Local) Version: %s, Type: %s, Greenroom: %s, Room password: %s, Room broadcasting password: %s' %
              (self._swf_version, self._roomtype, self.greenroom, self.room_pass, self.room_broadcast_pass))

    # TODO: Add custom allocations for 'replacement variables'.
    def replace_content(self, message, user=None, room=None):
        """
        Allows the replacement of specific content within a message with local data used by the program.
        :param message: str the message to replace content with.
        :param user: str a personal name to fill in for with the %user% variable.
        :param room: str a personal room to fill in for with the %room% variable.
        :return: str the altered message.
        """
        if '%user%' in message or '%room%' in message:
            if user is None:
                user = self.user_obj.nick
            if room is None:
                room = self.roomname
            message = message.replace('%user%', user).replace('%room%', room)
        return message


def main():
    if CONFIG['auto_connect']:
        room_name = CONFIG['room']
        nickname = CONFIG['nick']
        room_password = CONFIG['room_password']
        login_account = CONFIG['account']
        login_password = CONFIG['account_password']

        if len(room_name) is 0:
            print('The ROOM name is empty in the configuration. You can configure this in ' + CONFIG_FILE_NAME +
                  ' if you have \'auto_connect\' enabled.')
            # Exit to system safely whilst returning exit code 1.
            sys.exit(1)
    else:
        # Assign basic login variables.
        room_name = raw_input('Enter room name: ')

        while len(room_name) is 0:
            clear_console()
            print('Please enter a ROOM name to continue.')
            room_name = raw_input('Enter room name: ')

        room_password = pinylib.getpass.getpass('Enter room password (optional:password hidden): ')
        nickname = raw_input('Enter nick name (optional): ')
        login_account = raw_input('Login account (optional): ')
        login_password = pinylib.getpass.getpass('Login password (optional:password hidden): ')

    # Set up the TinychatBot class with the login details provided.
    client = TinychatBot(room_name, nick=nickname, account=login_account,
                         password=login_password, room_pass=room_password)

    # Start connection in a new thread.
    t = threading.Thread(target=client.prepare_connect)
    t.daemon = True
    t.start()

    # Wait for the connection to be established and then continue.
    while not client.is_connected:
        pinylib.time.sleep(1)

    # Initial threads.
    # - Bot thread management:
    threading.Thread(target=client.alive)
    client.console_write(pinylib.COLOR['white'], 'Started alive management.')

    # - Ping request thread management:
    # NOTE: Possibility of prolonging a connection with the server; a response is returned and we respond with data.
    threading.Thread(target=client.send_ping_request)
    client.console_write(pinylib.COLOR['white'], 'Started ping management.')

    while client.is_connected:
        chat_msg = raw_input()

        # TODO: Save pertinent bot data before exiting - MySQLDB implementation.
        # Stop the connection safely
        if chat_msg.lower() == '/q':
            client.disconnect()
            # Exit to system safely, whilst returning exit code 0.
            sys.exit(0)

        # Reconnect client back to the server.
        elif chat_msg.lower() == '/reconnect':
            client.reconnect()

        # Display server/room connection information in the console.
        elif chat_msg.lower() == '/connection':
            client.connection_info()

        # Modify the bot nickname from the console
        elif chat_msg.lower() == '/nick':
            new_nickname = raw_input('\nNew bot nickname: ')
            client.client_nick = new_nickname
            client.set_nick()

        # Send a private message to a user in the room
        elif chat_msg.lower() == '/pm':
            private_message_nick = raw_input('\nNick to Private Message (PM): ')
            private_message = raw_input('\nEnter your message: ')
            client.send_private_msg(private_message, private_message_nick)

        # NOTE: When implementing never use these as a point of access (this is to a restricted member of the class).
        # Manual broadcasting.
        elif chat_msg.lower() == '/camup':
            if not client.publish_connection:
                client._set_stream()
            else:
                print('Active stream present, close before starting another.')

        elif chat_msg.lower() == '/broadcast':
            if not client.publish_connection:
                client._set_stream(video=True)
            else:
                print('Active stream present, close before starting another.')

        elif chat_msg.lower() == '/camdown':
            if client.publish_connection:
                client._set_stream(stream=False)
            else:
                print('Start a stream first before you can close it.')

        else:
            if CONFIG['console_msg_notice']:
                client.send_bot_msg(chat_msg, client.is_client_mod)
            else:
                client.send_chat_msg(chat_msg)
                # Print our chat messages onto the console
                client.console_write(pinylib.COLOR['cyan'], 'You:' + chat_msg)


if __name__ == '__main__':
    if CONFIG['debug_to_file']:
        formatter = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        logging.basicConfig(filename=CONFIG['debug_file_name'], level=logging.DEBUG, format=formatter)
        log.info('Starting pinybot.py version: %s' % __version__)
    else:
        log.addHandler(logging.NullHandler())
    main()
