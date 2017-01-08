""" Contains functions to fetch info from tinychat's API. """
import random
import time
import os
import webbrowser
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

from utilities import web

# TODO: New tinychat.py (a rewrite to tinychat_api.py) by nortxort.
# TODO: Removed exceptions to handling un-formatted pages (this is not the orthodox way of doing things).


def delete_login_cookies():
    """ Delete tinychat login cookies. """
    cookies = ['pass', 'hash', 'user']
    for cookie in cookies:
        web.delete_cookie(cookie)


def post_login(account, password):
    """
    Post tinychat login info.
    :param account: str tinychat account name.
    :param password: str tinychat account password.
    :return: dict{'content', 'cookies', 'headers', 'status_code'} or None on error.
    """
    url = 'https://tinychat.com/login'
    header = {'Referer': url}
    form_data = {
        'form_sent': '1',
        'referer': '',
        'next': '',
        'username': account,
        'password': password,
        'passwordfake': 'Password',
        'remember': '1'
    }
    response = web.http_post(url, form_data, header=header)
    return response


def get_roomconfig_xml(room, roompass=None, proxy=None):
    """
    Finds room configuration for a given room name.
    :param room: str the room name to find info for.
    :param roompass: str the password to the room. Defaults to None.
    :param proxy: str use a proxy for this request.
    :return: dict {'tcurl', 'ip', 'port', 'app', 'roomtype', 'greenroom=bool', 'bpassword'}
    """
    if roompass:
        xmlurl = 'https://apl.tinychat.com/api/find.room/%s?site=tinychat&password=%s&url=tinychat.com' % \
                 (room, roompass)
    else:
        xmlurl = 'https://apl.tinychat.com/api/find.room/%s?site=tinychat&url=tinychat.com' % room

    response = web.http_get(xmlurl, proxy=proxy)
    if response['content'] is not None:
        try:
            xml = parseString(response['content'])
        except ExpatError:
            xml = None
        if xml is not None:
            broadcast_pass = None
            root = xml.getElementsByTagName('response')[0]
            result = root.getAttribute('result')
            if result == 'PW':
                return result
            # TODO: Handle in the event the room is closed i.e. result='CLOSED'
            elif result == 'CLOSED':
                return result
            else:
                roomtype = root.getAttribute('roomtype')
                tc_url = root.getAttribute('rtmp')
                rtmp_parts = tc_url.split('/')
                app = rtmp_parts[3]
                ip_port_parts = rtmp_parts[2].split(':')
                ip = ip_port_parts[0]
                port = int(ip_port_parts[1])

                if 'bpassword' in response['content']:
                    broadcast_pass = root.getAttribute('bpassword')
                if root.getAttribute('greenroom'):
                    greenroom = True
                else:
                    greenroom = False

                return {
                    'tcurl': tc_url,
                    'ip': ip,
                    'port': port,
                    'app': app,
                    'roomtype': roomtype,
                    'greenroom': greenroom,
                    'bpassword': broadcast_pass
                }
        return None


def tinychat_user_info(tc_account):
    """
    Finds info for a given tinychat account name.
    :param tc_account: str the account name.
    :return: dict {'username', 'tinychat_id', 'last_active', 'name', 'location', 'biography'} or None on error.
    """
    url = 'http://tinychat.com/api/tcinfo?username=%s' % tc_account
    response = web.http_get(url=url, json=True)
    if response['json'] is not None:
        try:
            username = response['json']['username']
            user_id = response['json']['id']
            last_active = time.ctime(int(response['json']['last_active']))
            name = response['json']['name']
            location = response['json']['location']
            biography = response['json']['biography']

            return {
                'username': username,
                'tinychat_id': user_id,
                'last_active': last_active,
                'name': name,
                'location': location,
                'biography': biography
            }
        except KeyError:
            return None


def spy_info(room):
    """
    Finds info for a given room name.

    The info shows many mods, broadcasters, total users and a users(list) with all the nick names.

    :param room: str the room name to get spy info for.
    :return: dict{'mod_count', 'broadcaster_count', 'total_count', list('users')} or PW on password protected room.,
    or None on failure or empty room.
    """
    url = 'https://api.tinychat.com/%s.json' % room
    check = get_roomconfig_xml(room)
    if check == 'PW':
        return check
    else:
        try:
            response = web.http_get(url, json=True)
            mod_count = str(response['json']['mod_count'])
            broadcaster_count = str(response['json']['broadcaster_count'])
            total_count = str(response['json']['total_count'])
            if total_count > 0:
                users = response['json']['names']
                return {
                    'mod_count': mod_count,
                    'broadcaster_count': broadcaster_count,
                    'total_count': total_count,
                    'users': users
                }
        except KeyError:
            return None


def get_bauth_token(roomname, nick, uid, greenroom, proxy=None):
    """
    Find the bauth token needed before we can start a broadcast.
    NOTE: Might need some more work related to green room.
    :param roomname: str the room name.
    :param nick: str the nick we use in the room.
    :param uid: str our ID in the room.
    :param greenroom: bool should be True if greenroom is enabled.
    :param proxy: str use a proxy for this request.
    :return: str token or PW if a password is needed to broadcast.
    """
    if greenroom:
        xmlurl = 'https://tinychat.com/api/broadcast.pw?site=greenroom&name=%s&nick=%s&id=%s' % (roomname, nick, uid)
    else:
        xmlurl = 'https://tinychat.com/api/broadcast.pw?site=tinychat&name=%s&nick=%s&id=%s' % (roomname, nick, uid)

    response = web.http_get(xmlurl, proxy=proxy)
    if response['content'] is not None:
        xml = parseString(response['content'])
        root = xml.getElementsByTagName('response')[0]
        result = root.getAttribute('result')
        if result == 'PW':
            return result
        else:
            token = root.getAttribute('token')
            return token


def get_captcha_key(roomname, uid, proxy=None):
    """
    Find the captcha key needed before we can send messages in a room.
    :param roomname: str the room name.
    :param uid: str the ID we have in the room.
    :param proxy: str use a proxy for this request.
    :return: str the captcha key or None on captcha enabled room.
    """
    url = 'https://tinychat.com/api/captcha/check.php?room=tinychat^%s&guest_id=%s' % (roomname, uid)
    response = web.http_get(url, json=True, proxy=proxy)
    if response['json'] is not None:
        if 'key' in response['json']:
            return response['json']['key']
        else:
            return None


def get_cauth_cookie(roomname, proxy=None):
    """
    Find the cauth 'cookie' needed to make a successful connection.

    NOTE: This is not really a cookie, but named so after its name in the json response.
    :param roomname: str the room name.
    :param proxy: str use a proxy for this request.
    :return: str the 'cookie'
    """
    ts = int(round(time.time() * 1000))
    url = 'https://tinychat.com/cauth?room=%s&t=%s' % (roomname, ts)
    response = web.http_get(url, json=True, proxy=proxy)
    if response['json'] is not None:
        if 'cookie' in response['json']:
                return response['json']['cookie']
        else:
            return None


def recaptcha(proxy=None):
    """
    Check if we have to solve a captcha before we can connect.
    If yes, then it will open in the default browser.
    :param proxy: str use a proxy for this request.
    :return: dict{'cookies'} this is NOT used in the code , but is left here for debugging purposes.
    """
    t = str(random.uniform(0.9, 0.10))
    url = 'https://tinychat.com/cauth/captcha?%s' % t
    response = web.http_get(url, json=True, proxy=proxy)
    if response['json'] is not None:
        recaptcha_required = False

        link = ''
        if response['json']['need_to_solve_captcha'] == 1:
            link = 'https://tinychat.com/cauth/recaptcha?token=%s' % response['json']['token']
            recaptcha_required = True
        elif response['json']['need_to_solve_captcha'] == 0:
            return recaptcha_required

        if recaptcha_required:
            print(link)
            if os.name == 'nt':
                webbrowser.open(link, new=1, autoraise=True)
            raw_input('Solve the captcha and click enter to continue (OR hit enter to join anonymously).'
                      '\nNOTE: You will not be able to interact with the room whilst in anonymous mode.\n')
        else:
            print('No ReCaptcha is required.')

        return response['cookies']


def generate_snapshot(process_file=None, client_name=None, client_room=None):
    """
    Generate a snapshot given an image file, this will send the image of to Tinychat servers.
    :param client_name: str the name of the room in which the client is residing.
    :param client_room: str the name of the client.
    :param process_file: str the full path and name (with extension) to the file on the server.
    :return: str the raw image link that was generated with the snapshot on the server and the embed link for the image.
    """

    snapshot_header = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-GB,en-US;q=0.8,en;q=0.6',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/51.0.2704.103 Safari/537.36',
        'X-Requested-With': 'ShockwaveFlash/22.0.0.19',
        'DNT': '1',
        'Content-Type': 'multipart /form-data',
        'Origin': 'https://tinychat.com',
        'Connection': 'keep-alive',
        'Host': 'upload.tinychat.com'
    }

    date_formatted = time.strftime('%m-%d-%Y')
    post_url = 'https://upload.tinychat.com/savess?file=%s%s%s.jpg' % \
               (client_name + '%2B', client_room + '%2B', date_formatted)
    print('Sending to: %s Filename: %s' % (post_url, process_file))

    if process_file:
        form_data_file = open(process_file, 'rb')
        form_data = form_data_file.read()

        # print int(os.path.getsize(process_file)), 'bytes'

        pr = web.http_post(post_url, post_data=form_data, header=snapshot_header)
        raw_link = pr['content'].strip()
        embed_link = raw_link.replace('upload.', '')
        embed_link = embed_link.replace('.jpg', '')
        return raw_link, embed_link
    else:
        print('Please provide an image file.')
        return None


