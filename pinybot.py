# -*- coding: utf-8 -*-
"""
pinybot

EDITED from: tinybot by nortxort (https://github.com/nortxort/tinybot)
"""

import sys
import logging
import re
import threading

import pinylib
import util.media_manager
from util import auto_url, unicode_catalog, tag_handler
from page import privacy
from apis import youtube, soundcloud, lastfm, other, locals_


__base_version__ = '6.1.0'
__version__ = '1.5.0'
__version_name__ = 'Sunlight'
__status__ = 'beta.3'
__authors_information__ = 'Nortxort (https://github.com/nortxort/tinybot ) GoelBiju ' \
                          '(https://github.com/GoelBiju/pinybot )'

log = logging.getLogger(__name__)

# TODO: Replace CleverBot with cleverwrap - https://github.com/edwardslabs/cleverwrap.py.
# TODO: Public mode layout in message handler.
# TODO: Unicode symbols back in yt and sc commands when adding to playlist.


class TinychatBot(pinylib.TinychatRTMPClient):
    """ The main bot instance which inherits the TinychatRTMPClient from pinylib. """

    privacy_settings = None

    # Small broadcasting:
    _tinychat_logo_flv = 'util/resources/tinychat_logo.flv'
    _logo_publishing = False
    _logo_to_user = False

    # Media event variables:
    media = util.media_manager.MediaManager()
    media_timer_thread = None
    media_delay = 2.0

    # Media control variables:
    search_list = []
    is_search_list_youtube_playlist = False

    # TODO: Figure out what this does.
    is_broadcasting = False

    # Custom media event variables:
    radio_timer_thread = None
    latest_radio_track = None
    similar_radio_tracks = 0
    # media_request = {}
    # _syncing = False

    # Custom message variables:
    # TODO: Implement !ytlast.
    latest_yt_video_id = str

    # Initiate CleverBot related variables:
    # _cleverbot_session = None
    # _cleverbot_msg_time = int(pinylib.time.time())

    # Compile regex patterns for use later:
    _automatic_url_identifier_pattern = re.compile(r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-'
                                                   r']*[\w@?^=%&/~+#-])?', re.IGNORECASE)
    _tinychat_spam_pattern = re.compile(r'tinychat.com\/\w+|tinychat. com\/\w+|tinychat .com\/\w+($| |\/+ |\/+$|\n+)\s',
                                        re.IGNORECASE)
    _youtube_pattern = re.compile(r'http(?:s*):\/\/(?:www\.youtube|youtu)\.\w+(?:\/watch\?v=|\/)(.{11})', re.IGNORECASE)
    _character_limit_pattern = re.compile(r'(\s*[A-Z0-9]){%r,}' % pinylib.CONFIG.B_CAPITAL_CHARACTER_LIMIT_LENGTH)

    # Message sanitation variables:
    _snapshot_message = 'I just took a video snapshot of this chatroom. Check it out here:'

    # Automatically setting the media to work on playlist mode if public media has been enabled.
    if pinylib.CONFIG.B_PUBLIC_MEDIA_MODE:
        pinylib.CONFIG.B_PLAYLIST_MODE = True

    def on_join(self, join_info):
        """ Application message received when a user joins the room.

        :param join_info: Information about the user joining.
        :type join_info: dict
        """
        log.info('user join info: %s' % join_info)
        _user = self.users.add(join_info)

        if _user is not None:
            if _user.account:
                tc_info = pinylib.apis.tinychat.user_info(_user.account)
                if tc_info is not None:
                    _user.tinychat_id = tc_info['tinychat_id']
                    _user.last_login = tc_info['last_active']

                # TODO: 1.5.0 - Modified to add in to optionally show joins information (this can be changed in the
                #       configuration file).
                if _user.is_owner:
                    _user.user_level = 1
                    if pinylib.CONFIG.ROOM_EVENT_INFORMATION:
                        self.console_write(pinylib.COLOR['red'], 'Room Owner %s:%d:%s' %
                                           (_user.nick, _user.id, _user.account))
                elif _user.is_mod:
                    _user.user_level = 3
                    if pinylib.CONFIG.ROOM_EVENT_INFORMATION:
                        self.console_write(pinylib.COLOR['bright_red'], 'Moderator %s:%d:%s' %
                                           (_user.nick, _user.id, _user.account))
                else:
                    _user.user_level = 5
                    if pinylib.CONFIG.ROOM_EVENT_INFORMATION:
                        self.console_write(pinylib.COLOR['bright_yellow'], '%s:%d has account: %s' %
                                           (_user.nick, _user.id, _user.account))

                    if _user.account in pinylib.CONFIG.B_ACCOUNT_BANS:
                        if self.is_client_mod:
                            self.send_ban_msg(_user.nick, _user.id)
                            if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                                self.send_forgive_msg(_user.id)
                            self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned:* (bad account)')

            else:
                _user.user_level = 5
                if _user.id is not self._client_id:
                    # Handle entry to users who are have not entered the captcha and are just previewing the room.
                    if _user.lf and not pinylib.CONFIG.B_ALLOW_LURKERS and self.is_client_mod:
                        self.send_ban_msg(_user.nick, _user.id)
                        if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                            self.send_forgive_msg(_user.id)
                        self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned:* (lurkers not allowed)')

                    # Handle entry to users who are only guests.
                    elif not pinylib.CONFIG.B_ALLOW_GUESTS and self.is_client_mod:
                        self.send_ban_msg(_user.nick, _user.id)
                        if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                            self.send_forgive_msg(_user.id)
                        self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned:* (guests not allowed)')
                    else:
                        self.console_write(pinylib.COLOR['cyan'], '%s:%d joined the room.' % (_user.nick, _user.id))

    def on_joinsdone(self, greenroom=False):
        """ Application message received when all room users information have been received.

        :param greenroom: boolean (default: False)
        """
        if not greenroom:
            if self.is_client_mod:
                self.send_banlist_msg()
                self.load_list(nicks=True, accounts=True, strings=True)

            # Handle retrieving the privacy settings information for the room
            # (if the bot is on the room owner's account).
            if self.is_client_owner and self.param.roomtype != 'default':
                threading.Thread(target=self.get_privacy_settings).start()

            self.console_write(pinylib.COLOR['cyan'], 'Received all joins information from the server.')
        else:
            self.console_write(pinylib.COLOR['cyan'], 'Received all greenroom joins information from the server.')

    def on_avon(self, uid, name, greenroom=False):
        """ Application message received when a user starts broadcasting.

        :param uid: The Id of the user.
        :type uid: str
        :param name: The nick name of the user.
        :type name: str
        :param greenroom: True the user is waiting in the greenroom.
        :type greenroom: bool
        """
        if not greenroom:
            _user = self.users.search(name)
            # Set the user waiting to false if the user was already waiting in the greenroom.
            if _user is not None and _user.is_waiting:
                _user.is_waiting = False

            if not pinylib.CONFIG.B_ALLOW_BROADCASTS and self.is_client_mod:
                self.send_close_user_msg(name)
                self.console_write(pinylib.COLOR['cyan'], 'Auto closed broadcast %s:%s' % (name, uid))
            else:
                # TODO: Find the user object using the name.
                # avon_user = self.users.search(name)
                # TODO: Add code into to get the device type on which the user is using to broadcast.

                # Handle auto-closing users which has been set to happen for guests/new users.
                if pinylib.CONFIG.B_AUTO_CLOSE:
                    if name.startswith('newuser'):
                        self.send_close_user_msg(name)
                    elif name.startswith('guest-'):
                        self.send_close_user_msg(name)
                    return

                # Handle welcome messages with a new broadcaster.
                if pinylib.CONFIG.B_GREET_BROADCAST:
                    if len(name) is 2:
                        name = unicode_catalog.NO_WIDTH + name + unicode_catalog.NO_WIDTH

                    # TODO: Send as undercover message as well.
                    if not pinylib.CONFIG.B_GREET_BROADCAST_UNDERCOVER:
                        self.send_bot_msg(unicode_catalog.NOTIFICATION + pinylib.CONFIG.B_GREET_BROADCAST_MESSAGE + '*'
                                          + unicode_catalog.NO_WIDTH + name + unicode_catalog.NO_WIDTH + '*')
                    else:
                        self.send_undercover_msg(name, pinylib.CONFIG.B_GREET_BROADCAST_MESSAGE + '*' +
                                                 unicode_catalog.NO_WIDTH + name + unicode_catalog.NO_WIDTH + '*')

                self.console_write(pinylib.COLOR['cyan'], '%s:%s is broadcasting.' % (name, uid))
        else:
            _greenroom_user = self.users.search_by_id(uid)
            if _greenroom_user is not None:
                _greenroom_user.is_waiting = True
                self.console_write(pinylib.COLOR['bright_green'], '%s:%s is broadcasting in the greenroom; waiting for '
                                                                  'approval.' % (_greenroom_user.nick,
                                                                                 _greenroom_user.id))
                if pinylib.CONFIG.B_AUTO_GREENROOM:
                    self.send_cam_approve_msg(_greenroom_user.nick, _greenroom_user.id)
                    _greenroom_user.is_waiting = False
                    self.send_bot_msg(unicode_catalog.INDICATE_UPWARDS + ' *Automatic Greenroom* broadcast approved: %s'
                                      % _greenroom_user.nick)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE_UPWARDS + ' *Automatic Greenroom*: %s is requesting'
                                                                         ' broadcast approval. You can approve with '
                                                                         '*%s*.' % (_greenroom_user.nick, '!approve ' +
                                                                                    _greenroom_user.nick))
            else:
                # TODO: Move this to on_greenroom_join, if that is possible.
                self.console_write(pinylib.COLOR['bright_red'], 'An unknown user joined the greenroom with id %s and '
                                                                'greenroom id %s.' % (uid, name))
                self.send_bot_msg(unicode_catalog.INDICATE + ' There is an *unknown greenroom user*:'
                                                             ' *%s*:%s (*user id*:greenroom id)' % (uid, name))

    def on_nick(self, old, new, uid):
        """ Application message received when a user changes nick name.

        :param old: The old nick name of the user.
        :type old: str
        :param new: The new nick name of the user
        :type new: str
        :param uid: The Id of the user.
        :type uid: int
        """
        if uid == self._client_id:
            self.nickname = new
            self.console_write(pinylib.COLOR['bright_cyan'],
                               'Received confirmation of setting client nickname. Set to: %s' % self.nickname)
        old_info = self.users.search(old)
        old_info.nick = new
        if not self.users.change(old, new, old_info):
            log.error('failed to change nick for user: %s' % new)
        if self.check_nick(old, old_info):
            if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                self.send_forgive_msg(uid)
        elif uid != self._client_id:
            # TODO: Send as undercover message as well.
            if self.is_client_mod and pinylib.CONFIG.B_GREET:
                if old_info.account:
                    if len(pinylib.CONFIG.B_GREET_MESSAGE) is 0:
                        if not pinylib.CONFIG.B_GREET_UNDERCOVER:
                            self.send_bot_msg(unicode_catalog.NOTIFICATION + '*Welcome* %s:%s:%s' %
                                              (new, uid, old_info.account))
                        else:
                            self.send_undercover_msg(new, '*Welcome %s:%s:%s' % (new, uid, old_info.account))
                    else:
                        # TODO: Add in replace content method here to allow the custom message
                        #      {user} and {roomname} information to be placed into the string.
                        if not pinylib.CONFIG.B_GREET_UNDERCOVER:
                            self.send_bot_msg(unicode_catalog.NOTIFICATION + pinylib.CONFIG.B_GREET_MESSAGE)
                        else:
                            self.send_undercover_msg(new, pinylib.CONFIG.B_GREET_MESSAGE)
                else:
                    if not pinylib.CONFIG.B_GREET_UNDERCOVER:
                        self.send_bot_msg('*Welcome* %s:%s' % (new, uid))
                    else:
                        self.send_undercover_msg(new, '*Welcome* %s:%s' % (new, uid))

            if self.media.has_active_track():
                if not self.media.is_mod_playing:
                    self.send_media_broadcast_start(self.media.track().type,
                                                    self.media.track().id,
                                                    time_point=self.media.elapsed_track_time(),
                                                    private_nick=new)

        # TODO: Additional functions.
        # TODO: Add the AUTO PM function.
        # if pinylib.CONFIG.B_GREET_PRIVATE:
        #     self.send_auto_pm(new)
        if self._logo_publishing:
            self._logo_to_user = True

        self.console_write(pinylib.COLOR['bright_cyan'], '%s:%s changed nick to: %s' % (old, uid, new))

    # TODO: We could add in the do_kick, do_quit functions here and tidy_exit for botters, botteraccounts
    #       and blocked broadcasts.

    # TODO: Do the docstring for this function.
    def on_reported(self, nick, uid):
        """
        Overrides handling the 'reported' private message when a user reports the client.
        :param nick: str the nickname of the user who reported the bot.
        :param uid: str the user id of the user in the room.
        """
        self.console_write(pinylib.COLOR['bright_red'], 'You were reported by: %s:%s' % (nick, uid))
        if pinylib.CONFIG.B_BOT_REPORT_KICK:
            self.send_ban_msg(nick, uid)
            self.send_bot_msg('*Auto-Banned*: (reporting bot)')
            if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                self.send_forgive_msg(uid)

    # Media Events.
    def on_media_broadcast_start(self, media_type, video_id, usr_nick):
        """ A user started a media broadcast.

        :param media_type: The type of media. youTube or soundCloud.
        :type media_type: str
        :param video_id: The youtube ID or souncloud trackID.
        :type video_id: str
        :param usr_nick: The user name of the user playing media.
        :type usr_nick: str
        """
        self.cancel_media_event_timer()

        if media_type == 'youTube':
            _youtube = youtube.video_details(video_id, check=False)
            if _youtube is not None:
                self.media.mb_start(self.active_user.nick, _youtube)

        elif media_type == 'soundCloud':
            _soundcloud = soundcloud.track_info(video_id)
            if _soundcloud is not None:
                self.media.mb_start(self.active_user.nick, _soundcloud)

        self.media_event_timer(self.media.track().time)
        self.console_write(pinylib.COLOR['bright_magenta'], '%s is playing %s %s' %
                           (usr_nick, media_type, video_id))

    def on_media_broadcast_close(self, media_type, usr_nick):
        """ A user closed a media broadcast.

        :param media_type: The type of media. youTube or soundCloud.
        :type media_type: str
        :param usr_nick: The user name of the user closing the media.
        :type usr_nick: str
        """
        self.cancel_media_event_timer()
        self.media.mb_close()
        self.console_write(pinylib.COLOR['bright_magenta'], '%s closed the %s' % (usr_nick, media_type))

    def on_media_broadcast_paused(self, media_type, usr_nick):
        """ A user paused the media broadcast.

        :param media_type: The type of media being paused. youTube or soundCloud.
        :type media_type: str
        :param usr_nick: The user name of the user pausing the media.
        :type usr_nick: str
        """
        self.cancel_media_event_timer()
        self.media.mb_pause()
        self.console_write(pinylib.COLOR['bright_magenta'], '%s paused the %s' % (usr_nick, media_type))

    def on_media_broadcast_play(self, media_type, time_point, usr_nick):
        """ A user resumed playing a media broadcast.

        :param media_type: The media type. youTube or soundCloud.
        :type media_type: str
        :param time_point: The time point in the tune in milliseconds.
        :type time_point: int
        :param usr_nick: The user resuming the tune.
        :type usr_nick: str
        """
        self.cancel_media_event_timer()
        new_media_time = self.media.mb_play(time_point)
        self.media_event_timer(new_media_time)

        self.console_write(pinylib.COLOR['bright_magenta'], '%s resumed the %s at: %s' %
                           (usr_nick, media_type, self.format_time(time_point)))

    def on_media_broadcast_skip(self, media_type, time_point, usr_nick):
        """ A user time searched a tune.

        :param media_type: The media type. youTube or soundCloud.
        :type media_type: str
        :param time_point: The time point in the tune in milliseconds.
        :type time_point: int
        :param usr_nick: The user time searching the tune.
        :type usr_nick: str
        """
        self.cancel_media_event_timer()
        new_media_time = self.media.mb_skip(time_point)
        if not self.media.is_paused:
            self.media_event_timer(new_media_time)

        self.console_write(pinylib.COLOR['bright_magenta'], '%s time searched the %s at: %s' %
                           (usr_nick, media_type, self.format_time(time_point)))

    # Media Message Method.
    # def send_media_broadcast_start(self, media_type, video_id, time_point=0, private_nick=None):
    #     """
    #     Starts a media broadcast.
    #     :param media_type: str 'youTube' or 'soundCloud'
    #     :param video_id: str the media video ID.
    #     :param time_point: int where to start the media from in milliseconds.
    #     :param private_nick: str if not None, start the media broadcast for this username only.
    #     """
    #     mbs_msg = '/mbs %s %s %s' % (media_type, video_id, time_point)
    #     if private_nick is not None:
    #         self.send_undercover_msg(private_nick, mbs_msg)
    #     else:
    #         self.send_chat_msg(mbs_msg)

    # Message Method.
    def send_bot_msg(self, msg, use_chat_msg=False):
        """ Send a chat message to the room.

        NOTE: If the client is moderator, send_owner_run_msg will be used.
        If the client is not a moderator, send_chat_msg will be used.
        Setting use_chat_msg to True, forces send_chat_msg to be used.

        :param msg: The message to send.
        :type msg: str
        :param use_chat_msg: True, use normal chat messages,
        False, send messages depending on weather or not the client is mod.
        :type use_chat_msg: bool
        """
        if use_chat_msg:
            self.send_chat_msg(msg)
        else:
            if self.is_client_mod:
                self.send_owner_run_msg(msg)
            else:
                self.send_chat_msg(msg)

    # Command Handler.
    def message_handler(self, decoded_msg):
        """ Message handler.

        :param decoded_msg: The decoded message (text).
        :type decoded_msg: str
        """
        # Spam checks to prevent any text from spamming the room chat and being parsed by the bot.
        spam_potential = False
        if self.is_client_mod:
            if pinylib.CONFIG.B_SANITIZE_MESSAGES and self.active_user.user_level > 4:
                # Start sanitizing the message.
                spam_potential = self.sanitize_message(decoded_msg)
                # TODO: See spam potential without being a moderator, to reduce spam in console(?)

        # Make sure we check if there is no spam going through to the commands before we parse it.
        if not spam_potential:
            # Retrieve the command prefix we are using.
            prefix = pinylib.CONFIG.B_PREFIX
            # Is this a custom command?
            if decoded_msg.startswith(prefix):
                # Split the message in to parts.
                parts = decoded_msg.split(' ')
                # parts[0] is the command.
                cmd = parts[0].lower().strip()
                # The rest is a command argument.
                cmd_arg = ' '.join(parts[1:]).strip()

                # Owner and super mod commands.
                if self.has_level(1):

                    # Only possible if bot is using the room owner account.
                    if self.is_client_owner:

                        if cmd == prefix + 'mod':
                            threading.Thread(target=self.do_make_mod, args=(cmd_arg,)).start()

                        elif cmd == prefix + 'rmod':
                            threading.Thread(target=self.do_remove_mod, args=(cmd_arg,)).start()

                        elif cmd == prefix + 'dir':
                            threading.Thread(target=self.do_directory).start()

                        elif cmd == prefix + 'p2t':
                            threading.Thread(target=self.do_push2talk).start()

                        elif cmd == prefix + 'gr':
                            threading.Thread(target=self.do_green_room).start()

                        elif cmd == prefix + 'crb':
                            threading.Thread(target=self.do_clear_room_bans).start()

                    if cmd == prefix + 'kill':
                        self.do_kill()

                    elif cmd == prefix + 'reboot':
                        self.do_reboot()

                # Bot controller commands.
                if self.has_level(2):

                    if cmd == prefix + 'mi':
                        self.do_media_info()

                # Mod commands.
                if self.has_level(3):

                    if cmd == prefix + 'botter':  # op
                        self.do_op_user(cmd_arg)

                    elif cmd == prefix + 'rmbotter':  # deop
                        self.do_deop_user(cmd_arg)

                    # elif cmd == prefix + 'up':
                    #     print('got request')
                    #     self.do_cam_up()
                    #
                    # elif cmd == prefix + 'logo':
                    #     threading.Thread(target=self.do_cam_logo).start()
                    #
                    # elif cmd == prefix + 'down':
                    #     self.do_cam_down()

                    elif cmd == prefix + 'nocam':
                        self.do_nocam()

                    elif cmd == prefix + 'noguest':
                        self.do_guests()

                    elif cmd == prefix + 'lurkers':
                        self.do_lurkers()

                    elif cmd == prefix + 'guestnick':
                        self.do_guest_nicks()

                    elif cmd == prefix + 'newusers':
                        self.do_newusers()

                    elif cmd == prefix + 'greet':
                        self.do_greet()

                    elif cmd == prefix + 'pub':
                        self.do_public_cmds()

                    if cmd == prefix + 'rs':
                        self.do_room_settings()

                    elif cmd == prefix + 'top':
                        threading.Thread(target=self.do_lastfm_chart, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'ran':
                        threading.Thread(target=self.do_lastfm_random_tunes, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'tag':
                        threading.Thread(target=self.do_search_lastfm_by_tag, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'pls':
                        threading.Thread(target=self.do_youtube_playlist_search, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'plp':
                        threading.Thread(target=self.do_play_youtube_playlist, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'ssl':
                        self.do_show_search_list()

                if self.has_level(4):

                    if cmd == prefix + 'close':
                        self.do_close_broadcast(cmd_arg)

                    # TODO: This was not working or has issues.
                    # elif cmd == prefix + 'clr':
                    #     self.do_clear()

                    elif cmd == prefix + 'skip':
                        self.do_skip()

                    elif cmd == prefix + 'del':
                        self.do_delete_playlist_item(cmd_arg)

                    elif cmd == prefix + 'replay':  # rpl
                        self.do_media_replay()

                    elif cmd == prefix + 'resume':  # mbpl
                        self.do_play_media()

                    elif cmd == prefix + 'pause':  # mbpa
                        self.do_media_pause()

                    elif cmd == prefix + 'seek':
                        self.do_seek_media(cmd_arg)

                    elif cmd == prefix + 'stop':  # cm
                        self.do_close_media()

                    elif cmd == prefix + 'cpl':
                        self.do_clear_playlist()

                    elif cmd == prefix + 'spl':
                        self.do_playlist_info()

                    elif cmd == prefix + 'nick':
                        self.do_nick(cmd_arg)

                    elif cmd == prefix + 'topic':
                        self.do_topic(cmd_arg)

                    elif cmd == prefix + 'kick':
                        threading.Thread(target=self.do_kick, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'ban':
                        threading.Thread(target=self.do_ban, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'bn':
                        self.do_bad_nick(cmd_arg)

                    elif cmd == prefix + 'rmbn':
                        self.do_remove_bad_nick(cmd_arg)

                    elif cmd == prefix + 'bs':
                        self.do_bad_string(cmd_arg)

                    elif cmd == prefix + 'rmbs':
                        self.do_remove_bad_string(cmd_arg)

                    elif cmd == prefix + 'ba':
                        self.do_bad_account(cmd_arg)

                    elif cmd == prefix + 'rmba':
                        self.do_remove_bad_account(cmd_arg)

                    elif cmd == prefix + 'list':
                        self.do_list_info(cmd_arg)

                    elif cmd == prefix + 'uinfo':
                        self.do_user_info(cmd_arg)

                    elif cmd == prefix + 'yts':
                        threading.Thread(target=self.do_youtube_search, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'pyts':
                        self.do_play_youtube_search(cmd_arg)

                    # TODO: Implement greenroom reading information function.
                    elif cmd == prefix + 'approve':  # cam
                        threading.Thread(target=self.do_broadcast_approve, args=(cmd_arg,)).start()

                # Public commands (if enabled).
                if (pinylib.CONFIG.B_PUBLIC_CMD and self.has_level(5)) or self.active_user.user_level < 5:

                    if cmd == prefix + 'fs':
                        self.do_full_screen(cmd_arg)

                    elif cmd == prefix + 'wp':
                        self.do_who_plays()

                    # TODO: Update version information.
                    elif cmd == prefix + 'v':
                        threading.Thread(target=self.do_version).start()

                    elif cmd == prefix + 'help':
                        self.do_help()

                    elif cmd == prefix + 't':  # uptime
                        self.do_uptime()

                    elif cmd == prefix + 'pmme':
                        self.do_pmme()

                    elif cmd == prefix + 'q':
                        self.do_playlist_status()

                    elif cmd == prefix + 'next':  # n
                        self.do_next_tune_in_playlist()

                    elif cmd == prefix + 'now':  # now
                        self.do_now_playing()

                    elif cmd == prefix + 'yt':
                        threading.Thread(target=self.do_play_youtube, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'ytme':  # pyt
                        threading.Thread(target=self.do_play_private_youtube, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'sc':
                        threading.Thread(target=self.do_play_soundcloud, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'scme':  # psc
                        threading.Thread(target=self.do_play_private_soundcloud, args=(cmd_arg,)).start()

                    # Tinychat API commands.
                    elif cmd == prefix + 'spy':
                        threading.Thread(target=self.do_spy, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'acspy':
                        threading.Thread(target=self.do_account_spy, args=(cmd_arg,)).start()

                    # Other API commands.
                    elif cmd == prefix + 'urb':
                        threading.Thread(target=self.do_search_urban_dictionary, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'wea':
                        threading.Thread(target=self.do_worldwide_weather_search, args=(cmd_arg,)).start()

                    elif cmd == prefix + 'ip':
                        threading.Thread(target=self.do_who_is_ip, args=(cmd_arg,)).start()

                    # Just for fun.
                    elif cmd == prefix + 'cn':
                        threading.Thread(target=self.do_chuck_norris).start()

                    elif cmd == prefix + '8ball':
                        self.do_8ball(cmd_arg)

                    elif cmd == prefix + 'roll':
                        self.do_dice()

                    elif cmd == prefix + 'flip':
                        self.do_flip_coin()

                    elif cmd == prefix + 'up':
                        print('got request')
                        self.do_cam_up()

                    elif cmd == prefix + 'logo':
                        threading.Thread(target=self.do_cam_logo).start()

                    elif cmd == prefix + 'down':
                        self.do_cam_down()

                # Handle extra commands if they are not handled by the default ones.
                self.custom_message_handler(cmd, cmd_arg)

                # Print command to console.
                self.console_write(pinylib.COLOR['yellow'], self.active_user.nick + ': ' + cmd + ' ' + cmd_arg)
            else:
                # Start in a new thread the custom chat message handler.
                threading.Thread(target=self.custom_chat_message_handler, args=(decoded_msg,)).start()

                #  Print chat message to console.
                self.console_write(pinylib.COLOR['green'], self.active_user.nick + ': ' + decoded_msg)

            self.active_user.last_msg = decoded_msg

        else:
            self.console_write(pinylib.COLOR['bright_red'], 'Spam inbound - halt handling.')

    # Custom Message Command Handler.
    def custom_message_handler(self, cmd, cmd_arg):
        """
        The custom message handler is where all extra commands that have been added to tinybot/pinybot is to be kept.
        This will include the use of other external API's and basic ones, all new commands should be added here
        and linked to it's function below.

        :param cmd: The command that we received.
        :type cmd: str
        :param cmd_arg: The command argument that we received.
        :type cmd_arg: str
        """
        # print('(Custom message handler) Received command, command argument:', cmd, cmd_arg)
        prefix = pinylib.CONFIG.B_PREFIX

        if self.has_level(1):
            pass

        if self.has_level(2):

            # TODO: Option to toggle sanitizing messages on/off.
            if cmd == prefix + 'sanitize':
                self.do_set_sanitize_message()

            # TODO: Be cautious with this command, we do not really know what it does.
            elif cmd == prefix + 'privateroom':
                self.do_set_private_room()

        if self.has_level(3):

            if cmd == prefix + 'snapshots':
                self.do_set_allow_snapshots()

            # TODO: Re-do this function.
            # elif cmd == prefix + 'camblock':
            #     self.do_camblock(cmd_arg)

            elif cmd == prefix + 'autoclose':
                self.do_set_auto_close()

            elif cmd == prefix + 'mobiles':
                self.do_set_ban_mobiles()

            elif cmd == prefix + 'autogreenroom':
                self.do_set_auto_greenroom()

            elif cmd == prefix + 'selfapproval':
                self.do_set_self_greenroom_approval()

            elif cmd == prefix + 'autourl':
                self.do_set_auto_url_mode()

            # elif cmd == prefix + 'cleverbot':
            #     self.do_set_cleverbot()

            # TODO: Adjust how auto pm works.
            elif cmd == prefix + 'pm':
                self.do_set_greet_pm()

            # TODO: Test this.
            # elif cmd == prefix + 'publiclimit':
            #     self.do_set_media_limit_public()

            # TODO: Test this.
            # elif cmd == prefix + 'playlistlimit':
            #     self.do_set_media_limit_playlist()

            # TODO: Test this.
            # elif cmd == prefix + 'limit':
            #     self.do_media_limit_duration(cmd_arg)

            # TODO: Test this.
            # elif cmd == prefix + 'radio':
            #     self.do_set_radio()

            # TODO: We may not need these functions anymore.
            # elif cmd == prefix + 'pl':
            #     threading.Thread(target=self.do_youtube_playlist_videos, args=(cmd_arg,)).start()

            # elif cmd == prefix + 'plsh':
            #     threading.Thread(target=self.do_youtube_playlist_search, args=(cmd_arg,)).start()

            # elif cmd == prefix + 'pladd':
            #     threading.Thread(target=self.do_youtube_playlist_search_choice, args=(cmd_arg,)).start()

        if self.has_level(4):

            # TODO: Implement this.
            # if cmd == prefix + 'a':
            #     self.do_request_media_accept()

            # TODO: Implement this.
            # elif cmd == prefix + 'd':
            #     self.do_request_media_decline()

            # if cmd == prefix + 'playlist':
            #     self.do_set_playlist_mode()

            # elif cmd == prefix + 'publicmedia':
            #     self.do_set_public_media_mode()

            if cmd == prefix + 'mute':
                self.do_mute()

            elif cmd == prefix + 'p2tnow':
                self.do_instant_push2talk()

            elif cmd == prefix + 'charts':
                threading.Thread(target=self.do_official_charts).start()

            elif cmd == prefix + 'top40':
                threading.Thread(target=self.do_radio_one_top40_charts).start()

            # elif cmd == prefix + 'startradio':
            #     self.do_start_radio_auto_play()

            # elif cmd == prefix + 'stopradio':
            #     self.do_stop_radio_auto_play()

        if (pinylib.CONFIG.B_PUBLIC_CMD and self.has_level(5)) or self.active_user.user_level < 5:

            # if cmd == prefix + 'reqyt':
            #     threading.Thread(target=self.do_media_request, args=(cmd_arg,)).start()

            # elif cmd == prefix + 'reqsc':
            #     threading.Thread(target=self.do_media_request, args=(cmd_arg,)).start()

            # elif cmd == prefix + 'sync':
            #     threading.Thread(target=self.do_sync_media, args=(cmd_arg,)).start()

            # elif cmd == prefix + 'stopme':
            #     threading.Thread(target=self.do_stop_private_media).start()

            if cmd == prefix + 'ddg':
                threading.Thread(target=self.do_duckduckgo_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'imdb':
                threading.Thread(target=self.do_imdb_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'define':
                threading.Thread(target=self.do_definition, args=(cmd_arg,)).start()

            elif cmd == prefix + 'joke':
                threading.Thread(target=self.do_one_liner, args=(cmd_arg,)).start()

            elif cmd == prefix + 'food':
                threading.Thread(target=self.do_food_recipe_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'advice':
                threading.Thread(target=self.do_advice).start()

            # elif cmd == prefix + 'cb':
            #     threading.Thread(target=self.do_cleverbot, args=(cmd_arg,)).start()

            elif cmd == prefix + 'ety':
                threading.Thread(target=self.do_etymology_search, args=(cmd_arg,)).start()

            elif cmd == prefix + 'wunderwea':
                threading.Thread(target=self.do_wunderground_weather_search, args=(cmd_arg,)).start()

        # TODO: No support for unicode/ascii symbols yet.

    def custom_chat_message_handler(self, decoded_msg):
        """
        Handles chat message specific actions. This includes functions to send or store the content of the message
        for use in e.g. auto-url title's or APIs for replying to a message.
        NOTE: APIs do not need to be started in a new thread unless you need to as this function should have
              been originally called from a thread from the message handler.

        :param decoded_msg: The message received from the user.
        :type decoded_msg: str
        """
        url_message = False
        handle_message = decoded_msg.lower()
        # If Auto URL has been switched on, run, in a new the thread, the automatic URL header retrieval.
        # This should only be run in the case that we have message sanitation turned on.
        if pinylib.CONFIG.B_AUTO_URL_MODE:
            url_message = self.do_auto_url(handle_message)

        # If we will be using the last posted YouTube URL, we want to check if the identified URL
        # is one from YouTube or not.
        if pinylib.CONFIG.B_AUTO_YOUTUBE_URL:
            matched_yt_url = self._youtube_pattern.match(handle_message)
            if matched_yt_url is not None:
                self.latest_yt_video_id = matched_yt_url.group(1)

        # TODO: CleverBot will only work now if it is not given a command and the message did not
        #       have a url the message.
        # if pinylib.CONFIG.B_CLEVERBOT:
        #     if not url_message:
        #         self.cleverbot_message_handler(handle_message)

        # TODO: Moved check_msg procedure to the sanitize message procedure.

    def do_make_mod(self, account):
        """ Make a tinychat account a room moderator.

        :param account: The account to make a moderator.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is not 0:
                tc_user = self.privacy_settings.make_moderator(account)
                if tc_user is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' *The account is invalid.*')
                elif not tc_user:
                    self.send_bot_msg('*%s* is already a moderator.' % account)
                elif tc_user:
                    self.send_bot_msg('*%s* was made a room moderator.' % account)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing account name.')

    def do_remove_mod(self, account):
        """ Removes a tinychat account from the moderator list.

        :param account: The account to remove from the moderator list.
        :type account: str
        """
        if self.is_client_owner:
            if len(account) is not 0:
                tc_user = self.privacy_settings.remove_moderator(account)
                if tc_user:
                    self.send_bot_msg('*%s* is no longer a room moderator.' % account)
                elif not tc_user:
                    self.send_bot_msg('*%s* is not a room moderator.' % account)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing account name.')

    def do_directory(self):
        """ Toggles if the room should be shown on the directory. """
        if self.is_client_owner:
            if self.privacy_settings.show_on_directory():
                self.send_bot_msg('*Room IS shown on the directory.*')
            else:
                self.send_bot_msg('*Room is NOT shown on the directory.*')

    def do_push2talk(self):
        """ Toggles if the room should be in push2talk mode. """
        if self.is_client_owner:
            if self.privacy_settings.set_push2talk():
                self.send_bot_msg('*Push2Talk is enabled.*')
            else:
                self.send_bot_msg('*Push2Talk is disabled.*')

    def do_green_room(self):
        """ Toggles if the room should be in greenroom mode. """
        if self.is_client_owner:
            if self.privacy_settings.set_greenroom():
                self.send_bot_msg('*Green room is enabled.*')
            else:
                self.send_bot_msg('*Green room is disabled.*')

    def do_clear_room_bans(self):
        """ Clear all room bans. """
        if self.is_client_owner:
            if self.privacy_settings.clear_bans():
                self.send_bot_msg(unicode_catalog.STATE + ' *All room bans were cleared.*')

    def do_kill(self):
        """ Kills the bot. """
        self.disconnect()
        if self.is_greenroom_connected:
            self.disconnect(greenroom=True)

    def do_reboot(self):
        """ Reboots the bot. """
        self.send_bot_msg(unicode_catalog.RELOAD + ' Reconnecting to *' + self.roomname + '*.')
        if self.is_greenroom_connected:
            self.disconnect(greenroom=True)
        self.reconnect()

    def do_media_info(self):
        """ Shows basic media info. """
        if self.is_client_mod:
            self.send_owner_run_msg('*Playlist Length:* ' + str(len(self.media.track_list)))
            self.send_owner_run_msg('*Track List Index:* ' + str(self.media.track_list_index))
            self.send_owner_run_msg('*Elapsed Track Time:* ' +
                                    self.format_time(self.media.elapsed_track_time()))
            self.send_owner_run_msg('*Active Track:* ' + str(self.media.has_active_track()))
            self.send_owner_run_msg('*Active Threads:* ' + str(threading.active_count()))

    def do_op_user(self, user_name):
        """ Lets the room owner, a mod or a bot controller make another user a bot controller.

        :param user_name: The user to op.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is not 0:
                _user = self.users.search(user_name)
                if _user is not None:
                    _user.user_level = 4
                    self.send_bot_msg(unicode_catalog.BLACK_STAR + ' *%s* is now a bot controller (L4)' % user_name)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: %s' % user_name)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')

    def do_deop_user(self, user_name):
        """ Lets the room owner, a mod or a bot controller remove a user from being a bot controller.

        :param user_name: The user to deop.
        :param user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is not 0:
                _user = self.users.search(user_name)
                if _user is not None:
                    _user.user_level = 5
                    self.send_bot_msg(unicode_catalog.WHITE_STAR + ' *%s* is not a bot controller anymore (L5)' %
                                      user_name)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: %s' % user_name)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')

    def do_cam_up(self):
        """ Makes the bot cam up. """
        print('in cam up')
        if self._camera_published is False:
            self.send_bauth_msg()
            self.connection.createstream()
        else:
            self.send_bot_msg(unicode_catalog.CROSS_MARK + ' *Camera already published*, please close it before '
                                                           'publishing again.')

    def do_cam_logo(self):
        """ Display Tinychat logo when the camera is broadcasting

        CAUTION EXPERIMENTAL: This may stop the connection between Tinychat and your client.
        """
        if self._camera_published is True and not self._logo_publishing:
            pinylib.time.sleep(5)
            self._logo_publishing = True
            _logo_video = open(self._tinychat_logo_flv, 'rb')
            _logo_frames = tag_handler.iterate_frames(_logo_video)
            _logo_video.close()

            self._logo_to_user = True
            while self._camera_published:
                if self._logo_to_user:
                    for x in range(5):
                        for frame in range(len(_logo_frames)):
                            # print([frames[frame][1]])
                            data = bytes(_logo_frames[frame][1])
                            self.connection.transmit_video(data)
                            pinylib.time.sleep(1)
                    self._logo_to_user = False
            self._logo_publishing = False
        # else:
        #     self.send_bot_msg(unicode_catalog.INDICATE + ' *Camera not published*, please publish it before '
        #                                                  'transmitting.')

    def do_cam_down(self):
        """ Makes the bot cam down. """
        if self._camera_published:
            self.connection.closestream()
            self._camera_published = False
        else:
            self.send_bot_msg(unicode_catalog.CROSS_MARK + ' *Camera not published*, publish it in order to close it.')

    def do_nocam(self):
        """ Toggles if broadcasting is allowed or not. """
        pinylib.CONFIG.B_ALLOW_BROADCASTS = not pinylib.CONFIG.B_ALLOW_BROADCASTS
        self.send_bot_msg('*Allow Broadcasts:* %s' % pinylib.CONFIG.B_ALLOW_BROADCASTS)

    def do_guests(self):
        """ Toggles if guests are allowed to join the room or not. """
        pinylib.CONFIG.B_ALLOW_GUESTS = not pinylib.CONFIG.B_ALLOW_GUESTS
        self.send_bot_msg('*Allow Guests:* %s' % pinylib.CONFIG.B_ALLOW_GUESTS)

    def do_lurkers(self):
        """ Toggles if lurkers are allowed or not. """
        pinylib.CONFIG.B_ALLOW_LURKERS = not pinylib.CONFIG.B_ALLOW_LURKERS
        self.send_bot_msg('*Allow Lurkers:* %s' % pinylib.CONFIG.B_ALLOW_LURKERS)

    def do_guest_nicks(self):
        """ Toggles if guest nicks are allowed or not. """
        pinylib.CONFIG.B_ALLOW_GUESTS_NICKS = not pinylib.CONFIG.B_ALLOW_GUESTS_NICKS
        self.send_bot_msg('*Allow Guest Nicks:* %s' % pinylib.CONFIG.B_ALLOW_GUESTS_NICKS)

    def do_newusers(self):
        """ Toggles if newusers are allowed to join the room or not. """
        pinylib.CONFIG.B_ALLOW_NEWUSERS = not pinylib.CONFIG.B_ALLOW_NEWUSERS
        self.send_bot_msg('*Allow Newusers:* %s' % pinylib.CONFIG.B_ALLOW_NEWUSERS)

    def do_greet(self):
        """ Toggles if users should be greeted on entry. """
        pinylib.CONFIG.B_GREET = not pinylib.CONFIG.B_GREET
        self.send_bot_msg('*Greet Users:* %s' % pinylib.CONFIG.B_GREET)

    def do_public_cmds(self):
        """ Toggles if public commands are public or not. """
        pinylib.CONFIG.B_PUBLIC_CMD = not pinylib.CONFIG.B_PUBLIC_CMD
        self.send_bot_msg('*Public Commands Enabled:* %s' % pinylib.CONFIG.B_PUBLIC_CMD)

    def do_room_settings(self):
        """ Shows current room settings. """
        if self.is_client_owner:
            settings = self.privacy_settings.current_settings()
            self.send_undercover_msg(self.active_user.nick, '*Broadcast Password:* %s' % settings['broadcast_pass'])
            self.send_undercover_msg(self.active_user.nick, '*Room Password:* %s' % settings['room_pass'])
            self.send_owner_run_msg('*Login Type:* %s' % settings['allow_guest'])
            self.send_owner_run_msg('*Directory:* %s' % settings['show_on_directory'])
            self.send_owner_run_msg('*Push2Talk:* %s' % settings['push2talk'])
            self.send_owner_run_msg('*Greenroom:* %s' % settings['greenroom'])

    def do_lastfm_chart(self, chart_items):
        """ Makes a playlist from the currently most played tunes on last.fm

        :param chart_items: The amount of tunes we want. The string must be able to be converted to int.
        :type chart_items: str
        """
        if self.is_client_mod:
            if chart_items is 0 or chart_items is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify the amount of tunes you want.')
            else:
                try:
                    _items = int(chart_items)
                except ValueError:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                else:
                    if 0 < _items < 30:
                        self.send_bot_msg(unicode_catalog.STATE + ' *Please wait* while creating a playlist...')
                        last = lastfm.chart(_items)
                        if last is not None:
                            self.media.add_track_list(self.active_user.nick, last)
                            self.send_bot_msg(unicode_catalog.PENCIL + ' *Added:* ' + str(len(last)) +
                                              ' *tunes from last.fm chart.*')
                            if not self.media.has_active_track():
                                track = self.media.get_next_track()
                                self.send_media_broadcast_start(track.type, track.id)
                                self.media_event_timer(track.time)
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' Failed to retrieve a result from last.fm.')
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No more than 30 tunes.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_lastfm_random_tunes(self, max_tunes):
        """ Creates a playlist from what other people are listening to on last.fm.

        :param max_tunes: The max amount of tunes. The string must be able to be converted to int.
        :type max_tunes: str
        """
        if self.is_client_mod:
            if max_tunes is not 0 or max_tunes is not None:
                try:
                    _items = int(max_tunes)
                except ValueError:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                else:
                    if 0 < _items < 50:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Please wait while creating a playlist...')
                        last = lastfm.listening_now(max_tunes)
                        if last is not None:
                            self.media.add_track_list(self.active_user.nick, last)
                            self.send_bot_msg(unicode_catalog.PENCIL + ' *Added:* ' + str(len(last)) +
                                              ' *tunes from last.fm*')
                            if not self.media.has_active_track():
                                track = self.media.get_next_track()
                                self.send_media_broadcast_start(track.type, track.id)
                                self.media_event_timer(track.time)
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' Failed to retrieve a result from last.fm.')
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No more than 50 tunes.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify the max amount of tunes you want.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_search_lastfm_by_tag(self, search_tag):
        """ Searches last.fm for tunes matching the search term and creates a playlist from them.

        :param search_tag: The search term to search for.
        :type search_tag: str
        """
        if self.is_client_mod:
            if len(search_tag) is not 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please wait while creating playlist..')
                last = lastfm.tag_search(search_tag)
                if last is not None:
                    self.media.add_track_list(self.active_user.nick, last)
                    self.send_bot_msg(unicode_catalog.PENCIL + ' *Added:* ' + str(len(last)) + ' *tunes from last.fm*')
                    if not self.media.has_active_track():
                        track = self.media.get_next_track()
                        self.send_media_broadcast_start(track.type, track.id)
                        self.media_event_timer(track.time)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Failed to retrieve a result from last.fm.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing search tag.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_youtube_playlist_search(self, search_term):
        """ Searches youtube for a play list matching the search term.

        :param search_term: The search to search for.
        :type search_term: str
        """
        if self.is_client_mod:
            if len(search_term) is not 0:
                self.search_list = youtube.playlist_search(search_term)
                if len(self.search_list) is not 0:
                    self.is_search_list_youtube_playlist = True
                    for i in range(0, len(self.search_list)):
                        self.send_owner_run_msg('(%s) *%s*' % (i, self.search_list[i]['playlist_title']))
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Failed to find playlist matching search term: %s' %
                                      search_term)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing search term.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_play_youtube_playlist(self, int_choice):
        """ Finds the videos from the youtube playlist search.

        :param int_choice: The index of the play list on the search_list.
        The string must be able to be converted to int.
        :type int_choice: str
        """
        if self.is_client_mod:
            if self.is_search_list_youtube_playlist:
                try:
                    index_choice = int(int_choice)
                except ValueError:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                else:
                    if 0 <= index_choice <= len(self.search_list) - 1:
                        self.send_bot_msg(unicode_catalog.STATE + ' Please wait while creating playlist..')
                        tracks = youtube.playlist_videos(self.search_list[index_choice]['playlist_id'])
                        if len(tracks) is not 0:
                            self.media.add_track_list(self.active_user.nick, tracks)
                            self.send_bot_msg(unicode_catalog.PENCIL + ' *Added:* %s *tracks from youtube playlist.*' %
                                              len(tracks))
                            if not self.media.has_active_track():
                                track = self.media.get_next_track()
                                self.send_media_broadcast_start(track.type, track.id)
                                self.media_event_timer(track.time)
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' Failed to retrieve videos from youtube '
                                                                         'playlist.')
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Please make a choice between 0-%s' %
                                          str(len(self.search_list) - 1))
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' The search list does not contain any youtube playlist '
                                                             'id\'s.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_close_broadcast(self, user_name):
        """ Close a user broadcasting.

        :param user_name: The username to close.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is not 0:
                if self.users.search(user_name) is not None:
                    self.send_close_user_msg(user_name)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: ' + user_name)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')
        else:
            self.send_bot_msg('Command not enabled.')

    # TODO: This seems to cause issues with the room server.
    # def do_clear(self):
    #     """ Clears the chat box. """
    #     if self.is_client_mod:
    #         for x in range(0, 29):
    #             self.send_owner_run_msg(' ')
    #     else:
    #         clear = '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133' \
    #                 '133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133,133'
    #         self.connection.call('privmsg', [clear, u'#262626,en'])

    # TODO: How does skip handle radio media event handler.
    def do_skip(self):
        """ Play the next item in the playlist. """
        if self.is_client_mod:
            # if not pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY:
            if self.media.is_last_track():
                self.send_bot_msg(unicode_catalog.STATE + ' This is the *last tune in the playlist*.')
            elif self.media.is_last_track() is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *No tunes* to skip. The *playlist is empty*.')
            else:
                self.cancel_media_event_timer()
                current_type = self.media.track().type
                next_track = self.media.get_next_track()
                if current_type != next_track.type:
                    self.send_media_broadcast_close(media_type=current_type)
                self.send_media_broadcast_start(next_track.type, next_track.id)
                self.media_event_timer(next_track.time)

                # Handle if a radio tracks are being added to the playlist, we will cancel the current timer
                # and adjust to the new time of the track.
                # if pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY and self.radio_timer_thread is not None:
                #     self.cancel_radio_event_timer()
                #     threading.Thread(target=self.radio_event_timer, args=(next_track.time,)).start()
                #     self.radio_event_timer(next_track.time)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_delete_playlist_item(self, to_delete):
        """ Delete item(s) from the playlist by index.

        :param to_delete: Index(es) to delete.
        :type to_delete: str
        """
        if self.is_client_mod:
            if len(self.media.track_list) is 0:
                self.send_bot_msg(unicode_catalog.STATE + ' The track list is *empty*.')
            elif len(to_delete) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' No indexes to delete provided.')
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
                except ValueError as ve:
                    log.error('wrong format: %s' % ve)
                    # self.send_undercover_msg(self.user.nick, 'Wrong format (ValueError).')
                else:
                    indexes = []
                    for i in temp_indexes:
                        if i < len(self.media.track_list) and i not in indexes:
                            indexes.append(i)

                if indexes is not None and len(indexes) > 0:
                    result = self.media.delete_by_index(indexes, by_range)
                    if result is not None:
                        if by_range:
                            self.send_bot_msg(unicode_catalog.SCISSORS + ' *Deleted from index:* %s *to index:* %s' %
                                              (result['from'], result['to']))
                        elif result['deleted_indexes_len'] is 1:
                            self.send_bot_msg(unicode_catalog.SCISSORS + ' *Deleted* %s' % result['track_title'])
                        else:
                            self.send_bot_msg(unicode_catalog.SCISSORS + ' *Deleted tracks at index:* %s' %
                                              ', '.join(result['deleted_indexes']))
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Nothing was deleted.')
        else:
            self.send_bot_msg('Command not enabled.')

    def do_media_replay(self):
        """ Replays the last played media."""
        if self.is_client_mod:
            if self.media.track() is not None:
                self.cancel_media_event_timer()
                self.media.we_play(self.media.track())
                self.send_media_broadcast_start(self.media.track().type,
                                                self.media.track().id)
                self.media_event_timer(self.media.track().time)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_play_media(self):
        """ Resumes a track in pause mode. """
        if self.is_client_mod:
            track = self.media.track()
            if track is not None:
                if self.media.has_active_track():
                    self.cancel_media_event_timer()
                if self.media.is_paused:
                    ntp = self.media.mb_play(self.media.elapsed_track_time())
                    self.send_media_broadcast_play(track.type, self.media.elapsed_track_time())
                    self.media_event_timer(ntp)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_media_pause(self):
        """ Pause the media playing. """
        if self.is_client_mod:
            track = self.media.track()
            if track is not None:
                if self.media.has_active_track():
                    self.cancel_media_event_timer()
                self.media.mb_pause()
                self.send_media_broadcast_pause(track.type)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_close_media(self):
        """ Closes the active media broadcast."""
        if self.is_client_mod:
            if self.media.has_active_track():
                self.cancel_media_event_timer()
                self.media.mb_close()
                self.send_media_broadcast_close(self.media.track().type)
        else:
            self.send_bot_msg('Command not enabled.')

    def do_seek_media(self, time_point):
        """ Seek on a media playing.

        :param time_point str the time point to skip to.
        """
        if self.is_client_mod:
            if ('h' in time_point) or ('m' in time_point) or ('s' in time_point):
                mls = pinylib.string_util.convert_to_millisecond(time_point)
                if mls is not 0:
                    track = self.media.track()
                    if track is not None:
                        if 0 < mls < track.time:
                            if self.media.has_active_track():
                                self.cancel_media_event_timer()
                            new_media_time = self.media.mb_skip(mls)
                            if not self.media.is_paused:
                                self.media_event_timer(new_media_time)
                            self.send_media_broadcast_skip(track.type, mls)
                else:
                    self.console_write(pinylib.COLOR['bright_red'], 'The seek time you entered was invalid.')
            else:
                # TODO: Instructions on how to type in the seek time.
                self.send_bot_msg('')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Command not enabled.')

    def do_clear_playlist(self):
        """ Clear the playlist. """
        if self.is_client_mod:
            if len(self.media.track_list) > 0:
                pl_length = str(len(self.media.track_list))
                self.media.clear_track_list()
                self.send_bot_msg(unicode_catalog.SCISSORS + ' *Deleted* ' + pl_length + ' *items in the playlist.*')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *The playlist is empty*, nothing to delete.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Command not enabled.')

    def do_playlist_info(self):
        """ Shows the next 5 tracks in the track list. """
        if self.is_client_mod:
            if len(self.media.track_list) > 0:
                tracks = self.media.get_track_list()
                if tracks is not None:
                    i = 0
                    for pos, track in tracks:
                        if i == 0:
                            self.send_owner_run_msg('(%s) *Next track: %s* %s' %
                                                    (pos, track.title, self.format_time(track.time)))
                        else:
                            self.send_owner_run_msg('(%s) *%s* %s' % (pos, track.title, self.format_time(track.time)))
                        i += 1
            else:
                self.send_owner_run_msg(unicode_catalog.INDICATE + ' *No tracks in the playlist.*')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Command not enabled.')

    # TODO: Adjust if/else statements.
    def do_show_search_list(self):
        """ Shows what is in the search list. """
        if len(self.search_list) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' No items in the search list.')
        elif self.is_search_list_youtube_playlist:
            self.send_bot_msg('*Youtube Playlist\'s.*')
            for i in range(0, len(self.search_list)):
                self.send_bot_msg('(%s) *%s*' % (i, self.search_list[i]['playlist_title']))
        else:
            self.send_bot_msg('*Youtube Tracks:*')
            for i in range(0, len(self.search_list)):
                self.send_bot_msg('(%s) *%s* %s' %
                                  (i, self.search_list[i]['video_title'], self.search_list[i]['video_time']))

    def do_nick(self, new_nick):
        """ Set a new nick for the bot.

        :param new_nick: The new nick.
        :type new_nick: str
        """
        if len(new_nick) is 0:
            self.nickname = pinylib.string_util.create_random_string(5, 25)
            self.set_nick()
        else:
            if re.match('^[][{}a-zA-Z0-9_]{1,25}$', new_nick):
                self.nickname = new_nick
                self.set_nick()

    def do_topic(self, topic):
        """ Sets the room topic.

        :param topic: The new topic.
        :type topic: str
        """
        if self.is_client_mod:
            if len(topic) is not 0:
                self.send_topic_msg(topic)
                self.send_bot_msg(unicode_catalog.STATE + ' The *room topic* was set to: ' + topic)
            else:
                self.send_topic_msg('')
                self.send_bot_msg(unicode_catalog.STATE + ' Topic was *cleared*.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Command not enabled.')

    def do_kick(self, user_name):
        """ Kick a user out of the room.

        :param user_name: The username to kick.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')
            elif user_name == self.nickname:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Action not allowed.')
            else:
                if user_name.startswith('*'):
                    user_name = user_name.replace('*', '')
                    _users = self.users.search_containing(user_name)
                    if len(_users) > 0:
                        for i, user in enumerate(_users):
                            if user.nick != self.nickname and user.user_level > self.active_user.user_level:
                                if i <= pinylib.CONFIG.B_MAX_MATCH_BANS - 1:
                                    self.send_ban_msg(user.nick, user.id)
                                    a = pinylib.string_util.random.uniform(0.0, 1.0)
                                    pinylib.time.sleep(a)
                                    self.send_forgive_msg(user.id)
                                    pinylib.time.sleep(0.5)
                else:
                    _user = self.users.search(user_name)
                    if _user is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: *%s*' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Not allowed.')
                    else:
                        self.send_ban_msg(user_name, _user.id)
                        self.send_forgive_msg(_user.id)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Command not enabled.')

    def do_ban(self, user_name):
        """ Ban a user from the room.

        :param user_name: The username to ban.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')
            elif user_name == self.nickname:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Action not allowed.')
            else:
                if user_name.startswith('*'):
                    user_name = user_name.replace('*', '')
                    _users = self.users.search_containing(user_name)
                    if len(_users) > 0:
                        for i, user in enumerate(_users):
                            if user.nick != self.nickname and user.user_level > self.active_user.user_level:
                                if i <= pinylib.CONFIG.B_MAX_MATCH_BANS - 1:
                                    self.send_ban_msg(user.nick, user.id)
                                    a = pinylib.string_util.random.uniform(0.0, 1.5)
                                    pinylib.time.sleep(a)
                else:
                    _user = self.users.search(user_name)
                    if _user is None:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: *%s*' % user_name)
                    elif _user.user_level < self.active_user.user_level:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Not allowed.')
                    else:
                        self.send_ban_msg(user_name, _user.id)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_bad_nick(self, bad_nick):
        """ Adds a username to the nicks bans file.

        :param bad_nick: The bad nick to write to file.
        :type bad_nick: str
        """
        if self.is_client_mod:
            if len(bad_nick) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')
            elif bad_nick in pinylib.CONFIG.B_NICK_BANS:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *%s* is already in list.' % bad_nick)
            else:
                pinylib.file_handler.file_writer(self.config_path(),
                                                 pinylib.CONFIG.B_NICK_BANS_FILE_NAME, bad_nick)
                self.send_bot_msg('*%s* was added to file.' % bad_nick)
                self.load_list(nicks=True)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_remove_bad_nick(self, bad_nick):
        """ Removes a nick from the nick bans file.

        :param bad_nick: The bad nick to remove from the nick bans file.
        :type bad_nick: str
        """
        if self.is_client_mod:
            if len(bad_nick) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username')
            else:
                if bad_nick in pinylib.CONFIG.B_NICK_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path(),
                                                                pinylib.CONFIG.B_NICK_BANS_FILE_NAME, bad_nick)
                    if rem:
                        self.send_bot_msg('*%s* was removed.' % bad_nick)
                        self.load_list(nicks=True)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_bad_string(self, bad_string):
        """ Adds a string to the strings bans file.

        :param bad_string: The bad string to add to file.
        :type bad_string: str
        """
        if self.is_client_mod:
            if len(bad_string) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Ban string can\'t be blank.')
            elif len(bad_string) < 3:
                self.send_bot_msg('Ban string to short: ' + str(len(bad_string)))
            elif bad_string in pinylib.CONFIG.B_STRING_BANS:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *%s* is already in list.' % bad_string)
            else:
                pinylib.file_handler.file_writer(self.config_path(),
                                                 pinylib.CONFIG.B_STRING_BANS_FILE_NAME, bad_string)
                self.send_bot_msg('*%s* was added to file.' % bad_string)
                self.load_list(strings=True)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_remove_bad_string(self, bad_string):
        """ Removes a string from the strings bans file.

        :param bad_string: The bad string to remove from file.
        :type bad_string: str
        """
        if self.is_client_mod:
            if len(bad_string) is 0:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing word string.')
            else:
                if bad_string in pinylib.CONFIG.B_STRING_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path(),
                                                                pinylib.CONFIG.B_STRING_BANS_FILE_NAME, bad_string)
                    if rem:
                        self.send_bot_msg('*%s* was removed.' % bad_string)
                        self.load_list(strings=True)
                # TODO: Decide what to reply with here.
                else:
                    self.send_bot_msg('The bad string you wanted to remove was *not added to the list*.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # TODO: Short this issue out; order of if statements.
    def do_bad_account(self, bad_account_name):
        """ Adds an account name to the accounts bans file.

        :param bad_account_name: The bad account name to add to file.
        :type bad_account_name: str
        """
        if self.is_client_mod:
            if len(bad_account_name) is not 0:
                pinylib.file_handler.file_writer(self.config_path(),
                                                 pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME, bad_account_name)
                self.send_bot_msg('*%s* was added to file.' % bad_account_name)
                self.load_list(accounts=True)
            elif bad_account_name in pinylib.CONFIG.B_ACCOUNT_BANS:
                self.send_bot_msg(unicode_catalog.INDICATE + ' %s is already in list.' % bad_account_name)
                # TODO: Account names can be shorter than 3 characters in length (thank you to Technetium1 for
                #       pointing this out).
                # elif len(bad_account_name) < 3:
                #     self.send_bot_msg('Account to short: ' + str(len(bad_account_name)))
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Account can\'t be blank.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_remove_bad_account(self, bad_account):
        """ Removes an account from the accounts bans file.

        :param bad_account: The bad account name to remove from file.
        :type bad_account: str
        """
        if self.is_client_mod:
            if len(bad_account) is not 0:
                if bad_account in pinylib.CONFIG.B_ACCOUNT_BANS:
                    rem = pinylib.file_handler.remove_from_file(self.config_path(),
                                                                pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME, bad_account)
                    if rem:
                        self.send_bot_msg('*%s* was removed.' % bad_account)
                        self.load_list(accounts=True)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' The account was not found in the accounts bans.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing account.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_list_info(self, list_type):
        """ Shows info of different lists/files.

        :param list_type: The type of list to find info for.
        :type list_type: str
        """
        if self.is_client_mod:
            if len(list_type) is not 0:
                if list_type.lower() == 'bn':
                    if len(pinylib.CONFIG.B_NICK_BANS) is 0:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in this list.')
                    else:
                        self.send_bot_msg('%s *bad nicks in list.*' % len(pinylib.CONFIG.B_NICK_BANS))

                elif list_type.lower() == 'bs':
                    if len(pinylib.CONFIG.B_STRING_BANS) is 0:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in this list.')
                    else:
                        self.send_bot_msg('%s *string bans in list.*' % pinylib.CONFIG.B_STRING_BANS)

                elif list_type.lower() == 'ba':
                    if len(pinylib.CONFIG.B_ACCOUNT_BANS) is 0:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' No items in this list.')
                    else:
                        self.send_bot_msg('%s *bad accounts in list.*' % pinylib.CONFIG.B_ACCOUNT_BANS)

                elif list_type.lower() == 'mods':
                    if self.is_client_owner:
                        if len(self.privacy_settings.room_moderators) is 0:
                            self.send_bot_msg(unicode_catalog.STATE +
                                              ' *There are currently no moderators for this room.*')
                        elif len(self.privacy_settings.room_moderators) > 0:
                            mods = ', '.join(self.privacy_settings.room_moderators)
                            self.send_bot_msg('*Moderators:* ' + mods)

                # TODO: Handle blocked media urls.
                # elif list_type.lower() == 'bm':
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing list type.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_user_info(self, user_name):
        """ Shows user object info for a given user name.

        :param user_name: The user name of the user to show the info for.
        :type user_name: str
        """
        if self.is_client_mod:
            if len(user_name) is not 0:
                _user = self.users.search(user_name)
                if _user is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No user named: %s' % user_name)
                else:
                    if _user.account and _user.tinychat_id is None:
                        user_info = pinylib.apis.tinychat.user_info(_user.account)
                        if user_info is not None:
                            _user.tinychat_id = user_info['tinychat_id']
                            _user.last_login = user_info['last_active']
                    self.send_owner_run_msg('*User Level:* %s' % _user.user_level)
                    online_time = (pinylib.time.time() - _user.join_time) * 1000
                    self.send_owner_run_msg('*Online Time:* %s' % self.format_time(online_time))

                    if _user.tinychat_id is not None:
                        self.send_owner_run_msg('*Account:* ' + str(_user.account))
                        self.send_owner_run_msg('*Tinychat ID:* ' + str(_user.tinychat_id))
                        self.send_owner_run_msg('*Last login:* ' + str(_user.last_login))
                    self.send_owner_run_msg('*Last message:* ' + str(_user.last_msg))
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing username.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_youtube_search(self, search_str):
        """ Searches youtube for a given search term, and returns a list of candidates.

        :param search_str: The search term to search for.
        :type search_str: str
        """
        if self.is_client_mod:
            if len(search_str) is not 0:
                self.search_list = youtube.search_list(search_str, results=5)
                if len(self.search_list) is not 0:
                    self.is_search_list_youtube_playlist = False
                    for i in range(0, len(self.search_list)):
                        v_time = self.format_time(self.search_list[i]['video_time'])
                        v_title = self.search_list[i]['video_title']
                        self.send_owner_run_msg('(%s) *%s* %s' % (i, v_title, v_time))
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find: %s' % search_str)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Missing search term.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_play_youtube_search(self, int_choice):
        """ Plays a youtube from the search list.

        :param int_choice: The index in the search list to play.
        :type int_choice: str
        """
        if self.is_client_mod:
            if not self.is_search_list_youtube_playlist:
                if len(self.search_list) > 0:
                    try:
                        index_choice = int(int_choice)
                    except ValueError:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' Only numbers allowed.')
                    else:
                        if 0 <= index_choice <= len(self.search_list) - 1:
                            if self.media.has_active_track():
                                track = self.media.add_track(self.active_user.nick, self.search_list[index_choice])
                                self.send_bot_msg(unicode_catalog.PENCIL + ' *Added* (%s) *%s* %s' %
                                                  (self.media.last_track_index(), track.title, track.time))
                            else:
                                track = self.media.mb_start(self.active_user.nick, self.search_list[index_choice],
                                                            mod_play=False)
                                self.send_media_broadcast_start(track.type, track.id)
                                self.media_event_timer(track.time)
                        else:
                            self.send_bot_msg(unicode_catalog.INDICATE + ' Please make a choice between 0-%s' %
                                              str(len(self.search_list) - 1))
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' No youtube track id\'s in the search list.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' The search list only contains youtube playlist id\'s.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # == Public Command Methods. ==
    def do_full_screen(self, room_name):
        """ Post a full screen link.

        :param room_name: The room name you want a full screen link for.
        :type room_name: str
        """
        if not room_name:
            self.send_undercover_msg(self.active_user.nick, 'http://tinychat.com/embed/Tinychat-11.1-1.0.0.' +
                                     pinylib.CONFIG.SWF_VERSION + '.swf?target=client&key=tinychat&room=' +
                                     self.roomname)
        else:
            self.send_undercover_msg(self.active_user.nick, 'http://tinychat.com/embed/Tinychat-11.1-1.0.0.' +
                                     pinylib.CONFIG.SWF_VERSION + '.swf?target=client&key=tinychat&room=' +
                                     room_name)

    def do_who_plays(self):
        """ Shows who is playing the track. """
        if self.media.has_active_track():
            track = self.media.track()
            time_elapsed = self.format_time(int(pinylib.time.time() - track.rq_time) * 1000)
            self.send_bot_msg(unicode_catalog.STATE + ' *' + track.owner + '* added this track: ' + time_elapsed +
                              ' ago.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' *No track playing*.')

    def do_version(self):
        """ Show version information. """
        self.send_undercover_msg(self.active_user.nick, '*pinybot*: %s (%s - %s), *pinylib*: %s' %
                                 (__version__, __version_name__, __status__, pinylib.__version__))
        self.send_undercover_msg(self.active_user.nick, '*Repository/Authors*: %s' % __authors_information__)
        self.send_undercover_msg(self.active_user.nick, '*Platform:* %s, *Runner*: %s' %
                                 (sys.platform, sys.version_info[0:3]))

    def do_help(self):
        """ Posts a link to GitHub README/wiki or other page about the bot commands. """
        self.send_undercover_msg(self.active_user.nick, '*Help:* https://github.com/GoelBiju/pinybot/wiki/')

    def do_uptime(self):
        """ Shows the bots uptime. """
        self.send_bot_msg('*Uptime:* ' + self.format_time(self.get_runtime()) +
                          ' *Reconnect Delay:* ' + self.format_time(self._reconnect_delay * 1000))

    def do_pmme(self):
        """ Opens a PM session with the bot. """
        self.send_private_msg('How can I help you *' + unicode_catalog.NO_WIDTH + self.active_user.nick +
                              unicode_catalog.NO_WIDTH + '*?', self.active_user.nick)

    #  == Media Related Command Methods. ==
    def do_playlist_status(self):
        """ Shows info about the playlist. """
        if self.is_client_mod:
            if len(self.media.track_list) is not 0:
                in_queue = self.media.queue()
                if in_queue is not None:
                    self.send_bot_msg(str(in_queue[0]) + ' *items in the playlist.* ' +
                                      str(in_queue[1]) + ' *Still in queue.*')
            else:
                self.send_bot_msg('*The playlist is empty.*')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_next_tune_in_playlist(self):
        """ Shows next item in the playlist. """
        if self.is_client_mod:
            if self.media.is_last_track():
                self.send_bot_msg(unicode_catalog.STATE + ' This is the *last track* in the playlist.')
            elif self.media.is_last_track() is None:
                self.send_bot_msg(unicode_catalog.STATE + ' *No tracks in the playlist.*')
            else:
                pos, next_track = self.media.next_track_info()
                if next_track is not None:
                    self.send_bot_msg('(' + str(pos) + ') *' + next_track.title + '* ' +
                                      self.format_time(next_track.time))
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + 'Not enabled right now.')

    def do_now_playing(self):
        """ Shows the currently playing media title. """
        if self.is_client_mod:
            if self.media.has_active_track():
                track = self.media.track()
                if len(self.media.track_list) > 0:
                    self.send_undercover_msg(self.active_user.nick, 'Now playing (' +
                                             str(self.media.current_track_index() + 1) + '): *' + track.title +
                                             '* (' + self.format_time(track.time) + ')')
                else:
                    self.send_undercover_msg(self.active_user.nick, 'Now playing: *' + track.title + '* (' +
                                             self.format_time(track.time) + ')')
            else:
                self.send_undercover_msg(self.active_user.nick, '*No track playing.*')

    def do_play_youtube(self, search_video):
        """ Plays a YouTube video matching the search term.

        :param search_video: The video to search for.
        :type search_video: str
        """
        log.info('User: %s:%s is searching youtube: %s' % (self.active_user.nick, self.active_user.id, search_video))
        if self.is_client_mod:
            if len(search_video) is not 0:
                # Try checking the search term to see if matches our URL regex pattern.
                # If so, we can extract the video id from the URL. Many thanks to Aida (Autotonic) for this feature.
                match_url = self._youtube_pattern.match(search_video)
                if match_url is not None:
                    video_id = match_url.group(1)
                    _youtube = youtube.video_details(video_id)
                else:
                    _youtube = youtube.search(search_video)

                if _youtube is None:
                    log.warning('Youtube request returned: %s' % _youtube)
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find video: ' + search_video)
                else:
                    log.info('Youtube found: %s' % _youtube)
                    if self.media.has_active_track() and pinylib.CONFIG.B_PLAYLIST_MODE:
                        track = self.media.add_track(self.active_user.nick, _youtube)
                        self.send_bot_msg(unicode_catalog.PENCIL + ' *' + track.title + '* (' +
                                          self.format_time(track.time) + ') at *' + unicode_catalog.NUMERO + ' ' +
                                          str(len(self.media.track_list)) + '*')
                    else:
                        track = self.media.mb_start(self.active_user.nick, _youtube, mod_play=False)
                        self.send_media_broadcast_start(track.type, track.id)
                        self.media_event_timer(track.time)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify *YouTube* title, ID or link.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_play_private_youtube(self, search_video):
        """ Plays a YouTube matching the search term privately.

        NOTE: The video will only be visible for the message sender.
        :param search_video: The video to search for.
        :type search_video: str
        """
        if self.is_client_mod:
            if len(search_video) is not 0:
                _youtube = youtube.search(search_video)
                if _youtube is None:
                    self.send_undercover_msg(self.active_user.nick, 'Could not find video: %s' % search_video)
                else:
                    self.send_media_broadcast_start(_youtube['type'], _youtube['video_id'],
                                                    private_nick=self.active_user.nick)
            else:
                self.send_undercover_msg(self.active_user.nick, 'Please specify *YouTube* title, id or link.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_play_soundcloud(self, search_track):
        """ Plays a SoundCloud matching the search term.

        :param search_track: The track to search for.
        :type search_track: str
        """
        if self.is_client_mod:
            if len(search_track) is not 0:
                _soundcloud = soundcloud.search(search_track)
                if _soundcloud is None:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find SoundCloud: %s' % search_track)
                else:
                    if self.media.has_active_track() and pinylib.CONFIG.B_PLAYLIST_MODE:
                        track = self.media.add_track(self.active_user.nick, _soundcloud)
                        self.send_bot_msg(unicode_catalog.PENCIL + ' *' + track.title + '* (' +
                                          self.format_time(track.time) + ') at *' + unicode_catalog.NUMERO + ' ' +
                                          str(len(self.media.track_list)) + '*')
                    else:
                        track = self.media.mb_start(self.active_user.nick, _soundcloud, mod_play=False)
                        self.send_media_broadcast_start(track.type, track.id)
                        self.media_event_timer(track.time)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify *SoundCloud* title or id.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_play_private_soundcloud(self, search_track):
        """ Plays a SoundCloud matching the search term privately.

        NOTE: The video will only be visible for the message sender.
        :param search_track: The track to search for.
        :type search_track: str
        """
        if self.is_client_mod:
            if len(search_track) is not 0:
                _soundcloud = soundcloud.search(search_track)
                if _soundcloud is None:
                    self.send_undercover_msg(self.active_user.nick, 'Could not find video: ' + search_track)
                else:
                    self.send_media_broadcast_start(_soundcloud['type'], _soundcloud['video_id'],
                                                    private_nick=self.active_user.nick)
            else:
                self.send_undercover_msg(self.active_user.nick, 'Please specify *SoundCloud* title or id.')
        else:
            self.send_bot_msg('Not enabled right now.')

    def do_broadcast_approve(self, username):
        """ Send a camera approval message to a user.

        :param username: The nickname of the user we want to send the broadcast request for.
        :type username: str
        """
        if self.is_client_mod and self.param.is_greenroom:
            if len(username) > 0:
                _approve_user = self.users.search(username)
                if _approve_user is not None and self.active_user.is_waiting:
                    self.console_write(pinylib.COLOR['bright_green'], '%s sending broadcast approval for: %s' %
                                       (self.active_user.nick, _approve_user.nick))
                    # Send the camera approval message and set the waiting attribute to false as the
                    # user is now broadcasting.
                    self.send_cam_approve_msg(_approve_user.nick, _approve_user.id)
                    self.active_user.is_waiting = False
                    self.send_bot_msg(unicode_catalog.STATE + ' Greenroom *broadcast approved* for: %s' %
                                      _approve_user.nick)
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' We could not find a user named: %s' % username)

            # TODO: Create a toggle function for SELF APPROVAL configuration.
            # Allow users who are already waiting to approve themselves to broadcast
            # (this is only applicable if it has been configured to or self approval is turned on).
            elif pinylib.CONFIG.B_SELF_GREENROOM_APPROVAL and len(username) is 0 and self.active_user.is_waiting:
                self.active_user.is_waiting = False
                self.send_cam_approve_msg(self.active_user.nick, self.active_user.id)
                self.console_write(pinylib.COLOR['bright_green'], '%s:%s self-approved their greenroom broadcast.' %
                                   (self.active_user.nick, self.active_user.id))
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter the *nickname* you would like to '
                                                             'provide broadcast approval for.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # == Tinychat API Command Methods. ==
    def do_spy(self, room_name):
        """ Shows information for a given room.

        :param room_name: The room name to find the information of.
        :type room_name: str
        """
        if self.is_client_mod:
            if len(room_name) is not 0:
                spy_info = pinylib.apis.tinychat.spy_info(room_name)
                if spy_info is None:
                    self.send_undercover_msg(self.active_user.nick, 'Failed to retrieve information.')
                elif 'error' in spy_info:
                    self.send_undercover_msg(self.active_user.nick, spy_info['error'])
                else:
                    self.send_undercover_msg(self.active_user.nick, '*Mods*: %s, *Broadcasters*: %s, *Users*: %s' %
                                             (spy_info['mod_count'],
                                              spy_info['broadcaster_count'],
                                              spy_info['total_count']))
                    if self.has_level(3):
                        users = ', '.join(spy_info['users'])
                        self.send_undercover_msg(self.active_user.nick, '*' + users + '*')
            else:
                self.send_undercover_msg(self.active_user.nick, 'Missing room name.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_account_spy(self, account):
        """ Shows information about a Tinychat account.

        :param account: Tinychat account to fetch information from.
        :type account: str
        """
        if self.is_client_mod:
            if len(account) is not 0:
                tc_usr = pinylib.apis.tinychat.user_info(account)
                if tc_usr is None:
                    self.send_undercover_msg(self.active_user.nick, 'Could not find Tinychat info for: ' + account)
                else:
                    self.send_undercover_msg(self.active_user.nick, '*ID*: %s, *Last login*: %s' %
                                             (tc_usr['tinychat_id'],
                                              tc_usr['last_active']))
            else:
                self.send_undercover_msg(self.active_user.nick, 'Missing username to search for.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # == Other API Command Methods. ==
    def do_search_urban_dictionary(self, search_term):
        """ Shows Urban-Dictionary definition of search string.

        :param search_term: The search term to look up a definition for.
        :type search_term: str
        """
        if self.is_client_mod:
            if len(search_term) is not 0:
                urban = other.urbandictionary_search(search_term)
                if urban is None:
                    self.send_bot_msg('Could not find a definition for: ' + search_term)
                else:
                    if len(urban) > 70:
                        chunks = pinylib.string_util.chunk_string(urban, 70)
                        for i in range(0, 2):
                            self.send_bot_msg(chunks[i])
                    else:
                        self.send_bot_msg(urban)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify something to look up.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_worldwide_weather_search(self, location):
        """ Shows weather information for a given location, using the World-Weather-Online website.

        :param location: The location to find weather data for.
        :type location: str
        """
        if len(location) is not 0:
            weather = other.worldwide_weather_search(location)
            if weather is not None:
                self.send_bot_msg(weather)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find weather data for: %s' % location)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify a location to search for on '
                                                         '*World-Weather-Online*.')

    def do_wunderground_weather_search(self, city):
        """ Shows weather information given a city, using the Wunderground website.

        :param city: The city which we should get the weather status of.
        :type city: str
        """
        if len(city) is not 0:
            weather = other.wunderground_weather_search(city)
            if weather is not None:
                self.send_bot_msg(weather)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' Could not find weather data for: %s' % city)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please specify a city to search for on *Wunderground*.')

    def do_who_is_ip(self, ip_address):
        """ Shows who-is info for a given ip address.

        :param ip_address: The ip address to find info for.
        :type ip_address: str
        """
        if len(ip_address) is not 0:
            who_is = other.who_is(ip_address)
            if who_is is None:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *No information found for*: %s' % ip_address)
            else:
                self.send_bot_msg(who_is)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please provide an IP address.')

    # == Just For Fun Command Methods. ==
    def do_chuck_norris(self):
        """ Shows a chuck norris joke/quote. """
        chuck = other.chuck_norris()
        if chuck is not None:
            self.send_bot_msg(chuck)

    def do_8ball(self, question):
        """ Shows magic eight ball answer to a yes/no question.

        :param question: The yes/no question.
        :type question: str
        """
        if len(question) is 0:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please ask a *yes or no question* to get a reply.')
        else:
            self.send_bot_msg('*8Ball* %s' % locals_.eight_ball())

    def do_dice(self):
        """ Roll the dice. """
        self.send_bot_msg('*The dice rolled:* %s' % locals_.roll_dice())

    def do_flip_coin(self):
        """ Flip a coin. """
        self.send_bot_msg('*The coin was:* %s' % locals_.flip_coin())

    # Custom command handling functions:
    def do_set_sanitize_message(self):
        """ Toggle message message sanitation configuration. """
        pinylib.CONFIG.B_SANITIZE_MESSAGES = not pinylib.CONFIG.B_SANITIZE_MESSAGES
        self.send_bot_msg('*Sanitize messages*: %s' % pinylib.CONFIG.B_SANITIZE_MESSAGES)

    # TODO: Handle private room commands.
    def do_set_private_room(self):
        """ Toggle 'private_room' configuration. """
        if self.is_client_mod:
            self.send_private_room_msg(not self._private_room)
            self.send_bot_msg(unicode_catalog.STATE + 'Private room was sent as: *%s*' % (not self._private_room))
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_set_allow_snapshots(self):
        """ Toggle allowing snapshots configuration. """
        pinylib.CONFIG.B_ALLOW_SNAPSHOTS = not pinylib.CONFIG.B_ALLOW_SNAPSHOTS
        self.send_bot_msg('*Allow snapshots*: %s' % pinylib.CONFIG.B_ALLOW_SNAPSHOTS)

    def do_set_auto_close(self):
        """ Toggle automatic broadcast closing configuration. """
        pinylib.CONFIG.B_AUTO_CLOSE = not pinylib.CONFIG.B_AUTO_CLOSE
        self.send_bot_msg('*Auto-close*: %s' % pinylib.CONFIG.B_AUTO_CLOSE)

    def do_set_ban_mobiles(self):
        """ Toggle automatic mobile banning configuration. """
        pinylib.CONFIG.B_BAN_MOBILES = not pinylib.CONFIG.B_BAN_MOBILES
        self.send_bot_msg('*Ban mobiles*: %s' % pinylib.CONFIG.B_BAN_MOBILES)

    def do_set_auto_greenroom(self):
        """ Toggle automatic monitoring greenroom broadcasts configuration. """
        pinylib.CONFIG.B_AUTO_GREENROOM = not pinylib.CONFIG.B_AUTO_GREENROOM
        self.send_bot_msg('*Automatic Greenroom*: %s' % pinylib.CONFIG.B_AUTO_GREENROOM)

    def do_set_self_greenroom_approval(self):
        """ Toggle allowing approve to themselves configuration. """
        pinylib.CONFIG.B_SELF_GREENROOM_APPROVAL = not pinylib.CONFIG.B_SELF_GREENROOM_APPROVAL
        self.send_bot_msg('*Greenroom self-approval*: %s' % pinylib.CONFIG.B_SELF_GREENROOM_APPROVAL)

    def do_set_auto_url_mode(self):
        """ Toggle auto URL function configuration. """
        pinylib.CONFIG.B_AUTO_URL_MODE = not pinylib.CONFIG.B_AUTO_URL_MODE
        self.send_bot_msg('*Auto URL*: %s' % pinylib.CONFIG.B_AUTO_URL_MODE)

    # def do_set_cleverbot(self):
    #     """ Toggle CleverBot function configuration. """
    #     pinylib.CONFIG.B_CLEVERBOT = not pinylib.CONFIG.B_CLEVERBOT
    #     self.send_bot_msg('*CleverBot*: %s' % pinylib.CONFIG.B_CLEVERBOT)

    # def do_set_playlist_mode(self):
    #     """ Toggle playlist mode for media configuration. """
    #     pinylib.CONFIG.B_PLAYLIST_MODE = not pinylib.CONFIG.B_PLAYLIST_MODE
    #     self.send_bot_msg('*Playlist Mode*: %s' % pinylib.CONFIG.B_PLAYLIST_MODE)

    # def do_set_public_media_mode(self):
    #     """ Toggle public mode for media configuration. """
    #     pinylib.CONFIG.B_PUBLIC_MEDIA_MODE = not pinylib.CONFIG.B_PUBLIC_MEDIA_MODE
    #     self.send_bot_msg('*Public Media Mode*: %s' % pinylib.CONFIG.B_PUBLIC_MEDIA_MODE)

    def do_set_greet_pm(self):
        """ Toggle setting a greetings private message configuration. """
        pinylib.CONFIG.B_GREET_PRIVATE = not pinylib.CONFIG.B_GREET_PRIVATE
        self.send_bot_msg('*Greet Users Private Message*: %s' % pinylib.CONFIG.B_GREET_PRIVATE)

    # def do_set_media_limit_public(self):
    #     """ Toggle media limiting on all media configuration. """
    #     if pinylib.CONFIG.B_PUBLIC_MEDIA_MODE:
    #         pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC = not pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC
    #         self.send_bot_msg('*Media Limit Public*: %s' % pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC)
    #     else:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' *Public media mode* not turned on, turn it on first or '
    #                                                      'set to media limit playlist.')
    #
    # def do_set_media_limit_playlist(self):
    #     """ Toggle media limiting when playlist is turned on configuration. """
    #     pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST = not pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST
    #     self.send_bot_msg('*Media Limit Playlist*: %s' % pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST)

    # def do_media_limit_duration(self, new_duration):
    #     """ Set a media duration if media limiting is turned on.
    #
    #     :param new_duration: The maximum number of seconds each media broadcast should played for.
    #     :type new_duration: int
    #     """
    #     if self.is_client_mod:
    #         if pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC or pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST:
    #             if len(new_duration) is not 0:
    #                 pinylib.CONFIG.B_MEDIA_LIMIT_DURATION = int(new_duration)
    #                 self.send_bot_msg('*Media limit duration* was set to: %s seconds' %
    #                                   str(pinylib.CONFIG.B_MEDIA_LIMIT_DURATION))
    #             else:
    #                 self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a *duration (seconds) for '
    #                                                              'YouTube/SoundCloud media*.')
    #         else:
    #             self.send_bot_msg(unicode_catalog.INDICATE + ' *Media limiting* for public media mode or '
    #                                                          'the playlist is *not turned on*.')
    #     else:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # def do_set_radio(self):
    #     """ Toggle turning on the radio (via YouTube) configuration. """
    #     pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY = not pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY
    #     self.send_bot_msg('*Capital FM auto-play*: %s' % pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY)

    # TODO: When playing a track then adding another track to the playlist, stopping the current track
    #       and turning radio and start radio on. First video on the radio plays but when playing next on radio,
    #       the song that was added to the playlist gets played next.
    # def do_start_radio_auto_play(self):
    #     """ """
    #     if self.is_client_mod:
    #         if pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY:
    #             if self.radio_timer_thread is None:
    #                 # If media limiting is turned on, the radio cannot be in use.
    #                 if pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST or pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC:
    #                     self.send_bot_msg(unicode_catalog.INDICATE +
    #                                       ' *Media limiting is on*, please turn it off for the playlist or public media'
    #                                       ' with *!playlistlimit* or *!publiclimit*.')
    #                 else:
    #                     # Start the radio event thread and state the message that we are playing from
    #                     # the radio's list of songs.
    #                     threading.Thread(target=self._auto_play_radio_track).start()
    #                     self.send_bot_msg(unicode_catalog.MUSICAL_NOTE_SIXTEENTH + ' *Playing Capital FM Radio* ' +
    #                                       unicode_catalog.MUSICAL_NOTE_SIXTEENTH)
    #                     self.send_bot_msg('You can *listen live* at: http://www.capitalfm.com/digital/radio/player/')
    #             else:
    #                 self.send_bot_msg(unicode_catalog.INDICATE + ' The radio event is already playing, please close it '
    #                                                              'with *!stopradio* to start again.')
    #         else:
    #             self.send_bot_msg(unicode_catalog.INDICATE + ' *Capital FM auto-play* is turned off, please turn it on'
    #                                                          ' with *!radio*.')
    #     else:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    # def do_stop_radio_auto_play(self):
    #     """ """
    #     if self.is_client_mod:
    #         self.cancel_radio_event_timer()
    #         self.do_close_media()
    #         self.send_bot_msg(unicode_catalog.STATE + ' *Stopped playing Capital FM Radio*.')
    #     else:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_mute(self):
        """ Send a mute room message. """
        self.send_mute_msg()

    def do_instant_push2talk(self):
        """ Send a push2talk room message. """
        self.send_push2talk_msg()

    # def do_request_media(self, request_info):
    #     """
    #
    #     :param request_info: str
    #     """

    # def do_request_media_accept(self):
    #     """
    #
    #     """
    #     pass

    # def do_request_media_decline(self):
    #     """
    #
    #     """
    #     pass

    def do_official_charts(self):
        """ """
        if self.is_client_mod:
            if pinylib.CONFIG.B_PLAYLIST_MODE:
                self.send_bot_msg(unicode_catalog.STATE + ' Retrieving *Official Charts* Top40 Singles.')

                charts_list = list(reversed(other.official_charts()))
                if charts_list is not None and charts_list is not False:
                    video_list = []
                    for track in charts_list:
                        youtube_search = youtube.search(track)
                        if youtube_search is not None:
                            video_list.append(youtube_search)

                    if len(video_list) > 0:
                        self.media.add_track_list(self.active_user.nick, video_list)
                        self.send_bot_msg(unicode_catalog.PENCIL +
                                          ' *Official Charts* have been *added*. Ready to play from *40 ' +
                                          unicode_catalog.ARROW_SIDEWAYS + ' 1*.')
                        # If there is no track playing at the moment, start this list.
                        if not self.media.has_active_track():
                            track = self.media.get_next_track()
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' *No search results were returned* from YouTube.')
                elif charts_list is False:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' The Top40 tracks could not be fetched.')
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' There is an issue in preparing to send the request.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *Playlist mode is switched off*, please turn it on to '
                                                             'add music from charts.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_radio_one_top40_charts(self):
        """ Retrieves the Top40 songs from the BBC Radio 1 charts and adds it to the playlist. """
        if self.is_client_mod:
            if pinylib.CONFIG.B_PLAYLIST_MODE:
                self.send_bot_msg(unicode_catalog.STATE + ' *Retrieving Top40* charts list.')

                # Get the latest charts list.
                charts_list = list(reversed(other.radio_top40_charts()))
                if charts_list is not None and charts_list is not False:
                    # Load a list of the videos from the charts list.
                    video_list = []
                    for track in charts_list:
                        youtube_search = youtube.search(track)
                        if youtube_search is not None:
                            video_list.append(youtube_search)

                    # Verify we have some videos to play and add them to the playlist.
                    if len(video_list) > 0:
                        self.media.add_track_list(self.active_user.nick, video_list)
                        self.send_bot_msg(unicode_catalog.PENCIL + ' *Top40* chart has been *added*. Ready to play from'
                                                                   ' *40 ' + unicode_catalog.ARROW_SIDEWAYS + ' 1*.')

                        # If there is no track playing at the moment, start this list.
                        if not self.media.has_active_track():
                            track = self.media.get_next_track()
                            self.send_media_broadcast_start(track.type, track.id)
                            self.media_event_timer(track.time)
                    else:
                        self.send_bot_msg(unicode_catalog.INDICATE + ' *No search results were returned* from YouTube.')
                elif charts_list is False:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' The Top40 tracks could not be fetched.')
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' There is an issue in preparing to send the request.')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' *Playlist mode is switched off*, please turn it on to '
                                                             'add music from charts.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Not enabled right now.')

    def do_duckduckgo_search(self, search_query):
        """ Shows information/definitions regarding a particular search on DuckDuckGo.

        :param search_query: Search query to search for.
        :type search_query: str
        """
        if len(search_query) is not 0:
            search_result = other.duck_duck_go_search(search_query)
            if search_result is not None:
                for part in range(len(search_result)):
                    if len(search_result[part]) > 160:
                        information = search_result[part][0:159] + '\n ' + search_result[part][159:]
                    else:
                        information = search_result[part]
                    self.send_bot_msg(str(part + 1) + ' *' + information + '*')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a search term to search on DuckDuckGo.')

    def do_imdb_search(self, search_entertainment):
        """ Shows information from the IMDb database OMDb, regarding a search for a show/movie.

        :param search_entertainment: The show/movie to search for on IMDb.
        :type search_entertainment: str
        """
        if len(search_entertainment) is not 0:
            omdb_details = other.omdb_search(search_entertainment)
            if omdb_details is not None:
                self.send_bot_msg(omdb_details)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' We could not find any details for: *%s*' %
                                  search_entertainment)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a *movie or television show* to load details.')

    def do_definition(self, lookup_term):
        """ Retrieves a definition for the term from the Longman Dictionary.

        :param lookup_term: The word to lookup in the dictionary.
        :type lookup_term: str
        """
        if len(lookup_term) is not 0:
            definitions = other.longman_dictionary(lookup_term)
            if definitions is not None:
                self.send_bot_msg('*Longman Dictionary\'s* definition(s) for: %s' % lookup_term)
                for definition in definitions:
                    self.send_bot_msg(definition)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' We could not find any definitions for: %s' % lookup_term)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a *look-up term* to search for a definition in'
                                                         ' the *Longman Dictionary*.')

    def do_one_liner(self, category):
        """ Show a random "one-liner" from a given category or one randomly picked from various categories.

        :param category: A specific category to pick a random joke from OR state '?' to
                         list all the possible categories.
        :type category: str
        """
        if len(category) is not 0:
            if category in other.ONE_LINER_TAGS:
                one_liner = other.one_liners(category)
                if one_liner is not None:
                    self.send_bot_msg('*' + one_liner + '*')
                else:
                    self.send_bot_msg(unicode_catalog.INDICATE + ' We were *unable to retrieve a "one-liner"* joke with'
                                                                 'under the category: %s.' % category)
            elif category == '?':
                all_categories = ', '.join(other.ONE_LINER_TAGS)
                self.send_undercover_msg(self.active_user.nick, '*Possible categories*: ' + str(all_categories))
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + 'We *do not recognise the category* you have entered.')
        else:
            one_liner = other.one_liners()
            if one_liner is not None:
                self.send_bot_msg('*' + one_liner + '*')
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' We were *unable to retrieve a "one-liner"* joke.')

    def do_food_recipe_search(self, search_ingredient):
        """ """
        if len(search_ingredient) is not 0:
            food_search = other.food_search(search_ingredient)
            if food_search is not None:
                self.send_bot_msg('*Food search*: ' + food_search)
            else:
                self.send_bot_msg(unicode_catalog.INDICATE + ' We were unable to retrieve food search results.')
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Please *enter an ingredient* to find recipes for.')

    def do_advice(self):
        """ Replies with a random line of advice. """
        advice_reply = other.online_advice()
        if advice_reply is not None:
            self.send_bot_msg('*' + unicode_catalog.NO_WIDTH + self.active_user.nick +
                              unicode_catalog.NO_WIDTH + '*, ' + advice_reply.lower())
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' We were *unable to retrieve an advice* from the website.')

    # TODO: When instant is used initially without using !cb to initialise the session,
    #       the instant message is not printed.
    # def do_cleverbot(self, cleverbot_query, instant_query=False):
    #     """ Shows the reply from CleverBot.
    #
    #     :param cleverbot_query: str the statement/question to ask CleverBot.
    #     :type cleverbot_query: str
    #     :param instant_query: True/False whether the request was from when a user typed in the client's nickname or
    #                           manually requested a response.
    #     :type instant_query: bool
    #     """
    #     if pinylib.CONFIG.B_CLEVERBOT:
    #         if len(cleverbot_query) is not 0:
    #             if self._cleverbot_session is None:
    #                 # Open a new connection to CleverBot in the event we do not already have one set up.
    #                 self._cleverbot_session = clever_client_bot.CleverBot()
    #                 # Start CleverBot message timer.
    #                 threading.Thread(target=self._cleverbot_timer).start()
    #                 if not instant_query:
    #                     self.send_bot_msg(unicode_catalog.VICTORY_HAND + ' *Waking up* ' + self.nickname)
    #
    #             if self._cleverbot_session is not None:
    #                 # Request the response from the server and send it as a normal user message.
    #                 response = self._cleverbot_session.converse(cleverbot_query)
    #                 if not instant_query:
    #                     self.send_bot_msg('*CleverBot* %s: %s' % (unicode_catalog.STATE, response))
    #                 else:
    #                     self.send_bot_msg(response, use_chat_msg=True)
    #
    #                 self.console_write(pinylib.COLOR['green'], '[CleverBot]: ' + response)
    #
    #             # Record the time at which the response was sent.
    #             self._cleverbot_msg_time = int(pinylib.time.time())
    #         else:
    #             if not instant_query:
    #                 self.send_bot_msg(unicode_catalog.INDICATE + ' Please enter a statement/question.')
    #     else:
    #         self.send_bot_msg(unicode_catalog.INDICATE + ' Please enable CleverBot to use this function.')

    def do_etymology_search(self, term_etymology):
        """ Searches the Etymonline website to return potential etymology for a word.

        :param term_etymology: The term you want to search the etymology for.
        :type term_etymology: str
        """
        if len(term_etymology) is not 0:
            etymology = other.etymonline(term_etymology)
            if etymology is not None:
                if len(etymology) > 295:
                    etymology_information = etymology[:294] + '...'
                    self.send_bot_msg(etymology_information)
                else:
                    self.send_bot_msg(etymology)
        else:
            self.send_bot_msg(unicode_catalog.INDICATE + ' Enter *search term* to lookup etymology for.')

    # Private Message Command Handler.
    def private_message_handler(self, private_msg):
        """ A user private message to the client.

        :param private_msg: The private message.
        :type private_msg: str
        """

        prefix = pinylib.CONFIG.B_PREFIX
        # Is this a custom PM command?
        if private_msg.startswith(prefix):
            # Split the message in to parts.
            pm_parts = private_msg.split(' ')
            # pm_parts[0] is the command.
            pm_cmd = pm_parts[0].lower().strip()
            # The rest is a command argument.
            pm_arg = ' '.join(pm_parts[1:]).strip()

            # Super mod commands.
            if self.has_level(1):
                if self.is_client_owner:
                    # Only possible if bot is using the room owner account.
                    if pm_cmd == prefix + 'rp':
                        threading.Thread(target=self.do_set_room_pass, args=(pm_arg,)).start()

                    elif pm_cmd == prefix + 'bp':
                        threading.Thread(target=self.do_set_broadcast_pass, args=(pm_arg,)).start()

                if pm_cmd == prefix + 'key':
                    self.do_key(pm_arg)

                elif pm_cmd == prefix + 'clrbn':
                    self.do_clear_bad_nicks()

                elif pm_cmd == prefix + 'clrbs':
                    self.do_clear_bad_strings()

                elif pm_cmd == prefix + 'clrba':
                    self.do_clear_bad_accounts()

            # Public commands.
            if self.has_level(5):
                if pm_cmd == prefix + 'opme':
                    self.do_opme(pm_arg)

                elif pm_cmd == prefix + 'pm':
                    self.do_pm_bridge(pm_parts)

        # Print to console.
        msg = str(private_msg).replace(pinylib.CONFIG.B_KEY, '***KEY***').replace(pinylib.CONFIG.B_SUPER_KEY,
                                                                                  '***SUPER KEY***')
        self.console_write(pinylib.COLOR['white'], 'Private message from %s: %s' % (self.active_user.nick, msg))

    def do_set_room_pass(self, password):
        """ Set a room password for the room.

        :param password: The room password.
        :type password: str
        """
        if self.is_client_owner:
            if not password:
                self.privacy_settings.set_room_password()
                self.send_bot_msg('*The room password was removed.*')
                pinylib.time.sleep(1)
                self.send_private_msg('The room password was removed.', self.active_user.nick)
            elif len(password) > 1:
                self.privacy_settings.set_room_password(password)
                self.send_private_msg('*The room password is now:* ' + password, self.active_user.nick)
                pinylib.time.sleep(1)
                self.send_bot_msg('*The room is now password protected.*')

    def do_set_broadcast_pass(self, password):
        """ Set a broadcast password for the room.

        :param password: The broadcast password.
        :type password: str | None
        """
        if self.is_client_owner:
            if not password:
                self.privacy_settings.set_broadcast_password()
                self.send_bot_msg('*The broadcast password was removed.*')
                pinylib.time.sleep(1)
                self.send_private_msg('The broadcast password was removed.', self.active_user.nick)
            elif len(password) > 1:
                self.privacy_settings.set_broadcast_password(password)
                self.send_private_msg('*The broadcast password is now:* ' + password, self.active_user.nick)
                pinylib.time.sleep(1)
                self.send_bot_msg('*Broadcast password is enabled.*')

    def do_key(self, new_key):
        """ Shows or sets a new secret key.

        :param new_key: The new secret key.
        :type new_key: str
        """
        if len(new_key) is 0:
            self.send_private_msg('The current key is: *%s*' % pinylib.CONFIG.B_KEY, self.active_user.nick)
        elif len(new_key) < 6:
            self.send_private_msg('*Key must be at least 6 characters long:* %s' % len(new_key),
                                  self.active_user.nick)
        elif len(new_key) >= 6:
            # Reset all bot controllers back to normal users.
            for user in self.users.all:
                if self.users.all[user].user_level is 2 or self.users.all[user].user_level is 4:
                    self.users.all[user].user_level = 5
            pinylib.CONFIG.B_KEY = new_key
            self.send_private_msg('The key was changed to: *%s*' % new_key, self.active_user.nick)

    def do_clear_bad_nicks(self):
        """ Clears the bad nicks file. """
        pinylib.CONFIG.B_NICK_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path(), pinylib.CONFIG.B_NICK_BANS_FILE_NAME)

    def do_clear_bad_strings(self):
        """ Clears the bad strings file. """
        pinylib.CONFIG.B_STRING_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path(), pinylib.CONFIG.B_STRING_BANS_FILE_NAME)

    def do_clear_bad_accounts(self):
        """ Clears the bad accounts file. """
        pinylib.CONFIG.B_ACCOUNT_BANS[:] = []
        pinylib.file_handler.delete_file_content(self.config_path(), pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME)

    # == Public PM Command Methods. ==
    def do_opme(self, key):
        """ Makes a user a bot controller if user provides the right key.

        :param key: A secret key.
        :type key: str
        """
        if len(key) is 0:
            self.send_private_msg('Missing key.', self.active_user.nick)
        elif key == pinylib.CONFIG.B_SUPER_KEY:
            if self.is_client_owner:
                self.active_user.user_level = 1
                self.send_private_msg('*You are now a super mod.*', self.active_user.nick)
            else:
                self.send_private_msg('*The client is not using the owner account.*', self.active_user.nick)
        elif key == pinylib.CONFIG.B_KEY:
            if self.is_client_mod:
                self.active_user.user_level = 2
                self.send_private_msg('*You are now a bot controller.*', self.active_user.nick)
            else:
                self.send_private_msg('*The client is not moderator.*', self.active_user.nick)
        else:
            self.send_private_msg('Wrong key.', self.active_user.nick)

    def do_pm_bridge(self, pm_parts):
        """ Makes the bot work as a PM message bridge between 2 user who are not signed in.

        :param pm_parts: The pm message as a list separated by the words given in the message.
        :type pm_parts: list
        """
        if len(pm_parts) == 1:
            self.send_private_msg('Missing username.', self.active_user.nick)
        elif len(pm_parts) == 2:
            self.send_private_msg('The command is: ' + pinylib.CONFIG.B_PREFIX + 'pm username message',
                                  self.active_user.nick)
        elif len(pm_parts) >= 3:
            pm_to = pm_parts[1]
            msg = ' '.join(pm_parts[2:])
            is_user = self.users.search(pm_to)
            if is_user is not None:
                if is_user.id == self._client_id:
                    self.send_private_msg('Action not allowed.', self.active_user.nick)
                else:
                    self.send_private_msg('*<' + self.active_user.nick + '>* ' + msg, pm_to)
            else:
                self.send_private_msg('No user named: ' + pm_to, self.active_user.nick)

    # Timed auto functions.
    def media_event_handler(self):
        """ This method gets called whenever a media is done playing. """
        # If there is a track is playing and we are limiting the media time, then close the media.
        # if pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST or pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC:
        #     print('Limiting turned on.')
        #     if self.media.has_active_track():
        #         print('Track is playing, closing it.')
        #         self.do_close_media()

        if len(self.media.track_list) > 0:
            if self.media.is_last_track():
                self.media.clear_track_list()
            else:
                # Add a media delay to add a gap between the each video/track that is played in the room.
                pinylib.time.sleep(self.media_delay)

                # Process the next track in the playlist, if we are not using the custom radio mode.
                track = self.media.get_next_track()
                if track is not None and self.is_connected:
                    self.send_media_broadcast_start(track.type, track.id)
                self.media_event_timer(track.time)

    def media_event_timer(self, video_time):
        """ Start a media event timer.

        :param video_time: The time in milliseconds.
        :type video_time: int
        """
        # If we are limiting the media duration set the video time to be the limited duration.
        # if not pinylib.CONFIG.B_MEDIA_LIMIT_PLAYLIST and not pinylib.CONFIG.B_MEDIA_LIMIT_PUBLIC:
        #     video_time_in_seconds = video_time / 1000
        # else:
        #     video_time_in_seconds = pinylib.CONFIG.B_MEDIA_LIMIT_DURATION

        # Star the media timer thread.
        self.media_timer_thread = threading.Timer(video_time/1000, self.media_event_handler)  # video_time_in_seconds
        self.media_timer_thread.start()

    # Helper Methods.
    def get_privacy_settings(self):
        """ Parse the privacy settings page. """
        log.info('Parsing %s\'s privacy page. Proxy %s' % (self.account, self._proxy))
        self.privacy_settings = privacy.Privacy(self._proxy)
        self.privacy_settings.parse_privacy_settings()

    def config_path(self):
        """ Returns the path to the rooms configuration directory. """
        path = pinylib.CONFIG.CONFIG_PATH + self.roomname + '/'
        return path

    # TODO: Implement blocked media lists.
    def load_list(self, nicks=False, accounts=False, strings=False, blocked_media=False):
        """ Loads different list to memory.

        :param nicks: True load nick bans file.
        :type nicks: bool
        :param accounts: True load account bans file.
        :type accounts: bool
        :param strings: True load ban strings file.
        :type strings: bool

        :param blocked_media: True load blocked media file.
        :type blocked_media: bool
        """
        if nicks:
            pinylib.CONFIG.B_NICK_BANS = pinylib.file_handler.file_reader(self.config_path(),
                                                                          pinylib.CONFIG.B_NICK_BANS_FILE_NAME)
        if accounts:
            pinylib.CONFIG.B_ACCOUNT_BANS = pinylib.file_handler.file_reader(self.config_path(),
                                                                             pinylib.CONFIG.B_ACCOUNT_BANS_FILE_NAME)
        if strings:
            pinylib.CONFIG.B_STRING_BANS = pinylib.file_handler.file_reader(self.config_path(),
                                                                            pinylib.CONFIG.B_STRING_BANS_FILE_NAME)

        # if blocked_media:
        #     pinylib.CONFIG.B_BLOCKED_MEDIA = pinylib.file_handler.file_reader(self.config_path(),
        #                                                                       pinylib.CONFIG.B_BLOCKED_MEDIA_FILE_NAME)

    def has_level(self, level):
        """ Checks the active user for correct user level.

        :param level: The level to check the active user against.
        :type level: int
        """
        if self.active_user.user_level is 6:
            return False
        elif self.active_user.user_level <= level:
            return True
        return False

    def cancel_media_event_timer(self):
        """ Cancel the media event timer if it is running.

        :return: True if canceled, else False.
        :rtype: bool
        """
        if self.media_timer_thread is not None:
            if self.media_timer_thread.is_alive():
                self.media_timer_thread.cancel()
                self.media_timer_thread = None
                return True
            return False
        return False

    @staticmethod
    def format_time(milliseconds):
        """ Converts milliseconds to (day(s)) hours minutes seconds.

        :param milliseconds: Milliseconds to convert.
        :type milliseconds: int
        :return: A string in the format (days) hh:mm:ss.
        :rtype: str
        """
        m, s = divmod(milliseconds/1000, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)

        if d == 0 and h == 0:
            human_time = '%02d:%02d' % (m, s)
        elif d == 0:
            human_time = '%d:%02d:%02d' % (h, m, s)
        else:
            human_time = '%d Day(s) %d:%02d:%02d' % (d, h, m, s)
        return human_time

    def check_msg(self, msg):
        """ Checks the chat message for bad string.

        :param msg: The chat message.
        :type msg: str
        """
        was_banned = False
        chat_words = msg.split(' ')
        for bad in pinylib.CONFIG.B_STRING_BANS:
            if bad.startswith('*'):
                _ = bad.replace('*', '')
                if _ in msg:
                    self.send_ban_msg(self.active_user.nick, self.active_user.id)
                    was_banned = True
            elif bad in chat_words:
                    self.send_ban_msg(self.active_user.nick, self.active_user.id)
                    was_banned = True

        # Make sure we return a boolean value, so we can indicate to stop sanitizing the message,
        # in the sanitize message function.
        if was_banned:
            if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                self.send_forgive_msg(self.active_user.id)
            return True
        return False

    def check_nick(self, old, user_info):
        """ Check a users nick.

        :param old: The old nickname of the user.
        :type old: str
        :param user_info: The User object. This will contain the new nick.
        :type user_info: User
        """
        if self._client_id != user_info.id:
            if str(old).startswith('guest-') and self.is_client_mod:
                if str(user_info.nick).startswith('guest-'):
                    if not pinylib.CONFIG.B_ALLOW_GUESTS_NICKS:
                        self.send_ban_msg(user_info.nick, user_info.id)
                        self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned*: (bot nick detected)')
                        return True
                if str(user_info.nick).startswith('newuser'):
                    if not pinylib.CONFIG.B_ALLOW_NEWUSERS:
                        self.send_ban_msg(user_info.nick, user_info.id)
                        self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned*: (newuser detected)')
                        return True
                if len(pinylib.CONFIG.B_NICK_BANS) > 0:
                    for bad_nick in pinylib.CONFIG.B_NICK_BANS:
                        if bad_nick.startswith('*'):
                            a = bad_nick.replace('*', '')
                            if a in user_info.nick:
                                self.send_ban_msg(user_info.nick, user_info.id)
                                self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned*: (bad nick)')
                                return True
                        elif user_info.nick in pinylib.CONFIG.B_NICK_BANS:
                                self.send_ban_msg(user_info.nick, user_info.id)
                                self.send_bot_msg(unicode_catalog.TOXIC + '*Auto-Banned*: (bad nick)')
                                return True
                return False

    # TODO: Evaluate design.
    def sanitize_message(self, decoded_msg):
        """ Spam checks to ensure chat box is rid any potential further spam.

        NOTE: This function should only be executed if the client is a moderator,
              make sure there is a check to see if that is true before allowing the this to run.

        :param decoded_msg: The message the user sent.
        :type decoded_msg: str
        """
        # Reset the spam check at each message check, this allows us to know if the message should be passed onto
        # any further procedures.
        # TODO: Test to see if this works or not.
        spam_characters = [u'\u0020', u'\u0085', u'\u0333', u'\u25B2']
        # TODO: What do ',8192', ',10' (line break/feed), ',9650' stand for in unicode?

        # Ban those who post messages with special unicode characters which is considered spam.
        if pinylib.CONFIG.B_UNICODE_SPAM:
            decoded_msg_pieces = [decoded_msg.strip()]
            for spam_unicode in range(len(spam_characters)):
                if spam_characters[spam_unicode] in decoded_msg_pieces:
                    self.send_ban_msg(self.active_user.nick, self.active_user.id)
                    return True

        # Always check to see if the user's message in the chat contains any bad strings.
        checked_message = self.check_msg(decoded_msg)
        if checked_message:
            return True

        # TODO: Working method.
        # Kick/ban those who post links to other rooms.
        if pinylib.CONFIG.B_TINYCHAT_ROOM_LINK_SPAM:
            # TODO: You could get around this by inserting a small link to the current room in with lots of
            #       other links elsewhere
            # We need to check to see if the message does not contain the current room's link and that
            # we do not unnecessarily ban due to a snapshot message containing the website address in the message.
            # Many thanks to "zootshecfur" for pointing this out.
            if 'tinychat.com/' + self.roomname not in decoded_msg and self._snapshot_message not in decoded_msg:
                # TODO: Regex does not handle carriage returns after the string - Added more regex to handle
                #       line feed, whitespaces and various possible ways of the URL displaying (and on multiple lines).
                #       any characters after it. Previous: r'tinychat.com\/\w+($| |\/+ |\/+$)'
                #       Now: r'tinychat.com\/\w+|tinychat. com\/\w+|tinychat .com\/\w+($| |\/+ |\/+$|\n+)\s'

                # Perform searching on the strings with 'tinychat.com' in them.
                msg_search = self._tinychat_spam_pattern.search(decoded_msg)
                if msg_search is not None:
                    located = msg_search.group()
                    if located[0] is not None:
                        self.send_ban_msg(self.active_user.nick, self.active_user.id)
                        # TODO: Optionally put in the forgive auto-bans.
                        if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                            self.send_forgive_msg(self.active_user.id)
                        return True

        # Ban those who post excessive messages in both uppercase and exceeding a specified character limit.
        if pinylib.CONFIG.B_CAPITAL_CHARACTER_LIMIT:
            # if len(raw_msg) >= self.caps_char_limit:
            # Search for all caps and numbers in the message which exceed the length of the characters stated in
            # the character limit.
            # TODO: Test if character limit regex works or not: r'[A-Z+0-9+\W+]{50,}' OR [A-Z0-9]
            # regex_pattern = r'[A-Z0-9\W+]{%s,}' % self.caps_char_limit
            over_limit = self._character_limit_pattern.search(decoded_msg)
            if over_limit:
                self.send_ban_msg(self.active_user.nick, self.active_user.id)
                if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                    self.send_forgive_msg(self.active_user.id)
                return True

        # If snapshot prevention is on, make sure we kick/ban any user taking snapshots in the room.
        if not pinylib.CONFIG.B_ALLOW_SNAPSHOTS:
            if self._snapshot_message in decoded_msg:
                self.send_ban_msg(self.active_user.nick, self.active_user.id)
                if pinylib.CONFIG.B_FORGIVE_AUTO_BANS:
                    self.send_forgive_msg(self.active_user.id)
                return True

    def identify_url(self, text_to_identify):
        """ Identify if a piece of text is a URL and to retrieve the address if it is.

        Search for possible URLs using a regex pattern.
        Pattern was found on StackOverflow, answered with by user
        "CodeWrite" (http://stackoverflow.com/users/454718/codewrite).
        Regex: '(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'

        :param text_to_identify:
        :type text_to_identify: str
        :return identified, identified_result:
        :rtype identified: boolean
        :rtype identified_result: boolean
        """
        # Use the regex pattern to check the text for a URL.
        url_search = self._automatic_url_identifier_pattern.search(text_to_identify)
        if url_search is not None:
            # Pick out the URL from the identified text.
            identified_url = url_search.group()
            if identified_url is not None:
                return True, identified_url
        return False, None

    # TODO: Prevent auto-url colliding with CleverBot, if part of the url is the same as the nickname of the client.
    # TODO: Should we capture more than one url in a message?
    # TODO: Evaluate design.
    def do_auto_url(self, decoded_message):
        """ Retrieve header information for a given link.

        :param decoded_message: The complete message sent by the user, which we will check for a URL.
        :type decoded_message: str
        """
        # TODO: We don't want auto-url to be called on every message, make sure there is a URL in the message first.
        # Make sure we read all the url's in lowercase to make processes quicker.
        # TODO: Replaced section with regex to retrieve url.
        # TODO: If an exclamation mark is in the URL, will this not proceed?
        if ('!' not in decoded_message) and ('tinychat.com' not in decoded_message):
            identified, identified_url = self.identify_url(decoded_message)
            if identified and identified_url is not None:
                # Retrieve the website title.
                url_title = auto_url.auto_url(identified_url)
                if url_title is not None:
                    self.send_owner_run_msg(unicode_catalog.DAGGER_FOOTNOTE + ' *' + url_title + '*')
                    self.console_write(pinylib.COLOR['cyan'], '%s posted a URL: %s' %
                                       (self.active_user.nick, url_title))
                    return True
        return False

    # TODO: Evaluate design.
    # TODO: Added CleverBot instant call.
    # def cleverbot_message_handler(self, decoded_msg):
    #     """ CleverBot message handler handles incoming decoded messages and provides it to the right function.
    #
    #     :param decoded_msg: The message that was sent into the room.
    #     :type decoded_msg: str
    #     :return: bool True/False
    #     """
    #     if pinylib.CONFIG.B_CLEVERBOT and pinylib.CONFIG.B_INSTANT_CLEVERBOT:
    #         if self.nickname in decoded_msg.lower():
    #             query = decoded_msg.lower().replace(self.nickname, '')
    #             self.console_write(pinylib.COLOR['yellow'], '%s [CleverBot]: %s' % (self.active_user.nick,
    #                                                                                 query.strip()))
    #             self.do_cleverbot(query, True)

    # TODO: Evaluate design - we do not need this in the event that we restrict the form data.
    # TODO: Added in a timer to monitor the CleverBot session & reset the messages periodically.
    # def _cleverbot_timer(self):
    #     """ Clear POST data from CleverBot sessions
    #
    #     NOTE: If messages are sent to CleverBot within 2.5 minutes (150 seconds),
    #           otherwise clear all the data that was previously recorded.
    #
    #           Due to clearing POST data, anything asked, before clearing, to CleverBot may
    #           reply with an inaccurate reply as we are not including the POST data with the request.
    #     """
    #     # Reset the POST log in the CleverBot instance to an empty list in order to clear the previous
    #     # message history. This occurs if it has been 5 minutes or great since the last message
    #     # has been sent and stored in the log.
    #     while self._cleverbot_session is not None:
    #         if int(pinylib.time.time()) - self._cleverbot_msg_time >= 150 and \
    #                         len(self._cleverbot_session.post_log) is not 0:
    #             self._cleverbot_session.post_log = []
    #             self._cleverbot_msg_time = int(pinylib.time.time())
    #         pinylib.time.sleep(1)

    # TODO: Support SoundCloud.
    # def _auto_play_radio_track(self):
    #     """
    #     Handles adding YouTube media content to the playlist from the artist and track information on
    #     the Capital FM Radio website.
    #     """
    #     if pinylib.CONFIG.B_RADIO_CAPITAL_FM_AUTO_PLAY:
    #         # Retrieve the artist name and track title from Capital FM.
    #         radio_now_playing = other.capital_fm_latest()
    #         # Make sure we are not playing the same track again, if we have received the same track,
    #         # we can use the timer to wait another 2 minutes before checking again.
    #         if self.latest_radio_track == radio_now_playing:
    #             self.similar_radio_tracks += 1
    #             if self.similar_radio_tracks > 2:
    #                 self.send_bot_msg('*Capital FM Radio*: If you are receiving similar/same tracks this could mean '
    #                                   'the radio station has switched to another provider. Please switch the radio off'
    #                                   'with *!stopradio* and use it 6 or 7 hours later.')
    #                 self.similar_radio_tracks = 0
    #             self.radio_event_timer(60000)
    #         else:
    #             self.latest_radio_track = radio_now_playing
    #             print('Information received: ', radio_now_playing)
    #             if radio_now_playing is not None:
    #                 # Retrieve a matching video from YouTube.
    #                 _radio_video = youtube.search(radio_now_playing)
    #                 print('video found:', _radio_video)
    #                 if _radio_video is not None:
    #                     # Add to the playlist if there is a track playing already.
    #                     # TODO: If another track is playing when we add a new track, the radio timer thread will
    #                     #       not compensate for the time remaining on the current track before starting the
    #                     #       radio event timer.
    #                     if self.media.has_active_track():
    #                         radio_track = self.media.add_track(self.active_user.nick, _radio_video)
    #                         self.send_bot_msg(unicode_catalog.MUSICAL_NOTE_SIXTEENTH +
    #                                           ' *Added Capital FM Radio Track* ' +
    #                                           unicode_catalog.MUSICAL_NOTE_SIXTEENTH + ': ' + radio_track.title)
    #
    #                         # TODO: Make sure the remaining time is in milliseconds and this is working.
    #                         # Start the radio timer (taking into account the time remaining on the current media).
    #                         self.radio_event_timer(self.media.remaining_time() + radio_track.time)
    #                     else:
    #                         # Start the track if there was nothing playing.
    #                         radio_track = self.media.mb_start(self.active_user.nick, _radio_video)
    #                         self.send_media_broadcast_start(radio_track.type, radio_track.id)
    #                         self.media_event_timer(radio_track.time)
    #
    #                         # Start the radio event timer to call this function again, when the track finishes.
    #                         self.radio_event_timer(radio_track.time)
    #                 else:
    #                     # TODO: If we can't find a video, should we wait and check again?
    #                     self.send_bot_msg(unicode_catalog.INDICATE + ' We could not find a *YouTube* video for: *' +
    #                                       radio_now_playing + '*')
    #                     self.send_bot_msg(unicode_catalog.INDICATE + ' We will wait a while until searching for a new '
    #                                                                  'track.')
    #                     # If we did not find anything we will check after a minute.
    #                     self.radio_event_timer(60000)
    #             else:
    #                 self.send_bot_msg(unicode_catalog.INDICATE +
    #                                   ' We were unable to retrieve any songs from Capital FM.')

    # TODO: Does the timer automatically start in a timer?
    # def radio_event_timer(self, wait_time):
    #     """ Radio Event Time to handle the radio auto-play events.
    #
    #     :param wait_time: The time to wait until we should add another track.
    #     :type wait_time: int
    #     """
    #     wait_time_in_seconds = wait_time / 1000
    #     self.radio_timer_thread = threading.Timer(wait_time_in_seconds, self._auto_play_radio_track)
    #     self.radio_timer_thread.start()
    #
    # def cancel_radio_event_timer(self):
    #     """ Cancel active radio auto-play events. """
    #     if self.radio_timer_thread is not None:
    #         if self.radio_timer_thread.is_alive():
    #             self.radio_timer_thread.cancel()
    #             self.radio_timer_thread = None
    #         return False
    #     return False
    #
