""" A collection of functions to fetch info from tinychat's API. """

import time
import random
import webbrowser
import web_request
import os
import datetime

from xml.dom.minidom import parseString


def get_roomconfig_xml(room, roompass=None, proxy=None):
    """
    Finds room configuration for a given room name.
    :param room: str the room name to find info for.
    :param roompass: str the password to the room. Defaults to None.
    :param proxy: str use a proxy for this request.
    :return: dict {'tcurl', 'ip', 'port', 'app', 'roomtype', 'greenroom=bool', 'room_broadcast_pass'}
    """
    if roompass:
        xmlurl = 'http://api.tinychat.com/api/find.room/%s?site=tinychat&password=%s&url=tinychat.com' % \
                 (room, roompass)
    else:
        xmlurl = 'http://api.tinychat.com/api/find.room/%s?site=tinychat&url=tinychat.com' % room

    web_content = web_request.get_request(xmlurl, proxy=proxy)
    if web_content is not None:
        xml = parseString(web_content['content'])

        root = xml.getElementsByTagName('response')[0]
        result = root.getAttribute('result')
        if result == 'PW':
            return result
        else:
            roomtype = root.getAttribute('roomtype')
            tc_url = root.getAttribute('rtmp')
            rtmp_parts = tc_url.split('/')
            app = rtmp_parts[3]
            ip_port_parts = rtmp_parts[2].split(':')
            ip = ip_port_parts[0]
            port = int(ip_port_parts[1])
            room_broadcast_pass = None

            if root.getAttribute('greenroom'):
                greenroom = True
                try:
                    room_broadcast_pass = root.getAttribute('bpassword')
                except Exception:
                    pass
            else:
                greenroom = False

            return {'tcurl': tc_url, 'ip': ip, 'port': port, 'app': app, 'roomtype': roomtype, 'greenroom': greenroom,
                    'room_broadcast_pass': room_broadcast_pass}


def tinychat_user_info(tc_account):
    """
    Finds info for a given tinychat account name.
    :param tc_account: str the account name.
    :return: dict {'username', 'tinychat_id', 'last_active', 'name', 'location'}.
    """
    url = 'http://tinychat.com/api/tcinfo?username=%s' % tc_account
    json_data = web_request.get_request(url=url, json=True)
    if json_data is not None:
        try:
            user_id = json_data['content']['id']
            username = json_data['content']['username']
            name = json_data['content']['name']
            location = json_data['content']['location']
            last_active = time.ctime(int(json_data['content']['last_active']))

            return {'username': username, 'tinychat_id': user_id, 'last_active': last_active,
                    'name': name, 'location': location}
        except KeyError:
            return None


def spy_info(room):
    """
    Finds info for a given room name.
    The info shows many mods, broadcasters, total users and a users(list) with all the nicknames.

    :param room: str the room name to get spy info for.
    :return: dict{'mod_count', 'broadcaster_count', 'total_count', list('users')} or PW on password protected room.,
    or None on failure or empty room.
    """
    url = 'http://api.tinychat.com/%s.json' % room
    check = get_roomconfig_xml(room)
    if check == 'PW':
        return check
    else:
        try:
            json_data = web_request.get_request(url, json=True)
            mod_count = str(json_data['content']['mod_count'])
            broadcaster_count = str(json_data['content']['broadcaster_count'])
            total_count = json_data['content']['total_count']
            status_code = json_data['status_code']
            if total_count > 0:
                users = json_data['content']['names']
                return {'mod_count': mod_count, 'broadcaster_count': broadcaster_count,
                        'total_count': str(total_count), 'users': users, 'status_code': status_code}
        except (TypeError, IndexError, KeyError):
            return None


def get_bauth_token(roomname, nick, uid, greenroom, proxy=None):
    #  A token IS present even if password is enabled, will it work? needs more testing ...
    """
    Find the bauth token needed before we can start a broadcast.
    :param roomname: str the room name.
    :param nick: str the nick we use in the room.
    :param uid: str our ID in the room.
    :param greenroom: bool should be True if greenroom is enabled.
    :param proxy: str use a proxy for this request.
    :return: str token or PW if a password is needed to broadcast.
    """
    if greenroom:
        xmlurl = 'http://tinychat.com/api/broadcast.pw?site=greenroom&name=%s&nick=%s&id=%s' % (roomname, nick, uid)
    else:
        xmlurl = 'http://tinychat.com/api/broadcast.pw?site=tinychat&name=%s&nick=%s&id=%s' % (roomname, nick, uid)

    web_content = web_request.get_request(xmlurl, proxy=proxy)
    if web_content is not None:
        xml = parseString(web_content['content'])
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
    url = 'http://tinychat.com/api/captcha/check.php?room=tinychat^%s&guest_id=%s' % (roomname, uid)
    json_data = web_request.get_request(url, json=True, proxy=proxy)
    if json_data is not None:
        if 'key' in json_data['content']:
            try:
                return json_data['content']['key']
            except (Exception, KeyError):
                # Handle abnormal response regarding the captcha key data to work by forcing a
                # text parse for the captcha key; originally sourced from Pinychat (notnola).
                # We might not receive the content in JSON format, so we try text.
                return json_data['content'].split('"key":"')[1].split('"')[0]
        else:
            return None


def get_cauth_cookie(roomname, proxy=None):
    """
    Find the cauth 'cookie' needed to make a successful connection.

    This is not really a cookie, but named so after its name in the json response.
    :param roomname: str the room name.
    :param proxy: str use a proxy for this request.
    :return: str the 'cookie'
    """
    ts = int(round(time.time() * 1000))
    url = 'http://tinychat.com/cauth?room=%s&t=%s' % (roomname, str(ts))
    json_data = web_request.get_request(url, json=True, proxy=proxy)
    if json_data is not None:
        if 'cookie' in json_data['content']:
            try:
                return json_data['content']['cookie']
            except (Exception, KeyError):
                # Handle abnormal response regarding the cauth cookie data to work by forcing a
                # text parse for the cauth cookie. We might not receive the content in JSON format, so we try text.
                return json_data['content'].split('{"cookie":"')[1].split('"')[0]
        else:
            return None


def recaptcha(proxy=None):
    """
    Check if we have to solve a captcha before we can connect.
    If yes, then it will open in the default browser.
    :param proxy: str use a proxy for this request.
    :return: dict{'cookies'} this is NOT used in the code , but are left here for debugging purposes.
    """
    t = str(random.uniform(0.9, 0.10))
    url = 'http://tinychat.com/cauth/captcha?%s' % t
    response = web_request.get_request(url, json=True, proxy=proxy)
    if response is not None:
        if 'need_to_solve_captcha' in response['content']:
            successful_recaptcha = False
            link = ''
            try:
                if response['content']['need_to_solve_captcha'] == 1:
                    link = 'http://tinychat.com/cauth/recaptcha?token=%s' % response['content']['token']
                    successful_recaptcha = True
            except (Exception, KeyError):
                if '"need_to_solve_captcha":1' in response['content']:
                    token = response['content'].split('"token":"')[1].split('"')[0]
                    link = 'http://tinychat.com/cauth/recaptcha?token=%s' % token

            if successful_recaptcha:
                print(link)
                if os.name == 'nt':
                    webbrowser.open(link, new=1, autoraise=True)
                raw_input('Solve the captcha and hit enter to continue (OR hit enter to join anonymously).')

        return response['cookies']


def generate_snapshot(client_name=None, client_room=None, process_file=None):
    """

    :param client_name:
    :param client_room:
    :return: str the link that was generated with the snapshot on the server.
    """

    snapshot_header = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'en-GB,en-US;q=0.8,en;q=0.6',
        'DNT': '1',
        'Content - Type': 'multipart / form - data',
        'User - Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0' + \
                        '.2704.103 Safari/537.36',
        'X-Requested-With': 'ShockwaveFlash/22.0.0.19',
        'Origin': 'https://tinychat.com',
        'Connection': 'keep-alive',
        'Host': 'upload.tinychat.com'
    }

    today_date = datetime.date.today()
    date_formatted = today_date.strftime('%m-%d-%Y')
    post_url = 'http://upload.tinychat.com/savess?file=%s%s%s.jpg' % (client_name + '%2B', client_room + '%2B',
                                                                      date_formatted)

    if process_file:
        form_data_file = open(process_file)
        form_data = form_data_file.read()
        print [form_data]
        print int(os.path.getsize(process_file)), 'bytes'
        post_session = web_request.new_session(ret_session=True)
        pr = post_session.request(method='POST', url=post_url, data=form_data, headers=snapshot_header, stream=True,
                                  allow_redirects=False)
        print(pr.content)


