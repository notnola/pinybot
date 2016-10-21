#!/usr/bin/env python2
# -*- coding: utf-8 -*-

""" A Tinychat bot (based on the pinylib library) with additional features/commands.
           _             __          __
    ____  (_)___  __  __/ /_  ____  / /_
   / __ \/ / __ \/ / / / __ \/ __ \/ __/
  / /_/ / / / / / /_/ / /_/ / /_/ / /_
 / .___/_/_/ /_/\__, /_.___/\____/\__/
/_/            /____/

"""

# Supplementary Information:
# Description: Tinychat Python bot,
# Repository homepage: https://goelbiju.github.io/pinybot/,
# Repository: https://github.com/GoelBiju/pinybot/

# Acknowledgements to Nortxort (https://github.com/nortxort/) and Autotonic (https://github.com/autotonic/).
# Many others, including Notnola (https://github.com/notnola/) and Technetium1 (https://github.com/technetium1),
# have helped with this project, as well all the contributors on the GitHub repository who have made this
# project flourish. I would like to say thank to you as well for choosing to contribute by using this
# open-source software.

import sys
import logging
import random
import re
import threading

# TODO: Auto-url moved to utilities folder.
import pinylib
from apis import youtube, soundcloud, lastfm, other, locals, clever_client_bot
from utilities import string_utili, console_utili, media_manager, privacy_settings, auto_url, unicode_catalog

# TODO: Issue: Configuration format to new base - JSON style; non-viewable.
# State the name of the '.ini' configuration file here:
CONFIG_FILE_NAME = '/config.ini'
# Make sure we only parse the 'bot' section in the configuration.
CONFIG, CONFIG_PATH = pinylib.load_config(CONFIG_FILE_NAME, 'Bot')
if CONFIG is None:
    print('No file named %s found in: %s \nWe cannot proceed to start-up without the configuration file.' %
          (CONFIG_FILE_NAME, CONFIG_PATH))
    # Exit to system safely whilst returning exit code 1.
    sys.exit(1)

# TODO: 'bot_message_to_console' configuration option added.
# TODO: 'public_cmds' configuration option added.
# TODO: Rework on the text files, new naming and content changes.

# TODO: Logging issue - TypeError: not all arguments converted during string formatting - debug_to_file.
log = logging.getLogger(__name__)
__version__ = '1.5.0'
build_name = '"Quantum"'
author_info = 'https://github.com/GoelBiju/pinybot ) ' + \
              '*NOTE:* Acknowledgements/general information can be found in the repository.'

# TODO: Clear console (console_utili.py) procedure moved to utilities.
# TODO: Eight ball moved to locals.


class TinychatBot(pinylib.TinychatRTMPClient):
    """ Overrides event methods in TinychatRTMPClient that the client should to react to. """

    # TODO: Set full path for the PATH key in the CONFIG dictionary.
    # Set the path for CONFIG key.
    CONFIG['path'] = sys.path[0] + '/' + CONFIG['path']

    # Initial settings:
    key = CONFIG['key']

    # - Privilege settings:
    botters = []  # Botters will only be temporarily stored until the next bot restart.

    # TODO: Implement database.
    # TODO: Move loading and creation of files for each room into a separate function and call it when initialising.
    # - Loads/creates permanent botter accounts files:
    # if not os.path.exists(self.config_path() + CONFIG['botteraccounts']):
    #     open(TinychatBot.config_path() + CONFIG['botteraccounts'], mode='w')
    # botteraccounts = pinylib.fh.file_reader(self.config_path(), CONFIG['botteraccounts'])
    #
    # - Loads/creates autoforgive files:
    # if not os.path.exists(CONFIG['path'] + CONFIG['autoforgive']):
    #     open(self.config_path() + CONFIG['autoforgive'], mode='w')
    # autoforgive = pinylib.fh.file_reader(config_path(), CONFIG['autoforgive'])

    # TODO: Move this along with loading the other files.
    # Loads the 'ascii.txt' file with ASCII/unicode text into a dictionary.
    if CONFIG['ascii_chars']:
        ascii_dict = pinylib.fh.unicode_loader(CONFIG['path'] + CONFIG['ascii_file'])
        ascii_chars = True
        if ascii_dict is None:
            ascii_chars = False
            print('No ' + CONFIG['ascii_file'] + ' was not found at: ' + CONFIG['path'])
            print('As a result the unicode text was not loaded. Please check your configurations.\n')

    # - media events/variables settings:
    media_manager = media_manager.MediaManager()
    media_timer_thread = None
    search_play_lists = []
    search_list = []

    yt_type = 'youTube'
    sc_type = 'soundCloud'
    media_request = None
    playback_delay = 2.5
    playlist_mode = CONFIG['playlist_mode']
    public_media = CONFIG['public_media']

    # - Audio and video settings:
    # camera_manager = camera_manager.CameraManager()
    # logo_stream = False
    # flv1_logo_data = open('utilities/camera_manager/logo.flv1', 'rb').read()

    # - module settings:
    privacy_settings = object

    cleverbot_enable = CONFIG['cleverbot_enable']
    cleverbot_session = None
    cleverbot_instant = CONFIG['cleverbot_instant']
    cleverbot_msg_time = int(pinylib.time.time())

    # - join settings:
    is_newusers_allowed = CONFIG['new_users_allowed']
    is_broadcasting_allowed = CONFIG['broadcasting_allowed']
    is_guest_entry_allowed = CONFIG['guests_allowed']
    is_guest_nicks_allowed = CONFIG['guest_nicks_allowed']

    join_quit_notifications = CONFIG['join_quit_notifications']
    auto_pm = CONFIG['auto_pm']
    pm_msg = CONFIG['pm_msg']
    welcome_user = CONFIG['welcome_user']
    welcome_broadcast_msg = CONFIG['welcome_broadcast_msg']
    auto_close = CONFIG['auto_close']
    ban_mobiles = CONFIG['ban_mobiles']

    # - method settings:
    auto_url_mode = CONFIG['auto_url_mode']
    cam_blocked = []
    bot_listen = True
    forgive_all = False
    syncing = False
    is_cmds_public = CONFIG['public_cmds']

    # - spam prevention settings:
    spam_prevention = CONFIG['spam_prevention']
    check_bad_string = CONFIG['check_bad_string']
    snapshot_spam = CONFIG['snapshot_spam']
    snap_line = 'I just took a video snapshot of this chatroom. Check it out here:'
    unicode_spam = CONFIG['unicode_spam']
    message_caps_limit = CONFIG['message_caps_limit']
    room_link_spam = CONFIG['room_link_spam']
    caps_char_limit = CONFIG['caps_char_limit']
    bot_report_kick = CONFIG['bot_report_kick']

    # - regex settings:
    # TODO: Will we need to add the specific flag (re.I) for each search function?
    tinychat_spam_pattern = re.compile(r'tinychat.com\/\w+|tinychat. com\/\w+|tinychat .com\/\w+($| |\/+ |\/+$|\n+)\s',
                                       re.I)
    youtube_pattern = re.compile(r'http(?:s*):\/\/(?:www\.youtube|youtu)\.\w+(?:\/watch\?v=|\/)(.{11})')
    character_limit_pattern = re.compile(r'[A-Z0-9]{50,}')

    # TODO: Can we make this more succint?
    # Allow playlist mode to be enforced upon turning on public media.
    if public_media:
        playlist_mode = True

    # TODO: Imports and variables names, adjust to match new base.

    def on_join(self, join_info_dict):
        log.info('User join info: %s' % join_info_dict)
        user = self.add_user_info(join_info_dict)

        if join_info_dict['account']:
            tc_info = pinylib.tinychat.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']

            if self.join_quit_notifications:
                if join_info_dict['own']:
                    self.console_write(pinylib.COLOR['red'], 'Room Owner %s:%d:%s' %
                                       (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))
                elif join_info_dict['mod']:
                    self.console_write(pinylib.COLOR['bright_red'], 'Moderator %s:%d:%s' %
                                       (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))
                else:
                    self.console_write(pinylib.COLOR['bright_yellow'], '%s:%d has account: %s' %
                                       (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))

            # TODO: Test to see if this works.
            ba = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badaccounts'])
            if ba is not None:
                if join_info_dict['account'] in ba:
                    if self._is_client_mod:
                        self.send_ban_msg(join_info_dict['nick'], join_info_dict['id'])
                        if CONFIG['baforgive']:
                            self.send_forgive_msg(join_info_dict['id'])
                        self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-Banned:* %s (bad account)' %
                                          join_info_dict['account'], self._is_client_mod)

            # TODO: Implement database.
            # Assign botteraccounts if they were in the locally stored file.
            if join_info_dict['account'] in self.botteraccounts:
                user.has_power = True
        else:
            if join_info_dict['id'] is not self._client_id:
                if not self.is_guest_entry_allowed:
                    self.send_ban_msg(join_info_dict['nick'], join_info_dict['id'])
                    # Remove next line to keep ban.
                    self.send_forgive_msg(join_info_dict['id'])
                    self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-Banned:* (guests not allowed)')
                else:
                    if self.join_quit_notifications:
                        self.console_write(pinylib.COLOR['bright_cyan'], '%s:%d joined the room.' %
                                           (join_info_dict['nick'], join_info_dict['id']))

    def on_joinsdone(self):
        if not self._is_reconnected:
            if CONFIG['auto_message_enabled']:
                self.start_auto_msg_timer()
        if self._is_client_mod:
            self.send_banlist_msg()
        if self._is_client_owner and self._room_type != 'default':
            threading.Thread(target=self.get_privacy_settings).start()

    def on_avon(self, uid, name):
        if not self.is_broadcasting_allowed or name in self.cam_blocked:
            self.send_close_user_msg(name)
            self.console_write(pinylib.COLOR['cyan'], 'Auto closed broadcast %s:%s' % (name, uid))
        else:
            user = self.find_user_info(name)

            if not user.is_owner or not user.is_mod or not user.has_power:
                uid_parts = str(uid).split(':')
                if len(uid_parts) is 2:
                    clean_uid = uid_parts[0]
                    user_device = u'' + uid_parts[1]
                    if user_device not in ['android', 'ios']:
                        user_device = 'unknown'
                    # TODO: 'device_type' attribute update
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
                    name = unicode_catalog.NO_WIDTH + name + unicode_catalog.NO_WIDTH
                self.send_bot_msg('%s *%s*' % (self.welcome_broadcast_msg, name), self._is_client_mod)

            self.console_write(pinylib.COLOR['cyan'], '%s:%s is broadcasting.' % (name, uid))

    def send_auto_pm(self, nickname):
        room = self._roomname.upper()
        new_pm_msg = self.replace_content(self.pm_msg, nickname, room)

        if '|' in new_pm_msg:
            message_parts = new_pm_msg.split('|')
            for x in range(len(message_parts)):
                self.send_private_msg(len(message_parts), nickname)
        else:
            self.send_private_msg(new_pm_msg, nickname)

    def on_nick(self, old, new, uid):
        if uid != self._client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self._room_users.keys():
                del self._room_users[old]
                self._room_users[new] = old_info

            # Fetch latest information regarding the user.
            user = self.find_user_info(new)

            # Transfer temporary botter privileges on a nick change.
            if old in self.botters:
                self.botters.remove(old)
                self.botters.append(new)

            if not user.is_owner or user.is_mod or user.has_power:
                if new.startswith('guest-') and not self.is_guest_nicks_allowed:
                    if self._is_client_mod:
                        self.send_ban_msg(new, uid)
                        # Remove next line to keep ban.
                        self.send_forgive_msg(uid)
                        self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-Banned:* (bot nick detected)')
                        return

                elif new.startswith('newuser') and not self.is_newusers_allowed:
                    if self._is_client_mod:
                            self.send_ban_msg(new, uid)
                            self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-Banned:* (new-user nick detected)')
                            return

            if old.startswith('guest-'):
                # TODO: Confirm this works and reads the file correctly.
                # bn = pinylib.fh.file_reader(CONFIG['path'], CONFIG['badnicks'])
                bn = pinylib.fh.file_reader(self.config_path(), CONFIG['nick_bans'])

                if bn is not None and new in bn:
                    if self._is_client_mod:
                        self.send_ban_msg(new, uid)
                        if CONFIG['bnforgive']:
                            self.send_forgive_msg(uid)
                        self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-Banned:* (bad nick)')

                else:
                    if user is not None:
                        if self.welcome_user:
                            # TODO: Welcome user owner message if an account is present,
                            # otherwise it is an undercover message.
                            if user.account:
                                # Greet user with account name/message.
                                self.send_bot_msg(unicode_catalog.NOTIFICATION + ' Welcome to ' + self._roomname +
                                                  ': *' + unicode_catalog.NO_WIDTH + new + unicode_catalog.NO_WIDTH +
                                                  '* (' + user.account + ')')
                            else:
                                self.send_undercover_msg(user.nick, 'Welcome to %s: *%s*' %
                                                         (self._roomname, user.account))

                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                        if not self.media_manager.is_mod_playing:
                            # Play the media at the correct start time when the user has set their nick name.
                            self.send_media_broadcast_start(self.media_manager.track().type,
                                                            self.media_manager.track().id,
                                                            time_point=self.media_manager.elapsed_track_time(),
                                                            private_nick=new)

                    # Send any private messages set to be sent once their nickname has been set.
                    if self.auto_pm and len(self.pm_msg) is not 0:
                        self.send_auto_pm(new)

            self.console_write(pinylib.COLOR['bright_cyan'], '%s:%s changed nick to: %s' % (old, uid, new))

    def on_kick(self, uid, name):
        if uid != self._client_id:
            user = self.find_user_info(name)
            # TODO: Implement database.
            if user.account in self.autoforgive:
                self.send_forgive_msg(user.id)
                self.console_write(pinylib.COLOR['bright_red'], '%s:%s was kicked and was automatically forgiven.' %
                                   (name, uid))
            else:
                self.console_write(pinylib.COLOR['bright_red'], '%s:%s was banned.' % (name, uid))
                self.send_banlist_msg()

    def on_quit(self, uid, name):
        if uid is not self._client_id:
            if name in self._room_users.keys():
                # Execute the tidying method before deleting the user from our records.
                self.tidy_exit(name)
                del self._room_users[name]
                if self.join_quit_notifications:
                    self.console_write(pinylib.COLOR['cyan'], '%s:%s left the room.' % (name, uid))

    def tidy_exit(self, name):
        user = self.find_user_info(name)
        # Delete user from botters/botteraccounts if they were instated.
        if user.nick in self.botters:
            self.botters.remove(user.nick)
        if user.account:
            # TODO: Implement database.
            if user.account in self.botteraccounts:
                self.botteraccounts.remove(user.account)
        # Delete the nickname from the cam blocked list if the user was in it.
        if user.nick in self.cam_blocked:
            self.cam_blocked.remove(user.nick)

    def on_reported(self, uid, nick):
        self.console_write(pinylib.COLOR['bright_red'], 'The bot was reported by %s:%s.' % (nick, uid))
        if self.bot_report_kick:
            self.send_ban_msg(nick, uid)
            self.send_bot_msg('*Auto-Banned:* (reporting the bot)', self._is_client_mod)
            # Remove next line to keep ban.
            self.send_forgive_msg(uid)

    # Media Events.
    def on_media_broadcast_start(self, media_type, video_id, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media, youTube or soundCloud.
        :param video_id: str the YouTube ID or SoundCloud track ID.
        :param usr_nick: str the user name of the user playing media.
        """
        self.cancel_media_event_timer()

        if media_type == 'youTube':
            _youtube = youtube.youtube_time(video_id, check=False)
            if _youtube is not None:
                self.media_manager.mb_start(self.user.nick, _youtube)

        elif media_type == 'soundCloud':
            _soundcloud = soundcloud.soundcloud_track_info(video_id)
            if _soundcloud is not None:
                self.media_manager.mb_start(self.user.nick, _soundcloud)

        self.media_event_timer(self.media_manager.track().time)
        self.console_write(pinylib.COLOR['bright_magenta'], '%s is playing %s %s' % (usr_nick, media_type, video_id))

    def on_media_broadcast_close(self, media_type, usr_nick):
        """
        A user closed a media broadcast.
        :param media_type: str the type of media, youTube or soundCloud.
        :param usr_nick: str the user name of the user closing the media.
        """
        self.cancel_media_event_timer()
        self.media_manager.mb_close()
        self.console_write(pinylib.COLOR['bright_magenta'], '%s closed the %s' % (usr_nick, media_type))

    def on_media_broadcast_paused(self, media_type, usr_nick):
        """
        A user paused the media broadcast.
        :param media_type: str the type of media being paused, youTube or soundCloud.
        :param usr_nick: str the user name of the user pausing the media.
        """
        self.cancel_media_event_timer()
        self.media_manager.mb_pause()
        self.console_write(pinylib.COLOR['bright_magenta'], '%s paused the %s' % (usr_nick, media_type))

    def on_media_broadcast_play(self, media_type, time_point, usr_nick):
        """
        A user resumed playing a media broadcast.
        :param media_type: str the media type, youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user resuming the tune.
        """
        self.cancel_media_event_timer()
        new_media_time = self.media_manager.mb_play(time_point)
        self.media_event_timer(new_media_time)

        self.console_write(pinylib.COLOR['bright_magenta'], '%s resumed the %s at: %s' %
                           (usr_nick, media_type, self.format_time(time_point)))

    def on_media_broadcast_skip(self, media_type, time_point, usr_nick):
        """
        A user time searched a tune.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user time searching the tune.
        """
        self.cancel_media_event_timer()
        new_media_time = self.media_manager.mb_skip(time_point)
        if not self.media_manager.is_paused:
            self.media_event_timer(new_media_time)

        self.console_write(pinylib.COLOR['bright_magenta'], '%s time searched the %s at: %s' %
                           (usr_nick, media_type, self.format_time(time_point)))

    # Media Message Method.
    def send_media_broadcast_start(self, media_type, video_id, time_point=0, private_nick=None):
        """
        Starts a media broadcast.
        NOTE: This method replaces play_youtube and play_soundcloud.
        :param media_type: str 'youTube' or 'soundCloud'.
        :param video_id: str the media video ID.
        :param time_point: int where to start the media from in milliseconds.
        :param private_nick: str if not None, start the media broadcast for this username only.
        """
        mbs_msg = '/mbs %s %s %s' % (media_type, video_id, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbs_msg)
        else:
            self.send_chat_msg(mbs_msg)

    # Message Method.
    def send_bot_msg(self, msg, use_chat_msg=False):
        """
        Send a chat message to the room.

        :param msg: str the message to send.
        :param use_chat_msg: boolean True/False, use normal chat messages/send messages
                             depending on whether or not the client is a moderator.
        """
        if use_chat_msg:
            self.send_chat_msg(msg)
        else:
            if self._is_client_mod:
                self.send_owner_run_msg(msg)
            else:
                self.send_chat_msg(msg)
        if CONFIG['bot_msg_to_console']:
            self.console_write(pinylib.COLOR['white'], msg)

    def message_handler(self, msg_sender, decoded_msg):
        """
        Custom command handler.

        NOTE: Any method using an API should be started in a new thread.
        :param msg_sender: str the user sending the message.
        :param decoded_msg: str the message.
        """
        # Spam checks to prevent any text from spamming the room chat and being parsed by the bot.
        if self.spam_prevention:
            if not self.user.is_owner and not self.user.is_super and not self.user.is_mod \
                    and not self.user.has_power:

                # Start the spam check.
                spam_potential = self.sanitize_message(msg_sender, self.raw_msg)
                # TODO: See spam potential without being a moderator, to reduce spam in console(?)
                if spam_potential:
                    self.console_write(pinylib.COLOR['bright_red'], 'Spam inbound - halting handling.')
                    return

            # If auto URL has been switched on, run, in a new the thread, the automatic URL header retrieval.
            if self.auto_url_mode:
                threading.Thread(target=self.do_auto_url, args=(decoded_msg,)).start()

        # TODO: Move CleverBot handle to elsewhere.
        # TODO: Added CleverBot instant call.
        # if the message begins with the client nickname and CleverBot Instant is turned on, send the message to
        # to the active session.
        if self.cleverbot_enable:
            if self.cleverbot_instant:
                if self.client_nick in decoded_msg.lower():
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
                    query = decoded_msg.lower().replace(self.client_nick, '')
                    self.console_write(pinylib.COLOR['yellow'], '%s [CleverBot]: %s' % (self.user.nick, query.strip()))
                    threading.Thread(target=self.do_cleverbot, args=(query, True,)).start()
                    return

        # Is this a custom command?
        if decoded_msg.startswith(CONFIG['prefix']):
            # Split the message into parts.
            parts = decoded_msg.split(' ')
            # parts[0] is the command.
            cmd = parts[0].lower().strip()
            # The rest is the command argument.
            cmd_arg = ' '.join(parts[1:]).strip()

            # TODO: Review permission control - focus of permissions changes, miscellaneous grouping?
            # Waive handling messages to normal users if the bot listening is set to False and the user
            # is not owner/super mod/mod/botter.
            # TODO: Maybe use the public_cmds option instead of this?
            if not self.bot_listen:
                if cmd == CONFIG['prefix'] + 'pmme':
                    self.do_pmme()
                else:
                    self.console_write(pinylib.COLOR['bright_red'], '%s:%s [Not handled - sleeping]' %
                                       (self.user.nick, decoded_msg))
                return

            # Super mod commands:
            if self.user.is_super:
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
            if self.user.is_owner or self.user.is_super:
                if cmd == CONFIG['prefix'] + 'kill':
                    self.do_kill()

            # Owner and bot controller commands:
            if self.user.is_owner or self.user.is_super or self.user.has_power:
                if cmd == CONFIG['prefix'] + 'mi':
                    self.do_media_info()

            # Mod and bot controller commands:
            # - Lower-level commands (toggles):
            if self.user.is_owner or self.user.is_super or \
                    self.user.is_mod or self.user.has_power:

                if cmd == CONFIG['prefix'] + 'rs':
                    self.do_room_settings()

                elif cmd == CONFIG['prefix'] + 'sleep':
                    self.do_sleep()

                elif cmd == CONFIG['prefix'] + 'reboot':
                    self.do_reboot()

                # TODO: Change command name and functions.
                elif cmd == CONFIG['prefix'] + 'spam':
                    self.do_text_spam_prevention()

                # TODO: Change command name and functions.
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
                    self.do_newuser_ban()

                elif cmd == CONFIG['prefix'] + 'mute':
                    threading.Thread(target=self.do_mute).start()

                elif cmd == CONFIG['prefix'] + 'p2tnow':
                    self.do_instant_push2talk()

                elif cmd == CONFIG['prefix'] + 'autopm':
                    self.do_auto_pm()

                # elif cmd == CONFIG['prefix'] + 'privateroom':
                #     self.do_private_room()

                # TODO: Add in cleverbot enable toggles.
                elif cmd == CONFIG['prefix'] + 'cleverbot':
                    self.do_cleverbot_state()

                # - Higher-level commands:
                # TODO: Implement database.
                elif cmd == CONFIG['prefix'] + 'botter':
                    threading.Thread(target=self.do_botter, args=(cmd_arg,)).start()

                # TODO: Implement database.
                elif cmd == CONFIG['prefix'] + 'protect':
                    threading.Thread(target=self.do_autoforgive, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'cam':
                    self.do_cam_approve(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'close':
                    self.do_close_broadcast(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'clr':
                    self.do_clear()

                elif cmd == CONFIG['prefix'] + 'nick':
                    self.do_nick(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'topic':
                    self.do_topic(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'topicis':
                    threading.Thread(target=self.do_current_topic).start()

                elif cmd == CONFIG['prefix'] + 'kick':
                    self.do_kick(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'ban':
                    self.do_kick(cmd_arg, True)

                elif cmd == CONFIG['prefix'] + 'forgive':
                    threading.Thread(target=self.do_forgive, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'bn':
                    threading.Thread(target=self.do_bad_nick, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'rmbn':
                    self.do_remove_bad_nick(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'bs':
                    threading.Thread(target=self.do_bad_string, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'rmbs':
                    self.do_remove_bad_string(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'ba':
                    threading.Thread(target=self.do_bad_account, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'rmba':
                    self.do_remove_bad_account(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'list':
                    self.do_list_info(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'uinfo':
                    threading.Thread(target=self.do_user_info, args=(cmd_arg,)).start()

                # Standard media commands:
                elif cmd == CONFIG['prefix'] + 'yt':
                    threading.Thread(target=self.do_play_youtube, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'sc':
                    threading.Thread(target=self.do_play_soundcloud, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'syt':
                    threading.Thread(target=self.do_youtube_search, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'psyt':
                    threading.Thread(target=self.do_play_youtube_search, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'a':
                    threading.Thread(target=self.do_media_request_choice, args=(True,)).start()

                elif cmd == CONFIG['prefix'] + 'd':
                    threading.Thread(target=self.do_media_request_choice, args=(False,)).start()

                # TODO: Media manager now linked to commands and their respective functions.
                # elif cmd == CONFIG['prefix'] + 'pause':
                #     self.do_media_pause()

                # elif cmd == CONFIG['prefix'] + 'resume':
                #     self.do_media_resume()

                # elif cmd == CONFIG['prefix'] + 'seek':
                #     self.do_media_seek(cmd_arg)

                # elif cmd == CONFIG['prefix'] + 'skip':
                #     self.do_media_skip()

                elif cmd == CONFIG['prefix'] + 'replay':
                    self.do_media_replay()

                elif cmd == CONFIG['prefix'] + 'stop':
                    self.do_media_stop()

                # Playlist media commands:
                elif cmd == CONFIG['prefix'] + 'pl':
                    threading.Thread(target=self.do_youtube_playlist_videos, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'plsh':
                    threading.Thread(target=self.do_youtube_playlist_search, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'pladd':
                    threading.Thread(target=self.do_youtube_playlist_search_choice, args=(cmd_arg,)).start()

                # Specific media control commands:
                # TODO: Requires new media handling class.
                # TODO: Issue when replaying, current time point continues and does not reset/becomes zero (this issue
                #       could be persistent in the majority of functions.
                # TODO: Check all of the media_manager module.

                # TODO: API checks.
                elif cmd == CONFIG['prefix'] + 'top40':
                    threading.Thread(target=self.do_charts).start()

                elif cmd == CONFIG['prefix'] + 'top':
                    threading.Thread(target=self.do_lastfm_chart, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'ran':
                    threading.Thread(target=self.do_lastfm_random_tunes, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'tag':
                    threading.Thread(target=self.search_lastfm_by_tag, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'rm':
                    self.do_delete_playlist_item(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'cpl':
                    self.do_clear_playlist()

            # Public commands:
            if self.is_cmds_public or self.user.is_owner or self.user.is_super or \
                    self.user.is_mod or self.user.has_power:

                if cmd == CONFIG['prefix'] + 'v':
                    threading.Thread(target=self.do_version).start()

                elif cmd == CONFIG['prefix'] + 'help':
                    threading.Thread(target=self.do_help).start()

                elif cmd == CONFIG['prefix'] + 'uptime':
                    threading.Thread(target=self.do_uptime).start()

                elif cmd == CONFIG['prefix'] + 'pmme':
                    self.do_pmme()

                elif cmd == CONFIG['prefix'] + 'fs':
                    threading.Thread(target=self.do_full_screen, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'reqyt':
                    threading.Thread(target=self.do_media_request, args=(self.yt_type, cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'reqsc':
                    threading.Thread(target=self.do_media_request, args=(self.sc_type, cmd_arg,)).start()

                # TODO: 'now' command is 'np'.
                elif cmd == CONFIG['prefix'] + 'np':
                    threading.Thread(target=self.do_now_playing).start()

                # TODO: Who plays command.
                elif cmd == CONFIG['prefix'] + 'wp':
                    threading.Thread(target=self.do_who_plays).start()

                elif cmd == CONFIG['prefix'] + 'pls':
                    threading.Thread(target=self.do_playlist_status).start()

                elif cmd == CONFIG['prefix'] + 'next':
                    threading.Thread(target=self.do_next_tune_in_playlist).start()

                # - Private media commands:
                elif cmd == CONFIG['prefix'] + 'ytme':
                    threading.Thread(target=self.do_play_private_media, args=(self.yt_type, cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'scme':
                    threading.Thread(target=self.do_play_private_media, args=(self.sc_type, cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'stopme':
                    threading.Thread(target=self.do_stop_private_media).start()

                elif cmd == CONFIG['prefix'] + 'sync':
                    threading.Thread(target=self.do_sync_media, args=(cmd_arg,)).start()

                # API commands:
                # - Tinychat API commands:
                elif cmd == CONFIG['prefix'] + 'spy':
                    threading.Thread(target=self.do_spy, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'acspy':
                    threading.Thread(target=self.do_account_spy, args=(cmd_arg,)).start()

                # - Other API commands:
                elif cmd == CONFIG['prefix'] + 'urb':
                    threading.Thread(target=self.do_search_urban_dictionary, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'wea':
                    threading.Thread(target=self.do_weather_search, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'ip':
                    threading.Thread(target=self.do_whois_ip, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'm5c':
                    threading.Thread(target=self.do_md5_hash_cracker, args=(cmd_arg,)).start()

                # TODO: Test the module.
                # elif cmd == CONFIG['prefix'] + 'ddg':
                #     threading.Thread(target=self.do_duckduckgo_search, args=(cmd_arg,)).start()

                # TODO: Removed Wikipedia module usage.

                elif cmd == CONFIG['prefix'] + 'imdb':
                    threading.Thread(target=self.do_omdb_search, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'ety':
                    threading.Thread(target=self.do_etymonline_search, args=(cmd_arg,)).start()

                # Entertainment/alternative media commands:
                elif cmd == CONFIG['prefix'] + 'cb':
                    threading.Thread(target=self.do_cleverbot, args=(cmd_arg,)).start()

                elif cmd == CONFIG['prefix'] + 'cn':
                    threading.Thread(target=self.do_chuck_norris).start()

                elif cmd == CONFIG['prefix'] + '8ball':
                    self.do_8ball(cmd_arg)

                elif cmd == CONFIG['prefix'] + 'yomama':
                    threading.Thread(target=self.do_yo_mama_joke).start()

                elif cmd == CONFIG['prefix'] + 'advice':
                    threading.Thread(target=self.do_advice).start()

                elif cmd == CONFIG['prefix'] + 'joke':
                    threading.Thread(target=self.do_one_liner, args=(cmd_arg,)).start()

                # TODO: Place these two function into one and provide variable to determine the use of one.
                # elif cmd == CONFIG['prefix'] + 'time':
                #     threading.Thread(target=self.do_time, args=(cmd_arg, False, False,)).start()

                # elif cmd == CONFIG['prefix'] + 'time+':
                #     threading.Thread(target=self.do_time, args=(cmd_arg, True, False,)).start()

                # TODO: Allow 'non-military' time conversion (24 hr --> 12 hr with AM/PM) via argument(?)
                # elif cmd == CONFIG['prefix'] + 'time12':
                #     threading.Thread(target=self.do_time, args=(cmd_arg, True, True,)).start()

                else:
                    # TODO: This code is not tidy, tidy it up - it is in the incorrect place (if the requested command
                    #       is in another branch then it might request this if the user does not have privileges.
                    # Main call to check if the command is an ASCII command.
                    if self.ascii_chars:
                        ascii_result = self.do_ascii(cmd)
                        if ascii_result:
                            return

            # Print command to console.
            self.console_write(pinylib.COLOR['yellow'], msg_sender + ': ' + cmd + ' ' + cmd_arg)
        else:
            # Print chat message to console.
            # if self._nickname_color == 'default':
            #     self.console_write(pinylib.COLOR['green'], self.user.nick + ': ' + decoded_msg)
            # else:
            #     self.console_write(pinylib.COLOR['white'], self.user.nick + ': ' + decoded_msg)

            self.console_write(pinylib.COLOR['green'], self.user.nick + ': ' + decoded_msg)

        # Add msg to user object last_msg attribute.
        self.user.last_msg = decoded_msg

    # TODO: Removed the usage of 'is_client_mod'/'_is_client_mod' to just the message we want to send.
    # TODO: Look at who has permission to access each function.

    # == Super Mod Commands Methods. ==
    def do_make_mod(self, account):
        """
        Make a Tinychat account a room moderator.
        :param account: str the account to make a moderator.
        """
        if self._is_client_owner:
            if self.user.is_super:
                if len(account) is 0:
                    self.send_bot_msg('*Missing account name.*')
                else:
                    tc_user = self.privacy_settings.make_moderator(account)
                    if tc_user is None:
                        self.send_bot_msg('*The account is invalid.*')
                    elif not tc_user:
                        self.send_bot_msg('*The account is already a moderator.*')
                    elif tc_user:
                        self.send_bot_msg('*' + account + ' was made a room moderator.*')

    def do_remove_mod(self, account):
        """
        Removes a Tinychat account from the moderator list.
        :param account: str the account to remove from the moderator list.
        """
        if self._is_client_owner:
            if self.user.is_super:
                if len(account) is 0:
                    self.send_bot_msg('*Missing account name.*')
                else:
                    tc_user = self.privacy_settings.remove_moderator(account)
                    if tc_user:
                        self.send_bot_msg('*' + account + ' is no longer a room moderator.*')
                    elif not tc_user:
                        self.send_bot_msg('*' + account + ' is not a room moderator.*')

    def do_directory(self):
        """ Toggles if the room should be shown on the directory. """
        if self._is_client_owner:
            if self.privacy_settings.show_on_directory():
                self.send_bot_msg('*Room IS shown on the directory.*')
            else:
                self.send_bot_msg('*Room is NOT shown on the directory.*')

    def do_push2talk(self):
        """ Toggles if the room should be in push2talk mode. """
        if self._is_client_owner:
            if self.privacy_settings.set_push2talk():
                self.send_bot_msg('Push2Talk is *enabled*.')
            else:
                self.send_bot_msg('Push2Talk is *disabled*.')

    def do_green_room(self):
        """ Toggles if the room should be in greenroom mode. """
        if self._is_client_owner:
            if self.privacy_settings.set_greenroom():
                self.send_bot_msg('Green room is *enabled*.')
                self._greenroom = True
            else:
                self.send_bot_msg('Green room is *disabled*.')
                self._greenroom = False

    def do_clear_room_bans(self):
        """ Clear all room bans. """
        if self._is_client_owner:
            if self.privacy_settings.clear_bans():
                self.send_bot_msg('*All room bans was cleared.*')

    # == Owner And Super Mod Command Methods. ==
    def do_kill(self):
        """ Kills the bot. """
        self.disconnect()
        # TODO: We want the whole program to exit, not hang.
        # Exit normally.
        sys.exit(0)

    # == Owner And Mod Command Methods. ==
    def do_reboot(self):
        """ Reboots the bot. """
        self.reconnect()

    # == Owner/ Super Mod/ Mod/ Power users Command Methods. ==
    def do_media_info(self):
        """ Shows basic media info. """
        if self._is_client_mod:
            self.send_owner_run_msg('*Track List Index:* ' + str(self.media_manager.track_list_index))
            self.send_owner_run_msg('*Playlist Length*: ' + str(len(self.media_manager.track_list)))
            self.send_owner_run_msg('*Current Time Point:* ' +
                                    self.format_time(self.media_manager.elapsed_track_time()))
            self.send_owner_run_msg('*Active Threads:* ' + str(threading.active_count()))
            self.send_owner_run_msg('*Is Mod Playing:* ' + str(self.media_manager.is_mod_playing))

    def do_room_settings(self):
        """ Shows current room settings. """
        if self._is_client_owner:
            settings = self.privacy_settings.current_settings()
            # Send the broadcast and room passwords as am undercover message to the room owner.
            self.send_undercover_msg(self.user.nick, '*Broadcast Password:* ' + settings['broadcast_pass'])
            self.send_owner_run_msg('*Room Password:* ' + settings['room_pass'])
            self.send_owner_run_msg('*Login Type:* ' + settings['allow_guests'])
            self.send_owner_run_msg('*Directory:* ' + settings['show_on_directory'])
            self.send_owner_run_msg('*Push2Talk:* ' + settings['push2talk'])
            self.send_owner_run_msg('*Greenroom:* ' + settings['greenroom'])

    # TODO: Possible sleep mode/night/inactive/low-power mode; allow hibernation activities/features.
    def do_sleep(self):
        """ Sets the bot to sleep so commands from everyone will be ignored until it is woken up by a PM. """
        self.bot_listen = False
        self.send_bot_msg('*Bot listening set to*: %s' % self.bot_listen)

    def do_text_spam_prevention(self):
        """ Toggles spam prevention """
        self.spam_prevention = not self.spam_prevention
        self.send_bot_msg('*Text Spam Prevention*: %s' % self.spam_prevention)

    def do_snapshot(self):
        """ Toggles 'snapshot' prevention. """
        self.snapshot_spam = not self.snapshot_spam
        self.send_bot_msg('*Snapshot Prevention*: %s' % self.snapshot_spam)

    def do_autoclose(self):
        """ Toggles autoclose. """
        self.auto_close = not self.auto_close
        self.send_bot_msg('*Auto closing mobiles/guests/newusers*: %s' % self.auto_close)

    def do_ban_mobiles(self):
        """ Toggles ban on all recognised, broadcasting mobile devices. """
        self.ban_mobiles = not self.ban_mobiles
        self.send_bot_msg('*Banning mobile users on cam*: %s' % self.ban_mobiles)

    def do_auto_url_mode(self):
        """ Toggles auto url mode. """
        self.auto_url_mode = not self.auto_url_mode
        self.send_bot_msg('*Auto-Url Mode*: %s' % self.auto_url_mode)

    # TODO: Media timer issue when adding songs to the playlist after turning it off and turning it on;
    #       instantly played media stops after a while.
    def do_playlist_mode(self):
        """ Toggles playlist mode. """
        self.playlist_mode = not self.playlist_mode
        self.send_bot_msg('*Playlist Mode*: %s' % self.playlist_mode)

    def do_public_media(self):
        """
        Toggles public media mode which allows the public to add media to the playlist or play media.
        NOTE: Playlist mode will be automatically enforced when public media is turned on. This is to prevent the
              spamming of media plays in the room. Playlist mode will have to be turned off manually if it is not
              going to be used if public media is going to be disabled.
        """
        self.public_media = not self.public_media
        if self.public_media:
            self.playlist_mode = True
        self.send_bot_msg('*Public Media Mode*: %s' % self.public_media)

    def do_guest_nick_ban(self):
        """ Toggles guest nickname banning. """
        self.is_guest_nicks_allowed = not self.is_guest_nicks_allowed
        self.send_bot_msg('*"guests-" allowed*: %s' % self.is_guest_nicks_allowed)

    def do_newuser_ban(self):
        """ Toggles new user banning. """
        self.is_newusers_allowed = not self.is_newusers_allowed
        self.send_bot_msg('*"newuser"\'s allowed*: %s' % self.is_newusers_allowed)

    def do_camblock(self, on_block):
        """
        Adds a user to the cam-blocked list to prevent them from broadcasting temporarily.
        :param: on_block: str the nick name of the user who may or may not be in the blocked list.
        """
        if len(on_block) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please state a user to cam block.')
        else:
            user = self.find_user_info(on_block)
            if user is not None:
                if user.nick not in self.cam_blocked:
                    self.cam_blocked.append(user.nick)
                    self.send_close_user_msg(user.nick)
                    self.send_bot_msg(unicode_catalog.TICK_MARK + ' *' + unicode_catalog.NO_WIDTH +
                                      user.nick + unicode_catalog.NO_WIDTH + '* is now cam blocked.')
                else:
                    self.cam_blocked.remove(user.nick)
                    self.send_bot_msg(unicode_catalog.CROSS_MARK + ' *' + unicode_catalog.NO_WIDTH +
                                      user.nick + unicode_catalog.NO_WIDTH + '* is no longer cam blocked.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' The user you stated does not exist.')

    def do_mute(self):
        """ Sends a room mute microphone message to all broadcasting users. """
        self.send_mute_msg()

    def do_instant_push2talk(self):
        """ Sets microphones broadcasts to 'push2talk'. """
        self.send_push2talk_msg()

    def do_auto_pm(self):
        """ Toggles on the automatic room private message. """
        if len(self.pm_msg) is not 0:
            self.auto_pm = not self.auto_pm
            self.send_bot_msg('*Auto-P.M.*: %s' % self.auto_pm)
        else:
            self.send_bot_msg('There is *no private message set* in the configuration file.')

    # TODO: Do we need this function?
    # def do_private_room(self):
    #     """" Sets room to private room. """
    #     if self._is_client_mod:
    #         self.send_private_room_msg()
    #         self.private_room = not self.private_room
    #         self.send_bot_msg('*Private Room* is now set to: %s' % self.private_room)
    #     else:
    #         self.send_bot_msg('Command not enabled.')

    def do_cleverbot_state(self):
        """ Sets CleverBot to function in the room (as an instant call or via command). """
        self.cleverbot_enable = not self.cleverbot_enable
        self.send_bot_msg('*CleverBot enabled*: %s' % self.cleverbot_enable)

    # TODO: Implement database.
    # TODO: Levels of botters - maybe just media users.
    def do_botter(self, new_botter):
        """
        Adds a new botter to allow control over the bot and appends the user to the list
        of botters, and IF they are signed, in to the botter accounts list and save their
        account to file as well.
        :param new_botter: str the nick name of the user to bot.
        """
        if len(new_botter) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please state a nickname to bot.')
        else:
            bot_user = self.find_user_info(new_botter)
            if bot_user is not None:
                if not bot_user.is_owner or not bot_user.is_mod:
                    # Adding new botters.
                    if bot_user.account and bot_user.account not in self.botteraccounts:
                        self.botteraccounts.append(bot_user.account)
                        writer = pinylib.fh.file_writer(CONFIG['path'], CONFIG['botteraccounts'], bot_user.account)
                        if writer:
                            bot_user.has_power = True
                            self.send_bot_msg(unicode_catalog.BLACK_STAR + ' *%s* was added as a verified botter.' %
                                              new_botter)

                    elif not bot_user.account and bot_user.nick not in self.botters:
                        self.botters.append(bot_user.nick)
                        bot_user.has_power = True
                        self.send_bot_msg(unicode_catalog.BLACK_STAR + ' *%s* was added as a temporary botter.' %
                                          new_botter)

                    else:
                        # Removing existing botters or verified botters.
                        remove = False

                        if bot_user.account:
                            for x in range(len(self.botteraccounts)):
                                if self.botteraccounts[x] == bot_user.account:
                                    del self.botteraccounts[x]
                                    remove = pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['botteraccounts'],
                                                                         bot_user.account)
                                    break
                        else:
                            for x in range(len(self.botters)):
                                if self.botters[x] == bot_user.nick:
                                    del self.botters[x]
                                    remove = True
                                    break

                        if remove:
                            bot_user.has_power = False
                            self.send_bot_msg(unicode_catalog.WHITE_STAR + ' *' + new_botter +
                                              '* was removed from botting.')
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' This user already has privileges. No need to bot.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: ' + new_botter)

    # TODO: Implement database.
    def do_autoforgive(self, new_autoforgive):
        """
        Adds a new autoforgive user, IF the user is logged in, to the autoforgive file;
        all users in this file be automatically forgiven if they are banned.
        :param new_autoforgive: str the nick name of the user to add to autoforgive.
        """
        if len(new_autoforgive) is not 0:
            autoforgive_user = self.find_user_info(new_autoforgive)
            if autoforgive_user is not None:
                if autoforgive_user.account and autoforgive_user.account not in self.autoforgive:
                    self.autoforgive.append(autoforgive_user.account)
                    self.send_bot_msg(unicode_catalog.BLACK_HEART + ' *' + unicode_catalog.NO_WIDTH + new_autoforgive +
                                      unicode_catalog.NO_WIDTH + '*' + ' is now protected.')
                    pinylib.fh.file_writer(CONFIG['path'], CONFIG['autoforgive'], autoforgive_user.account)
                elif not autoforgive_user.account:
                    self.send_bot_msg(unicode_catalog.INDICATE +
                                      ' Protection is only available to users with accounts.')
                else:
                    for x in range(len(self.autoforgive)):
                        if self.autoforgive[x] == autoforgive_user.account:
                            del self.autoforgive[x]
                            pinylib.fh.remove_from_file(CONFIG['path'], CONFIG['autoforgive'],
                                                        autoforgive_user.account)
                            self.send_bot_msg(unicode_catalog.WHITE_HEART + ' *' + unicode_catalog.NO_WIDTH +
                                              new_autoforgive + unicode_catalog.NO_WIDTH + '* is no longer protected.')
                            break
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: ' + new_autoforgive)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please state a nickname to protect.')

    def do_cam_approve(self, nick_name):
        """ Send a cam approve message to a user. """
        if self._is_client_mod:
            if self._b_password is None:
                conf = pinylib.tinychat.get_roomconfig_xml(self._roomname, self.room_pass, proxy=self._proxy)
                self._b_password = conf['bpassword']
                self._greenroom = conf['greenroom']
            if self._greenroom:
                if len(nick_name) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname to approve.')
                else:
                    user = self.find_user_info(nick_name)
                    if user is not None:
                        self.send_cam_approve_msg(user.id, user.nick)
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No nickname called: %s' % nick_name)

    def do_close_broadcast(self, nick_name):
        """
        Close a user broadcasting.
        :param nick_name: str the nickname to close.
        """
        if self._is_client_mod:
            if len(nick_name) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname.')
            else:
                user = self.find_user_info(nick_name)
                if user is not None:
                    self.send_close_user_msg(nick_name)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No nickname called: %s' % nick_name)

    # TODO: Updated _send_command to follow calls.
    def do_clear(self):
        """ Clears the chat-box. """
        if self._is_client_mod:
            for x in range(0, 29):
                self.send_owner_run_msg(' ')
        else:
            clear = '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133' \
                    '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133'
            # self._send_command('privmsg', [clear, u'#262626,en'])
            self.connection.call('privmsg', [clear, u'#262626,en'])

        self.send_bot_msg(unicode_catalog.STATE + ' *The chat was cleared by ' + str(self.user.nick) + '*')

    def do_nick(self, new_nick):
        """
        Set a new nick for the bot.
        :param new_nick: str the new nick.
        """
        if len(new_nick) is 0:
            self.client_nick = string_utili.create_random_string(5, 25)
            self.set_nick()
        else:
            if re.match('^[][{}a-zA-Z0-9_]{1,25}$', new_nick):
                self.client_nick = new_nick
                self.set_nick()

    def do_topic(self, topic):
        """
        Sets the room topic.
        :param topic: str the new topic.
        """
        if self._is_client_mod:
            if len(topic) is 0:
                self.send_topic_msg('')
                self.send_bot_msg('Topic was *cleared*.')
            else:
                self.send_topic_msg(topic)
                self.send_bot_msg(unicode_catalog.STATE + ' The *room topic* was set to: ' + topic)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_current_topic(self):
        """ Replies to the user what the current room topic is. """
        self.send_undercover_msg(self.user.nick, 'The *current topic* is: %s' % self._topic_msg)

    # TODO: Tidy up this function.
    def do_kick(self, nick_name, ban=False, discrete=False):
        """
        Kick/ban a user out of the room.
        :param nick_name: str the nickname to kick or ban.
        :param ban: boolean True/False respectively if the user should be banned or not.
        :param discrete: boolean True/False respectively if the user to kick/ban should not produce any further
                         notices from the bot.
        """
        if self._is_client_mod:
            if len(nick_name) is 0:
                if not discrete:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname.')
            elif nick_name == self.client_nick:
                if not discrete:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Action not allowed.')
            else:
                user = self.find_user_info(nick_name)
                if user is not None:
                    if user.is_owner or user.is_super or user.is_mod and not self.user.is_owner:
                        if not discrete:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' You cannot kick/ban a user with privileges.')
                        return

                    if not self.user.is_owner or not self.user.is_super or not self.user.is_mod:
                        if user.nick in self.botters:
                            if not discrete:
                                self.send_bot_msg(unicode_catalog.INDICATE + ' You cannot kick/ban another botter.')
                            return
                        elif user.account:
                            # TODO: Relate botteraccounts to database.
                            if user.account in self.botteraccounts:
                                if not discrete:
                                    self.send_bot_msg(unicode_catalog.INDICATE +
                                                      ' You cannot kick/ban another verified botter.')
                                return

                    self.send_ban_msg(user.nick, user.id)
                    if not ban:
                        self.send_forgive_msg(user.id)

                else:
                    if not discrete:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: *' + unicode_catalog.NO_WIDTH +
                                          nick_name + unicode_catalog.NO_WIDTH + '*')
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
        if self.user.is_owner or self.user.is_super or self.user.is_mod or self.user.has_power:
            if len(self._room_banlist) > 0:
                if len(nick_name) is not 0:
                    if nick_name in self._room_banlist:
                        uid = self._room_banlist[nick_name]
                        self.send_forgive_msg(str(uid))
                        self.send_bot_msg('*' + unicode_catalog.NO_WIDTH + nick_name + unicode_catalog.NO_WIDTH +
                                          '* has been forgiven.')
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' The user was not found in the banlist.')
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please state a nick to forgive from the ban list.')
            else:
                self.send_bot_msg('The *banlist is empty*. No one to forgive.')

    def do_forgive_all(self):
        """ Forgive all the user in the ban-list. """
        if self.user.is_owner or self.user.is_super or self.user.is_mod or self.user.has_power:
            if not self.forgive_all:
                self.send_undercover_msg(self.user.nick, 'Now *forgiving all* users in the banlist...')
                self.forgive_all = True
                for user_id in self._room_banlist.values():
                    self.send_forgive_msg(str(user_id))
                    pinylib.time.sleep(1)
                self.forgive_all = False
            else:
                self.send_bot_msg('We have not finished forgiving everyone in the ban-list. Please try again later..')

    def do_bad_nick(self, bad_nick):
        """
        Adds a bad nickname to the bad nicks file.
        :param bad_nick: str the bad nick to write to the file.
        """
        if self._is_client_mod:
            if len(bad_nick) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname.')
            else:
                # TODO: Performance tweaks.
                badnicks = pinylib.fh.file_reader(self.config_path(), CONFIG['nick_bans'])
                if badnicks is None:
                    pinylib.fh.file_writer(self.config_path(), CONFIG['nick_bans'], bad_nick)
                else:
                    if bad_nick in badnicks:
                        self.send_bot_msg(bad_nick + ' is already in the list.')
                    else:
                        pinylib.fh.file_writer(self.config_path(), CONFIG['nick_bans'], bad_nick)
                        # TODO: States type of file the name was added to.
                        self.send_bot_msg('*' + bad_nick + '* was added to *nick bans*.')
                        # Ban the nickname if it is present in the room.
                        if bad_nick in self._room_users.keys():
                            bn_user = self.find_user_info(bad_nick)
                            threading.Thread(target=self.send_ban_msg, args=(bn_user.nick, bn_user.id,)).start()

    def do_remove_bad_nick(self, bad_nick):
        """
        Removes a bad nick from bad nicks file.
        :param bad_nick: str the bad nick to remove from the file.
        """
        if self._is_client_mod:
            if len(bad_nick) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname.')
            else:
                # TODO: Performance tweaks.
                rem = pinylib.fh.remove_from_file(self.config_path(), CONFIG['nick_bans'], bad_nick)
                if rem:
                    self.send_bot_msg(bad_nick + ' was removed.')

    def do_bad_string(self, bad_string):
        """
        Adds a bad string to the bad strings file.
        :param bad_string: str the bad string to add to the file.
        """
        if self._is_client_mod:
            if len(bad_string) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Bad string can\'t be blank.')
            elif len(bad_string) < 3:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Bad string too short: ' + str(len(bad_string)))
            else:
                # TODO: Performance tweaks.
                bad_strings = pinylib.fh.file_reader(self.config_path(), CONFIG[''])
                if bad_strings is None:
                    # TODO: Need output information here.
                    pinylib.fh.file_writer(self.config_path(), CONFIG['ban_strings'], bad_string)
                else:
                    if bad_string in bad_strings:
                        self.send_bot_msg(bad_string + ' is already in the list.')
                    else:
                        pinylib.fh.file_writer(self.config_path(), CONFIG['ban_strings'], bad_string)
                        self.send_bot_msg('*' + bad_string + '* was added to *ban strings*.')

    def do_remove_bad_string(self, bad_string):
        """
        Removes a bad string from the bad strings file.
        :param bad_string: str the bad string to remove from the file.
        """
        if self._is_client_mod:
            if len(bad_string) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing word string.')
            else:
                rem = pinylib.fh.remove_from_file(self.config_path(), CONFIG['ban_strings'], bad_string)
                if rem:
                    self.send_bot_msg(bad_string + ' was removed.')

    def do_bad_account(self, bad_account_name):
        """
        Adds a bad account name to the bad accounts file.
        :param bad_account_name: str the bad account name to the file.
        """
        if self._is_client_mod:
            if len(bad_account_name) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Account can\'t be blank.')
            # TODO: Account names can be shorter than 3 characters.
            # elif len(bad_account_name) < 3:
            #     self.send_bot_msg(unicode_catalog.INDICATE + ' Account name too short: ' +
            #                       str(len(bad_account_name)))
            else:
                bad_accounts = pinylib.fh.file_reader(self.config_path(), CONFIG['account_bans'])
                if bad_accounts is None:
                    # TODO: Need output information here.
                    pinylib.fh.file_writer(self.config_path(), CONFIG['account_bans'], bad_account_name)
                else:
                    if bad_account_name in bad_accounts:
                        self.send_bot_msg(bad_account_name + ' is already in list.')
                    else:
                        pinylib.fh.file_writer(self.config_path(), CONFIG['account_bans'], bad_account_name)
                        self.send_bot_msg('*' + bad_account_name + '* was added to *account bans*.')
                        # Bans the account name if the account is currently in the room.
                        for nickname in self._room_users.keys():
                            user = self.find_user_info(nickname)
                            if user.account == bad_account_name:
                                threading.Thread(target=self.send_ban_msg, args=(user.nick, user.id,)).start()
                                break

    def do_remove_bad_account(self, bad_account):
        """
        Removes a bad account from the bad accounts file.
        :param bad_account: str the bad account name to remove from the file.
        """
        if self._is_client_mod:
            if len(bad_account) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing account.')
            else:
                rem = pinylib.fh.remove_from_file(self.config_path(), CONFIG['account_bans'], bad_account)
                if rem:
                    self.send_bot_msg(bad_account + ' was removed.')

    def do_list_info(self, list_type):
        """
        Shows info. of different lists/files.
        :param list_type: str the type of list to find info for.
        """
        if self._is_client_mod:
            if len(list_type) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing list type.')
            else:
                # TODO: Specify type of list on the 'no items' response.
                if list_type.lower() == 'bn':
                    bad_nicks = pinylib.fh.file_reader(self.config_path(), CONFIG['nick_bans'])
                    if bad_nicks is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in the ban nicks list.')
                    else:
                        self.send_bot_msg(str(len(bad_nicks)) + ' bad nicks in list.')

                elif list_type.lower() == 'bs':
                    bad_strings = pinylib.fh.file_reader(self.config_path(), CONFIG['ban_strings'])
                    if bad_strings is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in the ban strings list.')
                    else:
                        self.send_bot_msg(str(len(bad_strings)) + ' bad strings in list.')

                elif list_type.lower() == 'ba':
                    bad_accounts = pinylib.fh.file_reader(self.config_path(), CONFIG['account_bans'])
                    if bad_accounts is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in the bad accounts list.')
                    else:
                        self.send_bot_msg(str(len(bad_accounts)) + ' bad accounts in list.')

                elif list_type.lower() == 'pl':
                    if len(self.media_manager.track_list) > 0:
                        tracks = self.media_manager.get_track_list()
                        if tracks is not None:
                            i = 0
                            for pos, track in tracks:
                                if i == 0:
                                    self.send_owner_run_msg('(%s) *Next track: %s* %s' %
                                                            (pos, track.title, self.format_time(track.time)))
                                else:
                                    self.send_owner_run_msg('(%s) *%s* %s' %
                                                            (pos, track.title, self.format_time(track.time)))
                                i += 1
                    else:
                        self.send_owner_run_msg(unicode_catalog.INDICATE + ' No items in the playlist.')

                elif list_type.lower() == 'mods':
                    if self._is_client_owner and self.user.is_super:
                        if len(self.privacy_settings.room_moderators) is 0:
                            self.send_bot_msg('*There are currently no moderators for this room.*')
                        elif len(self.privacy_settings.room_moderators) is not 0:
                            mods = ', '.join(self.privacy_settings.room_moderators)
                            self.send_bot_msg('*Moderators:* ' + mods)

    def do_user_info(self, nick_name):
        """
        Shows user object info. for a given nick name.
        :param nick_name: str the nick name of the user to show the information for.
        """
        if self._is_client_mod:
            if len(nick_name) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing nickname.')
            else:
                user = self.find_user_info(nick_name)
                if user is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: ' + nick_name)
                else:
                    if user.account and user.tinychat_id is None:
                        user_info = pinylib.tinychat.tinychat_user_info(user.account)
                        if user_info is not None:
                            user.tinychat_id = user_info['tinychat_id']
                            user.last_login = user_info['last_active']
                    self.send_owner_run_msg('*ID:* %s' % user.id)
                    self.send_owner_run_msg('*Owner:* %s' % user.is_owner)
                    # self.send_owner_run_msg('*Is Mod:* %s' % user.is_mod)
                    self.send_owner_run_msg('*Device Type:* %s' % user.btype)
                    self.send_owner_run_msg('*User Account Type:* %s' % str(user.stype))
                    self.send_owner_run_msg('*User Account Gift Points:* %d' % user.gp)
                    # TODO: Change attribute name.
                    if not user.is_owner and not user.is_mod:
                        if user.nick or user.account in self.botters or self.botteraccounts:
                            self.send_owner_run_msg('*Sudo:* %s' % user.is_super)
                            self.send_owner_run_msg('*Bot Controller:* %s' % user.has_power)
                    # TODO: Change attribute names.
                    self.send_undercover_msg(self.user.nick, '*Account:* ' + str(user.account))
                    self.send_undercover_msg(self.user.nick, '*Tinychat ID:* ' + user.tinychat_id)
                    self.send_undercover_msg(self.user.nick, '*Last login:* ' + user.last_login)
                    self.send_owner_run_msg('*Last message:* ' + str(user.last_msg))

                    # TODO: Overall speed enhancement when playing youtube videos.

    # TODO: Added public media and playlist mode.
    # TODO: Removed do_play_media - was extremely long and prone to errors.
    # TODO: Allow multiple videos to be added to the playlist (if playlist mode is enabled).
    # TODO: Separated to do_play_youtube again for ease of editing - quite a long function.
    def do_play_youtube(self, search):
        """
        Plays a YouTube video matching the search term.
        :param search:
        """
        log.info('User: %s:%s is searching youtube: %s' % (self.user.nick, self.user.id, search))
        if self._is_client_mod:

            # TODO: Place public media handling in the appropriate place.
            # if self.public_media:

            if len(search) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify *YouTube title, id or link*.')
            else:
                # TODO: Make searches more accurate - direct video id search instead or URL search.
                # Try checking the search term to see if matches our URL regex pattern. If so,
                # we can extract the video id from the URL.
                match_url = self.youtube_pattern.match(search)
                # print('Match URL:', match_url)
                if match_url is not None:
                    video_id = match_url.group(1)
                    _media = youtube.youtube_time(video_id)
                else:
                    _media = youtube.youtube_search(search)

                if _media is None:
                    log.warning('Media search returned: %s' % _media)
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find media: ' + search)
                else:
                    # TODO: If the playlist was '!stop' then it will not show the media as having been added since
                    #       the media timer thread is not alive if the media was paused.
                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive() \
                            and self.playlist_mode:
                        self.media_manager.add_track(self.user.nick, _media)
                        self.send_bot_msg(unicode_catalog.PENCIL + ' ' + unicode_catalog.MUSICAL_NOTE + ' *' +
                                          str(_media['video_title']) + ' ' + unicode_catalog.MUSICAL_NOTE +
                                          ' at #' + str(len(self.media_manager.track_list)) + '*')
                    else:
                        self.media_manager.add_track(self.user.nick, _media)
                        track = self.media_manager.get_next_track()
                        self.send_media_broadcast_start(track.type, track.id)
                        self.media_event_timer(track.time)
        else:
            self.send_bot_msg('Not enabled right now.')

    # TODO: Separated to do_play_soundcloud again for ease of editing - quite a long function.
    def do_play_soundcloud(self, search):
        """
        Plays a SoundCloud track matching the search term.
        :param search:
        """
        log.info('User: %s:%s is searching soundcloud: %s' % (self.user.nick, self.user.id, search))
        if self._is_client_mod:

            # TODO: Place public media handling in the appropriate place.
            # if self.public_media:

            if len(search) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify *SoundCloud title or link*.')
            else:
                _media = soundcloud.soundcloud_search(search)

                if _media is None:
                    log.warning('Media search returned: %s' % _media)
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find media: ' + search)
                else:
                    # TODO: If the playlist was '!stop' then it will not show the media as having been added since
                    #       the media timer thread is not alive if the media was paused.
                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive() \
                            and self.playlist_mode:
                        self.media_manager.add_track(self.user.nick, _media)
                        self.send_bot_msg(unicode_catalog.PENCIL + ' ' + unicode_catalog.MUSICAL_NOTE + ' *' +
                                          str(_media['video_title']) + ' ' + unicode_catalog.MUSICAL_NOTE +
                                          ' at #' + str(len(self.media_manager.track_list)) + '*')
                    else:
                        self.media_manager.add_track(self.user.nick, _media)
                        track = self.media_manager.get_next_track()
                        self.send_media_broadcast_start(track.type, track.id)
                        self.media_event_timer(track.time)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_youtube_search(self, search_str):
        """
        Searches youtube for a given search term, and adds the results to a list.
        :param search_str: str the search term to search for.
        """
        if self._is_client_mod:
            if len(search_str) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing search term.')
            else:
                self.search_list = youtube.youtube_search_list(search_str, results=5)
                if len(self.search_list) is not 0:
                    for i in range(0, len(self.search_list)):
                        v_time = self.format_time(self.search_list[i]['video_time'])
                        v_title = self.search_list[i]['video_title']
                        self.send_owner_run_msg('(%s) *%s* %s' % (i, v_title, v_time))
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find: ' + search_str)

    def do_play_youtube_search(self, int_choice):
        """
        Plays a youtube from the search list.
        :param int_choice: int the index in the search list to play.
        """
        if self._is_client_mod:
            if len(self.search_list) > 0:
                try:
                    index_choice = int(int_choice)
                    if 0 <= index_choice <= 4:
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive()\
                                and self.playlist_mode:
                            track = self.media_manager.add_track(self.user.nick, self.search_list[index_choice])
                            self.send_bot_msg('(' + str(self.media_manager.last_track_index()) + ') Added:*' +
                                              track.title + '* to playlist ' + track.time)
                        else:
                            track = self.media_manager.mb_start(self.user.nick,
                                                                self.search_list[index_choice], mod_play=False)
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Please make a choice between 0-4.')
                except ValueError:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')

                    # TODO: Possibly add tags to show who requested the media as a room message.

    # TODO: Allow multiple media requests?
    def do_media_request_choice(self, request_choice):
        """
        Allows owners/super mods/moderators/botters to accept/decline any temporarily stored media requests.
        :param request_choice: bool True/False if the media request was accepted or declined by the privileged user.
        """
        if self._is_client_mod:
            # TODO: We could integrate media requests into the media manager.
            if self.media_request is not None:
                if request_choice is True:
                    # TODO: Media requests do not get added to the playlist.
                    if self.media_timer_thread is not None and self.media_timer_thread.is_alive() \
                            and self.playlist_mode:
                        # TODO: This will state whoever accepted the request, not who requested it.
                        self.media_manager.add_track(self.user.nick, self.media_request)
                        self.media_manager.get_next_track().was_request = True
                        self.send_bot_msg(unicode_catalog.ARROW_STREAK +
                                          ' The media request was *accepted*. Added media to the playlist.')
                    else:
                        self.media_manager.add_track(self.user.nick, self.media_request)
                        requested_track = self.media_manager.get_next_track()
                        requested_track.was_request = True
                        self.send_media_broadcast_start(requested_track.type, requested_track.id)
                        self.media_event_timer(requested_track.pause_time)
                        self.send_bot_msg(unicode_catalog.ARROW_SIDEWAYS +
                                          ' This was a *media request* submitted by %s.' % requested_track.nick)
                    self.media_request = None
                else:
                    self.send_bot_msg(unicode_catalog.ITALIC_CROSS +
                                      ' The media request was *declined*. New media requests can be made.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *No pending media request* to review.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_media_pause(self):
        """ Pause the media playing. """
        track = self.media_manager.track()
        if track is not None:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                self.cancel_media_event_timer()
            self.media_manager.mb_pause()
            self.send_media_broadcast_pause(track.type)

    def do_media_resume(self):
        """ Resumes a track in pause mode. """
        track = self.media_manager.track()
        if track is not None:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                self.cancel_media_event_timer()
            if self.media_manager.is_paused:
                ntp = self.media_manager.mb_play(self.media_manager.elapsed_track_time())
                self.send_media_broadcast_play(track.type, self.media_manager.elapsed_track_time())
                self.media_event_timer(ntp)

    # TODO: Seeking when paused sets the time point incorrectly, however sends the request correctly.
    # TODO: Need an error statement if there is no seek times present.
    def do_media_seek(self, time_point):
        """
        Seek on a media broadcast playing.
        :param time_point: str the time point to skip to.
        """
        if ('h' in time_point) or ('m' in time_point) or ('s' in time_point):
            mls = string_utili.convert_to_millisecond(time_point)
            if mls is 0:
                self.console_write(pinylib.COLOR['bright_red'], 'Invalid seek time: %s.' % time_point)
            else:
                track = self.media_manager.track()
                if track is not None:
                    if 0 < mls < track.time:
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.cancel_media_event_timer()
                        new_media_time = self.media_manager.mb_skip(mls)
                        if not self.media_manager.is_paused:
                            self.media_event_timer(new_media_time)
                        self.send_media_broadcast_skip(track.type, mls)

    # TODO: Issue.
    def do_media_skip(self):
        """ Play the next item in the playlist. """
        if self.media_manager.is_last_track():
            self.send_bot_msg(unicode_catalog.INDICATE + ' This is the *last tune* in the playlist.')
        elif self.media_manager.is_last_track() is None:
            self.send_bot_msg(unicode_catalog.INDICATE + ' *No tunes to skip. The playlist is empty.*')
        else:
            # TODO: Handle the event in which the media we are skipping to is not of the same type.
            #       This is to ensure the previous media type stops playing.
            # next_track = self.media_manager.get_next_track()
            # TODO: Replace get_next_track with next_track_info so we can get the next track information.
            pos, next_track = self.media_manager.next_track_info()
            print(pos, next_track.type, self.media_manager.track().type)
            self.cancel_media_event_timer()

            if next_track.type != self.media_manager.track().type:
                print('stopping track of different type')
                self.media_manager.mb_close()
                self.send_media_broadcast_close(self.media_manager.track().type)

            self.media_manager.we_play(next_track)
            print('sending broadcast start')
            self.send_media_broadcast_start(next_track.type, next_track.id)
            self.media_event_timer(next_track.time)

    def do_media_replay(self):
        """ Replays the last played media. """
        if self.media_manager.track() is not None:
            self.cancel_media_event_timer()
            self.media_manager.we_play(self.media_manager.track())
            self.send_media_broadcast_start(self.media_manager.track().type, self.media_manager.track().id)
            self.media_event_timer(self.media_manager.track().time)

    # TODO: if two media broadcasts are playing, only the most recent is monitored and closed.
    def do_media_stop(self):
        """ Closes the active media broadcast. """
        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
            self.cancel_media_event_timer()
        self.media_manager.mb_close()
        self.send_media_broadcast_close(self.media_manager.track().type)

    def do_youtube_playlist_videos(self, playlist):
        """
        Retrieves and adds video IDs of songs from a playlist.
        Add all the videos from the given playlist.
        :param: playlist: str the playlist or playlist ID.
        """
        if self._is_client_mod:
            if self.playlist_mode:
                if len(playlist) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a playlist url or playlist ID.')
                else:
                    # TODO: Make this more efficient.
                    # Get only the playlist ID from the provided link.
                    playlist_id = ''
                    if '=' in playlist:
                        location_equal = playlist.index('=')
                        playlist_id = playlist[location_equal + 1:len(playlist)]
                    else:
                        if 'http' or 'www' or 'youtube' not in playlist:
                            playlist_id = playlist

                    self.send_bot_msg(unicode_catalog.STATE +
                                      ' *Just a minute* while we fetch the videos in the playlist...')

                    video_list, non_public = youtube.youtube_playlist_all_videos(playlist_id)
                    if len(video_list) is 0:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No videos in playlist or none were found.')
                    else:
                        if non_public > 0:
                            playlist_message = unicode_catalog.PENCIL + ' Added *' + str(len(video_list)) +\
                                               ' videos* to the playlist. ' + 'There were *' + \
                                               unicode_catalog.NO_WIDTH + str(non_public) + \
                                               unicode_catalog.NO_WIDTH + '* non-public videos.'
                        else:
                            playlist_message = unicode_catalog.PENCIL + ' Added *' + str(len(video_list)) +\
                                               ' videos* to the playlist.'

                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.media_manager.add_track_list(self.user.nick, video_list)
                            self.send_bot_msg(playlist_message)
                        else:
                            self.media_manager.add_track_list(self.user.nick, video_list)
                            track = self.media_manager.get_next_track()
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
                            self.send_bot_msg(playlist_message)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')

    def do_youtube_playlist_search(self, playlist_search):
        """
        Retrieves search results for a youtube playlist search.
        :param playlist_search: str the name of the playlist you want to search.
        """
        log.info('User %s:%s is searching a YouTube playlist: %s' % (self.user.nick, self.user.id, playlist_search))
        if self._is_client_mod:
            if self.playlist_mode:
                if len(playlist_search) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a playlist search query.')
                else:
                    self.search_play_lists = youtube.youtube_playlist_search(playlist_search, results=4)
                    if self.search_play_lists is None:
                        log.warning('The search returned an error.')
                        self.send_bot_msg(unicode_catalog.INDICATE +
                                          ' There was an error while fetching the results.')
                    elif len(self.search_play_lists) is 0:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' The search returned no results.')
                    else:
                        log.info('YouTube playlists were found: %s' % self.search_play_lists)
                        for x in range(len(self.search_play_lists)):
                            self.send_undercover_msg(self.user.nick, '*' + str(x + 1) + '. ' +
                                                     self.search_play_lists[x]['playlist_title'] + ' - ' +
                                                     self.search_play_lists[x]['playlist_id'] + '*')
                            pinylib.time.sleep(0.2)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')

    def do_youtube_playlist_search_choice(self, index_choice):
        """
        Starts a playlist from the search list.
        :param index_choice: int the index in the play lists to start.
        """
        if self.playlist_mode:
            if len(self.search_play_lists) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE +
                                  ' No previous playlist search committed to confirm ID. Please do *!plsh*.')
            elif len(index_choice) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE +
                                  ' Please choose your selection from the playlist IDs,  e.g. *!pladd 2*')
            else:
                if 0 <= int(index_choice) <= 4:
                    threading.Thread(target=self.do_youtube_playlist_videos,
                                     args=(self.search_play_lists[int(index_choice) - 1]['playlist_id'],)).start()
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')

    def do_charts(self):
        """ Retrieves the Top40 songs list and adds the songs to the playlist. """
        if self._is_client_mod:
            if self.playlist_mode:
                self.send_bot_msg(unicode_catalog.STATE + ' *Hang on* while we retrieve the Top40 songs...')

                songs_list = other.top40()
                top40_list = list(reversed(songs_list))
                if songs_list is None:
                    self.send_bot_msg(unicode_catalog.INDICATE +
                                      ' We could not fetch the Top40 songs list.')
                elif len(songs_list) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No songs were found.')
                else:
                    video_list = []
                    for x in range(len(top40_list)):
                        search_str = top40_list[x][0] + ' - ' + top40_list[x][1]
                        _youtube = youtube.youtube_search(search_str)
                        if _youtube is not None:
                            video_list.append(_youtube)

                    if len(video_list) > 0:
                        self.send_bot_msg(unicode_catalog.PENCIL + ' *Added Top40* songs (40 --> 1) to playlist.')
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.media_manager.add_track_list(self.user.nick, video_list)
                        else:
                            self.media_manager.add_track_list(self.user.nick, video_list)
                            track = self.media_manager.get_next_track()
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')

    def do_lastfm_chart(self, chart_items):
        """
        Makes a playlist from the currently most played tunes on Last.fm.
        :param chart_items: int the amount of tunes we want.
        """
        if self._is_client_mod:
            if self.playlist_mode:
                if chart_items is 0 or chart_items is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify the amount of tunes you want.')
                else:
                    try:
                        _items = int(chart_items)
                    except ValueError:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                    else:
                        # TODO: "No more than 30" --> smaller or equal to 30.
                        if 0 < _items <= 30:
                            self.send_bot_msg(unicode_catalog.STATE + ' *Please wait* while we create a playlist...')
                            last = lastfm.get_lastfm_chart(_items)
                            if last is not None:
                                if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                    self.media_manager.add_track_list(self.user.nick, last)
                                    self.send_bot_msg(unicode_catalog.PENCIL + '*Added:* ' + str(len(last)) +
                                                      ' *tunes from last.fm chart.*')
                                else:
                                    self.media_manager.add_track_list(self.user.nick, last)
                                    self.send_bot_msg(unicode_catalog.PENCIL + '*Added:* ' + str(len(last)) +
                                                      ' *tunes from last.fm chart.*')
                                    track = self.media_manager.get_next_track()
                                    self.send_media_broadcast_start(track.type, track.id)
                                    self.media_event_timer(track.time)
                            else:
                                self.send_bot_msg(unicode_catalog.INDICATE +
                                                  ' Failed to retrieve a result from last.fm.')
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' No more than 30 tunes.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_lastfm_random_tunes(self, max_tunes):
        """
        Creates a playlist from what other people are listening to on Last.fm.
        :param max_tunes: int the maximum amount of tunes.
        """
        if self._is_client_mod:
            if self.playlist_mode:
                if max_tunes is 0 or max_tunes is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify the max amount of tunes you want.')
                else:
                    try:
                        _items = int(max_tunes)
                    except ValueError:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                    else:
                        # TODO: "No more than 50" --> smaller or equal to 50.
                        if 0 < _items <= 50:
                            self.send_bot_msg(unicode_catalog.STATE + ' *Please wait* while we create a playlist...')
                            last = lastfm.lastfm_listening_now(max_tunes)
                            if last is not None:
                                if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                                    self.media_manager.add_track_list(self.user.nick, last)
                                    self.send_bot_msg(unicode_catalog.PENCIL + ' Added *' + str(len(last)) +
                                                      '* tunes from *last.fm*')
                                else:
                                    self.media_manager.add_track_list(self.user.nick, last)
                                    self.send_bot_msg(unicode_catalog.PENCIL + ' Added *' + str(len(last)) +
                                                      ' * tunes from *last.fm*')
                                    track = self.media_manager.get_next_track()
                                    self.send_media_broadcast_start(track.type, track.id)
                                    self.media_event_timer(track.time)
                            else:
                                self.send_bot_msg(unicode_catalog.INDICATE +
                                                  ' Failed to retrieve a result from last.fm.')
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' No more than 50 tunes.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def search_lastfm_by_tag(self, search_str):
        """
        Searches Last.fm for tunes matching the search term and creates a playlist from them.
        :param search_str: str the search term to search for.
        """
        if self._is_client_mod:
            if self.playlist_mode:
                if len(search_str) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Missing search tag.')
                else:
                    self.send_bot_msg(unicode_catalog.STATE + ' *Please wait* while we create a playlist...')
                    last = lastfm.search_lastfm_by_tag(search_str)
                    if last is not None:
                        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
                            self.media_manager.add_track_list(self.user.nick, last)
                            self.send_bot_msg(unicode_catalog.PENCIL + ' Added *' + str(len(last)) +
                                              '* tunes from *last.fm*')
                        else:
                            self.media_manager.add_track_list(self.user.nick, last)
                            self.send_bot_msg(unicode_catalog.PENCIL + ' Added *' + str(len(last)) +
                                              '* tunes from *last.fm*')
                            track = self.media_manager.get_next_track()
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE +
                                          ' Failed to retrieve a result from last.fm.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Turn on *playlist mode* to use this feature.')
        else:
            self.send_bot_msg('Not enabled right now.')

    # TODO: Index search to true length from list.
    def do_delete_playlist_item(self, to_delete):
        """
        Delete item(s) from the playlist by index.
        :param to_delete: str index(es) to delete.
        """
        if len(self.media_manager.track_list) is 0:
            self.send_bot_msg('The track list is empty.')
        elif len(to_delete) is 0:
            self.send_bot_msg('No indexes to delete provided.')
        else:
            indexes = None
            by_range = False

            try:
                if ':' in to_delete:
                    range_indexes = map(int, to_delete.split(':'))
                    temp_indexes = range(range_indexes[0], range_indexes[1] + 1)
                    if len(temp_indexes) > 1:
                        by_range = True
                else:
                    temp_indexes = map(int, to_delete.split(','))
            except ValueError:
                # Add logging here?
                self.send_undercover_msg(self.user.nick, 'Wrong format.')
            else:
                indexes = []
                for i in temp_indexes:
                    if i < len(self.media_manager.track_list) and i not in indexes:
                        indexes.append(i)

            if indexes is not None and len(indexes) > 0:
                result = self.media_manager.delete_by_index(indexes, by_range)
                if result is not None:
                    if by_range:
                        self.send_bot_msg(
                            '*Deleted from index:* %s *to index:* %s' % (result['from'], result['to']))
                    elif result['deleted_indexes_len'] is 1:
                        self.send_bot_msg('*Deleted*: %s' % result['track_title'])
                    else:
                        self.send_bot_msg('*Deleted tracks at index:* %s' % ', '.join(result['deleted_indexes']))
                else:
                    self.send_bot_msg('Nothing was deleted.')

    def do_clear_playlist(self):
        """ Clear the playlist. """
        if len(self.media_manager.track_list) > 0:
            # TODO: Move this to outer.
            pl_length = str(len(self.media_manager.track_list))
            self.media_manager.clear_track_list()
            self.send_bot_msg(unicode_catalog.SCISSORS + ' *Deleted* ' + pl_length + ' *items* in the playlist.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' The playlist is empty, *nothing to clear*.')

    # == Public Command Methods. ==
    # TODO: Make use of sys.version & sys.platform (possibly as command information).
    def do_version(self):
        """ Replies with relevant version information concerning the bot. """
        self.send_undercover_msg(self.user.nick, '*pinybot* %s, *code name:* %s, *pinylib version*: %s' %
                                 (__version__, build_name, pinylib.about.__version__))
        self.send_undercover_msg(self.user.nick, '*Repository/Editor:* ' + author_info)
        self.send_undercover_msg(self.user.nick, '*Platform:* %s *Runner:* %s' % (sys.platform, sys.version_info[0:4]))

    def do_help(self):
        """ Posts a link to a GitHub README/Wiki about the bot commands. """
        self.send_bot_msg('*Commands:* https://github.com/GoelBiju/pinybot/wiki/Features/'
                          '\n*README:* https://github.com/GoelBiju/pinybot/blob/master/README.md')

    def do_uptime(self):
        """ Shows the bots uptime. """
        self.send_bot_msg(unicode_catalog.TIME + ' *Uptime:* ' + self.format_time(self.get_runtime()) +
                          ' *Reconnect Delay:* ' + self.format_time(self._reconnect_delay * 1000))

    def do_pmme(self):
        """ Opens a PM session with the bot. """
        self.send_private_msg('How can I help you *' + unicode_catalog.NO_WIDTH + self.user.nick +
                              unicode_catalog.NO_WIDTH + '*?', self.user.nick)

    def do_full_screen(self, room_name):
        """
        Post a full screen link.
        :param room_name: str the room name you want a full screen link for.
        """
        if len(room_name) is 0:
            self.send_undercover_msg(self.user.nick, 'http://tinychat.com/embed/Tinychat-11.1-1.0.0.' +
                                     pinylib.CONFIG['swf_version'] + '.swf?target=client&key=tinychat&room=' +
                                     self._roomname)
        else:
            self.send_undercover_msg(self.user.nick, 'http://tinychat.com/embed/Tinychat-11.1-1.0.0.' +
                                     pinylib.CONFIG['swf_version'] + '.swf?target=client&key=tinychat&room=' +
                                     room_name)

    # == Media Related Status Methods. ==
    def do_media_request(self, request_type, request_search):
        """
        Allows user's to make media requests for both YouTube and SoundCloud and requests the media to
        be accepted/declined by a owner/super mod/moderator/botter.
        :param request_type: str the type of media it is YouTube/SoundCloud.
        :param request_search: str the item to request for link/id/title.
        """
        if self._is_client_mod:
            if self.media_request is None:
                # Set up the type of media to be added to the playlist/played.
                type_reply = str
                if request_type == self.yt_type:
                    type_reply = 'YouTube'
                elif request_type == self.sc_type:
                    type_reply = 'SoundCloud'

                if len(request_search) is 0:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify *' + type_reply +
                                      ' title, id or link to make a media request.*')
                else:
                    # Search for the specified media.
                    _media = None
                    # TODO: Support link regex here?
                    if request_type == self.yt_type:
                        _media = youtube.youtube_search(request_search)
                    elif request_type == self.sc_type:
                        _media = soundcloud.soundcloud_search(request_search)

                    # Handle starting media playback.
                    if _media is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find media: ' + request_search)
                    else:
                        self.media_request = _media
                        self.send_bot_msg(unicode_catalog.ARROW_SIDEWAYS + ' Media request has been *submitted*. ' +
                                          'Please wait until the request is accepted/declined.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please wait until a privileged user decides on the '
                                                             'current media request.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_now_playing(self):
        """ Shows the currently playing media title to the user. """
        if self._is_client_mod:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive() or \
                    self.media_manager.is_paused:
                track = self.media_manager.track()
                if len(self.media_manager.track_list) > 0:
                    # TODO: Owner_run_msg - appropriate unicode - list image?
                    self.send_undercover_msg(self.user.nick, '*%s* (%s)' % (track.title, self.format_time(track.time)))
                    # TODO: Shows the respective media URLs.
                    if track.type == self.yt_type:
                        self.send_undercover_msg(self.user.nick, '*YouTube link:* https://youtube.com/watch?v=' +
                                                 str(track.id))
                    elif track.type == self.sc_type:
                        track_info = soundcloud.soundcloud_track_info(track.id)
                        track_link = track_info['permalink_url']
                        self.send_undercover_msg(self.user.nick, '*SoundCloud link:* ' + str(track_link))
                else:
                    self.send_undercover_msg(self.user.nick, '*' + track.title + '* ' + self.format_time(track.time))
            else:
                self.send_undercover_msg(self.user.nick, '*No track is playing.*')

    def do_who_plays(self):
        """ Shows who is played/requested the track. """
        if self.media_timer_thread is not None and self.media_timer_thread.is_alive() or self.media_manager.is_paused:
            track = self.media_manager.track()
            time_since_request = self.format_time(int(pinylib.time.time() - track.rq_time) * 1000)
            self.send_undercover_msg(self.user.nick, '*%s* played/requested this track: *%s ago*.' %
                                     (track.nick, time_since_request))
        else:
            self.send_undercover_msg(self.user.nick, 'No track is playing.')

    # TODO: Issue.
    def do_playlist_status(self):
        """ Shows info about the playlist. """
        if self._is_client_mod:
            if len(self.media_manager.track_list) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' The playlist is *empty*.')
            else:
                inqueue = self.media_manager.queue()
                if inqueue is not None:
                    self.send_bot_msg(str(inqueue[0]) + ' *item(s) in the playlist.* ' +
                                      str(inqueue[1]) + ' *Still in queue.*')
        else:
            self.send_bot_msg('Not enabled right now.')

    # TODO: Issue.
    def do_next_tune_in_playlist(self):
        """ Shows next item in the playlist. """
        if self._is_client_mod:
            if self.media_manager.is_last_track():
                self.send_bot_msg(unicode_catalog.INDICATE + ' This is the *last tune* in the playlist.')
            elif self.media_manager.is_last_track() is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *No tunes* in the playlist.')
            else:
                pos, next_track = self.media_manager.next_track_info()
                if next_track is not None:
                    self.send_bot_msg(unicode_catalog.STATE + ' (%s) *%s* (%s)' % (str(pos), next_track.title,
                                                                                   self.format_time(next_track.time)))
        else:
            self.send_bot_msg('Not enabled right now.')

    # TODO: Private media handling via media manager?
    def do_play_private_media(self, media_type, search):
        """
        Plays a youTube or soundCloud matching the search term privately.
        :param media_type: str youTube or soundCloud depending on the type of media to play privately.
        :param search: str the search term.
        NOTE: The video will only be visible for the message sender.
        """
        if self._is_client_mod:
            type_reply = str
            if media_type == self.yt_type:
                type_reply = 'YouTube'
            elif media_type == self.sc_type:
                type_reply = 'SoundCloud'

            if len(type_reply) is 0:
                self.send_undercover_msg(self.user.nick, self.user.nick + ', please specify *' + type_reply +
                                         ' title, id or link.*')
            else:
                _media = None
                if media_type == self.yt_type:
                    _media = youtube.youtube_search(search)
                elif media_type == self.sc_type:
                    _media = soundcloud.soundcloud_search(search)

                if _media is None:
                    self.send_undercover_msg(self.user.nick, 'Could not find video: ' + search)
                else:
                    self.user.private_media = media_type
                    self.send_media_broadcast_start(media_type, _media['video_id'], private_nick=self.user.nick)
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_stop_private_media(self):
        """
        Stops a users private media (youTube or soundCloud) using a user attribute.
        If the attribute is not available, then both media are forcibly stopped.
        """
        # Close the private media depending if the attribute(s) exist.
        if hasattr(self.user, 'yt_type'):
            self.send_media_broadcast_close(self.yt_type, self.user.nick)
        elif hasattr(self.user, 'sc_type'):
            self.send_media_broadcast_close(self.sc_type, self.user.nick)
        else:
            # If none or both exist then issue a close media broadcast
            # for both types of media (YouTube and SoundCloud).
            self.send_media_broadcast_close(self.yt_type, self.user.nick)
            self.send_media_broadcast_close(self.sc_type, self.user.nick)

    # TODO: Split these into smaller functions.
    # TODO: Allow sync to capture media pause/resume states.
    # TODO: Should sync all be an option?
    def do_sync_media(self, nick_to_sync):
        """
        Sync a user with the media that is currently being played within the room.
        NOTE: We do not handle events in which two media events are occurring simultaneously.

        :param nick_to_sync: str the nickname to send the sync request to.
        """
        if self._is_client_mod:
            if self.media_timer_thread is not None and self.media_timer_thread.is_alive() or \
                    self.media_manager.is_paused:
                if len(nick_to_sync) is 0:
                    sync_nick = self.user.nick
                else:
                    sync_nick = self.find_user_info(nick_to_sync).nick

                if sync_nick is not None:
                    # Send the initial media, then proceed to send paused request if the media is in a paused state.
                    self.send_media_broadcast_start(self.media_manager.track().type, self.media_manager.track().id,
                                                    self.media_manager.elapsed_track_time(), private_nick=sync_nick)

                    # TODO: Shall we start playing then skip and pause at the paused section?
                    # TODO: Should we handle in the event that a media seek is issued at a specific point whilst issuing
                    #       a sync request (the seek/pause/close/play event is the only issue that will not be handled
                    #       in this case.
                    if self.media_manager.is_paused:
                        # TODO: Can we avoid sending this sleep time.
                        # Small delay to make sure the pause request is not sent prior to the start media request.
                        pinylib.time.sleep(0.1)
                        self.send_media_broadcast_pause(self.media_manager.track().type, private_nick=sync_nick)
                else:
                    self.send_undercover_msg(self.user.nick, 'The user you tried to send a *sync* to doesn\'t exist.')
            else:
                self.send_undercover_msg(self.user.nick, '*No media is playing* to sync to at the moment.')

    # == Tinychat API Command Methods. ==
    def do_spy(self, roomname):
        """
        Shows info for a given room.
        :param roomname: str the room name to find info for.
        """
        if self._is_client_mod:
            if len(roomname) is 0:
                self.send_undercover_msg(self.user.nick, 'Missing room name.')
            else:
                spy_info = pinylib.tinychat.spy_info(roomname)
                if spy_info is None:
                    self.send_undercover_msg(self.user.nick, 'The room is empty.')
                elif spy_info == 'PW':
                    self.send_undercover_msg(self.user.nick, 'The room is password protected.')
                # TODO: Added 'CLOSED' option to the reply.
                elif spy_info == 'CLOSED':
                    self.send_undercover_msg(self.user.nick, 'The room is closed.')
                else:
                    self.send_undercover_msg(self.user.nick,
                                             '*mods:* ' + spy_info['mod_count'] +
                                             ' *Broadcasters:* ' + spy_info['broadcaster_count'] +
                                             ' *Users:* ' + spy_info['total_count'])
                    if self.user.is_owner or self.user.is_mod or self.user.has_power:
                        users = ', '.join(spy_info['users'])
                        self.send_undercover_msg(self.user.nick, '*' + users + '*')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_account_spy(self, account):
        """
        Shows info about a Tinychat account.
        :param account: str Tinychat account.
        """
        if self._is_client_mod:
            if len(account) is 0:
                self.send_undercover_msg(self.user.nick, 'Missing account name to search for.')
            else:
                tc_usr = pinylib.tinychat.tinychat_user_info(account)
                if tc_usr is None:
                    self.send_undercover_msg(self.user.nick, 'Could not find Tinychat info for: ' + account)
                else:
                    self.send_undercover_msg(self.user.nick, '*ID:* ' + tc_usr['tinychat_id'] +
                                             ', *Last login:* ' + tc_usr['last_active'])
        else:
            self.send_bot_msg('Not enabled right now.')

    # == Other API Command Methods. ==
    def do_search_urban_dictionary(self, search):
        """
        Shows "Urban Dictionary" definition of search string.
        :param search: str the search term to look up a definition for.
        """
        if self._is_client_mod:
            if len(search) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify a search term for *Urban-Dictionary*.')
            else:
                urban_definition = other.urbandictionary_search(search)
                if urban_definition is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find a definition for: ' + search)
                else:
                    if len(urban_definition) > 70:
                        chunks = string_utili.chunk_string(urban_definition, 70)
                        for i in range(0, 2):
                            self.send_bot_msg(chunks[i])
                    else:
                        self.send_bot_msg(urban_definition)

    def do_weather_search(self, search_str):
        """
        Shows weather info for a given search string.
        :param search_str: str the search string to find weather data for.
        """
        if len(search_str) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify a location to retrieve weather information.')
        else:
            weather = other.weather_search(search_str)
            if weather is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find weather data for: ' + search_str)
            elif not weather:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing API key.')
            else:
                self.send_bot_msg(weather)

    def do_whois_ip(self, ip_str):
        """
        Shows whois info for a given IP address.
        :param ip_str: str the IP address to find info for.
        """
        if len(ip_str) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please provide an I.P. address.')
        else:
            whois = other.whois(ip_str)
            if whois is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' No information found for: ' + ip_str)
            else:
                self.send_bot_msg(whois)

    def do_md5_hash_cracker(self, hash_str):
        """
        Shows the attempt to crack an MD5 hash with the http://md5cracker.org/ API.
        :param hash_str: str the 32 character long hash.
        """
        if len(hash_str) is 0:
            self.send_bot_msg('Missing MD5 hash.')
        elif len(hash_str) is 32:
            result = other.hash_cracker(hash_str)
            if result is not None:
                if result['status']:
                    self.send_bot_msg(hash_str + ' = *' + unicode_catalog.NO_WIDTH + result['result'] +
                                      unicode_catalog.NO_WIDTH + '*')
                elif not result['status']:
                    self.send_bot_msg(result['message'])
        else:
            self.send_bot_msg('An MD5 *hash is exactly 32 characters* in length.')

    def do_duckduckgo_search(self, search):
        """
        Shows definitions/information relating to a particular DuckDuckGo search query.
        :param search: str the search query.
        """
        if len(search) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a *DuckDuckGo* search term.')
        else:
            definitions = other.duckduckgo_search(search)
            if definitions is not None:
                for x in range(len(definitions)):
                    # TODO: String utility implementation here.
                    if len(definitions[x]) > 160:
                        sentence = definitions[x][0:159] + '\n ' + definitions[x][159:]
                    else:
                        sentence = definitions[x]
                    self.send_bot_msg(str(x + 1) + ' *' + sentence + '*')

    def do_omdb_search(self, search):
        """
        Post information retrieved from OMDb (serving IMDB data) API.
        :param search: str the IMDB entertainment search.
        """
        if len(search) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify a *movie or television show*.')
        else:
            omdb = other.omdb_search(search)
            if omdb is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *Error or title does not exist.*')
            else:
                self.send_bot_msg(omdb)

    def do_etymonline_search(self, search):
        """
        Search http://etymonline.com/ to reply with etymology for particular search term.
        :param search: str the term you want its etymology for.
        """
        if len(search) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a *search term* to lookup on *Etymonline*.')
        else:
            etymology = other.etymonline(search)
            if etymology is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' We could not retrieve the etymology for your term.')
            else:
                # TODO: String utility implementation here.
                if len(etymology) > 295:
                    etymology = etymology[:294] + ' ...'
                self.send_bot_msg(etymology)

    # == Just For Fun Command Methods. ==
    # TODO: When instant is used initially without using !cb to initialise the session,
    # the instant message is not printed.
    def do_cleverbot(self, query, instant=False):
        """
        Shows the reply from the online self-learning A.I. CleverBot.
        :param query: str the statement/question to ask CleverBot.
        :param instant: bool True/False whether the request was from when a user typed in the client's nickname or
                       manually requested a response.
        """
        if self.cleverbot_enable:
            if len(query) is not 0:
                if self.cleverbot_session is None:
                    # Open a new connection to CleverBot in the event we do not already have one set up.
                    self.cleverbot_session = clever_client_bot.CleverBot()
                    # Start CleverBot message timer.
                    threading.Thread(target=self.cleverbot_timer).start()
                    if not instant:
                        self.send_bot_msg(unicode_catalog.VICTORY_HAND + ' *Waking up* ' + self.client_nick)

                if self.cleverbot_session is not None:
                    # Request the response from the server and send it as a normal user message.
                    response = self.cleverbot_session.converse(query)
                    if not instant:
                        self.send_bot_msg('*CleverBot* %s: %s' % (unicode_catalog.STATE, response))
                    else:
                        self.send_bot_msg(response, use_chat_msg=True)

                    self.console_write(pinylib.COLOR['green'], '[CleverBot]: ' + response)

                # Record the time at which the response was sent.
                self.cleverbot_msg_time = int(pinylib.time.time())
            else:
                if not instant:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a statement/question.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enable CleverBot to use this function.')

    def do_chuck_norris(self):
        """ Shows a Chuck Norris joke/quote. """
        chuck = other.chuck_norris()
        if chuck is not None:
            self.send_bot_msg('*' + chuck + '*')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Unable to retrieve from server.')

    def do_8ball(self, question):
        """
        Shows magic eight ball answer to a yes/no question.
        :param question: str the yes/no question.
        """
        if len(question) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Provide a *yes* or *no* question.')
        else:
            self.send_bot_msg('*8Ball:* ' + locals.eight_ball())

    def do_yo_mama_joke(self):
        """ Shows the reply from a 'Yo Mama' joke API. """
        yo_mama = str(other.yo_mama_joke())
        if yo_mama is not None:
            self.send_bot_msg('*' + unicode_catalog.NO_WIDTH + self.user.nick + unicode_catalog.NO_WIDTH +
                              '* says ' + yo_mama.lower())
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Unable to retrieve from server.')

    def do_advice(self):
        """ Shows the reply from an advice API. """
        advice = other.online_advice()
        if advice is not None:
            self.send_bot_msg('*' + unicode_catalog.NO_WIDTH + self.user.nick + unicode_catalog.NO_WIDTH + '*, ' +
                              advice.lower())
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Unable to retrieve from server.')

    # TODO: Simplify this section of code.
    def do_one_liner(self, tag):
        """
        Shows a random "one-liner" joke.
        :param tag: str a specific category to pick a random joke from OR state '?' to list categories.
        """
        if tag:
            if tag == '?':
                all_tags = ', '.join(other.ONE_LINER_TAGS) + '.'
                self.send_undercover_msg(self.user.nick, '*Possible tags*: ' + str(all_tags))
                return
            elif tag in other.ONE_LINER_TAGS:
                one_liner = other.one_liners(tag)
            else:
                self.send_bot_msg('The tag you specified is not available. Enter *!joke ?* to get a list of tags.')
                return
        else:
            one_liner = other.one_liners()

        if one_liner is not None:
            self.send_bot_msg('*' + one_liner + '*')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Unable to retrieve from server.')

    # TODO: Fix time issues when using additional time, 12 hour time and google time.
    # def do_time(self, location, additional, twelve_hour):
    #     """
    #     Shows the time in a location via Google (or time.is if specified otherwise).
    #     :param location: str location name.
    #     :param additional: bool True/False whether the time.is API should be used to fetch the time.
    #     :param twelve_hour: bool True/False (if additional is True) whether the time returned should be displayed in
    #                         analogue with AM/PM.
    #     """
    #     if len(location) is 0:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a location to fetch the time.')
    #     else:
    #         if additional is False:
    #             google_location, google_time = other.google_time(location)
    #             if (google_location is None) or (google_time is None):
    #                 self.send_bot_msg(unicode_catalog.INDICATE + ' We could not fetch the time in *"%s"*.' % location)
    #             else:
    #                 self.send_bot_msg('%s: *%s*' % (google_location, google_time))
    #         else:
    #             time = other.time_is(location)
    #             if time is None:
    #                 self.send_bot_msg(unicode_catalog.INDICATE + ' We could not fetch the time in "%s".' % location)
    #             else:
    #                 if twelve_hour:
    #                     time_status = 'AM'
    #                     raw_time = int(time[0:1])
    #                     if raw_time > 12:
    #                         time_status = 'PM'
    #                     time = str(raw_time - 12) + time[2:len(time)] + ' ' + time_status
    #                 self.send_bot_msg('The time in *%s* is: *%s*.' % (location, time))

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
                if key in self.ascii_dict:
                    ascii_message = self.ascii_dict[key]
                    # Allow for custom replacement variables in the ASCII message.
                    new_ascii_message = self.replace_content(ascii_message)
                    self.send_bot_msg('*%s*' % new_ascii_message)
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
                    threading.Thread(target=self.do_set_room_pass, args=(pm_arg,)).start()

                elif pm_cmd == CONFIG['prefix'] + 'bp':
                    threading.Thread(target=self.do_set_broadcast_pass, args=(pm_arg,)).start()

                # Owner and super mod commands.
                elif pm_cmd == CONFIG['prefix'] + 'key':
                    threading.Thread(target=self.do_key, args=(pm_arg,)).start()

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

                # TODO: Connect the broadcast options as main commands.
                elif pm_cmd == CONFIG['prefix'] + 'up':
                    threading.Thread(target=self.do_cam_up, args=(pm_arg, )).start()

                # elif pm_cmd == CONFIG['prefix'] + 'logo':
                #     threading.Thread(target=self.do_cam_up_logo, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'down':
                    threading.Thread(target=self.do_cam_down, args=(pm_arg, )).start()

                # elif pm_cmd == CONFIG['prefix'] + 'stoplogo':
                #     threading.Thread(target=self.do_cam_down_logo, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'nocam':
                    threading.Thread(target=self.do_nocam, args=(pm_arg, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'noguest':
                    threading.Thread(target=self.do_no_guest, args=(pm_arg, )).start()

                # TODO: Public commands option in PM.
                elif pm_cmd == CONFIG['prefix'] + 'pub':
                    self.do_public_cmds(pm_arg)

                elif pm_cmd == CONFIG['prefix'] + 'nick':
                    self.do_nick(pm_arg)

                elif pm_cmd == CONFIG['prefix'] + 'ban':
                    threading.Thread(target=self.do_kick, args=(pm_arg, True, True, )).start()

                elif pm_cmd == CONFIG['prefix'] + 'notice':
                    if self._is_client_mod:
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
                               .replace(self.key, '***KEY***')
                               .replace(CONFIG['super_key'], '***SUPER KEY***'))

    # == Super Mod Command Methods. ==
    def do_set_room_pass(self, password):
        """
        Set a room password for the room.
        :param password: str the room password
        """
        if self._is_client_owner:
            if self.user.is_super:
                if not password:
                    self.privacy_settings.set_room_password()
                    self.send_bot_msg('*The room password was removed.*')
                    pinylib.time.sleep(1)
                    self.send_private_msg('The room password was removed.', self.user.nick)
                elif len(password) > 1:
                    self.privacy_settings.set_room_password(password)
                    self.send_private_msg('*The room password is now:* ' + password, self.user.nick)
                    pinylib.time.sleep(1)
                    self.send_bot_msg('*The room is now password protected.*')

    def do_set_broadcast_pass(self, password):
        """
        Set a broadcast password for the room.
        :param password: str the password
        """
        if self._is_client_owner:
            if self.user.is_super:
                if not password:
                    self.privacy_settings.set_broadcast_password()
                    self.send_bot_msg('*The broadcast password was removed.*')
                    pinylib.time.sleep(1)
                    self.send_private_msg('The broadcast password was removed.', self.user.nick)
                elif len(password) > 1:
                    self.privacy_settings.set_broadcast_password(password)
                    self.send_private_msg('*The broadcast password is now:* ' + password, self.user.nick)
                    pinylib.time.sleep(1)
                    self.send_bot_msg('*Broadcast password is enabled.*')

    # == Owner And Super Mod Command Methods. ==
    def do_key(self, new_key):
        """
        Shows or sets a new secret key.
        :param new_key: str the new secret key.
        """
        if self.user.is_owner or self.user.is_super:
            if len(new_key) is 0:
                self.send_private_msg('The current key is: *' + self.key + '*', self.user.nick)
            elif len(new_key) < 6:
                self.send_private_msg('Key must be at least 6 characters long: ' + str(len(self.key)), self.user.nick)
            elif len(new_key) >= 6:
                self.key = new_key
                self.send_private_msg('The key was changed to: *' + self.key + '*', self.user.nick)

    # TODO: Adjusted file names to new file names.
    def do_clear_bad_nicks(self):
        """ Clears the bad nicks file. """
        if self.user.is_owner or self.user.is_super:
            pinylib.fh.delete_file_content(self.config_path(), CONFIG['nick_bans'])

    def do_clear_bad_strings(self):
        """ Clears the bad strings file. """
        if self.user.is_owner or self.user.is_super:
            pinylib.fh.delete_file_content(self.config_path(), CONFIG['ban_strings'])

    def do_clear_bad_accounts(self):
        """ Clears the bad accounts file. """
        if self.user.is_owner or self.user.is_super:
            pinylib.fh.delete_file_content(self.config_path(), CONFIG['account_bans'])

    # == Mod And Bot Controller Command Methods. ==
    def do_pm_disconnect(self, key):
        """
        Disconnects the bot via PM.
        :param key: str the key to access the command.
        """
        if self.user.is_owner or self.user.is_super or self.user.is_mod or self.user.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user.nick)
            else:
                if key == self.key:
                    log.info('User %s:%s commenced remote disconnect.' % (self.user.nick, self.user.id))
                    self.send_private_msg('The bot will disconnect from the room.', self.user.nick)
                    self.console_write(pinylib.COLOR['red'], 'Disconnected by %s.' % self.user.nick)
                    threading.Thread(target=self.disconnect).start()
                    # Exit with a normal status code.
                    sys.exit(1)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    # TODO: Show hibernation statistics when awoken.
    def do_pm_wake(self):
        """ Lets the bot resume normal activities from when it was set to sleep. """
        if self.user.is_owner or self.user.is_super or self.user.is_mod or self.user.has_power:
            # TODO: Remove the use of bot listen.
            self.bot_listen = True
            self.send_private_msg('The bot has *woken up* from sleep, normal activities may now be resumed.',
                                  self.user.nick)

    def do_op_user(self, msg_parts):
        """
        Lets the room owner, a mod or a bot controller make another user a bot controller.
        NOTE: Mods or bot controllers will have to provide a key, the owner does not.
        :param msg_parts: list the pm message as a list.
        """
        if self.user.is_owner or self.user.is_super:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user.nick)
            elif len(msg_parts) == 2:
                user = self.find_user_info(msg_parts[1])
                if user is not None:
                    if user.has_power:
                        self.send_private_msg('This user already has privileges. No need to re-instate.',
                                              self.user.nick)
                    else:
                        user.has_power = True
                        self.send_private_msg(user.nick + ' is now a bot controller.', self.user.nick)
                        self.send_private_msg('You are now a bot controller.', user.nick)
                else:
                    self.send_private_msg('No user named: ' + msg_parts[1], self.user.nick)

        elif self.user.is_mod or self.user.has_power:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user.nick)
            elif len(msg_parts) == 2:
                self.send_private_msg('Missing key.', self.user.nick)
            elif len(msg_parts) == 3:
                if msg_parts[2] == self.key:
                    user = self.find_user_info(msg_parts[1])
                    if user is not None:
                        if user.has_power:
                            self.send_private_msg('This user already has privileges. No need to re-instate.',
                                                  self.user.nick)
                        else:
                            user.has_power = True
                            self.send_private_msg(user.nick + ' is now a bot controller.', self.user.nick)
                            self.send_private_msg('You are now a bot controller.', user.nick)
                    else:
                        self.send_private_msg('No user named: ' + msg_parts[1], self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    def do_deop_user(self, msg_parts):
        """
        Lets the room owner, a mod or a bot controller remove a user from being a bot controller.
        NOTE: Mods or bot controllers will have to provide a key, owner does not.
        :param msg_parts: list the pm message as a list.
        """
        if self.user.is_owner or self.user.is_super:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user.nick)
            elif len(msg_parts) == 2:
                user = self.find_user_info(msg_parts[1])
                if user is not None:
                    if not user.has_power:
                        self.send_private_msg('This user was never instated as a bot controller. No need to DE-OP.',
                                              self.user.nick)
                    else:
                        user.has_power = False
                        self.send_private_msg(user.nick + ' is not a bot controller anymore.', self.user.nick)
                else:
                    self.send_private_msg('No user named: ' + msg_parts[1], self.user.nick)

        elif self.user.is_mod or self.user.has_power:
            if len(msg_parts) == 1:
                self.send_private_msg('Missing username.', self.user.nick)
            elif len(msg_parts) == 2:
                self.send_private_msg('Missing key.', self.user.nick)
            elif len(msg_parts) == 3:
                if msg_parts[2] == self.key:
                    user = self.find_user_info(msg_parts[1])
                    if user is not None:
                        if not user.has_power:
                            self.send_private_msg('This user was never instated as a bot controller. No need to DE-OP.',
                                                  self.user.nick)
                        else:
                            user.has_power = False
                            self.send_private_msg(user.nick + ' is not a bot controller anymore.', self.user.nick)
                    else:
                        self.send_private_msg('No user named: ' + msg_parts[1], self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    def do_cam_up(self, key):
        """
        Makes the bot cam up.
        :param key str the key needed for moderators/bot controllers.
        """
        if self.user.is_owner or self.user.is_super:
            self.set_stream()
        elif self.user.is_mod or self.user.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user.nick)
            elif key == self.key:
                self.set_stream()
            else:
                self.send_private_msg('Wrong key.', self.user.nick)

    # def do_cam_up_logo(self, key):
    #     """
    #     Makes the bot cam up with a single frame of flv1 data.
    #     :param key: str the key needed for moderators/bot controllers.
    #     """
    #     if self.user.is_owner or self.user.is_super:
    #         # self.set_stream()
    #         if self._publish_connection:
    #             self.logo_stream = True
    #             threading.Thread(target=self.image_stream, args=(self.flv1_logo_data, )).start()
    #         else:
    #             self.send_private_msg('No streaming connection established, have you ran *!up* [key]?.', self.user.nick)
    #     elif self.user.is_mod or self.user.has_power:
    #         if len(key) is 0:
    #             self.send_private_msg('Missing key.', self.user.nick)
    #         elif key == self.key:
    #             # self.set_stream()
    #             if self._publish_connection:
    #                 self.logo_stream = True
    #                 threading.Thread(target=self.image_stream, args=(self.flv1_logo_data, )).start()
    #             else:
    #                 self.send_private_msg('No streaming connection established, have you run *!up* [key]?.',
    #                                       self.user.nick)
    #         else:
    #             self.send_private_msg('Wrong key.', self.user.nick)

    def do_cam_down(self, key):
        """
        Makes the bot cam down.
        :param key: str the key needed for moderators/bot controllers.
        """
        if self.user.is_owner or self.user.is_super:
            self.set_stream(False)
        elif self.user.is_mod or self.user.has_power:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user.nick)
            elif key == self.key:
                self.set_stream(False)
            else:
                self.send_private_msg('Wrong key.', self.user.nick)

    # def do_cam_down_logo(self, key):
    #     """
    #     Makes the bot cam down the logo shown on the broadcast, however without
    #     stopping the broadcast altogether.
    #     :param key: str the key needed for moderators/bot controllers.
    #     """
    #     if self.user.is_owner or self.user.is_super:
    #         if self.logo_stream:
    #             self.logo_stream = False
    #         else:
    #             self.send_private_msg('No logo stream session present to close.', self.user.nick)
    #     elif self.user.is_mod or self.user.has_power:
    #         if len(key) is 0:
    #             self.send_private_msg('Missing key.', self.user.nick)
    #         elif key == self.key:
    #             if self.logo_stream:
    #                 self.logo_stream = False
    #             else:
    #                 self.send_private_msg('No logo stream session present to close.', self.user.nick)
    #         else:
    #             self.send_private_msg('Wrong key.', self.user.nick)

    def do_nocam(self, key):
        """
        Toggles if broadcasting is allowed or not.
        NOTE: Mods or bot controllers will have to provide a key, owner does not.
        :param key: str secret key.
        """
        if self.is_broadcasting_allowed:
            if self.user.is_owner or self.user.is_super:
                self.is_broadcasting_allowed = False
                self.send_private_msg('*Broadcasting is NOT allowed.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user.nick)
                elif key == self.key:
                    self.is_broadcasting_allowed = False
                    self.send_private_msg('*Broadcasting is NOT allowed.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)
        else:
            if self.user.is_owner or self.user.is_super:
                self.is_broadcasting_allowed = True
                self.send_private_msg('*Broadcasting is allowed.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user.nick)
                elif key == self.key:
                    self.is_broadcasting_allowed = True
                    self.send_private_msg('*Broadcasting is allowed.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    # TODO: no_normal users mode - only account mode (maybe a toggle for this here?)
    def do_no_guest(self, key):
        """
        Toggles if guests are allowed to join the room or not.
        NOTE: This will kick all guests that join the room, only turn it on if you are sure.
              Mods or bot controllers will have to provide a key, the owner does not.
        :param key: str secret key.
        """
        if self.is_guest_entry_allowed:
            if self.user.is_owner or self.user.is_super:
                self.is_guest_entry_allowed = False
                self.send_private_msg('*Guests are NOT allowed to join the room.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user.nick)
                elif key == self.key:
                    self.is_guest_entry_allowed = False
                    self.send_private_msg('*Guests are NOT allowed to join the room.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)
        else:
            if self.user.is_owner or self.user.is_super:
                self.is_guest_entry_allowed = True
                self.send_private_msg('*Guests ARE allowed to join the room.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('Missing key.', self.user.nick)
                elif key == self.key:
                    self.is_guest_entry_allowed = True
                    self.send_private_msg('*Guests ARE allowed to join the room.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    def do_public_cmds(self, key):
        """
        Toggles if public commands are public or not.
        NOTE: Mods or bot controllers will have to provide a key, owner and super does not.
        :param key: str secret key.
        """
        if self.is_cmds_public:
            if self.user.is_owner or self.user.is_super:
                self.is_cmds_public = False
                self.send_private_msg('*Public commands are disabled.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('missing key.', self.user.nick)
                elif key == self.key:
                    self.is_cmds_public = False
                    self.send_private_msg('*Public commands are disabled.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)
        else:
            if self.user.is_owner or self.user.is_super:
                self.is_cmds_public = True
                self.send_private_msg('*Public commands are enabled.*', self.user.nick)
            elif self.user.is_mod or self.user.has_power:
                if len(key) is 0:
                    self.send_private_msg('missing key.', self.user.nick)
                elif key == self.key:
                    self.is_cmds_public = True
                    self.send_private_msg('*Public commands are enabled.*', self.user.nick)
                else:
                    self.send_private_msg('Wrong key.', self.user.nick)

    def do_set_auto_pm(self, message):
        """
        Allows for owners/moderators/botters to change the room private message.
        :param message: str the new private message to be sent automatically to everyone upon entering the room.
        """
        if self.user.is_mod or self.user.has_power or self.user.is_owner:
            if self.auto_pm:
                if len(message) is 0:
                    self.send_private_msg('Please enter a new Room Private Message.', self.user.nick)
                else:
                    self.pm_msg = message
                    self.send_private_msg('Room private message now set to: ' + self.pm_msg, self.user.nick)
            else:
                self.send_private_msg('Automatic private message feature is not enabled in the configuration.',
                                      self.user.nick)

    # == Public PM Command Methods. ==
    def do_super_user(self, super_key):
        """
        Makes a user super mod, the highest level of mod.
        It is only possible to be a super mod if the client is owner.
        :param super_key: str the super key.
        """
        if self._is_client_owner:
            if len(super_key) is 0:
                self.send_private_msg('Missing super key.', self.user.nick)
            elif super_key == CONFIG['super_key']:
                self.user.is_super = True
                self.send_private_msg('*You are now a super mod.*', self.user.nick)
            else:
                self.send_private_msg('Wrong super key.', self.user.nick)
        else:
            self.send_private_msg('Client is owner: *' + str(self._is_client_owner) + '*', self.user.nick)

    def do_opme(self, key):
        """
        Makes a user a bot controller if user provides the right key.
        :param key: str the secret key.
        """
        if self.user.has_power:
            self.send_private_msg('You already have privileges. No need to OP again.', self.user.nick)
        else:
            if len(key) is 0:
                self.send_private_msg('Missing key.', self.user.nick)
            elif key == self.key:
                self.user.has_power = True
                self.send_private_msg('You are now a bot controller.', self.user.nick)
            else:
                self.send_private_msg('Wrong key.', self.user.nick)

    def do_pm_bridge(self, pm_parts):
        """
        Makes the bot work as a PM message bridge between two users who are not signed in.
        :param pm_parts: list the pm message as a list.
        """
        if len(pm_parts) == 1:
            self.send_private_msg('Missing username.', self.user.nick)
        elif len(pm_parts) == 2:
            self.send_private_msg('The command is: ' + CONFIG['prefix'] + 'pm username message', self.user.nick)
        elif len(pm_parts) >= 3:
            pm_to = pm_parts[1]
            msg = ' '.join(pm_parts[2:])
            is_user = self.find_user_info(pm_to)
            if is_user is not None:
                if is_user.id == self._client_id:
                    self.send_private_msg('Action not allowed.', self.user.nick)
                else:
                    self.send_private_msg('*<' + self.user.nick + '>* ' + msg, pm_to)
            else:
                self.send_private_msg('No user named: ' + pm_to, self.user.nick)

    # Timed auto functions.
    def media_event_handler(self):
        """ This method gets called whenever a media is done playing. """
        if len(self.media_manager.track_list) > 0:
            if self.media_manager.is_last_track():
                self.media_manager.clear_track_list()
            else:
                pinylib.time.sleep(self.playback_delay)
                track = self.media_manager.get_next_track()
                if track is not None and self.is_connected:
                    self.send_media_broadcast_start(track.type, track.id)
                self.media_event_timer(track.time)

                # TODO: If the track was a media request, then state who it was from.
                # Handle media request notices.
                if track.was_request:
                    self.send_bot_msg(unicode_catalog.ARROW_SIDEWAYS +
                                      ' This was a *media request* submitted by *%s*.' % track.nick)

    def media_event_timer(self, video_time):
        """
        Set of a timed event thread.
        :param video_time: int the time in milliseconds.
        """
        video_time_in_seconds = video_time / 1000
        self.media_timer_thread = threading.Timer(video_time_in_seconds, self.media_event_handler)
        self.media_timer_thread.start()

    def cancel_media_event_timer(self):
        """
        Cancel the media event timer if it is running.
        :return: True if canceled, else False
        """
        if self.media_timer_thread is not None and self.media_timer_thread.is_alive():
            self.media_timer_thread.cancel()
            self.media_timer_thread = None
            return True
        return False

    def random_msg(self):
        """
        Pick a random message from a list of messages.
        :return: str random message.
        """
        upnext = 'Use *' + CONFIG['prefix'] + 'yt* youtube title, link or id to add or play youtube.'
        plstat = 'Use *' + CONFIG['prefix'] + 'sc* soundcloud title or id to add or play soundcloud.'
        if self.media_manager.is_last_track() is not None and not self.media_manager.is_last_track():
            pos, next_track = self.media_manager.next_track_info()
            if next_track is not None:
                next_video_time = self.format_time(next_track.time)
                upnext = '*Next is:* (' + str(pos) + ') *' + next_track.title + '* ' + next_video_time
            queue = self.media_manager.queue()
            plstat = str(queue[0]) + ' *items in the playlist.* ' + str(queue[1]) + ' *Still in queue.*'

        messages = ['Reporting for duty..', 'Hello, is anyone here?', 'Awaiting command..', 'Observing behavior..',
                    upnext, plstat, '*I have been connected for:* ' + self.format_time(self.get_runtime()),
                    'Everyone alright?', 'What\'s everyone up to?',
                    'How is the weather where everyone is?', 'Why is everyone so quiet?',
                    'Anything in particular going on?',
                    'Type: *' + CONFIG['prefix'] + 'help* for a list of commands',
                    'Anything interesting in the news lately?']

        return random.choice(messages)

    def auto_msg_handler(self):
        """ The event handler for auto_msg_timer. """
        if self.is_connected:
            if CONFIG['auto_message_enabled']:
                self.send_bot_msg(self.random_msg(), use_chat_msg=True)
        self.start_auto_msg_timer()

    def start_auto_msg_timer(self):
        """
        In rooms with less activity, it can be useful to have the client send auto messages to keep the client alive.
        This method can be disabled by setting CONFIG['auto_message_sender'] to False.
        The interval for when a message should be sent, is set in CONFIG['auto_message_interval']
        """
        threading.Timer(CONFIG['auto_message_interval'], self.auto_msg_handler).start()

    def do_auto_url(self, message):
        """
        Retrieve header information for a given link.
        :param message: str complete message by the user.
        """
        if ('http://' in message) or ('https://' in message):
            # TODO: If an exclamation mark is in the URL, will this not proceed?
            if ('!' not in message) and ('tinychat.com' not in message):
                url = None
                if message.startswith('http://'):
                    url = message.split('http://')[1]
                    msgs = url.split(' ')[0]
                    url = auto_url.auto_url('http://' + msgs)

                elif message.startswith('https://'):
                    url = message.split('https://')[1]
                    msgs = url.split(' ')[0]
                    url = auto_url.auto_url('https://' + msgs)

                if url is not None:
                    self.send_bot_msg('*[ ' + url + ' ]*')
                    self.console_write(pinylib.COLOR['cyan'], self.user.nick + ' posted a URL: ' + url)

    # TODO: Added in a timer to monitor the CleverBot session & reset the messages periodically.
    def cleverbot_timer(self):
        """
        Start clearing POST data by checking if messages are sent to CleverBot within
        every 2.5 minutes (150 seconds), otherwise clear all the data that was previously recorded.
        NOTE: Anything as a result asked before that to CleverBot may reply with an inaccurate reply.
        """
        while self.cleverbot_session is not None:
            # Reset the POST log in CleverBot to an empty list to clear the previous message history if the time is
            # 5 minutes or over and messages have been sent in the log.
            if int(pinylib.time.time()) - self.cleverbot_msg_time >= 150 and \
                            len(self.cleverbot_session.post_log) is not 0:
                self.cleverbot_session.post_log = []
                self.cleverbot_msg_time = int(pinylib.time.time())
            pinylib.time.sleep(1)

    # Helper Methods.
    def get_privacy_settings(self):
        """ Parse the privacy settings page. """
        log.info('Parsing %s\'s privacy page. Proxy %s' % (self.account, self._proxy))
        self.privacy_settings = privacy_settings.TinychatPrivacyPage(self._proxy)
        self.privacy_settings.parse_privacy_settings()

    # TODO: Setup database and place all files in there.
    def config_path(self):
        """ Returns the path to the rooms configuration directory. """
        path = pinylib.CONFIG['config_path'] + self._roomname + '/'
        return path

    @staticmethod
    def format_time(milliseconds):
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
            formatted_time = '%02d:%02d' % (m, s)
        elif d == 0:
            formatted_time = '%d:%02d:%02d' % (h, m, s)
        else:
            formatted_time = '%d Day(s) %d:%02d:%02d' % (d, h, m, s)
        return formatted_time

    def sanitize_message(self, msg_sender, raw_msg):
        """
        Spam checks to ensure chat box is rid any potential further spam.
        :param msg_sender: str the nick name of the message sender.
        :param raw_msg: str the message the user sent.
        """
        # Reset the spam check at each message check, this allows us to know if the message should be passed onto
        # any further procedures.
        user = self.find_user_info(msg_sender)

        # Always check to see if the user's message has any bad strings initially.
        if self.check_bad_string:
            check = self.check_msg_for_bad_string(raw_msg)
            if check:
                return True

        # TODO: Test to see if this works or not.
        # The unicode characters UTF-16 decimal representation.
        # spam_chars = [',133', ',8192', ',10', ',9650']
        #
        # # Ban those who post messages with special unicode characters which is considered spam.
        # if self.unicode_spam:
        #     for spam_decimal in range(len(spam_chars)):
        #         # unicode_msg = decoded_msg.decode('utf-8')
        #         if raw_msg.find(spam_chars[spam_decimal]) >= 0:
        #             if self._is_client_mod:
        #                 # self.send_ban_msg(user.nick, user.id)
        #             return True

        # Ban those who post excessive messages in both uppercase and exceeding a specified character limit.
        if self.message_caps_limit:
            # if len(raw_msg) >= self.caps_char_limit:
            # Search for all caps and numbers in the message which exceed the length of the characters stated in
            # the character limit.
            # TODO: Test if character limit regex works or not: r'[A-Z+0-9+\W+]{50,}' OR [A-Z0-9]
            # regex_pattern = r'[A-Z0-9\W+]{%s,}' % self.caps_char_limit
            over_limit = self.character_limit_pattern.search(raw_msg)
            if over_limit:
                # if self._is_client_mod:
                    # self.send_ban_msg(user.nick, user.id)
                    # if CONFIG['caps_char_forgive']:
                    #     self.send_forgive_msg(user.id)
                return True

        # Kick/ban those who post links to other rooms.
        if self.room_link_spam:
            if 'tinychat.com/' + self._roomname not in raw_msg:
                # TODO: Regex does not handle carriage returns after the string - Added more regex to handle
                #       line feed, whitespaces and various possible ways of the URL displaying (and on multiple lines).
                #       any characters after it. Previous: r'tinychat.com\/\w+($| |\/+ |\/+$)'
                #       Now: r'tinychat.com\/\w+|tinychat. com\/\w+|tinychat .com\/\w+($| |\/+ |\/+$|\n+)\s'

                # Perform case-insensitive matching on the strings matching/similar to 'tinychat.com'.
                msg_search = self.tinychat_spam_pattern.search(raw_msg)
                if msg_search:
                    # if self._is_client_mod:
                        # self.send_ban_msg(user.nick, user.id)
                    return True

        # If snapshot prevention is on, make sure we kick/ban any user taking snapshots in the room.
        if self.snapshot_spam:
            if self.snap_line in raw_msg:
                # if self._is_client_mod:
                #     self.send_ban_msg(user.nick, user.id)
                    # Remove next line to keep ban.
                    # self.send_forgive_msg(user.id)
                return True

    def check_msg_for_bad_string(self, msg, pm=False):
        """
        Checks the chat message for bad string(s).
        :param msg: str the chat message.
        :param pm: boolean true/false if the check is from a private message or not.
        """
        msg_words = msg.split(' ')
        bad_strings = pinylib.fh.file_reader(self.config_path(), CONFIG['ban_strings'])
        if bad_strings is not None:
            for word in msg_words:
                if word in bad_strings:
                    if self._is_client_mod:
                        self.send_ban_msg(self.user.nick, self.user.id)
                        if CONFIG['bsforgive']:
                            self.send_forgive_msg(self.user.id)
                        if not pm:
                            self.send_bot_msg(unicode_catalog.TOXIC + ' *Auto-banned*: (bad string in message)')
                    return True
            return False

            # TODO: Add custom allocations for 'replacement variables'.

    # TODO: This is not tidy.
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
                user = self.user.nick
            if room is None:
                room = self._roomname
            message = message.replace('%user%', user).replace('%room%', room)
        return message

    # TODO: This is not tidy.
    def connection_info(self):
        """ Prints connection information into the console. """
        print('\n** Connection Information **')
        print('- Room Embed URL: %s, Room name: %s' % (self._embed_url, self._roomname))
        print('- RTMP Information:')
        print('  IP: %s, PORT: %s, Proxy: %s, RTMP URL: %s, Application: %s' %
              (self._ip, self._port, self._proxy, self._tc_url, self._app))
        print('  SWF (Desktop) Version: %s, SWF URL: %s' % (self._desktop_version, self._swf_url))
        print ('- Tinychat Room Information:')
        print('  Nickname: %s, ID: %s, Account: %s' % (self.client_nick, self._client_id, self.account))
        print('  Type: %s, Greenroom: %s, Room password: %s, Room broadcasting password: %s\n' %
              (self._room_type, self._greenroom, self.room_pass, self._b_password))


def main():
    if CONFIG['auto_connect']:
        room_name = CONFIG['room']
        nickname = CONFIG['nick']
        room_password = CONFIG['room_password']
        login_account = CONFIG['account']
        login_password = CONFIG['account_password']

        if len(room_name) is 0:
            print('The ROOM name is empty in the configuration. You can configure this in %s if you have '
                  '\'auto_connect\' enabled.' % CONFIG_FILE_NAME)
            # Exit to system safely whilst returning exit code 1.
            sys.exit(1)
    else:
        # Assign basic login variables.
        room_name = raw_input('Enter room name: ')

        while len(room_name) is 0:
            console_utili.clear_console()
            print('Please enter a ROOM name to continue.')
            room_name = raw_input('Enter room name: ')

        room_password = pinylib.getpass.getpass('Enter room password (optional:password hidden): ')
        nickname = 'pinybot'
        # nickname = raw_input('Enter nick name (optional): ')
        login_account = raw_input('Login account (optional): ')
        login_password = pinylib.getpass.getpass('Login password (optional:password hidden): ')
        console_utili.clear_console()

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

    # TODO: Removed alive.
    # Ping request thread management:
    threading.Thread(target=client.send_ping_request)
    client.console_write(pinylib.COLOR['white'], 'Started ping management.')

    if not CONFIG['server']:
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
                private_message_nick = raw_input('\nNick to Private Message: ')
                private_message = raw_input('\nEnter your message: ')
                client.send_private_msg(private_message, private_message_nick)

            elif chat_msg.lower() == '/notifications':
                client.join_quit_notifications = not client.join_quit_notifications
                print('\n** Hiding JOIN/QUIT notifications **')

            else:
                if CONFIG['console_msg_notice']:
                    client.send_bot_msg(chat_msg)
                else:
                    client.send_chat_msg(chat_msg)
                    # Print our chat messages onto the console
                    client.console_write(pinylib.COLOR['cyan'], 'You: ' + chat_msg)
    else:
        while client.is_connected:
            continue

if __name__ == '__main__':
    # TODO: Similar options in the pinylib section in the configuration parser.
    if CONFIG['debug_to_file']:
        formatter = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        logging.basicConfig(filename=CONFIG['debug_file_name'], level=logging.DEBUG, format=formatter)
        log.info('Starting pinybot.py version: %s' % __version__)
    else:
        log.addHandler(logging.NullHandler())
    main()
