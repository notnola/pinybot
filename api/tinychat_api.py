
""" A collection of functions to fetch info from tinychat's API. """
import time
import random
import webbrowser
from xml.dom.minidom import parseString
import web_request
import os


def get_roomconfig_xml(room, roompass=None, proxy=None):
    """
    Finds room configuration for a given room name.
    :param room: str the room name to find info for.
    :param roompass: str the password to the room. Defaults to None.
    :param proxy: str use a proxy for this request.
    :return: dict {'tcurl', 'ip', 'port', 'app', 'roomtype', 'greenroom=bool', 'roombroadcastpass'}
    """
    if roompass:
        # TODO: api ---> apl
        xmlurl = 'http://api.tinychat.com/api/find.room/%s?site=tinychat&password=%s&url=tinychat.com' % \
                 (room, roompass)
    else:
        # TODO: api ---> apl
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

            return {'tcurl': tc_url, 'ip': ip, 'port': port, 'app': app, 'roomtype': roomtype, \
                                'greenroom': greenroom, 'roombroadcastpass': room_broadcast_pass}


def tinychat_user_info(tc_account):
    """
    Finds info for a given tinychat account name.
    :param tc_account: str the account name.
    :return: dict {'username', 'tinychat_id', 'last_active', 'name', 'location'}
    """
    url = 'http://tinychat.com/api/tcinfo?username=%s' % tc_account
    json_data = web_request.get_request(url=url, json=True)
    if json_data is not None:
        try:
            username = json_data['content']['username']
            user_id = json_data['content']['id']
            last_active = time.ctime(int(json_data['content']['last_active']))
            name = json_data['content']['name']
            location = json_data['content']['location']

            return {'username': username, 'tinychat_id': user_id, 'last_active': last_active,
                    'name': name, 'location': location}
        except KeyError:
            return None


def spy_info(room):
    """
    Finds info for a given room name.

    The info shows many mods, broadcasters, total users and a users(list) with all the user names.

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
    #  A token IS present even if password is enabled, will it work? needs more testing..
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


# TODO: Remove use of tries.
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
    # print 'in captcha key'
    if json_data is not None:
        try:
            if 'key' in json_data['content']:
                return json_data['content']['key']
            else:
                return None
        except Exception:
            # Handle abnormal response regarding the captcha key data to work by forcing a
            # text parse for the captcha key
            raw = json_data['content']
            # print 'abnormal data received'
            # Credits to pinychat (NotNola)
            return raw.split('"key":"')[1].split('"')[0]


# TODO: Remove use of excessive tries.
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
    # print 'in cauth'
    if json_data is not None:
        try:
            # Normal cauth cookie parsing
            if 'cookie' in json_data['content']:
                # print 'normal cookie data received'
                return json_data['content']['cookie']
            else:
                return None
        except Exception:
            # Handle abnormal response regarding the cauth cookie data to work by forcing a
            # text parse for the cauth cookie
            raw = json_data['content']
            # print 'abnormal cookie data received'
            # Credits to pinychat (NotNola)
            return raw.split('{"cookie":"')[1].split('"')[0]


# TODO: Remove use of excessive tries.
def recaptcha(proxy=None):
    """
    Check if we have to solve a captcha before we can connect.
    If yes, then it will open in the default browser.
    :param proxy: str use a proxy for this request.
    :return: dict{'cookies'} this is NOT used in the code , but are left here for debugging purpose.
    """
    t = str(random.uniform(0.9, 0.10))
    url = 'http://tinychat.com/cauth/captcha?%s' % t
    response = web_request.get_request(url, json=True, proxy=proxy)
    # print 'in recaptcha'
    if response is not None:
        # print response['content']
        try:
            # print 'normal recaptcha token retrieval'
            # Handle abnormal response regarding the recaptcha data to work by forcing a
            # text parse for the recaptcha information
            if response['content']['need_to_solve_captcha'] == 1:
                # print 'normal recaptcha token used'
                link = 'http://tinychat.com/cauth/recaptcha?token=%s' % response['content']['token']
                print(link)
                if os.name == 'nt':
                    webbrowser.open(link, new=1)
                raw_input('Solve the captcha and hit enter to continue (OR hit enter to join anonymously).')
            else:
                # print 'normal recaptcha retrieval not used'
                pass
        except Exception:
            # print 'text recaptcha token retrieval'
            if '"need_to_solve_captcha":1' in response['content']:
                # print 'text recaptcha token used'
                # credits to pinychat (NotNola)
                token = response['content'].split('"token":"')[1].split('"')[0]
                link = 'http://tinychat.com/cauth/recaptcha?token=%s' % token
                print(link)
                if os.name == 'nt':
                    webbrowser.open(link, new=1)
                raw_input('Solve the captcha and hit enter to continue (OR hit enter to join anonymously).')
            else:
                # print 'text recaptcha retrieval not used'
                pass
        # Return the cookies
        # return response['cookies']
