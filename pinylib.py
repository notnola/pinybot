#!/usr/bin/env python2
# -*- coding: utf-8 -*-

""" Pinylib module by Nortxort (https://github.com/nortxort/pinylib) """

# Edited for pinybot (https://github.com/TechWhizZ199/pinybot)

import time
import threading
import random
import traceback
# TODO: Implement logging.
import logging

import os
import sys
import getpass

from rtmp import rtmp_protocol, message_structures
from files import file_handler as fh
from urllib import quote_plus
from api import web_request, tinychat_api

# Set console colors as false in the configuration file to prevent colorama from loading in interpreters or consoles
# which do not support the rendering of colors.
from colorama import init, Fore, Style
#  Console colors.
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

# except ImportError:
#     CONFIG['console_colors'] = False
#     seq = ('white', 'green', 'bright_green', 'yellow',
#            'bright_yellow', 'cyan', 'bright_cyan', 'red',
#            'bright_red', 'magenta', 'bright_magenta')
#     COLOR = dict.fromkeys(seq, False)


# TODO: Reorganise and reduce these initial configuration steps, shorten the link between.
#       pinybot.py and tinychat.py/pinylib.py.
# ------------------------------------------------------------------------------
# Loads CONFIG in the configuration file from the root directory:
CONFIG_FILE_NAME = '/config.ini'  # State the name of the '.ini' file here.
CURRENT_PATH = sys.path[0]
CONFIG_PATH = CURRENT_PATH + CONFIG_FILE_NAME
CONFIG = fh.configuration_loader(CONFIG_PATH)

if CONFIG is None:
    print('No file named ' + CONFIG_FILE_NAME + ' found in: ' + CONFIG_PATH)
    sys.exit(1)  # Exit to system safely whilst returning exit code 1.
# ------------------------------------------------------------------------------

# TODO: Web server importation if it is specified in the configuration.
# TODO: Remove files in a generic fashion rather than specifying the exact file names.
# Remove unnecessary files remaining from previous web-server runs
# if os.path.exists(str(CURRENT_PATH) + '/api/index.html'):
#     os.remove(str(CURRENT_PATH) + '/api/index.html')
# if os.path.exists(str(CURRENT_PATH) + '/api/recaptcha.txt'):
#     os.remove(str(CURRENT_PATH) + '/api/recaptcha.txt')


__version__ = 4.0
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
    fh.file_writer(CONFIG['log_path'], file_name, msg.encode('ascii', 'ignore'))


def random_color():
    """
    Get a random Tinychat color.
    :return: str random color
    """
    colors = ['#000000', '#7db257', '#a78901', '#9d5bb5', '#5c1a7a', '#c53332', '#821615', '#a08f23',
              '#487d21', '#c356a3', '#1d82eb', '#919104', '#b9807f', '#7bb224', '#1965b6', '#32a5d9']
    return random.choice(colors)


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
        self.user_account_giftpoints = None
        self.is_owner = False
        self.is_mod = False
        self.has_power = False
        self.tinychat_id = None
        self.last_login = None
        self.device_type = ''
        self.reading_only = False
        self.is_playable = False


class TinychatRTMPClient:
    """ Manages a single room connection to a given room. """
    def __init__(self, room, tcurl=None, app=None, room_type=None, nick=None, account=None,
                 password=None, room_pass=None, ip=None, port=None, proxy=None):

        # Standard settings
        self.roomname = room
        self.tc_url = tcurl
        self.app = app
        self.roomtype = room_type
        self.client_nick = nick
        self.account = account
        self.password = password
        self.room_pass = room_pass
        self.ip = ip
        self.port = port
        self.proxy = proxy
        self.greenroom = False
        self.private_room = False
        self.prefix = u'tinychat'
        self.swf_url = u'http://tinychat.com/embed/Tinychat-11.1-1.0.0.0665.swf?version=1.0.0.0665/[[DYNAMIC]]/8'
        self.desktop_version = u'Desktop 1.0.0.0665'
        self.swf_version = 'WIN 21,0,0,216'
        self.embed_url = u'http://tinychat.com/' + self.roomname
        self.client_id = None
        self.connection = None
        self.is_connected = False
        self.is_client_mod = False
        self.room_users = {}
        self.user_obj = object
        self.room_banlist = {}
        self.is_reconnected = False
        self.reconnect_delay = CONFIG['reconnect_delay']

        # Streams settings
        self.streams = {}
        self.stream_sort = False

        # Basic A/V configuration:
        self.publish_connection = False
        # Send audio packets?
        self.play_audio = True
        # Send video packets?
        self.play_video = True
        # Send a constant or automatic timestamp? (Default None automatically retrieves timestamps)
        self.force_time_stamp = None

        # self.play_connection = False
        self.create_stream_id = 1
        # self.setting_stream = None
        # self.play_publishers = {}

        # Others:
        self.ping_request = False
        # self.ping_content = None

    # TODO: Implement decode procedure utilised by the bot here so an array
    #       of unicode can be parsed without any further unicode errors.
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

        # TODO: Include the availability of RTMPE packets.
        # Run via RTMPE (RTMP Encrypted) instead if set in the configuration.
        # Thanks to Nola for advising us of the availability of encrypted messages.
        # if CONFIG['rtmp_encrypted']:
        #    self.tc_url = self.tc_url.replace('rtmp', 'rtmpe')

        if CONFIG['debug_mode']:
            for k in config:
                self.console_write(COLOR['white'], k + ': ' + str(config[k]))

        self.ip = config['ip']
        self.port = config['port']
        self.tc_url = config['tcurl']
        self.app = config['app']
        self.roomtype = config['roomtype']
        self.greenroom = config['greenroom']
        self.room_broadcast_pass = config['roombroadcastpass']

        self.console_write(COLOR['white'], '============ CONNECTING ============\n\n')
        self.connect()

    def connect(self):
        """ Attempts to make a RTMP connection with the given connection parameters. """
        if not self.is_connected:
            log.info('Trying to connect to: %s' % self.roomname)
            try:
                tinychat_api.recaptcha(proxy=self.proxy)

                cauth_cookie = tinychat_api.get_cauth_cookie(self.roomname, proxy=self.proxy)

                self.connection = rtmp_protocol.RtmpClient(self.ip, self.port, self.tc_url, self.embed_url,
                                                           self.swf_url, self.app, self.swf_version, self.roomtype, self.prefix,
                                                           self.roomname, self.desktop_version, cauth_cookie,
                                                           self.account, self.proxy)
                self.connection.connect([])

                # After-hand connection settings.
                self.is_connected = True
                # Set windows title as connected room name & IP ADDRESS:PORT of the room.
                window_message = str(self.roomname) + ' @ ' + str(self.ip) + ':' + str(self.port)
                set_window_title(window_message)

                # Initial NetConnection default communications channel
                self.streams['NetConnection'] = 0

                # Main command (callbacks) handle.
                self._callback()

            except Exception as ex:
                log.error('Connect error: %s' % ex, exc_info=True)
                self.is_connected = False
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
        :param amf0_cmd: list containg the amf decoded commands.
        """
        result_stream_id = int(amf0_cmd[3])
        self.streams['client_stream'] = result_stream_id
        self.streams['client_publish'] = result_stream_id
        self.streams['client_closestream'] = result_stream_id
        self.streams['client_deletestream'] = result_stream_id
        self.stream_sort = False
        self.console_write(COLOR['white'], 'Done client manager.')

    '''
    def start_play_connect(self):
        """ Add a new publisher to our local streams. """
        # while not self.play_connection:
            # time.sleep(1)
        if len(self.play_publishers) is not 0:
            for publisher in self.play_publishers.keys():
                print 'Publishing user:', publisher
                # TODO: Process gets caught up, possibly a loop - rtmp_protocol issue?
                # NONE Type issue?
                self.add_new_publisher(publisher)
                time.sleep(5)
                print 'added new publisher'
            print 'playstreams finished'
        else:
            self.console_write(COLOR['cyan'], 'No publishing users.')

    def add_new_publisher(self, publisher):
        """
        Opens a new stream for a publisher.
        :param publisher:
        """
        # Allocate a new stream for the publisher
        # user = self.find_user_info(publisher)
        self.play_connection = True
        self._send_create_stream(play=True)
        while self.stream_sort:
            time.sleep(1)
        # Issue a play stream request on the new stream
        print('request play:'+ publisher)
        self._send_play(int(self.streams['play' + str(self.create_stream_id)]), int(self.play_publishers[publisher]))
        print 'play was sent successfully'
        self.create_stream_id += 1

    def play_message(self, stream_id, stream_message):
        """
        Monitor the play messages regarding a particular playstream.
        :param stream_id: int the StreamID.
        :param stream_message: str the particular decoded code received.
        """
        print('received message:', stream_message, 'on StreamID:', stream_id)

    def play_manager(self, amf0_cmd):
        """
        A play stream managing function to start play stream for publishers and handle play events.
        :param amf0_cmd: list containg the amf decoded commands.
        """
        # Assign  RTMP stream information items key/pair values
        # in a dictionary to handle further commands
        result_stream_id = int(amf0_cmd[3])
        self.streams['stream' + str(self.create_stream_id)] = result_stream_id
        self.streams['play' + str(self.create_stream_id)] = result_stream_id
        self.streams['closestream' + str(self.create_stream_id)] = result_stream_id
        self.streams['deletestream' + str(self.create_stream_id)] = result_stream_id
        print 'Allocated StreamID:', result_stream_id

        #_result_info = {
        #    'TransactionID': str(amf0_cmd[1]),
        #    'CommandObject': str(amf0_cmd[2]),
        #    'StreamID': str(result_stream_id)
        #}

        # Finalise stream sorting; set it to False to make sure the next stream has a new id to play on
        # and record the user who is being streamed.
        self.stream_sort = False
        print 'stream sort off'
        self.play_connection = False
        print 'play connection off'
        # self.play_publishers[self.setting_stream] = result_stream_id
    '''

    def tidy_streams(self, stream_id):
        """
        Tidy up stream key/pair value in the streams dictionary by providing the StreamID.
        :param stream_id: int StreamID which should be found and all keys matching it
                          should be deleted from the streams dictionary.
        """
        self.console_write(COLOR['white'], 'Deleting all stream information residing on StreamID ' + str(stream_id) + '.')

        for stream_item in self.streams.keys():
            if self.streams[stream_item] == stream_id:
                del self.streams[stream_item]

    def _callback(self):
        """ Callback loop that reads from the RTMP stream. """
        failures = 0
        amf0_data_type = 0
        amf0_data = None
        while self.is_connected:
            try:
                amf0_data = self.connection.reader.next()
                amf0_data_type = amf0_data['msg']

                if CONFIG['amf_reply']:
                    print(amf0_data)

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
                if amf0_data_type == rtmp_protocol.DataTypes.SET_CHUNK_SIZE:
                    if 0 < amf0_data['chunk_size'] <= 65536:
                        self.connection.reader.chunk_size = amf0_data['chunk_size']
                        self.console_write(COLOR['white'], 'Server sent \'SET_CHUNK_SIZE\'; now reading chunks in size\'s of %s.'
                                                        % (str(self.connection.reader.chunk_size)))
                    else:
                        self.console_write(COLOR['red'], 'The CHUNK SIZE was not set; invalid size received.')

                elif amf0_data_type == rtmp_protocol.DataTypes.USER_CONTROL:
                    # if amf0_data['event_type'] == rtmp_protocol.UserControlTypes.STREAM_BEGIN:
                        # self.console_write(COLOR['white'], 'Server sent \'STREAM_BEGIN\'; ready to receive data.')
                    # elif amf0_data['event_type'] ==  rtmp_protocol.UserControlTypes.STREAM_EOF:
                        # self.console_write(COLOR['white'], 'Server sent \'STREAM_EOF\'; end of data.')
                    if amf0_data['event_type'] == rtmp_protocol.UserControlTypes.PING_RESPONSE:
                        self.console_write(COLOR['white'], 'Server sent \'PING_RESPONSE\'.')

                else:
                    try:
                        amf0_cmd = amf0_data['command']
                        cmd = amf0_cmd[0]
                        iparam0 = 0
                    except Exception:
                        continue

                    # ----------------------- ROOM CALLBACKS -----------------------
                    # These are most of the room callbacks that are identified within
                    # the SWF; the defunct callbacks have been ommitted for the library
                    # to be in correspondence with the currently established and working
                    # Tinychat protocol.

                    if cmd == '_result':
                        if self.stream_sort:
                            # if self.play_connection:
                                # Set stream for individual users
                                # self.play_manager(amf0_cmd)
                            # else:

                            # Set streams for the client
                            self.client_manager(amf0_cmd)
                            # result_info = {
                            #     'TransactionID': str(amf0_cmd[1]),
                            #     'CommandObject': str(amf0_cmd[2]),
                            #     'StreamID': str(amf0_cmd[3])
                            # }
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
                            except Exception as ex:
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
                        except Exception as ex:
                            log.error('"_error" callback error occured: %s' % amf0_cmd)
                            self.console_write(COLOR['red'], str(amf0_cmd))

                    elif cmd == 'onBWDone':
                        self.on_bwdone()

                    elif cmd == 'onStatus':
                        # try:
                            # self.stream_manager(amf0_data['stream_id'], amf0_data)
                        # except Exception:
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
                        except Exception as ex:
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
                        if msg_text == '/reported':
                            self.on_reported(msg_sender)
                        else:
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
                        self.console_write(COLOR['bright_red'], 'Unknown command:' + cmd)

            except Exception as ex:
                log.error('General callback error: %s' % ex, exc_info=True)
                if CONFIG['debug_mode']:
                    traceback.print_exc()

                    # Callback Event Methods.

    def on_result(self, result_info):
        if len(result_info) is 4 and type(result_info[3]) is int:
            # TODO: Verify that the stream ID works in this case.
            # self.stream_id = result_info[3]  # stream ID?
            log.debug('Stream ID: %s' % self.stream_id)
            pass
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
        user = self.add_user_info(client_info['nick'])
        user.id = client_info['id']
        user.nick = client_info['nick']
        user.user_account_type = client_info['stype']
        user.user_account_giftpoints = client_info['gp']
        user.is_owner = client_info['own']
        user.is_mod = self.is_client_mod

        self.console_write(COLOR['bright_green'], 'registered with ID: ' + str(self.client_id))

        key = tinychat_api.get_captcha_key(self.roomname, str(self.client_id), proxy=self.proxy)
        if key is None:
            self.console_write(COLOR['bright_red'], 'There was a problem parsing the captcha key. Key=' + str(key))
            sys.exit(1)
        else:
            self.console_write(COLOR['bright_green'], 'Captcha key found: ' + key)
            self.send_cauth_msg(key)
            self.set_nick()

    def on_join(self, join_info_dict):
        user = self.add_user_info(join_info_dict['nick'])
        user.nick = join_info_dict['nick']
        user.id = join_info_dict['id']
        user.user_account = join_info_dict['account']
        user.user_account_type = join_info_dict['stype']
        user.user_account_giftpoints = join_info_dict['gp']
        user.is_mod = join_info_dict['mod']
        user.is_owner = join_info_dict['own']
        user.device_type = str(join_info_dict['btype'])
        user.reading_only = join_info_dict['lf']

        if join_info_dict['account']:
            tc_info = tinychat_api.tinychat_user_info(join_info_dict['account'])
            if tc_info is not None:
                user.tinychat_id = tc_info['tinychat_id']
                user.last_login = tc_info['last_active']
            if join_info_dict['own']:
                self.console_write(COLOR['red'], 'Room Owner ' + join_info_dict['nick'] + ':'
                                   + str(join_info_dict['id']) + ':' + join_info_dict['account'])
            elif join_info_dict['mod']:
                self.console_write(COLOR['bright_red'], 'Moderator ' + join_info_dict['nick'] + ':'
                                   + str(join_info_dict['id']) + ':' + join_info_dict['account'])
            else:
                self.console_write(COLOR['bright_yellow'], join_info_dict['nick'] + ':' + str(join_info_dict['id'])
                                   + ' has account: ' + join_info_dict['account'])
        else:
            if join_info_dict['id'] is not self.client_id:
                self.console_write(COLOR['bright_cyan'], join_info_dict['nick'] + ':' + str(join_info_dict['id'])
                                   + ' joined the room.')

    def on_joins(self, joins_info_dict):
        user = self.add_user_info(joins_info_dict['nick'])
        user.nick = joins_info_dict['nick']
        user.id = joins_info_dict['id']
        user.user_account = joins_info_dict['account']
        user.user_account_type = joins_info_dict['stype']
        user.user_account_giftpoints = joins_info_dict['gp']
        user.is_mod = joins_info_dict['mod']
        user.is_owner = joins_info_dict['own']
        user.device_type = str(joins_info_dict['btype'])
        user.reading_only = joins_info_dict['lf']

        if joins_info_dict['account']:
            if joins_info_dict['own']:
                self.console_write(COLOR['red'], 'Joins Room Owner ' + joins_info_dict['nick'] + ':' +
                                   str(joins_info_dict['id']) + ':' + joins_info_dict['account'])
            elif joins_info_dict['mod']:
                self.console_write(COLOR['bright_red'], 'Joins Moderator ' + joins_info_dict['nick'] +
                                   ':' + str(joins_info_dict['id']) + ':' + joins_info_dict['account'])
            else:
                self.console_write(COLOR['bright_yellow'], 'Joins: ' + joins_info_dict['nick'] + ':' +
                                   str(joins_info_dict['id']) + ':' + joins_info_dict['account'])
        else:
            if joins_info_dict['id'] is not self.client_id:
                self.console_write(COLOR['bright_cyan'], 'Joins: ' + joins_info_dict['nick'] + ':' +
                                   str(joins_info_dict['id']))

    def on_joinsdone(self):
        self.console_write(COLOR['cyan'], 'All joins information received.')
        if self.is_client_mod:
            self.send_banlist_msg()

    def on_oper(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = True
        if uid != self.client_id:
            self.console_write(COLOR['bright_red'], nick + ':' + uid + ' is moderator.')

    def on_deop(self, uid, nick):
        user = self.add_user_info(nick)
        user.is_mod = False
        self.console_write(COLOR['red'], nick + ':' + uid + ' was deoped.')

    def on_owner(self):
        # self.is_client_mod = True
        # self.send_banlist_msg()
        pass

    def on_avon(self, uid, name):
        self.console_write(COLOR['cyan'], name + ':' + uid + ' is broadcasting.')

    def on_pro(self, uid):
        self.console_write(COLOR['cyan'], uid + ' is pro.')

    def on_nick(self, old, new, uid):
        # self.console_write(COLOR['cyan'], 'Received client nick: \'' +
        #                   str(self.client_nick) + '\' With ID: ' + str(uid))
        if uid is not self.client_id:
            old_info = self.find_user_info(old)
            old_info.nick = new
            if old in self.room_users.keys():
                del self.room_users[old]
                self.room_users[new] = old_info
            self.console_write(COLOR['bright_cyan'], old + ':' + str(uid) + ' changed nick to: ' + new)

    def on_nickinuse(self):
        self.client_nick += str(random.randint(0, 10))
        self.console_write(COLOR['white'], 'Nick already taken. Changing nick to: ' + self.client_nick)
        self.set_nick()

    def on_quit(self, uid, name):
        if name in self.room_users.keys():
            del self.room_users[name]
            self.console_write(COLOR['cyan'], name + ':' + uid + ' left the room.')

    def on_kick(self, uid, name):
        self.console_write(COLOR['bright_red'], name + ':' + uid + ' was banned.')
        self.send_banlist_msg()

    def on_banned(self):
        self.console_write(COLOR['red'], 'You are banned from this room.')

    def on_startbanlist(self):
        self.console_write(COLOR['cyan'], 'Checking banlist.')

    def on_banlist(self, uid, nick):
        if uid not in self.room_banlist.values():
            self.room_banlist[nick] = uid
            self.console_write(COLOR['bright_red'], 'Banned user: ' + nick + ':' + uid)

    def on_topic(self, topic):
        # TODO: Allow topic message to be a class variable so it can be recalled later.
        topic_msg = topic.encode('utf-8', 'replace')
        self.console_write(COLOR['cyan'], 'room topic: ' + topic_msg)

    def on_private_room(self):
        self.console_write(COLOR['cyan'], 'Private Room: ' + str(self.private_room))

    def on_from_owner(self, owner_msg):
        msg = str(owner_msg).replace('notice', '').replace('%20', ' ')
        self.console_write(COLOR['bright_red'], msg)

    def on_doublesignon(self):
        self.console_write(COLOR['bright_red'], 'This account is already in this room. Aborting!')
        self.is_connected = False
        if CONFIG['double_signon_reconnect']:
            self.reconnect()

    def on_reported(self, reporter):
        self.console_write(COLOR['bright_red'], 'You were reported by %s.' % reporter)

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

            elif msg_cmd[0] == '/mbs':
                media_type = msg_cmd[1]
                media_id = msg_cmd[2]
                time_point = int(msg_cmd[3])
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
                time_point = int(msg_cmd[2])
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
        self.console_write(COLOR['green'], msg_sender + ':' + msg)

    # Private message Handler.
    def private_message_handler(self, msg_sender, private_msg):
        """
        A user private message us.
        :param msg_sender: str the user sending the private message.
        :param private_msg: str the private message.
        """
        self.console_write(COLOR['white'], 'Private message from ' + msg_sender + ':' + private_msg)

    # Media Events.
    def on_media_broadcast_start(self, media_type, video_id, time_point, usr_nick):
        """
        A user started a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param video_id: str the youTube ID or soundCloud trackID.
        :param time_point: int the time in the video/track which we received to start playing.
        :param usr_nick: str the user name of the user playing media.
        """
        self.console_write(COLOR['bright_magenta'], usr_nick + ' is playing ' +
                                media_type + ' ' + video_id + ' (' + str(time_point) + ')' )

    def on_media_broadcast_close(self, media_type, usr_nick):
        """
        A user closed a media broadcast.
        :param media_type: str the type of media. youTube or soundCloud.
        :param usr_nick: str the user name of the user closing the media.
        """
        self.console_write(COLOR['bright_magenta'], usr_nick + ' closed the ' + media_type)

    def on_media_broadcast_paused(self, media_type, usr_nick):
        """
        A user paused the media broadcast.
        :param media_type: str the type of media being paused. youTube or soundCloud.
        :param usr_nick: str the user name of the user pausing the media.
        """
        self.console_write(COLOR['bright_magenta'], usr_nick + ' paused the ' + media_type)

    def on_media_broadcast_play(self, media_type, time_point, usr_nick):
        """
        A user resumed playing a media broadcast.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user resuming the tune.
        """
        self.console_write(COLOR['bright_magenta'], usr_nick + ' resumed the ' + media_type + ' at: ' + str(time_point))

    def on_media_broadcast_skip(self, media_type, time_point, usr_nick):
        """
        A user time searched a tune.
        :param media_type: str the media type. youTube or soundCloud.
        :param time_point: int the time point in the tune in milliseconds.
        :param usr_nick: str the user time searching the tune.
        """
        self.console_write(COLOR['bright_magenta'], usr_nick + ' time searched the ' + media_type + ' at: '
                           + str(time_point))

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

    # TODO: Refine this method in order remove the nested tries.
    def send_owner_run_msg(self, msg):
        """
        Send owner run message. The client has to be mod when sending this message.
        :param msg: the message str to send.
        """
        msg_encoded = ''
        for x in xrange(len(msg)):
            try:
                letter_number = ord(msg[x])
                if letter_number < 32 or letter_number > 126:
                    msg_encoded += quote_plus(msg[x])
                elif letter_number == 37:
                    msg_encoded += '%25'
                elif letter_number == 32:
                    msg_encoded += '%20'
                else:
                    msg_encoded += msg[x]
            except Exception:
                try:
                    msg_encoded += quote_plus(msg[x].encode('utf8'), safe='/')
                except Exception:
                    pass

        self._send_command('owner_run', [u'notice' + msg_encoded])

    # TODO: Move to bot file.
    def send_bot_msg(self, msg, is_mod=False):
        """
        Send a message in the color black.
        :param msg: str the message to send.
        :param is_mod: bool if True we send owner run message, else we send a normal message in the color black.
        """
        if is_mod:
            self.send_owner_run_msg(msg)
        else:
            self._send_command('privmsg', [u'' + self._encode_msg(msg), u'#262626,en'])

    # TODO: Move to bot file.
    def send_private_bot_msg(self, msg, nick):
        """
        Send a private message to a user in the color black.
        :param msg: str the message to send.
        :param nick: str the user to receive the message.
        """
        user = self.find_user_info(nick)
        if user is not None:
            self._send_command('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg), u'#262626,en',
                                           u'n' + str(user.id) + '-' + nick])
            self._send_command('privmsg', [u'' + self._encode_msg('/msg ' + nick + ' ' + msg), u'#262626,en',
                                           u'b' + str(user.id) + '-' + nick])

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
        self.console_write(COLOR['white'], 'Setting nick: ' + self.client_nick)
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

    def send_broadcast_accept_msg(self, nick):
        """
        Send a message to accept a pending broadcast in a greenroom.
        :param nick: str the nickname of the user.
        """
        user = self.find_user_info(nick)
        if user is not None and self.room_broadcast_pass is not None:
            self._send_command('privmsg', [u'' + self._encode_msg('/allowbroadcast ' + self.room_broadcast_pass),'#0,en',
                                           u'n' + str(user.id) + '-' + nick])

    def send_private_room_msg(self, state=None):
        """
        Send 'private room' message to the room. The client has to be mod when sending this message.
        We assume this prevents the room from being listed in the directory.
        OPTIONAL: param state: boolean default None and connection value is used, set as True/False depending on
                               whether private_room should be turned on or not.
        """
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
        NOTE: This method replaces stop_youtube and stop_soundcloud
        :param media_type: str 'youTube' or 'soundCloud'
        :param private_nick: str if not None, stop the media broadcast for this nickname only.
        """
        mbc_msg = '/mbc %s' % media_type
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbc_msg)
        else:
            self.send_chat_msg(mbc_msg)

    # TODO: implement this
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

    # TODO: implement this
    def send_media_broadcast_pause(self, media_type, private_nick=None):
        """
        Pause a currently playing media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'
        :param private_nick: str if not None, send this message to this username only.
        """
        mbpa_msg = '/mbpa %s' % media_type
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbpa_msg)
        else:
            self.send_chat_msg(mbpa_msg)

    # TODO: implement this
    def send_media_broadcast_skip(self, media_type, time_point, private_nick=None):
        """
        Time search a currently playing/paused media broadcast.
        :param media_type: str 'youTube' or 'soundCloud'
        :param time_point: int the time point to skip to.
        :param private_nick: str if not None, send this message to this username only.
        :return:
        """
        mbsk_msg = '/mbsk %s %s' % (media_type, time_point)
        if private_nick is not None:
            self.send_undercover_msg(private_nick, mbsk_msg)
        else:
            self.send_chat_msg(mbsk_msg)

    # TODO: Adapt this to work with the new base.
    # Message Construction.
    def _send_command(self, cmd, params=[]):
        """
         Sends command messages to the server.
         Calls remote procedure calls (RPC) at the receiving end.

        :param cmd: str command name.
        :param params: list command parameters.
        """
        # Retrieve message structure
        msg = message_structures.sendCommand(
            rtmp_protocol.DataTypes.COMMAND,
            cmd,
            params)

        try:
            self.connection.writer.write(msg)
            self.connection.writer.flush()

            if CONFIG['amf_sent']:
                print(msg)

        except Exception as ex:
            log.error('send command error: %s' % ex, exc_info=True)
            if CONFIG['debug_mode']:
                traceback.print_exc()
            self.reconnect()

    # Stream functions
    def _send_create_stream(self, play=False):
        """
        Send createStream message.
        :param play: Boolean True/False depending on whether the create stream is used for playing a stream.
        """
        if play:
            transaction_id = self.create_stream_id
        else:
            transaction_id = 0

        # Retrieve/generate message structure
        msg = message_structures.createStream(
            rtmp_protocol.DataTypes.COMMAND,
            transaction_id)

        self.console_write(COLOR['white'], 'Sending createStream message #' + str(transaction_id))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

        # Set to sort the stream information appropriately upon the arrival of _result
        self.stream_sort = True

    def _send_publish(self):
        """ Send publish message. """
        try:
            self.streams['client_publish']
        except KeyError:
            self.console_write(COLOR['white'], 'No StreamID available to start publish upon.')
            return

        # Publish type may vary from live, record or append. Though live is the only supported type at
        # the moment, the use of other types is not recommended and may cause further issues in the program.
        publish_type = 'live'

        # Retrieve/generate message structure
        msg = message_structures.publish(
            rtmp_protocol.DataTypes.COMMAND,
            self.streams['client_publish'],
            self.client_id,
            publish_type)

        self.console_write(COLOR['white'], 'Sending publish message on StreamID: ' + str(self.streams['client_publish']))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    # TODO: Make sure set chunk size is sent properly in rtmp_protocol.py
    def _send_set_chunk_size(self, new_chunk_size=None):
        """
        Send set chunk size message. Handles audio chunk size by default by sending 129.
        :param new_chunk_size: int the new chunk size.
        """
        try:
            self.streams['client_publish']
        except KeyError:
            self.console_write(COLOR['white'], 'No publish StreamID found to set chunk size upon.')
            return

        if new_chunk_size is not None:
            chunk_size = new_chunk_size
        else:
            self.console_write(COLOR['white'], 'No chunk size was provided.')
            return

        msg = message_structures.SET_CHUNK_SIZE(
            rtmp_protocol.DataTypes.SET_CHUNK_SIZE,
            self.streams['client_publish'],
            chunk_size)

        self.console_write(COLOR['white'], 'Sending chunk size message.')
        self.connection.writer.write(msg)
        self.connection.writer.flush()

        # Set writer to work with new chunk size
        self.connection.writer.chunk_size = chunk_size
        self.console_write(COLOR['white'], 'Set chunk size:' + str(self.connection.writer.chunk_size))

    def _send_play(self, stream_id, playID):
        """
        Send play message.
        :param stream_id:
        :param playID:
        """
        try:
            int(playID)
        except Exception:
            self.console_write(COLOR['white'], 'PlayID format incorrect, integers only allowed.')
            return

        msg = message_structures.play(
            rtmp_protocol.DataTypes.COMMAND,
            stream_id,
            playID)

        self.console_write(COLOR['white'], 'Starting playback for:' + str(playID) + ' on StreamID:' + str(stream_id))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _configure_av_packet(self, av_content):
        """
        Configures audio/video content for a packet given the frame content and the setttings
        and send the packet.
        :param av_content:
        """
        # Assign timestamp
        if self.force_time_stamp is not None:
            time_stamp = self.force_time_stamp
        else:
            time_stamp = av_content[3]

        # Assign control type
        control_type = av_content[2]

        # Setup audio packet
        if av_content[0] == rtmp_protocol.DataTypes.AUDIO:
            if not self.play_audio:
                # Send no audio data if it has been disabled.
                raw_data = b""
            else:
                raw_data = av_content[1]
            self._send_audio_packet(raw_data, control_type, time_stamp)

        # Setup video packet
        elif av_content[0] == rtmp_protocol.DataTypes.VIDEO:
            if not self.play_video:
                # Send no video data if it has been disabled.
                raw_data = b""
            else:
                raw_data = av_content[1]
            self._send_video_packet(raw_data, control_type, time_stamp)
        else:
            print("The frame is an invalid audio/video input.")

    def _send_audio_packet(self, packet_raw_data, packet_control_type, packet_timestamp=0):
        """
        Send Audio message.
        :param packet_raw_data: bytes the audio data (in the MP3 format) to be sent.
        :param packet_control_type: hexadecimal value of the control type (originally 0x66,
                                    though due to a lack of adequate audio encoding it is sent via
                                    inter-frame (0x22).
        :param packet_timestamp: int the timestamp for the packet (OPTIONAL)
        """
        msg = message_structures.audio(
            rtmp_protocol.DataTypes.AUDIO,
            self.streams['client_publish'],
            packet_raw_data,
            packet_control_type,
            packet_timestamp)

        # self.console_write(COLOR['white'], 'Sending audio message.')
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _send_video_packet(self, packet_raw_data, packet_control_type, packet_timestamp=0):
        """
        Send Video message.
        :param packet_raw_data: bytes the video data (in the FLV1 format) to be sent.
        :param packet_control_type: hexadecimal value of the control type, between 0x12 (key-frame), 0x22 (inter-frame),
                                    0x32 (disposable-frame) and 0x42 (generated-frame).
                                    NOTE: This can produce unexpected results.
        :param packet_timestamp: int the timestamp for the packet (OPTIONAL)
        """
        msg = message_structures.video(
            rtmp_protocol.DataTypes.VIDEO,
            self.streams['client_publish'],
            packet_raw_data,
            packet_control_type,
            packet_timestamp)

        # self.console_write(COLOR['white'], 'Sending video message.')
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _send_close_stream(self, stream_id=None):
        """
        Send closeStream message.
        :param stream_id:
        """
        try:
            self.streams['client_closestream']
        except KeyError:
            self.console_write(COLOR['white'], 'No closeStream StreamID found to send the closeStream request upon.')
            return

        if stream_id is None:
            stream_id = self.streams['client_closestream']

        msg = message_structures.closeStream(
            rtmp_protocol.DataTypes.COMMAND,
            stream_id)

        self.console_write(COLOR['white'], 'Sending closeStream message on StreamID:' + str(stream_id))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    def _send_delete_stream(self, stream_id=None):
        """
        Send deleteStream message.
        :param stream_id:
        """
        try:
            self.streams['client_deletestream']
        except KeyError:
            self.console_write(COLOR['white'], 'No deleteStream StreamID found to send the deleteStream request upon.')
            return

        if stream_id is None:
            stream_id = self.streams['client_deletestream']

        msg = message_structures.deleteStream(
            rtmp_protocol.DataTypes.COMMAND,
            stream_id)

        self.console_write(COLOR['white'], 'Sending deleteStream message on StreamID:' + str(stream_id))
        self.connection.writer.write(msg)
        self.connection.writer.flush()

    # Helper Methods
    def _send_ping_request(self, manual=False):
        """
        Send a ping request (experimental).
        NOTE: The client sends an unorthodox message i.e. *ping response* instead of a *ping response* due to
              the nature of how the servers were setup. Tinychat servers do not automatically request a ping,
              so we request one instead. We assume the data-types are reversed since an event_type of '7', which
              is usually only a client response, will also be shown by the server as it responds to your initial
              ping request.
        :param manual: Boolean True/False if you want to instantly request a 'reverse' ping request.
        """
        # TODO: Try to send a timestamp instead or try to parse the response in a different manner.

        msg = message_structures.PING(
            rtmp_protocol.DataTypes.USER_CONTROL,
            rtmp_protocol.UserControlTypes.PING_REQUEST)

        if not manual:
            while not self.is_connected:
                time.sleep(1)
            while self.is_connected and not self.publish_connection:
                self.connection.writer.write(msg)
                self.connection.writer.flush()
                time.sleep(120)
        elif manual:
            self.connection.writer.write(msg)
            # self.connection.handle_simple_message(msg)
            self.connection.writer.flush()

            # Save next ping content by allowing the response to be caught
            # self.ping_request = True

    # TODO: Turn decode and encode message procedures into static methods.
    # TODO: Monitor method to check for irregularities.
    @staticmethod
    def _encode_msg(msg):
        """
        Encode normal text str to comma separated decimal.
        :param msg: str the normal text to encode
        :return: comma separated decimal str.
        """
        return ','.join(str(ord(char)) for char in msg)

    # TODO: Monitor method to check for irregularities.
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

    # TODO: Set self.video and self.audio to more appropriate names e.g. video_on/audio_on
    def _set_upstream(self):
        """ Appropriately sets the necessary options into effect to start 'upstreaming'. """

        # Publish camera sequence:
        # Send broadcast authorisation message to the server
        self.send_bauth_msg()
        # Create a new stream onto which to send A/V packets
        self._send_create_stream()
        # Sort out the stream request reply from the server
        while self.stream_sort:
            time.sleep(1)
        # Send publish message to the server
        self._send_publish()
        # Acknowledge locally that we are publishing a stream
        self.publish_connection = True

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

    def alive(self):
        """
        A timed alive check on the bot.
        Reconnects if the bot is not in the XML file after 5 checks.
        """
        while not self.is_connected:
            time.sleep(1)

        times = 0
        while self.is_connected:
            time.sleep(200)

            room = tinychat_api.spy_info(self.roomname)
            if room is None or room == 'PW':
                times = 0
                continue

            if room['status_code'] != 200:
                times = 0
                continue

            if u'' + self.client_nick not in room['users']:
                if times == 3:
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
            # Exit to system safely whilst returning exit code 0
            sys.exit(0)
        else:
            client.send_bot_msg(chat_msg)

if __name__ == '__main__':
    # TODO: Initial logging.
    if CONFIG['debug_to_file']:
         formater = '%(asctime)s : %(levelname)s : %(filename)s : %(lineno)d : %(funcName)s() : %(name)s : %(message)s'
         # should there be a check to make sure the debug file name has been set?
         logging.basicConfig(filename=CONFIG['debug_file_name'], level=logging.DEBUG, format=formater)
         log.info('Starting pinylib version: %s' % __version__)
    main()
