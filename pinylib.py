# -*- coding: utf-8 -*-
""" Pinylib module by Nortxort (https://github.com/nortxort/pinylib). """

# Edited for specifically for pinybot (https://github.com/GoelBiju/pinybot/)

import getpass
import logging
import os
import random
import sys
import threading
import time
import traceback
from colorama import init, Fore, Style

import about
from qrtmp import rtmp
from apis import tinychat
from files import file_handler as fh
from utilities import string_utili

# TODO: Remove the use of quote_plus here.
from urllib import quote_plus

__version__ = '5.0.2'

#  Console colors.
# Set console colors as false in the configuration file to prevent colorama from loading in interpreters or consoles
# which do not support the rendering of colors.
COLOR = {
    'white': Fore.WHITE,
    'green': Fore.GREEN,
    'bright_green': Style.BRIGHT + Fore.GREEN,
    'yellow': Fore.YELLOW,
    'bright_yellow': Style.BRIGHT + Fore.YELLOW,
    'cyan': Fore.CYAN,
    'bright_cyan': Style.BRIGHT + Fore.CYAN,
    'red': Fore.RED,
    'bright_red': Style.BRIGHT + Fore.RED,
    'magenta': Fore.MAGENTA,
    'bright_magenta': Style.BRIGHT + Fore.MAGENTA
}


# TODO: Restrict the configuration parser to read from defined sections in the configuration file.
# Procedure to load configuration in the root directory.
def load_config(config_file_name, section=None):
    """
    A procedure to load any configuration file (.ini) stated in the given parameter.
    :param config_file_name: str the location of the configuration to load.
    :param section: A particular section in the configuration file that the content should be retrieved from.
    :return: The configuration dictionary and the configuration path which it was found in.
    """
    current_path = sys.path[0]
    config_path = current_path + config_file_name
    # Load the configuration dictionary (if a section is specified, then from that section in the file).
    conf = fh.configuration_loader(config_path, section)
    return conf, config_path

# State the name of the '.ini' configuration file here:
CONFIG_FILE_NAME = '/config.ini'
# Make sure we only parse the 'base' section in the configuration.
CONFIG, CONFIG_PATH = load_config(CONFIG_FILE_NAME, 'Base')
if CONFIG is None:
    print('No file named %s found in: %s \nWe cannot proceed to start-up without the configuration file.' %
          (CONFIG_FILE_NAME, CONFIG_PATH))
    # Exit to system safely whilst returning exit code 1.
    sys.exit(1)

if CONFIG['console_colors']:
    init(autoreset=True)

log = logging.getLogger(__name__)


def write_to_log(msg, room_name):
    """
    Writes chat events to log.
    The room name is used to construct a log file name from.
    :param msg: str the message to write to the log.
    :param room_name: str the room name.
    """
    d = time.strftime('%Y-%m-%d')
    file_name = d + '_' + room_name + '.log'
    path = CONFIG['config_path'] + room_name + '/logs/'
    fh.file_writer(path, file_name, msg.encode(encoding='UTF-8', errors='ignore'))


def set_window_title(window_message):
    """
    Set the console title depending on OS by correctly encoding the message.
    :param window_message: str the message we want to set as the title.
    """
    other_operating_systems = ['posix', 'os2', 'ce', 'java', 'riscos']

    if os.name in other_operating_systems:
        window_title = "echo -e '\033]2;''" + window_message + "''\007'"
    else:
        window_title = 'title ' + str(window_message)
    os.system(window_title)


class User:
    """
    A user object to hold info  about a user.

    Each user will have an object associated with their username.
    The object is used to store information about the user.
    """

    def __init__(self, **kwargs):
        """

        @param kwargs:
        """
        self.lf = kwargs.get('lf', None)
        self.account = kwargs.get('account', '')
        self.is_owner = kwargs.get('own', False)
        self.gp = kwargs.get('gp', 0)
        self.alevel = kwargs.get('alevel', '')
        self.bf = kwargs.get('bf', False)
        self.nick = kwargs.get('nick', None)
        self.btype = kwargs.get('btype', '')
        self.id = kwargs.get('id', -1)
        self.stype = kwargs.get('stype', 0)
        self.is_mod = kwargs.get('mod', False)

        self.tinychat_id = None
        self.last_login = None

        # Extras.
        self.last_msg = None
        self.has_power = False
        self.is_super = False


class TinychatRTMPClient:
    """ Manages a single room connection to a given room. """

    def __init__(self, room, tcurl=None, app=None, room_type=None, nick=None, account='',
                 password=None, room_pass=None, ip=None, port=None, proxy=None):
        """

        @param room:
        @param tcurl:
        @param app:
        @param room_type:
        @param nick:
        @param account:
        @param password:
        @param room_pass:
        @param ip:
        @param port:
        @param proxy:
        """
        # Internal settings:
        self.client_nick = nick
        self.account = account
        self.password = password
        self.room_pass = room_pass
        self.connection = None
        self.user = object
        self.is_connected = False
        self.raw_msg = ''

        # Connection settings:
        self._roomname = room
        self._tc_url = tcurl
        self._app = app
        self._room_type = room_type
        self._ip = ip
        self._port = port
        self._proxy = proxy
        self._greenroom = False
        self._prefix = u'tinychat'
        self._swf_url = u'http://tinychat.com/embed/Tinychat-11.1-1.0.0.{0}.swf?version=1.0.0.{0}/[[DYNAMIC]]/8' \
                        .format(CONFIG['swf_version'])
        self._desktop_version = u'Desktop 1.0.0.%s' % CONFIG['swf_version']
        self._embed_url = u'http://tinychat.com/' + self._roomname
        self._client_id = None
        self._bauth_key = None
        self._is_reconnected = False
        self._is_client_mod = False
        self._is_client_owner = False
        self._b_password = False
        self._room_users = {}
        self._reconnect_delay = CONFIG['reconnect_delay']
        self._init_time = time.time()

        # TODO: Flash-dummy version moved into the rtmp library.

        # Stream settings:
        # TODO: All these should be handled in NetStream section of the rtmp library.
        self._streams = {}
        self._selected_stream_name = None
        self._stream_sort = False
        self._publish_connection = False
        # self._manual_time_stamp = 0
        self.allow_audio = False
        self.allow_video = True

        # External settings:
        # TODO: Removed RTMPE connection configuration option from the configuration file.

        self._private_room = False
        self._room_banlist = {}
        self._topic_msg = None

    def console_write(self, color, message):
        """
        Writes message to console.
        :param color: the colorama color representation.
        :param message: str the message to write.
        """
        if CONFIG['use_24hour']:
            ts = time.strftime('%H:%M:%S')
        else:
            ts = time.strftime('%I:%M:%S:%p')
        if CONFIG['console_colors']:
            msg = COLOR['white'] + '[' + ts + '] ' + Style.RESET_ALL + color + message
        else:
            msg = '[' + ts + '] ' + message
        try:
            print(msg.encode(encoding='UTF-8', errors='ignore'))
        except UnicodeEncodeError as ue:
            log.error(ue, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()

        if CONFIG['chat_logging']:
            write_to_log('[' + ts + '] ' + message, self._roomname)

    def prepare_connect(self):
        """ Gather necessary connection parameters before attempting to connect. """
        if self.account and self.password:
            log.info('Deleting old login cookies.')
            tinychat.delete_login_cookies()

            # TODO: Account names can be shorter than 3 characters.
            # if len(self.account) > 3:
            log.info('Trying to log in with account: %s' % self.account)
            login = tinychat.post_login(self.account, self.password)
            if 'pass' in login['cookies']:
                log.info('Logged in as: %s Cookies: %s' % (self.account, login['cookies']))
                self.console_write(COLOR['green'], 'Logged in as: ' + login['cookies']['user'])
            else:
                # TODO: We sometimes keep on getting repeated "log in failed" messages even though we are
                #       entering in the right username and password.
                self.console_write(COLOR['red'], 'Log in Failed')
                self.account = raw_input('Enter account (optional): ')
                # TODO: Will leaving this blank assume we are logging in with an account to the library?
                if self.account:
                    self.password = getpass.getpass('Enter password (password hidden): ')
                self.prepare_connect()

            # TODO: Account names can be shorter than 3 characters.
            # else:
            #     self.console_write(COLOR['red'], 'Account name is too short.')
            #     self.account = raw_input('Enter account: ')
            #     self.password = getpass.getpass('Enter password (password hidden): ')
            #     self.prepare_connect()

        self.console_write(COLOR['white'], 'Parsing room config xml...')
        config = tinychat.get_roomconfig_xml(self._roomname, self.room_pass, proxy=self._proxy)

        if config == 'CLOSED':
            self.console_write(COLOR['red'], 'This room is closed.')
            sys.exit(0)

        while config == 'PW':
            self.room_pass = raw_input('The room is password protected. Enter room password (password hidden): ')
            if not self.room_pass:
                self._roomname = raw_input('Enter room name: ')
                self.room_pass = getpass.getpass('Enter room pass (optional:password hidden): ')
                self.account = raw_input('Enter account (optional): ')
                self.password = getpass.getpass('Enter password (optional:password hidden): ')
                self.prepare_connect()
            else:
                config = tinychat.get_roomconfig_xml(self._roomname, self.room_pass, proxy=self._proxy)
                if config != 'PW':
                    break
                else:
                    self.console_write(COLOR['red'], 'Password Failed.')

        if CONFIG['debug_mode']:
            for k in config:
                self.console_write(COLOR['white'], k + ': ' + str(config[k]))

        log.info('RTMP info found: %s' % config)
        self._ip = config['ip']
        self._port = config['port']
        self._tc_url = config['tcurl']
        self._app = config['app']
        self._room_type = config['roomtype']
        self._greenroom = config['greenroom']
        self._b_password = config['bpassword']

        self.console_write(COLOR['white'], '============ CONNECTING ============\n\n')
        self.connect()

    def connect(self):
        """ Attempts to make a RTMP connection with the given connection parameters. """
        if not self.is_connected:
            log.info('Trying to connect to: %s' % self._roomname)
            try:
                tinychat.recaptcha(proxy=self._proxy)
                cauth_cookie = tinychat.get_cauth_cookie(self._roomname, proxy=self._proxy)

                # TODO: Adapted connection style to match base; dictionary format.
                # TODO: Edit the connection process to match new rtmp library structure.
                # Initialise our RTMP library to communicate with the RTMP server:
                self.connection = rtmp.RtmpClient(self._ip, self._port, app=self._app, tc_url=self._tc_url,
                                                  page_url=self._embed_url, swf_url=self._swf_url, proxy=self._proxy)

                # Setup our custom connection object:
                self.connection.custom_connect_params(
                    {
                        'room': self._roomname,
                        'type': self._room_type,
                        'prefix': self._prefix,
                        'account': self.account,
                        'cookie': cauth_cookie,
                        'version': self._desktop_version
                    }
                )

                # Attempt a connection and return the connection status.
                self.is_connected = self.connection.connect()

                # After-hand connection settings:
                # - set windows title when connected with information regarding the room:
                #   '"ROOMNAME" - IP ADDRESS:PORT':
                window_message = '"%s" - %s:%s' % (self._roomname, self._ip, self._port)
                set_window_title(window_message)

                # - reset the connection runtime in the event of a new connection being made:
                if CONFIG['reset_time']:
                    self._init_time = time.time()

                # - start command (callbacks) handle:
                self._callback()

            except Exception as ex:
                log.error('Connect error: %s' % ex, exc_info=True)
                if CONFIG['debug_mode']:
                    traceback.print_exc()
                self.reconnect()

    def disconnect(self):
        """ Closes the RTMP connection with the remote server. """
        log.info('Disconnecting from server.')
        try:
            # Reset default variables.
            self.is_connected = False
            self._is_client_mod = False
            self._bauth_key = None
            self._room_users.clear()

            # Reset custom variables.
            self._room_banlist.clear()

            self.connection.disconnect()
        except Exception as ex:
            log.error('Disconnect error: %s' % ex, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()

    def reconnect(self):
        """ Reconnect to a room with the connection parameters already set. """
        reconnect_msg = '============ RECONNECTING IN ' + str(self._reconnect_delay) + ' SECONDS ============'
        log.info('Reconnecting: %s' % reconnect_msg)
        self.console_write(COLOR['bright_cyan'], reconnect_msg)
        self._is_reconnected = True
        self.disconnect()
        time.sleep(self._reconnect_delay)

        # Increase reconnect_delay after each reconnect.
        self._reconnect_delay *= 2
        if self._reconnect_delay > 900:
            self._reconnect_delay = CONFIG['reconnect_delay']

        if self.account and self.password:
            self.prepare_connect()
        else:
            self.connect()

    def _callback(self):
        """ Callback loop reading RTMP messages from the RTMP stream. """
        log.info('Starting the callback loop.')
        failures = 0
        # TODO: We do not need amf0_data_type, amf_data_type, amf0_data,
        #       since the header automatically initialises it as -1.
        packet = None
        while self.is_connected:
            try:
                # TODO: Previous read packet calls were known as:
                # amf0_data = self.connection.reader.next() and packet = self.connection.reader.read_packet().
                packet = self.connection.read_packet()

                if CONFIG['debug_mode']:
                    print(packet.body)

                # TODO: Removed the setting of amf0_data_type and amf_data_type.

            except Exception as ex:
                failures += 1
                log.error('amf data read error count: %s %s' % (failures, ex), exc_info=True)
                if failures == 2:  # The amount of failures we allow before doing a reconnect.
                    if CONFIG['debug_mode']:
                        traceback.print_exc()
                    # TODO: Reconnect is called here in the event we cannot receive any data.
                    self.reconnect()
                    break
            else:
                failures = 0
            try:
                # TODO: Moved handled by default into the rtmp library.
                # TODO: We may not require the try anymore, since everything goes through the handle_packet
                # TODO: Rename 'command'.
                # TODO: Allow us to check if the body of the packet is AMF and then parse callbacks.
                # TODO: Should we have iparam and have read packet return a full list of parsed AMF data,
                #       as opposed to the dictionary.
                # TODO: Retrieve based on whether the body is AMF formatted or not.
                if packet.body_is_amf:
                    cmd = packet.get_command_name()
                    packet_response = packet.get_response()
                    # TODO: Categorise into which callbacks we expect response data from and those which we do not.
                    # TODO: Simplify iparam0 without misconstruing the meaning.
                    # TODO: Order these callbacks in the order we think we should be receiving from the server.
                    # TODO: Command data parsing index value edits to match the response key value.
                    # TODO: Some of these (_result, _error, onBWDone, OnStatus) are all default RTMP callbacks,
                    #       it should be handled by the rtmp client.
                    # TODO: amf0_cmd was moved to being called amf_cmd before being altered to packet_response.
                    if cmd == '_result':
                        if self._stream_sort:
                            # Set streams for the client.
                            self._stream_manager(self._selected_stream_name, packet_response)
                        else:
                            self.on_result(packet_response)

                    elif cmd == '_error':
                        self.on_error(packet_response)

                    elif cmd == 'onBWDone':
                        self.on_bwdone()

                    elif cmd == 'onStatus':
                        self.on_status(packet_response)

                    elif cmd == 'owner':
                        self.on_owner()

                    elif cmd == 'nickinuse':
                        self.on_nickinuse()

                    elif cmd == 'banned':
                        self.on_banned()

                    elif cmd == 'startbanlist':
                        self.on_startbanlist()

                    elif cmd == 'doublesignon':
                        self.on_doublesignon()

                    elif cmd == 'joinsdone':
                        self.on_joinsdone()

                    elif cmd == 'registered':
                        client_info_dict = packet_response[0]
                        self.on_registered(client_info_dict)

                    elif cmd == 'join':
                        usr_join_info_dict = packet_response[0]
                        threading.Thread(target=self.on_join, args=(usr_join_info_dict, )).start()

                    # TODO: iparam0 removed.
                    elif cmd == 'joins':
                        current_room_users_info = packet_response
                        if len(current_room_users_info) is not 0:
                            for joins_info_user in current_room_users_info:
                                self.on_joins(joins_info_user)

                    # TODO: iparam0 removed.
                    # TODO: Is there a test to see if this can be parsed (depreciated command)?
                    elif cmd == 'oper':
                        oper_id_name = packet_response
                        if len(oper_id_name) is not 0:
                            for operator in oper_id_name:
                                oper_id = str(operator[0]).split('.0')
                                oper_name = oper_id_name[1]
                                self.on_oper(oper_id[0], oper_name)

                    # TODO: Is there a test to see if this can be parsed (depreciated command)?
                    elif cmd == 'deop':
                        deop_id = packet_response[0]
                        deop_nick = packet_response[1]
                        self.on_deop(deop_id, deop_nick)

                    # TODO: Is there a test to see if this can be parsed (depreciated command)?
                    # TODO: iparam0 removed.
                    elif cmd == 'avons':
                        avons_id_name = packet_response
                        if len(avons_id_name) is not 0:
                            for avons_user in avons_id_name:
                                avons_id = avons_user[0]
                                avons_name = avons_user[1]
                                self.on_avon(avons_id, avons_name)

                    # TODO: Is there a test to see if this can be parsed (depreciated command)?
                    elif cmd == 'pros':
                        pro_ids = packet_response[0]
                        if len(pro_ids) is not 0:
                            for pro_id in pro_ids:
                                pro_id = str(pro_id).replace('.0', '')
                                self.on_pro(pro_id)

                    elif cmd == 'nick':
                        old_nick = packet_response[0]
                        new_nick = packet_response[1]
                        nick_id = int(packet_response[2])
                        self.on_nick(old_nick, new_nick, nick_id)

                    elif cmd == 'quit':
                        quit_name = packet_response[0]
                        quit_id = packet_response[1]
                        self.on_quit(quit_id, quit_name)

                    elif cmd == 'kick':
                        kick_id = packet_response[0]
                        kick_name = packet_response[1]
                        self.on_kick(kick_id, kick_name)

                    # TODO: Test to see if this parses the response or not.
                    # TODO: iparam0 removed.
                    # TODO: Ban list replies with null types in the event we are not a moderator, so we cannot parse it.
                    elif cmd == 'banlist':
                        banlist_id_nick = packet_response
                        if len(banlist_id_nick) is not 0:
                            for banned_user in banlist_id_nick:
                                banned_id = banned_user[0]
                                banned_nick = banned_user[1]
                                self.on_banlist(banned_id, banned_nick)

                    elif cmd == 'topic':
                        topic = packet_response[0]
                        self.on_topic(topic)

                    elif cmd == 'from_owner':
                        owner_msg = packet_response[0]
                        self.on_from_owner(owner_msg)

                    elif cmd == 'privmsg':
                        self.raw_msg = packet_response[1]
                        msg_sender = packet_response[3]
                        # TODO: Implement prevent_spam by using self.msg_raw in pinybot.py
                        self.on_privmsg(msg_sender, self.raw_msg)

                    elif cmd == 'notice':
                        notice_msg = packet_response[0]
                        notice_msg_id = packet_response[1]
                        if notice_msg == 'avon':
                            avon_name = packet_response[2]
                            self.on_avon(notice_msg_id, avon_name)
                        elif notice_msg == 'pro':
                            self.on_pro(notice_msg_id)

                    elif cmd == 'private_room':
                        private_status = str(packet_response[0])

                        # TODO: We should not be setting these here - move to a handler.
                        self.on_private_room(private_status)

                    # TODO: We do not understand these callbacks fully.
                    elif cmd == 'gift':
                        self.console_write(COLOR['white'], str(packet_response))

                    elif cmd == 'prepare_gift_profile':
                        self.console_write(COLOR['white'], str(packet_response))

                    else:
                        self.console_write(COLOR['bright_red'], 'Unknown command: %s' % cmd)

            except Exception as ex:
                log.error('General callback error: %s' % ex, exc_info=True)
                if CONFIG['debug_mode']:
                    traceback.print_exc()

    # Callback Event Methods.
    # TODO: This should be handled in the rtmp library.
    def on_result(self, result_info):
        # TODO: This should be handled within rtmp_protocol.
        if len(result_info) is 4 and type(result_info[3]) is int:
            stream_id = result_info[3]
            log.debug('Stream ID: %s' % stream_id)
        if CONFIG['debug_mode']:
            for list_item in result_info:
                if type(list_item) is rtmp.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['white'], k + ': ' + str(list_item[k]))
                else:
                    self.console_write(COLOR['white'], str(list_item))

    # TODO: This should be handled in the rtmp library.
    def on_error(self, error_info):
        if CONFIG['debug_mode']:
            for list_item in error_info:
                if type(list_item) is rtmp.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['bright_red'], k + ': ' + str(list_item[k]))

                else:
                    self.console_write(COLOR['bright_red'], str(list_item))

    # TODO: This should be handled in the rtmp library.
    def on_status(self, status_info):
        if CONFIG['debug_mode']:
            for list_item in status_info:
                if type(list_item) is rtmp.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['white'], k + ': ' + str(list_item[k]))
                else:
                    self.console_write(COLOR['white'], str(list_item))

    # TODO: This should be handled in the rtmp library.
    def on_bwdone(self):
        self.console_write(COLOR['green'], 'Received Bandwidth Done.')
        if not self._is_reconnected:
            if CONFIG['enable_auto_job']:
                self.console_write(COLOR['white'], 'Starting auto job timer.')
                self.start_auto_job_timer()

    # TODO: Add docstring information.
    def on_registered(self, client_info):
        """

        :param client_info:
        """
        self._client_id = client_info['id']
        self._is_client_mod = client_info['mod']
        self._is_client_owner = client_info['own']
        self.add_user_info(client_info)

        self.console_write(COLOR['bright_green'], 'registered with ID: %d' % self._client_id)
        key = tinychat.get_captcha_key(self._roomname, str(self._client_id), proxy=self._proxy)
        if key is None:
            self.console_write(COLOR['bright_red'], 'There was a problem obtaining the captcha key. Key=%s' % str(key))
            sys.exit(1)
        else:
            self.console_write(COLOR['bright_green'], 'Captcha key found: %s' % key)
            self.send_cauth_msg(key)
            self.set_nick()

    # TODO: Add docstring information.
    def on_join(self, join_info_dict):
        """

        :param join_info_dict:
        """
        user = self.add_user_info(join_info_dict)

        if join_info_dict['account']:
            tc_info = tinychat.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']

            if join_info_dict['own']:
                self.console_write(COLOR['red'], 'Room Owner: %s:%d:%s' %
                                   (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))
            elif join_info_dict['mod']:
                self.console_write(COLOR['bright_red'], 'Moderator: %s:%d:%s' %
                                   (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))
            else:
                self.console_write(COLOR['bright_yellow'], '%s:%d has account: %s' %
                                   (join_info_dict['nick'], join_info_dict['id'], join_info_dict['account']))
        else:
            if join_info_dict['id'] is not self._client_id:
                self.console_write(COLOR['bright_cyan'], '%s:%d joined the room.' %
                                   (join_info_dict['nick'], join_info_dict['id']))

    # TODO: Add docstring information.
    def on_joins(self, joins_info_dict):
        """

        @param joins_info_dict:
        @return:
        """
        self.add_user_info(joins_info_dict)

        if joins_info_dict['account']:
            if joins_info_dict['own']:
                self.console_write(COLOR['red'], 'Joins Room Owner: %s:%d:%s' %
                                   (joins_info_dict['nick'], joins_info_dict['id'], joins_info_dict['account']))
            elif joins_info_dict['mod']:
                self.console_write(COLOR['bright_red'], 'Joins Moderator: %s:%d:%s' %
                                   (joins_info_dict['nick'], joins_info_dict['id'], joins_info_dict['account']))
            else:
                self.console_write(COLOR['bright_yellow'], 'Joins: %s:%d:%s' %
                                   (joins_info_dict['nick'], joins_info_dict['id'], joins_info_dict['account']))
        else:
            if joins_info_dict['id'] is not self._client_id:
                self.console_write(COLOR['bright_cyan'], 'Joins: %s:%d' %
                                   (joins_info_dict['nick'], joins_info_dict['id']))

    # TODO: Add docstring information.
    def on_joinsdone(self):
        """

        @return:
        """
        self.console_write(COLOR['cyan'], 'All joins information received.')
        if self._is_client_mod:
            self.send_banlist_msg()

    # TODO: Add docstring information.
    def on_oper(self, uid, nick):
        """

        @param uid:
        @param nick:
        @return:
        """
        user = self.find_user_info(nick)
        user.is_mod = True
        if uid != self._client_id:
            self.console_write(COLOR['bright_red'], '%s:%s is moderator.' % (nick, uid))

    # TODO: Add docstring information.
    def on_deop(self, uid, nick):
        """

        @param uid:
        @param nick:
        @return:
        """
        user = self.find_user_info(nick)
        user.is_mod = False
        self.console_write(COLOR['red'], '%s:%s was deoped.' % (nick, uid))

    # TODO: Add docstring information.
    # TODO: Do we need this function?
    # def on_owner(self):
    #     pass

    # TODO: Add docstring information.
    def on_avon(self, uid, name):
        """

        @param uid:
        @param name:
        @return:
        """
        self.console_write(COLOR['cyan'], '%s:%s is broadcasting.' % (name, uid))

    # TODO: Add docstring information.
    def on_pro(self, uid):
        """

        @param uid:
        @return:
        """
        self.console_write(COLOR['cyan'], '%s is pro.' % uid)

    # TODO: Add docstring information.
    def on_nick(self, old, new, uid):
        """

        @param old:
        @param new:
        @param uid:
        @return:
        """
        if uid != self._client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self._room_users.keys():
                del self._room_users[old]
                self._room_users[new] = old_info
            self.console_write(COLOR['bright_cyan'], '%s:%s changed nick to: %s  ' % (old, uid, new))

    # TODO: Add docstring information.
    def on_nickinuse(self):
        """

        @return:
        """
        self.client_nick += str(random.randint(0, 10))
        self.console_write(COLOR['white'], 'Nick already taken. Changing nick to: %s' % self.client_nick)
        self.set_nick()

    # TODO: Add docstring information.
    def on_quit(self, uid, name):
        """

        @param uid:
        @param name:
        @return:
        """
        if name in self._room_users.keys():
            del self._room_users[name]
            self.console_write(COLOR['cyan'], '%s:%s left the room.' % (name, uid))

    # TODO: Add docstring information.
    def on_kick(self, uid, name):
        """

        @param uid:
        @param name:
        @return:
        """
        self.console_write(COLOR['bright_red'], '%s:%s was banned.' % (name, uid))
        self.send_banlist_msg()

    # TODO: Add docstring information.
    def on_banned(self):
        """

        @return:
        """
        self.console_write(COLOR['red'], 'You are banned from this room.')

    # TODO: Add docstring information.
    def on_startbanlist(self):
        """

        @return:
        """
        self.console_write(COLOR['cyan'], 'Checking banlist.')

    # TODO: Add docstring information.
    def on_banlist(self, uid, nick):
        """

        @param uid:
        @param nick:
        @return:
        """
        self._room_banlist[nick] = uid
        # TODO: Console log of 'banlist' muted to allow reduced logging in the console.

    # TODO: Add docstring information.
    def on_topic(self, topic):
        """

        @param topic:
        @return:
        """
        self._topic_msg = topic.encode('utf-8', 'replace')
        self.console_write(COLOR['cyan'], 'Room topic: %s' % self._topic_msg)

    # TODO: Add docstring information.
    def on_private_room(self, private_status):
        """

        @param private_status:
        @return:
        """
        if private_status == 'yes':
            self._private_room = True
        elif private_status == 'no':
            self._private_room = False
        self.console_write(COLOR['cyan'], 'Private Room: %s' % self._private_room)

    # TODO: Add docstring information.
    def on_from_owner(self, owner_msg):
        """

        @param owner_msg:
        @return:
        """
        msg = str(owner_msg).replace('notice', '').replace('%20', ' ')
        self.console_write(COLOR['bright_red'], msg)

    # TODO: Add docstring information.
    def on_doublesignon(self):
        """"""

        self.console_write(COLOR['bright_red'], 'Double account sign on. Aborting!')
        self.is_connected = False
        # TODO: Removed double_signon_reconnect option.

    # TODO: Add docstring information.
    def on_reported(self, uid, nick):
        """

        @param uid:
        @param nick:
        @return:
        """
        self.console_write(COLOR['bright_red'], 'You were reported by: %s:%s' % (uid, nick))

    def on_privmsg(self, msg_sender, raw_msg):
        """
        Message command controller.

        :param msg_sender: str the sender of the message.
        :param raw_msg: str the unencoded message.
        """
        # Get user info object of the user sending the message..
        self.user = self.find_user_info(msg_sender)

        # Decode the message from comma separated decimal to normal text.
        decoded_msg = self._decode_msg(u'' + raw_msg)

        if decoded_msg.startswith('/'):
            msg_cmd = decoded_msg.split(' ')
            if msg_cmd[0] == '/msg':
                private_msg = ' '.join(msg_cmd[2:])
                self.private_message_handler(msg_sender, private_msg.strip())

            elif msg_cmd[0] == '/reported':
                self.on_reported(self.user.id, msg_sender)

            elif msg_cmd[0] == '/mbs':
                if self.user.is_mod:
                    if len(msg_cmd) is 3:
                        media_type = msg_cmd[1]
                        media_id = msg_cmd[2]
                        # TODO: int -> float, when handling SoundCloud media is this required?
                        # time_point = float(msg_cmd[3])
                        threading.Thread(target=self.on_media_broadcast_start,
                                         args=(media_type, media_id, msg_sender, )).start()

            elif msg_cmd[0] == '/mbc':
                if self.user.is_mod:
                    if len(msg_cmd) is 2:
                        media_type = msg_cmd[1]
                        self.on_media_broadcast_close(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpa':
                if self.user.is_mod:
                    if len(msg_cmd) is 2:
                        media_type = msg_cmd[1]
                        self.on_media_broadcast_paused(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpl':
                if self.user.is_mod:
                    if len(msg_cmd) is 3:
                        media_type = msg_cmd[1]
                        # TODO: Should the time point here be a float and not an integer?
                        # time_point = float(msg_cmd[2])
                        time_point = int(msg_cmd[2])
                        self.on_media_broadcast_play(media_type, time_point, msg_sender)

            elif msg_cmd[0] == '/mbsk':
                if self.user.is_mod:
                    if len(msg_cmd) is 3:
                        media_type = msg_cmd[1]
                        time_point = int(msg_cmd[2])
                        self.on_media_broadcast_skip(media_type, time_point, msg_sender)

        else:
            self.message_handler(msg_sender, decoded_msg.strip())

    # Message Handler.
    def message_handler(self, msg_sender, decoded_msg):
        """
        Message handler.

        :param msg_sender: str the user sending a message.
        :param decoded_msg: str the decoded message (text).
        """
        self.console_write(COLOR['green'], '%s: %s ' % (msg_sender, decoded_msg))

    # Private message Handler.
    def private_message_handler(self, msg_sender, private_msg):
        """
        A user private message us.
        :param msg_sender: str the user sending the private message.
        :param private_msg: str the private message.
        """
        self.console_write(COLOR['white'], 'Private message from %s: %s' % (msg_sender, private_msg))

    # Media Events.
    # TODO: Console write not printing.
    def on_media_broadcast_start(self, media_type, video_id, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param video_id: str the youTube ID or soundCloud trackID.
        :param usr_nick: str the user name of the user playing media.
        """
        # TODO: The use of time point here might not be necessary, this would remove the use of time point /mbs.
        # :param time_point: int the time in the video/track which we received to start playing.
        self.console_write(COLOR['bright_magenta'], '%s is playing %s %s' % (usr_nick, media_type, video_id))

    def on_media_broadcast_close(self, media_type, usr_nick):
        """
        A user closed a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param usr_nick: str the user name of the user closing the media.
        """
        self.console_write(COLOR['bright_magenta'], '%s closed the %s' % (usr_nick, media_type))

    def on_media_broadcast_paused(self, media_type, usr_nick):
        """
        A user paused the media broadcast.
        :param media_type: str the type of media being paused. youTube or soundCloud.
        :param usr_nick: str the user name of the user pausing the media.
        """
        self.console_write(COLOR['bright_magenta'], '%s paused the %s' % (usr_nick, media_type))

    def on_media_broadcast_play(self, media_type, time_point, usr_nick):
        """
        A user resumed playing a media broadcast.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user resuming the tune.
        """
        self.console_write(COLOR['bright_magenta'], '%s resumed the %s at: %s' % (usr_nick, media_type, time_point))

    def on_media_broadcast_skip(self, media_type, time_point, usr_nick):
        """
        A user time searched a tune.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user time searching the tune.
        """
        self.console_write(COLOR['bright_magenta'], '%s time searched the %s at: %s ' %
                           (usr_nick, media_type, time_point))

    # User Related
    def add_user_info(self, user_info):
        """
        Find the user object for a given user name and add to it.
        We use this method to add info to our user info object.
        :param user_info: dict the user information dictionary.
        :return: object a user object containing user info.
        """
        if user_info not in self._room_users.keys():
            self._room_users[user_info['nick']] = User(**user_info)
        return self._room_users[user_info['nick']]

    def find_user_info(self, usr_nick):
        """
        Find the user object for a given user name.
        Instead of adding to the user info object, we return None if the user name is NOT in the room_users dict.
        We use this method when we are getting user input to look up.

        :param usr_nick: str the user name to find info for.
        :return: object or None if no user name is in the room_users dict.
        """
        if usr_nick in self._room_users.keys():
            return self._room_users[usr_nick]
        return None

    # Message Methods.
    # TODO: Evaluate design.
    def send_bauth_msg(self):
        """ Get and send the bauth key needed before we can start a broadcast. """
        if self._bauth_key is not None:
            self.connection.call('bauth', [u'' + self._bauth_key])
        else:
            _token = tinychat.get_bauth_token(self._roomname, self.client_nick, self._client_id,
                                              self._greenroom, proxy=self._proxy)
            if _token != 'PW':
                self.connection.call('bauth', [u'' + _token])
                self._bauth_key = _token

    # TODO: Issue when sending the call, cauth key is sent on transaction id.
    # TODO: Evaluate design.
    def send_cauth_msg(self, cauthkey):
        """
        Send the cauth key message with a working cauth key, we need to send this before we can chat.
        :param cauthkey: str a working cauth key.
        """
        self.connection.call('cauth', [u'' + cauthkey])

    # TODO: Evaluate design.
    # TODO: Trim this method into something more simpler.
    def send_owner_run_msg(self, msg):
        """
        Send owner run message.
        :param msg: str the message to send.
        """
        if self._is_client_mod:
            msg_url_encoded = ''

            for x in xrange(len(msg)):
                try:
                    letter_number = ord(msg[x])
                    if letter_number < 32 or letter_number > 126:
                        msg_url_encoded += quote_plus(msg[x])
                    elif letter_number == 37:
                        msg_url_encoded += '%25'
                    elif letter_number == 32:
                        msg_url_encoded += '%20'
                    else:
                        msg_url_encoded += msg[x]
                except (Exception, UnicodeEncodeError):
                    try:
                        msg_url_encoded += quote_plus(msg[x].encode('utf-8'), safe='/')
                    except (Exception, UnicodeEncodeError):
                        pass

            self.connection.call('owner_run', [u'notice' + msg_url_encoded])

    # TODO: Evaluate design.
    def send_cam_approve_msg(self, nick, uid=None):
        """
        Send a camera approval message to accept a pending broadcast in a greenroom.
        NOTE: If no uid is provided, we try and look up the user by nick name.
        :param nick: str the nick to be approved.
        :param uid: (optional) int the user id.
        """
        if self._is_client_mod and self._b_password is not None:
            msg = '/allowbroadcast %s' % self._b_password
            if uid is None:
                user = self.find_user_info(nick)
                if user is not None:
                    self.connection.call('privmsg', [u'' + self._encode_msg(msg), u'#0,en',
                                                     u'n' + str(user.id) + '-' + nick])

            else:
                self.connection.call('privmsg', [u'' + self._encode_msg(msg), u'#0,en',
                                                 u'n' + str(uid) + '-' + nick])

    # TODO: Evaluate design.
    def send_chat_msg(self, msg):
        """
        Send a chat room message.
        :param msg: str the message to send.
        """
        self.connection.call('privmsg', [u'' + self._encode_msg(msg), u'#262626,en'])

    # TODO: Evaluate design.
    def send_private_msg(self, msg, nick):
        """
        Send a private message.
        :param msg: str the private message to send.
        :param nick: str the user name to receive the message.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self.connection.call('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg),
                                             u'#262626,en', u'n' + str(user.id) + '-' + nick])
            self.connection.call('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg),
                                             u'#262626,en', u'b' + str(user.id) + '-' + nick])

    # TODO: Evaluate design.
    def send_undercover_msg(self, nick, msg):
        """
        Send an 'undercover' message.
        This is a special message that appears in the main chat, but is only visible to the user it is sent to.
        It can also be used to play 'private' youTube/soundCloud with.
        :param nick: str the user name to send the message to.
        :param msg: str the message to send.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self.connection.call('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'n' + str(user.id) + '-' + nick])
            self.connection.call('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'b' + str(user.id) + '-' + nick])

    # TODO: Evaluate design.
    def set_nick(self):
        """ Send the nick message. """
        if not self.client_nick:
            self.client_nick = string_utili.create_random_string(5, 25)
        self.console_write(COLOR['white'], 'Setting nick: %s' % self.client_nick)
        # TODO: Issue when sending the remote call, the nick is sent on transaction id and not the options list.
        self.connection.call('nick', [u'' + self.client_nick])

    # TODO: Evaluate design.
    def send_ban_msg(self, nick, uid=None):
        """
        Send ban message. The client has to be mod when sending this message.
        :param nick: str the user name of the user we want to ban.
        :param uid: (optional) str the ID of the user we want to ban.
        """
        if self._is_client_mod:
            if uid is None:
                user = self.find_user_info(nick)
                if user is not None:
                    self.connection.call('kick', [u'' + nick, str(user.id)])
                    # Request updated ban list.
                    self.send_banlist_msg()
            else:
                self.connection.call('kick', [u'' + nick, str(uid)])
                # Request updated ban list.
                self.send_banlist_msg()

    # TODO: Evaluate design.
    def send_forgive_msg(self, uid):
        """
        Send forgive message.
        :param uid: int the ID of the user we want to forgive.
        """
        if self._is_client_mod:
            self.connection.call('forgive', [u'' + str(uid)])
            # Request updated ban list.
            self.send_banlist_msg()

    # TODO: Evaluate design.
    def send_banlist_msg(self):
        """ Send banlist message. """
        if self._is_client_mod:
            self.connection.call('banlist')

    # TODO: Evaluate design.
    def send_topic_msg(self, topic):
        """
        Send a room topic message.
        :param topic: str the new room topic.
        """
        if self._is_client_mod:
            self.connection.call('topic', [u'' + topic])

    # TODO: Evaluate design.
    def send_close_user_msg(self, nick):
        """
        Send close user broadcast message.
        :param nick: str the nickname of the user we want to close.
        """
        if self._is_client_mod:
            self.connection.call('owner_run', [u'_close' + nick])

    # TODO: Evaluate design.
    def send_mute_msg(self):
        """ Send mute message to mute all broadcasting users in the room. """
        if self._is_client_mod:
            self.connection.call('owner_run', [u'mute'])

    # TODO: Evaluate design.
    def send_push2talk_msg(self):
        """ Send 'push2talk' room message to force push to talk for all users. """
        if self._is_client_mod:
            self.connection.call('owner_run', [u'push2talk'])

    # TODO: Evaluate design.
    # TODO: Simplify this procedure - remove any unnecessary variables.
    # def send_private_room_msg(self, state=None):
    #     """
    #     Send 'private room' message to the room.
    #     We can assume this prevents the room from being listed in the directory.
    #     :param state: bool True/False (default None) and connection value is used,
    #                   set as True/False depending on whether private_room should be turned on or not.
    #     """
    #     if self._is_client_mod:
    #         value = ''
    #         if state is not None:
    #             if state:
    #                 value = 'yes'
    #             elif not state:
    #                 value = 'no'
    #         else:
    #             if not self._private_room:
    #                 value = 'yes'
    #             elif self._private_room:
    #                 value = 'no'
    #
    #         self.connection.call('private_room', [u'' + value])

    # Stream functions.
    # TODO: Converted create_stream to call standard.
    # TODO: Converted send_publish to call standard.

    # TODO: Move to RTMP library - set chunk size abstracted to RtmpClient->writer.
    # TODO: Convert to RtmpPacket.

    # TODO: May need an RtmpPacket to implement stream id.
    # TODO: Converted send_play to call standard.

    # TODO: Move to RTMP library - NetStream.
    # TODO: Convert to RtmpPacket.
    # def send_audio_packet(self, frame_raw_data, frame_control_type):  # frame_timestamp=0
    #     """
    #     Send Audio message.
    #     :param frame_raw_data: bytes the audio data (in the MP3 format) to be sent.
    #     :param frame_control_type: hexadecimal value of the control type (originally 0x66,
    #                                 though due to a lack of adequate audio encoding it is sent with an
    #                                 inter-frame (0x22) control type.
    #     """
    #     # :param frame_timestamp: (optional) int the timestamp for the packet.
    #
    #     audio_packet = self.connection.writer.new_packet()
    #
    #     audio_packet.set_type(rtmp.types.DT_AUDIO_MESSAGE)
    #     audio_packet.header.stream_id = self._streams['client_publish']
    #     # TODO: Internal time stamp should over-ride this.
    #     # audio_packet.header.timestamp = frame_timestamp
    #     audio_packet.body = {
    #         'control': frame_control_type,
    #         'audio_data': frame_raw_data
    #     }
    #
    #     self.connection.writer.setup_packet(audio_packet)

    # TODO: Move to RTMP library - NetStream.
    # TODO: Convert to RtmpPacket.
    # def send_video_packet(self, frame_raw_data, frame_control_type):  # frame_timestamp=0
    #     """
    #     Send Video message.
    #     NOTE: Altering the control type may produce unexpected results.
    #
    #     :param frame_raw_data: bytes the video data (in the FLV1 format) to be sent.
    #     :param frame_control_type: hexadecimal value of the control type, between 0x12 (key-frame), 0x22 (inter-frame),
    #                                0x32 (disposable-frame) and 0x42 (generated-frame).
    #     """
    #     # :param frame_timestamp: (optional) int the timestamp for the packet.
    #
    #     video_packet = self.connection.writer.new_packet()
    #
    #     video_packet.set_type(rtmp.types.DT_VIDEO_MESSAGE)
    #     video_packet.header.stream_id = self._streams['client_publish']
    #     # video_packet.header.timestamp = frame_timestamp
    #     video_packet.body = {
    #         'control': frame_control_type,
    #         'video_data': frame_raw_data
    #     }
    #
    #     self.connection.writer.setup_packet(video_packet)

    # TODO: Convert to RtmpPacket - we need to send streamId as well.
    # TODO: We need to send the streamId or we need to alter the format of the header and to specify the chunk stream
    #       it needs to be sent on/follow via the chunk stream id.

    # TODO: Converted send_delete_stream to call standard.

    # Media Message Functions
    def send_media_broadcast_start(self, media_type, video_id, time_point=0, private_nick=None):
        """
        Starts a media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'
        :param video_id: str the media video ID.
        :param time_point: int where to start the media from in milliseconds.
        :param private_nick: str if not None, start the media broadcast for this nickname only.
        """
        mbs_msg = '/mbs %s %s %s' % (media_type, video_id, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbs_msg)
        else:
            self.send_chat_msg(mbs_msg)

    def send_media_broadcast_close(self, media_type, private_nick=None):
        """
        Close a media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'
        :param private_nick: str if not None, send this message to this nickname only.
        """
        mbc_msg = '/mbc %s' % media_type
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbc_msg)
        else:
            self.send_chat_msg(mbc_msg)

    def send_media_broadcast_play(self, media_type, time_point, private_nick=None):
        """
        Play a currently paused media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'
        :param time_point: int where to play the media from in milliseconds.
        :param private_nick: str if not None, send this message to this username only.
        """
        mbpl_msg = '/mbpl %s %s' % (media_type, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbpl_msg)
        else:
            self.send_chat_msg(mbpl_msg)

    def send_media_broadcast_pause(self, media_type, private_nick=None):
        """
        Pause a currently playing media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'.
        :param private_nick: str if not None, send this message to this username only.
        """
        mbpa_msg = '/mbpa %s' % media_type
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbpa_msg)
        else:
            self.send_chat_msg(mbpa_msg)

    def send_media_broadcast_skip(self, media_type, time_point, private_nick=None):
        """
        Time search a currently playing/paused media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'.
        :param time_point: int the time point to skip to.
        :param private_nick: str if not None, send this message to this username only.
        :return:
        """
        mbsk_msg = '/mbsk %s %s' % (media_type, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbsk_msg)
        else:
            self.send_chat_msg(mbsk_msg)

    # TODO: We need to implement the try/except and reconnect if we cannot send the call.
    # TODO: The use of _send_command has depreciated and we now use the call function in RtmpClient class
    #       within the rtmp library.

    # Helper Methods:
    def get_runtime(self, milliseconds=True):
        """
        Get the time the connection has been alive.
        :param milliseconds: bool True return the time as milliseconds, False return seconds.
        :return: int milliseconds or seconds.
        """
        up = int(time.time() - self._init_time)
        if milliseconds:
            return up * 1000
        return up

    @staticmethod
    def _decode_msg(msg):
        """
        Decode str from comma separated decimal to normal text str.
        :param msg: str the encoded message.
        :return: str normal text.
        """
        chars = msg.split(',')
        msg = ''
        for i in chars:
            try:
                msg += unichr(int(i))
            except ValueError as ve:
                log.error('%s' % ve, exc_info=True)
        return msg

    @staticmethod
    def _encode_msg(msg):
        """
        Encode normal text str to comma separated decimal.
        :param msg: str the normal text to encode.
        :return: comma separated decimal str.
        """
        return ','.join(str(ord(char)) for char in msg)

    # TODO: Evaluate design.
    # TODO: We just want this function to loop ping requests, since we already have a function send ping requests.
    # def send_ping_request(self, manual=False):
    #     """
    #     Send a ping request (experimental).
    #
    #     NOTE: The client sends an unorthodox message i.e. *ping request* instead of a *ping response* due to
    #           the nature of how the servers for TinyChat were set up. Tinychat servers do not automatically request
    #           a ping, so we issue a request instead. We assume the data-types are reversed since an event_type of 7,
    #           which is only a client response, will be "accepted" by the server as it responds to your initial ping
    #           request with random data.
    #
    #     :param manual: Boolean True/False if you want to instantly initiate a 'reverse' ping conversation between
    #                    client and server.
    #     """
    #     self.connection.send_ping_request()
    #
    #     if not manual:
    #         while not self.is_connected:
    #             time.sleep(1)
    #         while self._publish_connection:
    #             time.sleep(1)
    #         while self.is_connected and not self._publish_connection:
    #             time.sleep(120)

    # TODO: Move to CameraManager class.
    # def configure_av_packet(self, av_content):
    #     """
    #     Configures audio/video content for a packet, given the frame content and the settings, and send the packet.
    #     :param av_content: list[type of packet - audio/video, raw data, packet control type, time stamp].
    #     """
    #     # Assign timestamp.
    #     # if self._manual_time_stamp is not None:
    #     #     time_stamp = self._manual_time_stamp
    #     # else:
    #     #     time_stamp = av_content[3]
    #
    #     # Assign control type.
    #     control_type = av_content[2]
    #
    #     # Setup audio packet.
    #     if av_content[0] == rtmp.types.DT_AUDIO_MESSAGE:
    #         if not self.allow_audio:
    #             # Send no audio data if it has been disabled.
    #             raw_data = b''
    #         else:
    #             raw_data = av_content[1]
    #         self.send_audio_packet(raw_data, control_type)  # time_stamp
    #
    #     # Setup video packet.
    #     elif av_content[0] == rtmp.types.DT_VIDEO_MESSAGE:
    #         if not self.allow_video:
    #             # Send no video data if it has been disabled.
    #             raw_data = b''
    #         else:
    #             raw_data = av_content[1]
    #         self.send_video_packet(raw_data, control_type)  # time_stamp
    #     else:
    #         print('This frame is an invalid audio/video input.')

    # TODO: Evaluate design.
    # TODO: Alter name and the variable names used throughout.
    def set_stream(self, stream=True):
        """
        Appropriately sets the necessary options into effect to start/close client streams.
        :param stream: bool True/False (default True) to state whether a
                       broadcasting session should be initiated or not.
        """
        if stream:
            if not self._publish_connection and self._selected_stream_name is None:
                # Publish camera sequence:
                self.console_write(COLOR['green'], 'Opening stream.')
                # Send broadcast authorisation message to the server.
                self.send_bauth_msg()
                # Create a new stream onto which we can send packets e.g. audio/video packets.
                self.connection.send_create_stream()

                self._selected_stream_name = self._client_id
                self._stream_sort = True
                # Sort out the stream request reply from the server.
                while self._stream_sort:
                    time.sleep(1)

                # Send publish message to the server.
                self.connection.send_publish(self._streams[str(self._client_id)]['publish'], self._client_id,
                                             self.connection.publish_live)

                # TODO: Should be replaced with transaction id method in the rtmp library,
                #       to allow us to notice if a stream is active and present.
                # Allow several seconds to establish a working stream.
                time.sleep(5)

                # Acknowledge locally that we are publishing a stream.
                self._publish_connection = True
            else:
                self.console_write(COLOR['bright_red'], 'No need to start stream, client broadcast already present.')

        elif not stream:
            if self._publish_connection and self._selected_stream_name is None:
                self._publish_connection = False

                # Close camera sequence:
                self.console_write(COLOR['green'], 'Closing stream.')
                self.connection.send_close_stream(self._streams[str(self._client_id)]['close'])
                self.connection.send_delete_stream(self._streams[str(self._client_id)]['delete'])

                # Delete all the stored stream information and turn off the publishing.
                self._tidy_streams(str(self._client_id))
            else:
                self.console_write(COLOR['bright_red'], 'No need to stop stream, client was not broadcasting.')
        else:
            self.console_write(COLOR['white'], 'No stream argument was passed, True/False should be passed to '
                                               'initiate/close streams respectively.')

    # TODO: Evaluate design.
    # TODO: This should be handled in the rtmp library.
    def _stream_manager(self, stream_name, result_response):
        """
        A client stream managing function to set up streams.
        :param result_response: list containing the amf decoded result.
        """
        result_stream_id = int(result_response[0])
        self._streams[str(stream_name)] = {}
        self._streams[str(stream_name)]['publish'] = result_stream_id
        self._streams[str(stream_name)]['close'] = result_stream_id
        self._streams[str(stream_name)]['delete'] = result_stream_id
        self._stream_sort = False
        self._selected_stream_name = None

    # TODO: Evaluate design.
    def _tidy_streams(self, stream_name):
        """
        Tidy up stream key/pair value in the streams dictionary by providing the StreamID.
        :param stream_name: str the stream name which should be found and all keys matching it
                          should be deleted from the streams dictionary.
        """
        if stream_name in self._streams:
            del self._streams[stream_name]

    # Timed Auto Methods.
    def auto_job_handler(self):
        """ The event handler for auto_job_timer. """
        if self.is_connected:
            conf = tinychat.get_roomconfig_xml(self._roomname, self.room_pass, proxy=self._proxy)
            if conf is not None:
                if self._is_client_mod:
                    self._greenroom = conf['greenroom']
                    self._b_password = conf['bpassword']
            log.info('recv configuration: %s' % conf)
        self.start_auto_job_timer()

    def start_auto_job_timer(self):
        """
        Just like using Tinychat within a browser, this method will
        fetch the room configuration from the Tinychat API every 5 minutes (300 seconds).
        NOTE: See line 228 at http://tinychat.com/embed/chat.js
        """
        threading.Timer(CONFIG['auto_job_interval'], self.auto_job_handler).start()


def main():
    room_name = raw_input('Enter room name: ')
    room_password = getpass.getpass('Enter room password (optional:password hidden): ')
    nickname = raw_input('Enter nick name (optional): ')
    login_account = raw_input('Login account (optional): ')
    login_password = getpass.getpass('Login password (optional:password hidden): ')

    client = TinychatRTMPClient(room_name, nick=nickname, account=login_account,
                                password=login_password, room_pass=room_password)

    t = threading.Thread(target=client.prepare_connect)
    t.daemon = True
    t.start()

    while not client.is_connected:
        time.sleep(1)

    while client.is_connected:
        chat_msg = raw_input()
        if chat_msg.lower() == '/q':
            client.disconnect()
            # Exit to system safely whilst returning exit code 0.
            sys.exit(0)
        else:
            client.send_chat_msg(chat_msg)

if __name__ == '__main__':
    if CONFIG['debug_to_file']:
        formatter = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
        # Should there be a check to make sure the debug file name has been set?
        logging.basicConfig(filename=CONFIG['debug_file_name'], level=logging.DEBUG, format=formatter)
        log.info('Starting pinylib version: %s' % about.__version__)
    else:
        log.addHandler(logging.NullHandler())
    main()
