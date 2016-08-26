# -*- coding: utf-8 -*-
""" Pinylib module by Nortxort (https://github.com/nortxort/pinylib) """

# Edited for pinybot (https://github.com/GoelBiju/pinybot/)

import time
import threading
import random
import traceback
import logging

import os
import sys
import getpass

from apis import web_request, tinychat_api
from files import file_handler as fh
from rtmp import rtmp_protocol, message_structures
from urllib import quote_plus
from colorama import init, Fore, Style

# FLV parser(s)
from FLV import tag_handler

# VideoCapture
from VideoCapture import Device

__version__ = '4.2.0'

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

# Loads CONFIG in the configuration file from the root directory:
CONFIG_FILE_NAME = '/config.ini'  # State the name of the '.ini' file here.
CURRENT_PATH = sys.path[0]
CONFIG_PATH = CURRENT_PATH + CONFIG_FILE_NAME
CONFIG = fh.configuration_loader(CONFIG_PATH)

if CONFIG is None:
    print('No file named ' + CONFIG_FILE_NAME + ' found in: ' + CONFIG_PATH)
    sys.exit(1)  # Exit to system safely whilst returning exit code 1.

if CONFIG['console_colors']:
    init(autoreset=True)

log = logging.getLogger(__name__)


def create_random_string(min_length, max_length, upper=False):
    """
    Creates a random string of letters and numbers.
    :param min_length: int the minimum length of the string
    :param max_length: int the maximum length of the string
    :param upper: bool do we need upper letters
    :return: random str of letters and numbers
    """
    randlength = random.randint(min_length, max_length)
    junk = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if upper:
        junk += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join((random.choice(junk) for i in xrange(randlength)))


def write_to_log(msg, room_name):
    """
    Writes chat events to log.
    The room name is used to construct a log file name from.
    :param msg: str the message to write to the log.
    :param room_name: str the room name.
    """
    d = time.strftime('%Y-%m-%d')
    file_name = d + '_' + room_name + '.log'
    path = CONFIG['log_path'] + room_name + '/logs/'
    fh.file_writer(path, file_name, msg.encode('ascii', 'ignore'))


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


class RoomUser:
    """
    A object to hold info about a user.
    Each user will have a object associated with there username.
    The object is used to store information about the user.
    """
    def __init__(self, nick, uid=None, last_msg=None):
        self.nick = nick
        self.id = uid
        self.last_msg = last_msg
        self.user_account = None
        self.user_account_type = None
        self.user_account_gift_points = None
        self.is_owner = False
        self.is_super = False
        self.is_mod = False
        self.has_power = False
        self.tinychat_id = None
        self.last_login = None
        self.device_type = ''
        self.reading_only = False


class TinychatRTMPClient:
    """ Manages a single room connection to a given room. """
    def __init__(self, room, tcurl=None, app=None, room_type=None, nick=None, account=None,
                 password=None, room_pass=None, ip=None, port=None, proxy=None):

        # Standard settings
        self.roomname = room
        self._tc_url = tcurl
        self._app = app
        self._roomtype = room_type
        self._ip = ip
        self._port = port
        self._prefix = u'tinychat'
        self._swf_url = u'http://tinychat.com/embed/Tinychat-11.1-1.0.0.0668.swf?version=1.0.0.0668/[[DYNAMIC]]/8'
        self._desktop_version = u'Desktop 1.0.0.0668'
        self._embed_url = u'http://tinychat.com/' + self.roomname
        self._swf_version = 'WIN 21,0,0,216'

        # Specific connection settings:
        self.client_nick = nick
        self.account = account
        self.password = password
        self.room_pass = room_pass
        self.proxy = proxy
        self.greenroom = False
        self.private_room = False
        self.room_broadcast_pass = None

        # Personal user settings:
        self.client_id = None
        self.connection = None
        self.is_connected = False
        self.is_client_owner = False
        self.is_client_mod = False
        self.room_users = {}
        self.user_obj = object
        self.room_banlist = {}
        self.is_reconnected = False
        self.topic_msg = None
        self.reconnect_delay = CONFIG['reconnect_delay']

        # Stream settings:
        self.streams = {}
        self.create_stream_id = 1
        self.stream_sort = False
        self.publish_connection = False
        self.force_time_stamp = 0
        self.play_audio = False
        self.play_video = True

    # TODO: New method of decoding unicode characters passed into the console_write procedures.
    #       Possibly implement the decode procedure utilised by the bot here -  _encode & _decode message.
    # TODO: No handlers could be found for logger "pinylib" when error in encoding unicode.
    def console_write(self, color, message):
        """
        Writes message to console.
        :param color: the colorama color representation.
        :param message: str the message to write.
        """
        # Print the message after formatting it; with the appropriate color, style and time.
        ts = time.strftime('%H:%M:%S')
        if CONFIG['console_colors']:
            msg = COLOR['white'] + '[' + ts + '] ' + Style.RESET_ALL + color + message
        else:
            msg = '[' + ts + '] ' + message
        try:
            print(msg)
        except UnicodeEncodeError as ue:
            log.error(ue, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()

        # Save message to the log, if it has been enabled.
        if CONFIG['chat_logging']:
            write_to_log('[' + ts + '] ' + message, self.roomname)

    def prepare_connect(self):
        """ Gather necessary connection parameters before attempting to connect. """
        if self.account and self.password:
            log.info('Deleting old login cookies.')
            web_request.delete_login_cookies()
            if len(self.account) > 3:
                log.info('Trying to log in with account: %s' % self.account)
                login = web_request.post_login(self.account, self.password)
                if 'pass' in login['cookies']:
                    log.info('Logged in as: %s Cookies: %s' % (self.account, login['cookies']))
                    self.console_write(COLOR['green'], 'Logged in as: ' + login['cookies']['user'])
                else:
                    self.console_write(COLOR['red'], 'Log in Failed')
                    self.account = raw_input('Enter account (optional): ')
                    if self.account:
                        self.password = getpass.getpass('Enter password (password hidden): ')
                    self.prepare_connect()
            else:
                self.console_write(COLOR['red'], 'Account name is to short.')
                self.account = raw_input('Enter account: ')
                self.password = getpass.getpass('Enter password (password hidden): ')
                self.prepare_connect()

        self.console_write(COLOR['white'], 'Parsing room config xml...')
        config = tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
        while config == 'PW':
            self.room_pass = raw_input('The room is password protected. Enter room password (password hidden): ')
            if not self.room_pass:
                self.roomname = raw_input('Enter room name: ')
                self.room_pass = getpass.getpass('Enter room pass (optional:password hidden): ')
                self.account = raw_input('Enter account (optional): ')
                self.password = getpass.getpass('Enter password (optional:password hidden): ')
                self.prepare_connect()
            else:
                config = tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
                if config != 'PW':
                    break
                else:
                    self.console_write(COLOR['red'], 'Password Failed.')

        if CONFIG['debug_mode']:
            for k in config:
                self.console_write(COLOR['white'], k + ': ' + str(config[k]))

        self._ip = config['ip']
        self._port = config['port']
        self._tc_url = config['tcurl']
        self._app = config['app']
        self._roomtype = config['roomtype']
        self.greenroom = config['greenroom']
        self.room_broadcast_pass = config['room_broadcast_pass']

        # Allow an RTMPE connection to be made to the server.
        if CONFIG['rtmpe_connection']:
            self._tc_url = self._tc_url.replace('rtmp', 'rtmpe')
            self.console_write(COLOR['white'], 'Connecting via RTMPE (as set in configuration).')

        self.console_write(COLOR['white'], '============ CONNECTING ============\n\n')
        self.connect()

    def connect(self):
        """ Attempts to make a RTMP connection with the given connection parameters. """
        if not self.is_connected:
            log.info('Trying to connect to: %s' % self.roomname)
            try:
                tinychat_api.recaptcha(proxy=self.proxy)
                cauth_cookie = tinychat_api.get_cauth_cookie(self.roomname, proxy=self.proxy)

                # Pass connection parameters and initiate a connection.
                self.connection = rtmp_protocol.RtmpClient(self._ip, self._port, self._tc_url, self._embed_url,
                                                           self._swf_url, self._app, self._swf_version, self._roomtype,
                                                           self._prefix, self.roomname, self._desktop_version,
                                                           cauth_cookie, self.account, self.proxy)
                self.connection.connect([])

                # After-hand connection settings.
                self.is_connected = True
                # Set windows title as connected room name & IP ADDRESS:PORT of the room.
                window_message = str(self.roomname) + ' @ ' + str(self._ip) + ':' + str(self._port)
                set_window_title(window_message)

                # Start command (callbacks) handle.
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
            self.is_connected = False
            self.is_client_mod = False
            self.room_users.clear()

            # Reset custom variables.
            self.room_banlist.clear()
            # TODO: The uptime should be a general information variable for the connection.
            self.uptime = 0

            self.connection.shutdown()
        except Exception as ex:
            log.error('Disconnect error: %s' % ex, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()

    def reconnect(self):
        """ Reconnect to a room with the connection parameters already set. """
        reconnect_msg = '============ RECONNECTING IN ' + str(self.reconnect_delay) + ' SECONDS ============'
        log.info('Reconnecting: %s' % reconnect_msg)
        self.console_write(COLOR['bright_cyan'], reconnect_msg)
        self.is_reconnected = True
        self.disconnect()
        time.sleep(self.reconnect_delay)

        # Increase reconnect_delay after each reconnect.
        self.reconnect_delay *= 2
        if self.reconnect_delay > 3600:
            self.reconnect_delay = CONFIG['reconnect_delay']

        if self.account and self.password:
            self.prepare_connect()
        else:
            self.connect()

    def client_manager(self, amf0_cmd):
        """
        A client stream managing function to set the streams required for the client to publish.
        :param amf0_cmd: list containing the amf decoded commands.
        """
        result_stream_id = int(amf0_cmd[3])
        self.streams['client_stream'] = result_stream_id
        self.streams['client_publish'] = result_stream_id
        self.streams['client_close_stream'] = result_stream_id
        self.streams['client_delete_stream'] = result_stream_id
        self.stream_sort = False
        self.console_write(COLOR['white'], 'Done client manager.')

    def tidy_streams(self, stream_id):
        """
        Tidy up stream key/pair value in the streams dictionary by providing the StreamID.
        :param stream_id: int StreamID which should be found and all keys matching it
                          should be deleted from the streams dictionary.
        """
        self.console_write(COLOR['white'], 'Deleting all stream information residing on StreamID %s.' % stream_id)

        for stream_item in self.streams.keys():
            if self.streams[stream_item] == stream_id:
                del self.streams[stream_item]

    def _callback(self):
        """ Callback loop that reads from the RTMP stream. """
        log.info('Starting the callback loop.')
        failures = 0
        amf0_data_type = -1
        amf0_data = None
        while self.is_connected:
            try:
                amf0_data = self.connection.reader.next()
                amf0_data_type = amf0_data['msg']

                if CONFIG['amf_reply']:
                    self.console_write(COLOR['white'], 'REPLY --> %s' % amf0_data)

            except Exception as ex:
                failures += 1
                log.info('amf data read error count: %s %s' % (failures, ex), exc_info=True)
                if failures == 2:
                    if CONFIG['debug_mode']:
                        traceback.print_exc()
                    self.reconnect()
                    break
            else:
                failures = 0
            try:
                handled = self.connection.handle_packet(amf0_data)
                if handled:
                    msg = 'Handled packet of type: %s Packet data: %s' % (amf0_data_type, amf0_data)
                    log.info(msg)
                    if CONFIG['debug_mode']:
                        self.console_write(COLOR['white'], msg)
                    continue

                else:
                    # This is specific to Tinychat.
                    if amf0_data_type == rtmp_protocol.data_types.USER_CONTROL:
                        if amf0_data['event_type'] == rtmp_protocol.user_control_types.PING_RESPONSE:
                            self.console_write(COLOR['white'], 'Server sent \'PING_RESPONSE\'.')

                    else:
                        try:
                            amf0_cmd = amf0_data['command']
                            cmd = amf0_cmd[0]
                            iparam0 = 0
                        except (Exception, KeyError):
                            traceback.print_exc()
                            continue

                        # ----------------------- ROOM CALLBACKS -----------------------
                        # These are most of the room callbacks that have been identified within
                        # the SWF; the defunct callbacks have been omitted to be in correspondence
                        #  with the currently established and working protocol.

                        if cmd == '_result':
                            if self.stream_sort:
                                # Set streams for the client.
                                self.client_manager(amf0_cmd)
                            else:
                                # Handle the initial NetConnection _result message.
                                try:
                                    _result_info = {
                                        'Capabilities': str(amf0_cmd[2]['capabilities']),
                                        'FmsVer': amf0_cmd[2]['fmsVer'],
                                        'Code': amf0_cmd[3]['code'],
                                        'ObjectEncoding': str(amf0_cmd[3]['objectEncoding']),
                                        'Description': amf0_cmd[3]['description'],
                                        'Level': amf0_cmd[3]['level']
                                    }
                                    self.on_result(_result_info)
                                except (Exception, KeyError):
                                    log.error('"_result" callback error occured: %s' % amf0_cmd)
                                    self.console_write(COLOR['green'], str(amf0_cmd))

                        elif cmd == '_error':
                            try:
                                _error_info = {
                                    'Code': amf0_cmd[3]['code'],
                                    'Description': amf0_cmd[3]['description'],
                                    'Level': amf0_cmd[3]['level']
                                }
                                self.on_error(_error_info)
                            except (Exception, KeyError):
                                log.error('"_error" callback error occured: %s' % amf0_cmd)
                                self.console_write(COLOR['red'], str(amf0_cmd))

                        elif cmd == 'onBWDone':
                            self.on_bwdone()

                        elif cmd == 'onStatus':
                            try:
                                self.stream_sort = False
                                _status_info = {
                                    'Level': amf0_cmd[3]['level'],
                                    'Code': amf0_cmd[3]['code'],
                                    'Details': amf0_cmd[3]['details'],
                                    'Clientid': amf0_cmd[3]['clientid'],
                                    'Description': amf0_cmd[3]['description']
                                }
                                self.on_status(_status_info)
                            except (Exception, KeyError):
                                log.error('"onStatus" callback error occured: %s' % amf0_cmd)
                                self.console_write(COLOR['magenta'], str(amf0_cmd))

                        elif cmd == 'registered':
                            client_info_dict = amf0_cmd[3]
                            self.on_registered(client_info_dict)

                        elif cmd == 'join':
                            usr_join_info_dict = amf0_cmd[3]
                            threading.Thread(target=self.on_join, args=(usr_join_info_dict, )).start()

                        elif cmd == 'joins':
                            current_room_users_info_list = amf0_cmd[3:]
                            if len(current_room_users_info_list) is not 0:
                                while iparam0 < len(current_room_users_info_list):
                                    self.on_joins(current_room_users_info_list[iparam0])
                                    iparam0 += 1

                        elif cmd == 'joinsdone':
                            self.on_joinsdone()

                        elif cmd == 'oper':
                            oper_id_name = amf0_cmd[3:]
                            while iparam0 < len(oper_id_name):
                                oper_id = str(oper_id_name[iparam0]).split('.0')
                                oper_name = oper_id_name[iparam0 + 1]
                                if len(oper_id) == 1:
                                    self.on_oper(oper_id[0], oper_name)
                                iparam0 += 2

                        elif cmd == 'deop':
                            deop_id = amf0_cmd[3]
                            deop_nick = amf0_cmd[4]
                            self.on_deop(deop_id, deop_nick)

                        elif cmd == 'owner':
                            self.on_owner()

                        elif cmd == 'avons':
                            avons_id_name = amf0_cmd[4:]
                            if len(avons_id_name) is not 0:
                                while iparam0 < len(avons_id_name):
                                    avons_id = avons_id_name[iparam0]
                                    avons_name = avons_id_name[iparam0 + 1]
                                    self.on_avon(avons_id, avons_name)
                                    iparam0 += 2

                        elif cmd == 'pros':
                            pro_ids = amf0_cmd[4:]
                            if len(pro_ids) is not 0:
                                for pro_id in pro_ids:
                                    pro_id = str(pro_id).replace('.0', '')
                                    self.on_pro(pro_id)

                        elif cmd == 'nick':
                            old_nick = amf0_cmd[3]
                            new_nick = amf0_cmd[4]
                            nick_id = int(amf0_cmd[5])
                            self.on_nick(old_nick, new_nick, nick_id)

                        elif cmd == 'nickinuse':
                            self.on_nickinuse()

                        elif cmd == 'quit':
                            quit_name = amf0_cmd[3]
                            quit_id = amf0_cmd[4]
                            self.on_quit(quit_id, quit_name)

                        elif cmd == 'kick':
                            kick_id = amf0_cmd[3]
                            kick_name = amf0_cmd[4]
                            self.on_kick(kick_id, kick_name)

                        elif cmd == 'banned':
                            self.on_banned()

                        elif cmd == 'banlist':
                            banlist_id_nick = amf0_cmd[3:]
                            if len(banlist_id_nick) is not 0:
                                while iparam0 < len(banlist_id_nick):
                                    banned_id = banlist_id_nick[iparam0]
                                    banned_nick = banlist_id_nick[iparam0 + 1]
                                    self.on_banlist(banned_id, banned_nick)
                                    iparam0 += 2

                        elif cmd == 'startbanlist':
                            self.on_startbanlist()

                        elif cmd == 'topic':
                            topic = amf0_cmd[3]
                            self.on_topic(topic)

                        elif cmd == 'gift':
                            self.console_write(COLOR['white'], str(amf0_cmd))

                        elif cmd == 'prepare_gift_profile':
                            self.console_write(COLOR['white'], str(amf0_cmd))

                        elif cmd == 'from_owner':
                            owner_msg = amf0_cmd[3]
                            self.on_from_owner(owner_msg)

                        elif cmd == 'doublesignon':
                            self.on_doublesignon()

                        elif cmd == 'privmsg':
                            # self.msg_raw = amf0_cmd[4]
                            msg_text = self._decode_msg(u'' + amf0_cmd[4])
                            msg_sender = str(amf0_cmd[6])
                            self.on_privmsg(msg_text, msg_sender)

                        elif cmd == 'notice':
                            notice_msg = amf0_cmd[3]
                            notice_msg_id = amf0_cmd[4]
                            if notice_msg == 'avon':
                                avon_name = amf0_cmd[5]
                                self.on_avon(notice_msg_id, avon_name)
                            elif notice_msg == 'pro':
                                self.on_pro(notice_msg_id)

                        elif cmd == 'private_room':
                            private_status = str(amf0_cmd[3])
                            if private_status == 'yes':
                                self.private_room = True
                            elif private_status == 'no':
                                self.private_room = False
                            self.on_private_room()

                        else:
                            self.console_write(COLOR['bright_red'], 'Unknown command: %s' % cmd)

            except Exception as ex:
                log.error('General callback error: %s' % ex, exc_info=True)
                if CONFIG['debug_mode']:
                    traceback.print_exc()

    # Callback Event Methods.
    def on_result(self, result_info):
        # TODO: We already parse and set the streamID elsewhere, we may not need this in the future.
        # if len(result_info) is 4 and type(result_info[3]) is int:
            # self.stream_id = result_info[3]  # stream ID?
            # log.debug('Stream ID: %s' % self.stream_id)
            # pass
        if CONFIG['debug_mode']:
            for list_item in result_info:
                if type(list_item) is rtmp_protocol.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['white'], k + ': ' + str(list_item[k]))
                else:
                    self.console_write(COLOR['white'], str(list_item))

    def on_error(self, error_info):
        if CONFIG['debug_mode']:
            for list_item in error_info:
                if type(list_item) is rtmp_protocol.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['bright_red'], k + ': ' + str(list_item[k]))
                else:
                    self.console_write(COLOR['bright_red'], str(list_item))

    def on_status(self, status_info):
        if CONFIG['debug_mode']:
            for list_item in status_info:
                if type(list_item) is rtmp_protocol.pyamf.ASObject:
                    for k in list_item:
                        self.console_write(COLOR['white'], k + ': ' + str(list_item[k]))
                else:
                    self.console_write(COLOR['white'], str(list_item))

    def on_bwdone(self):
        self.console_write(COLOR['green'], 'Received Bandwidth Done.')
        if not self.is_reconnected:
            if CONFIG['enable_auto_job']:
                self.console_write(COLOR['white'], 'Starting auto job timer.')
                self.start_auto_job_timer()

    def on_registered(self, client_info):
        self.client_id = client_info['id']
        self.is_client_mod = client_info['mod']
        self.is_client_owner = client_info['own']
        user = self.add_user_info(client_info['nick'])
        user.id = client_info['id']
        user.nick = client_info['nick']
        user.is_owner = client_info['own']
        user.user_account_type = client_info['stype']
        user.user_account_gift_points = client_info['gp']
        user.is_mod = self.is_client_mod

        self.console_write(COLOR['bright_green'], 'registered with ID: %d' % self.client_id)

        key = tinychat_api.get_captcha_key(self.roomname, str(self.client_id), proxy=self.proxy)
        if key is None:
            self.console_write(COLOR['bright_red'], 'There was a problem obtaining the captcha key. Key=%s' % str(key))
            sys.exit(1)
        else:
            self.console_write(COLOR['bright_green'], 'Captcha key found: %s' % key)
            self.send_cauth_msg(key)
            self.set_nick()

    def on_join(self, join_info_dict):
        user = self.add_user_info(join_info_dict['nick'])
        user.id = join_info_dict['id']
        user.is_mod = join_info_dict['mod']
        user.is_owner = join_info_dict['own']
        user.nick = join_info_dict['nick']
        user.user_account = join_info_dict['account']
        user.user_account_type = join_info_dict['stype']
        user.user_account_gift_points = join_info_dict['gp']
        user.device_type = str(join_info_dict['btype'])
        user.reading_only = join_info_dict['lf']

        if len(user.device_type) is 0:
            user.device_type = 'unknown'

        if join_info_dict['account']:
            tc_info = tinychat_api.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']
            if join_info_dict['own']:
                self.console_write(COLOR['red'],
                                   'Room Owner %s:%d:%s' % (join_info_dict['nick'], join_info_dict['id'],
                                                            join_info_dict['account']))
            elif join_info_dict['mod']:
                self.console_write(COLOR['bright_red'],
                                   'Moderator %s:%d:%s' % (join_info_dict['nick'], join_info_dict['id'],
                                                           join_info_dict['account']))
            else:
                self.console_write(COLOR['bright_yellow'],
                                   '%s:%d has account: %s' % (join_info_dict['nick'], join_info_dict['id'],
                                                              join_info_dict['account']))
        else:
            if join_info_dict['id'] is not self.client_id:
                self.console_write(COLOR['bright_cyan'],
                                   '%s:%d joined the room.' % (join_info_dict['nick'], join_info_dict['id']))

    def on_joins(self, joins_info_dict):
        user = self.add_user_info(joins_info_dict['nick'])
        user.nick = joins_info_dict['nick']
        user.id = joins_info_dict['id']
        user.is_mod = joins_info_dict['mod']
        user.is_owner = joins_info_dict['own']
        user.user_account = joins_info_dict['account']
        user.user_account_type = joins_info_dict['stype']
        user.user_account_gift_points = joins_info_dict['gp']
        user.device_type = str(joins_info_dict['btype'])
        user.reading_only = joins_info_dict['lf']

        if len(user.device_type) is 0:
            user.device_type = 'unknown'

        if joins_info_dict['account']:
            if joins_info_dict['own']:
                self.console_write(COLOR['red'],
                                   'Joins Room Owner %s:%d:%s' % (joins_info_dict['nick'], joins_info_dict['id'],
                                                                  joins_info_dict['account']))
            elif joins_info_dict['mod']:
                self.console_write(COLOR['bright_red'],
                                   'Joins Moderator %s:%d:%s' % (joins_info_dict['nick'], joins_info_dict['id'],
                                                                 joins_info_dict['account']))
            else:
                self.console_write(COLOR['bright_yellow'],
                                   'Joins: %s:%d:%s' % (joins_info_dict['nick'], joins_info_dict['id'],
                                                        joins_info_dict['account']))
        else:
            if joins_info_dict['id'] is not self.client_id:
                self.console_write(COLOR['bright_cyan'],
                                   'Joins: %s:%d' % (joins_info_dict['nick'], joins_info_dict['id']))

    def on_joinsdone(self):
        self.console_write(COLOR['cyan'], 'All joins information received.')
        if self.is_client_mod:
            self.send_banlist_msg()

    def on_oper(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = True
        if uid != self.client_id:
            self.console_write(COLOR['bright_red'], '%s:%s is moderator.' % (nick, uid))

    def on_deop(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = False
        self.console_write(COLOR['red'], '%s:%s was deoped.' % (nick, uid))

    def on_owner(self):
        pass

    def on_avon(self, uid, name):
        self.console_write(COLOR['cyan'], '%s:%s is broadcasting.' % (name, uid))

    def on_pro(self, uid):
        self.console_write(COLOR['cyan'], '%s is pro.' % uid)

    def on_nick(self, old, new, uid):
        if uid != self.client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self.room_users.keys():
                del self.room_users[old]
                self.room_users[new] = old_info
            self.console_write(COLOR['bright_cyan'], '%s:%s changed nick to: %s  ' % (old, uid, new))

    def on_nickinuse(self):
        self.client_nick += str(random.randint(0, 10))
        self.console_write(COLOR['white'], 'Nick already taken. Changing nick to: %s' % self.client_nick)
        self.set_nick()

    def on_quit(self, uid, name):
        if name in self.room_users.keys():
            del self.room_users[name]
            self.console_write(COLOR['cyan'], '%s:%s left the room.' % (name, uid))

    def on_kick(self, uid, name):
        self.console_write(COLOR['bright_red'], '%s:%s was banned.' % (name, uid))
        self.send_banlist_msg()

    def on_banned(self):
        self.console_write(COLOR['red'], 'You are banned from this room.')

    def on_startbanlist(self):
        self.console_write(COLOR['cyan'], 'Checking banlist.')

    def on_banlist(self, uid, nick):
        self.room_banlist[nick] = uid
        # TODO: Console log of "banlist" muted to allow reduced logging in the console.
        # self.console_write(COLOR['bright_red'], 'Banned user: %s:%s' % (nick, uid))

    def on_topic(self, topic):
        self.topic_msg = topic.encode('utf-8', 'replace')
        self.console_write(COLOR['cyan'], 'Room topic: %s' % self.topic_msg)

    def on_private_room(self):
        self.console_write(COLOR['cyan'], 'Private Room: %s' % self.private_room)

    def on_from_owner(self, owner_msg):
        msg = str(owner_msg).replace('notice', '').replace('%20', ' ')
        self.console_write(COLOR['bright_red'], msg)

    def on_doublesignon(self):
        self.console_write(COLOR['red'], 'Double account sign on. Aborting!')
        self.is_connected = False
        if CONFIG['double_signon_reconnect']:
            self.reconnect()
        else:
            self.console_write(COLOR['red'], 'Disconnecting from the server.')
            self.disconnect()
            # Exit with status code 1.
            sys.exit(1)

    def on_reported(self, uid, nick):
        self.console_write(COLOR['bright_red'], 'You were reported by %s:%s.' % (uid, nick))

    def on_privmsg(self, msg, msg_sender):
        """
        Message command controller.
        :param msg: str message.
        :param msg_sender: str the sender of the message.
        """
        # Get user info object of the user sending the message..
        self.user_obj = self.find_user_info(msg_sender)

        if msg.startswith('/'):
            msg_cmd = msg.split(' ')
            if msg_cmd[0] == '/msg':
                private_msg = ' '.join(msg_cmd[2:])
                self.private_message_handler(msg_sender, private_msg.strip())

            elif msg_cmd[0] == '/reported':
                self.on_reported(self.user_obj.id, msg_sender)

            elif msg_cmd[0] == '/mbs':
                media_type = msg_cmd[1]
                media_id = msg_cmd[2]
                # TODO: int --> float, issues when handling SoundCloud media.
                time_point = float(msg_cmd[3])
                # start in new thread
                threading.Thread(target=self.on_media_broadcast_start,
                                 args=(media_type, media_id, time_point, msg_sender, )).start()

            elif msg_cmd[0] == '/mbc':
                media_type = msg_cmd[1]
                self.on_media_broadcast_close(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpa':
                media_type = msg_cmd[1]
                self.on_media_broadcast_paused(media_type, msg_sender)

            elif msg_cmd[0] == '/mbpl':
                media_type = msg_cmd[1]
                time_point = float(msg_cmd[2])
                self.on_media_broadcast_play(media_type, time_point, msg_sender)

            elif msg_cmd[0] == '/mbsk':
                media_type = msg_cmd[1]
                time_point = int(msg_cmd[2])
                self.on_media_broadcast_skip(media_type, time_point, msg_sender)

        else:
            self.message_handler(msg_sender, msg.strip())

    # Message Handler.
    def message_handler(self, msg_sender, msg):
        """
        Message handler.
        :param msg_sender: str the user sending a message
        :param msg: str the message
        """
        self.console_write(COLOR['green'], '%s:%s' % (msg_sender, msg))

    # Private message Handler.
    def private_message_handler(self, msg_sender, private_msg):
        """
        A user private message us.
        :param msg_sender: str the user sending the private message.
        :param private_msg: str the private message.
        """
        self.console_write(COLOR['white'], 'Private message from %s:%s' % (msg_sender, private_msg))

    # Media Events.
    def on_media_broadcast_start(self, media_type, video_id, time_point, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param video_id: str the youTube ID or soundCloud trackID.
        :param time_point: int the time in the video/track which we received to start playing.
        :param usr_nick: str the user name of the user playing media.
        """
        self.console_write(COLOR['bright_magenta'], '%s is playing %s %s (%s)' %
                           (usr_nick, media_type, video_id, time_point))

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
        self.console_write(COLOR['bright_magenta'], '%s time searched the %s at: %s' %
                           (usr_nick, media_type, time_point))

    # User Related
    def add_user_info(self, usr_nick):
        """
        Find the user object for a given user name and add to it.
        We use this method to add info to our user info object.
        :param usr_nick: str the user name of the user we want to find info for.
        :return: object a user object containing user info.
        """
        if usr_nick not in self.room_users.keys():
            self.room_users[usr_nick] = RoomUser(usr_nick)
        return self.room_users[usr_nick]

    def find_user_info(self, usr_nick):
        """
        Find the user object for a given user name.
        Instead of adding to the user info object, we return None if the user name is NOT in the room_users dict.
        We use this method when we are getting user input to look up.

        :param usr_nick: str the user name to find info for.
        :return: object or None if no user name is in the room_users dict.
        """
        if usr_nick in self.room_users.keys():
            return self.room_users[usr_nick]
        return None

    # Message Methods.
    def send_bauth_msg(self):
        """ Get and send the bauth key needed before we can start a broadcast. """
        bauth_key = tinychat_api.get_bauth_token(self.roomname, self.client_nick, self.client_id,
                                                 self.greenroom, proxy=self.proxy)
        if bauth_key != 'PW':
            self._send_command('bauth', [u'' + bauth_key])

    def send_cauth_msg(self, cauth_key):
        """
        Send the cauth key message with a working cauth key, we need to send this before we can chat.
        :param cauth_key: str a working cauth key.
        """
        self._send_command('cauth', [u'' + cauth_key])

    def send_owner_run_msg(self, msg):
        """
        Send owner run message. The client has to be mod when sending this message.
        :param msg: str the message to send.
        :param ascii: bool True/False if the message to send contains ASCII/unicode characters.
        """
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
                    msg_url_encoded += quote_plus(msg[x].encode('utf8'), safe='/')
                except (Exception, UnicodeEncodeError):
                    pass

        self._send_command('owner_run', [u'notice' + msg_url_encoded])

    def send_chat_msg(self, msg):
        """
        Send a chat room message.
        :param msg: str the message to send.
        """
        self._send_command('privmsg', [u'' + self._encode_msg(msg), u'#262626,en'])

    def send_private_msg(self, msg, nick):
        """
        Send a private message.
        :param msg: str the private message to send.
        :param nick: str the user name to receive the message.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self._send_command('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg), u'#262626,en',
                                           u'n' + str(user.id) + '-' + nick])
            self._send_command('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg), u'#262626,en',
                                           u'b' + str(user.id) + '-' + nick])

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
            self._send_command('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'b' + str(user.id) + '-' + nick])
            self._send_command('privmsg', [u'' + self._encode_msg(msg), '#0,en', u'n' + str(user.id) + '-' + nick])

    def send_userinfo_request_msg(self, user_id):
        """
        Send user info request to a user.
        :param user_id: str user id of the user we want info from.
        :return:
        """
        self._send_command('account', [u'' + user_id])

    def set_nick(self):
        """ Send the nick message. """
        if not self.client_nick:
            self.client_nick = create_random_string(5, 25)
        self.console_write(COLOR['white'], 'Setting nick: %s' % self.client_nick)
        self._send_command('nick', [u'' + self.client_nick])

    def send_ban_msg(self, nick, uid):
        """
        Send ban message. The client has to be mod when sending this message.
        :param nick: str the user name of the user we want to ban.
        :param uid: str the ID of the user we want to ban.
        """
        self._send_command('kick', [u'' + nick, str(uid)])
        self.send_banlist_msg()

    def send_forgive_msg(self, uid):
        """
        Send forgive message. The client has to be mod when sending this message.
        :param uid: int ID of the user we want to forgive.
        """
        self._send_command('forgive', [u'' + str(uid)])
        self.send_banlist_msg()

    def send_banlist_msg(self):
        """
        Send banlist message. The client has to be mod when sending this message.
        """
        self._send_command('banlist', [])

    def send_topic_msg(self, topic):
        """
        Send a room topic message. The client has to be mod when sending this message.
        :param topic: str the new room topic.
        """
        self._send_command('topic', [u'' + topic])

    def send_close_user_msg(self, nick):
        """
        Send close user broadcast message. The client has to be mod when sending this message.
        :param nick: str the nickname of the user we want to close.
        """
        self._send_command('owner_run', [u'_close' + nick])

    def send_mute_msg(self):
        """
        Send mute message to mute all broadcasting users in the room.
        The client has to be mod when sending this message.
        """
        self._send_command('owner_run', [u'mute'])

    def send_push2talk_msg(self):
        """
        Send 'push2talk' room message to force push to talk for all users.
        The client has to be mod when sending this message.
        """
        self._send_command('owner_run', [u'push2talk'])

    # TODO: Work out how the broadcast acceptance message works on a normal client.
    def send_broadcast_accept_msg(self, nick):
        """
        Send a message to accept a pending broadcast in a greenroom.
        :param nick: str the nickname of the user.
        """
        user = self.find_user_info(nick)
        if user is not None and self.room_broadcast_pass is not None:
            self._send_command('privmsg', [u'' + self._encode_msg('/allowbroadcast ' + self.room_broadcast_pass),
                                           '#0,en', u'n' + str(user.id) + '-' + nick])

    def send_private_room_msg(self, state=None):
        """
        Send 'private room' message to the room. The client has to be mod when sending this message.
        We assume this prevents the room from being listed in the directory.
        OPTIONAL: param state: boolean default None and connection value is used, set as True/False depending on
                               whether private_room should be turned on or not.
        """
        value = ''
        if state is not None:
            if state:
                value = 'yes'
            elif not state:
                value = 'no'
        else:
            if not self.private_room:
                value = 'yes'
            elif self.private_room:
                value = 'no'

        self._send_command('private_room', [u'' + str(value)])

    # Media Message Functions
    def send_media_broadcast_start(self, media_type, video_id, time_point=0, private_nick=None):
        """
        Starts a media broadcast.
        NOTE: This method replaces play_youtube and play_soundcloud
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
        NOTE: This method replaces stop_youtube and stop_soundcloud.
        :param media_type: str 'youTube' or 'soundCloud'
        :param private_nick: str if not None, stop the media broadcast for this nickname only.
        """
        mbc_msg = '/mbc %s' % media_type
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbc_msg)
        else:
            self.send_chat_msg(mbc_msg)

    # TODO: Implement send_media_broadcast_play.
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

    # TODO: Implement send_media_broadcast_pause.
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

    # TODO: Implement send_media_broadcast_skip.
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

    # Message Construction.
    def _send_command(self, cmd, params=None, trans_id=0):
        """
         Sends command messages to the server.
         Calls remote procedure calls (RPC) at the receiving end.

        :param cmd: str command name.
        :param params: list command parameters.
        :param trans_id: int the transaction ID.
        """
        msg_format = [u'' + cmd, trans_id, None]
        if params and type(params) is list:
            msg_format.extend(params)

        # Retrieve/generate message structure.
        msg = message_structures.send_command(
            rtmp_protocol.data_types.COMMAND,
            msg_format)

        try:
            self.connection.writer.write(msg)
            self.connection.writer.flush()

            if CONFIG['amf_sent']:
                self.console_write(COLOR['white'], 'SENT --> ' + str(msg))

        except Exception as ex:
            log.error('send command error: %s' % ex, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()
            self.reconnect()

    # Stream functions
    def send_create_stream(self, play=False):
        """
        Send createStream message.
        :param play: Boolean True/False depending on whether the create stream is used for playing a stream.
        """
        if play:
            transaction_id = self.create_stream_id
        else:
            transaction_id = 0

        # Retrieve/generate message structure.
        msg = message_structures.create_stream(
            rtmp_protocol.data_types.COMMAND,
            transaction_id)

        self.console_write(COLOR['white'], 'Sending createStream message #%s' % transaction_id)
        self.connection.writer.write(msg)
        self.connection.writer.flush()

        # Set to sort the stream information appropriately upon the arrival of a "_result" packet from the server.
        self.stream_sort = True

    def send_publish(self):
        """ Send publish message. """
        if 'client_publish' in self.streams:

            # Publish type may vary from live, record or append. Live is the only supported publishing type at
            # the moment, the use of other types is not recommended and may cause further issues in the program.
            publish_type = 'live'

            # Retrieve/generate message structure.
            msg = message_structures.publish(
                rtmp_protocol.data_types.COMMAND,
                self.streams['client_publish'],
                self.client_id,
                publish_type)

            self.console_write(COLOR['white'], 'Sending publish message StreamID: %s' % self.streams['client_publish'])
            self.connection.writer.write(msg)
            self.connection.writer.flush()

        else:
            self.console_write(COLOR['white'], 'No StreamID available to start publish upon.')

    def send_set_chunk_size(self, new_chunk_size=None):
        """
        Send 'set chunk size' message.
        :param new_chunk_size: int the new chunk size.
        """
        if 'client_publish' in self.streams:
            if new_chunk_size is not None:
                chunk_size = new_chunk_size
            else:
                self.console_write(COLOR['white'], 'No chunk size was provided.')
                return

            msg = message_structures.set_chunk_size(
                rtmp_protocol.data_types.SET_CHUNK_SIZE,
                self.streams['client_publish'],
                chunk_size)

            self.console_write(COLOR['white'], 'Sending chunk size message.')
            self.connection.writer.write(msg)
            self.connection.writer.flush()

            # Set writer to work with new chunk size
            self.connection.writer.chunk_size = chunk_size
            self.console_write(COLOR['white'], 'Set chunk size: %s' % self.connection.writer.chunk_size)
        else:
            self.console_write(COLOR['white'], 'No publish StreamID found to set chunk size upon.')

    def send_play(self, stream_id, play_id):
        """
        Send 'play' message.
        :param stream_id: int the stream ID onto which the message should be sent on.
        :param play_id: str the ID of the stream to play, in this case this will be uid of a user.
        """
        if type(play_id) is int:
            # Retrieve/generate message structure.
            msg = message_structures.play(
                rtmp_protocol.data_types.COMMAND,
                stream_id,
                play_id)

            self.console_write(COLOR['white'], 'Starting playback for:%s on StreamID: %s' % (play_id, stream_id))
            self.connection.writer.write(msg)
            self.connection.writer.flush()
        else:
            self.console_write(COLOR['white'], 'PlayID format incorrect, integers only allowed.')

    def configure_av_packet(self, av_content):
        """
        Configures audio/video content for a packet, given the frame content and the settings, and send the packet.
        :param av_content: list [type of packet - audio/video, raw data, packet control type, time stamp].
        """
        # Assign timestamp.
        if self.force_time_stamp is not None:
            time_stamp = self.force_time_stamp
        else:
            time_stamp = av_content[3]

        # Assign control type.
        control_type = av_content[2]

        # Setup audio packet.
        if av_content[0] == rtmp_protocol.data_types.AUDIO_MESSAGE:
            if not self.play_audio:
                # Send no audio data if it has been disabled.
                raw_data = b''
            else:
                raw_data = av_content[1]
            self.send_audio_packet(raw_data, control_type, time_stamp)

        # Setup video packet.
        elif av_content[0] == rtmp_protocol.data_types.VIDEO_MESSAGE:
            if not self.play_video:
                # Send no video data if it has been disabled.
                raw_data = b''
            else:
                raw_data = av_content[1]
            self.send_video_packet(raw_data, control_type, time_stamp)
        else:
            print('This frame is an invalid audio/video input.')

    def send_audio_packet(self, packet_raw_data, packet_control_type, packet_timestamp=0):
        """
        Send Audio message.
        :param packet_raw_data: bytes the audio data (in the MP3 format) to be sent.
        :param packet_control_type: hexadecimal value of the control type (originally 0x66,
                                    though due to a lack of adequate audio encoding it is sent via
                                    inter-frame (0x22).
        :param packet_timestamp: int the timestamp for the packet (OPTIONAL)
        """
        # Retrieve/generate message structure.
        msg = message_structures.audio(
            rtmp_protocol.data_types.AUDIO_MESSAGE,
            self.streams['client_publish'],
            packet_raw_data,
            packet_control_type,
            packet_timestamp)

        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def send_video_packet(self, packet_raw_data, packet_control_type, packet_timestamp=0):
        """
        Send Video message.
        :param packet_raw_data: bytes the video data (in the FLV1 format) to be sent.
        :param packet_control_type: hexadecimal value of the control type, between 0x12 (key-frame), 0x22 (inter-frame),
                                    0x32 (disposable-frame) and 0x42 (generated-frame).
                                    NOTE: This can produce unexpected results.
        :param packet_timestamp: int the timestamp for the packet (OPTIONAL)
        """
        # Retrieve/generate message structure.
        msg = message_structures.video(
            rtmp_protocol.data_types.VIDEO_MESSAGE,
            self.streams['client_publish'],
            packet_raw_data,
            packet_control_type,
            packet_timestamp)

        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def send_close_stream(self, stream_id=None):
        """
        Send closeStream message.
        :param stream_id: int the stream ID onto which the message should be sent on.
        """
        if 'client_close_stream' in self.streams:
            if stream_id is None:
                stream_id = self.streams['client_close_stream']

            msg = message_structures.close_stream(
                rtmp_protocol.data_types.COMMAND,
                stream_id)

            self.console_write(COLOR['white'], 'Sending closeStream message on StreamID: %s' % stream_id)
            self.connection.writer.write(msg)
            self.connection.writer.flush()
        else:
            self.console_write(COLOR['white'], 'No closeStream StreamID found to send the closeStream request upon.')

    def send_delete_stream(self, stream_id=None):
        """
        Send deleteStream message.
        :param stream_id:
        """
        if 'client_delete_stream' in self.streams:
            if stream_id is None:
                stream_id = self.streams['client_delete_stream']

            msg = message_structures.delete_stream(
                rtmp_protocol.data_types.COMMAND,
                stream_id)

            self.console_write(COLOR['white'], 'Sending deleteStream message on StreamID: %s' % stream_id)
            self.connection.writer.write(msg)
            self.connection.writer.flush()
        else:
            self.console_write(COLOR['white'], 'No deleteStream StreamID found to send the deleteStream request upon.')

    # Helper Methods
    def send_ping_request(self, manual=False):
        """
        Send a ping request (experimental).
        NOTE: The client sends an unorthodox message i.e. *ping request* instead of a *ping response* due to
              the nature of how the servers were set up. Tinychat servers do not automatically request a ping,
              so we issue a request instead. We assume the data-types are reversed since an event_type of 7, which
              is only a client response, will be "accepted" by the server as it responds to your initial
              ping request with random data.
        :param manual: Boolean True/False if you want to instantly request a 'reverse' ping request.
        """
        msg = message_structures.ping(
            rtmp_protocol.data_types.USER_CONTROL,
            rtmp_protocol.user_control_types.PING_REQUEST)

        if not manual:
            while not self.is_connected:
                time.sleep(1)
            while self.publish_connection:
                time.sleep(1)
            while self.is_connected and not self.publish_connection:
                self.connection.writer.write(msg)
                self.connection.writer.flush()
                time.sleep(120)
        elif manual:
            self.connection.writer.write(msg)
            self.connection.writer.flush()

    @staticmethod
    def _encode_msg(msg):
        """
        Encode normal text str to comma separated decimal.
        :param msg: str the normal text to encode
        :return: comma separated decimal str.
        """
        return ','.join(str(ord(char)) for char in msg)

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
                pass
        return msg

    def _set_stream(self, stream=True, video=False):
        """
        Appropriately sets the necessary options into effect to start/close client streams.
        :param stream: bool
        :param video: bool
        """
        if stream:
            if not self.publish_connection:
                # Publish camera sequence:
                self.console_write(COLOR['white'], 'Opening stream.')
                # Send broadcast authorisation message to the server.
                self.send_bauth_msg()
                # Create a new stream onto which we can send packets e.g. audio/video packets.
                self.send_create_stream()
                # Sort out the stream request reply from the server.
                while self.stream_sort:
                    time.sleep(1)
                # Send publish message to the server.
                self.send_publish()
                # Acknowledge locally that we are publishing a stream.
                self.publish_connection = True

                # If there was a request to load the default FLV image onto the broadcast stream, then start it.
                if video:
                    time.sleep(10)
                    # self.console_write(COLOR['white'], 'Starting FLV playback.')
                    # self.load_flv()
                    self.load_webcam()
            else:
                self.console_write(COLOR['bright_red'], 'No need to start stream, client broadcast already present.')
        elif not stream:
            if self.publish_connection:
                # Set publish connection to false to stop any video threads publishing.
                self.publish_connection = False
                # Close camera sequence:
                self.console_write(COLOR['white'], 'Closing stream.')
                # Delete all the stored stream information and turn off the publishing.
                self.send_close_stream(self.streams['client_close_stream'])
                self.send_delete_stream(self.streams['client_delete_stream'])
                self.tidy_streams(self.streams['client_stream'])
            else:
                self.console_write(COLOR['bright_red'], 'No need to stop stream, client was not broadcasting.')
        else:
            self.console_write(COLOR['white'], 'No stream argument was passed, True/False should be passed to '
                                               'initiate/close streams respectively.')

    # TODO: Make this more concise.
    def _send_frames(self, frames):
        """
        Send the appropriate packets corresponding to the tag/frames.
        :param frames: list containing all the frame data.
        """
        # Start sending frames one by one in iterated order.
        if frames is not None:
            self.console_write(COLOR['white'], 'Received tag/frame data. Starting stream.')

            # Set an initial start frame delay which is smaller than the continuous delay.
            frame_delay = 0.0125
            self.console_write(COLOR['white'], 'Initial frame delay: %s' % frame_delay)

            for individual_frame in xrange(len(frames)):
                if self.publish_connection:
                    # Set the AV content to be configured and sent into the stream.
                    self.configure_av_packet(frames[individual_frame])
                    # Only enable this console print if you want to see if each frame is sent.
                    self.console_write(COLOR['green'], 'Sent frame #%s.' % (individual_frame + 1))

                    time.sleep(frame_delay)
                else:
                    self.console_write(COLOR['red'], 'The publish stream was closed.')
                    break
        else:
            self.console_write(COLOR['white'], 'No frames were received, returning.')

    # Image (FLV) loading.
    def load_flv(self):
        """ Load FLV and publish it's content to the room. """
        # The FLV file stored at '/files/defaults/'.
        temp_file = 'bunny.flv'
        with open(CONFIG['media_defaults'] + temp_file, 'rb') as file_object:
            # Load the tag within the FLV given the opened file.
            tags_list = tag_handler.iterate_frames(file_object)

        # Start the send frames thread to send the tags we have loaded.
        if len(tags_list) is not 0:
            self.console_write(COLOR['white'], 'Read tags and ready for broadcast.')
            threading.Thread(target=self._send_frames, args=(tags_list, )).start()
        else:
            self.console_write(COLOR['white'], 'No tags were found in the file.')

    def load_webcam(self):
        cam = Device(devnum=1)
        print('Initialised webcam on device: %s' % cam.getDisplayName())
        frame_num = 0
        while self.publish_connection:
            frame_num += 1
            cam_buffer = cam.getBuffer()
            raw_data = cam_buffer[0]
            control_type = 0x18
            timestamp = 0
            self.send_video_packet(raw_data, control_type, timestamp)
            print('Sent frame #%s' % frame_num)

    # Timed Auto Methods.
    def auto_job_handler(self):
        """ The event handler for auto_job_timer. """
        if self.is_connected:
            log.info('Executing auto_job handler.')
            tinychat_api.get_roomconfig_xml(self.roomname, self.room_pass, proxy=self.proxy)
        self.start_auto_job_timer()

    def start_auto_job_timer(self):
        """
        Just like using Tinychat with a browser, this method will
        fetch the room config from Tinychat API every 5 minutes (300 seconds).
        See line 228 at http://tinychat.com/embed/chat.js
        """
        log.info('Starting auto_job_timer, with interval: %s' % CONFIG['auto_job_interval'])
        threading.Timer(CONFIG['auto_job_interval'], self.auto_job_handler).start()

    # TODO: Make this method more simpler - test to see if this method works.
    def alive(self):
        """
        Timed check to see if the bot is in the API XML file, if it is not present after 5 checks,
        the bot will reconnect.
        """
        times = 0
        while self.is_connected:
            time.sleep(200)

            # Request the XML file for the room.
            room = tinychat_api.spy_info(self.roomname)
            if room['status_code'] is not 200:
                times = 0
            elif room is None or room is 'PW':
                times = 0
            else:
                if u'' + self.client_nick not in room['users']:
                    if times is 3:
                        times = 0
                        self.reconnect()
                    else:
                        times += 1


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
        log.info('Starting pinylib version: %s' % __version__)
    else:
        log.addHandler(logging.NullHandler())
    main()
