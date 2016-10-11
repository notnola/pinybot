""" Contains functions to fetch info from api.soundcloud.com """
from utilities import web

# SoundCloud API key.
# b85334a9b08edb6778a50d965444fd39
SOUNDCLOUD_API_KEY = '4ce43a6430270a1eea977ff8357a25a3'


def soundcloud_search(search):
    """
    Searches SoundCloud's API for a given search term.

    :param search: str the search term to search for.
    :return: dict{'type=soundCloud', 'video_id', 'video_time', 'video_title'} or None on no match or error.
    """
    if search:
        search_url = 'http://api.soundcloud.com/tracks/?' \
                     'filter=streamable&q=%s&limit=25&client_id=%s' % (search, SOUNDCLOUD_API_KEY)

        response = web.http_get(search_url, json=True)
        if response['json'] is not None:
            try:
                track_id = response['json'][0]['id']
                track_time = response['json'][0]['duration']
                track_title = response['json'][0]['title'].encode('ascii', 'ignore')
                return {
                    'type': 'soundCloud',
                    'video_id': track_id,
                    'video_time': track_time,
                    'video_title': track_title
                }
            except (IndexError, KeyError):
                return None
        return None


def soundcloud_track_info(track_id):
    """
    Retrieve SoundCloud track information given a valid track id.

    :param track_id: str the track id of information of the track you want.
    :return: dict{'type=soundCloud', 'video_id', 'video_time', 'video_title', 'user_id'} or None on no match or error.
    """
    if track_id:
        info_url = 'http://api.soundcloud.com/tracks/%s?client_id=%s' % (track_id, SOUNDCLOUD_API_KEY)
        response = web.http_get(info_url, json=True)

        if response['json'] is not None:
            try:
                # TODO: Removed index from the JSON parsing, it is not required anymore.
                user_id = response['json']['user_id']
                track_time = response['json']['duration']
                track_title = response['json']['title'].encode('ascii', 'ignore')
                permalink_url = response['json']['permalink_url']
                # TODO: Added in the SoundCloud permalink_url field from the JSON response.
                return {
                    'type': 'soundCloud',
                    'video_id': track_id,
                    'video_time': track_time,
                    'video_title': track_title,
                    'user_id': user_id,
                    'permalink_url': permalink_url
                }
            except KeyError:
                return None
        return None


# TODO: Remove this after debugging.
# print(soundcloud_track_info('9128931'))
# print(soundcloud_search('https://soundcloud.com/ok/ok'))