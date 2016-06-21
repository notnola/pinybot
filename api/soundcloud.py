# -*- coding: utf-8 -*-

import web_request

# SoundCloud API key.
SOUNDCLOUD_API_KEY = 'b85334a9b08edb6778a50d965444fd39'


def soundcloud_search(search):
    """
    Searches SoundCloud's API for a given search term.

    :param search: str the search term to search for.
    :return: dict{'type=soundCloud', 'video_id', 'video_time', 'video_title'} or None on no match or error.
    """

    if search:
        search_url = 'http://api.soundcloud.com/tracks/?' \
                     'filter=streamable&q=%s&limit=25&client_id=%s' % (search, SOUNDCLOUD_API_KEY)

        response = web_request.get_request(search_url, json=True)
        if response is not None:
            try:
                track_id = response['content'][0]['id']
                track_time = response['content'][0]['duration']
                track_title = response['content'][0]['title'].encode('ascii', 'ignore')
                return {'type': 'soundCloud', 'video_id': track_id, 'video_time': track_time, 'video_title': track_title}
            except (IndexError, KeyError):
                return None
        return None


def soundcloud_track_info(track_id):
    """
    Retrieve SoundCloud track information given a valid track id.

    :param track_id: str the track id of the information of the track you want.
    :return: {'type=soundCloud', 'video_id', 'video_time', 'video_title', 'user_id'} or None on no match or error.
    """
    if track_id:
        info_url = 'http://api.soundcloud.com/tracks/%s?client_id=%s' % (track_id, SOUNDCLOUD_API_KEY)
        response = web_request.get_request(info_url, json=True)

        if response is not None:
            try:
                user_id = response['content'][0]['user_id']
                track_time = response['content'][0]['duration']
                track_title = response['content'][0]['title'].encode('ascii', 'ignore')
                return {'type': 'soundCloud', 'video_id': track_id, 'video_time': track_time,
                        'video_title': track_title, 'user_id': user_id}
            except (IndexError, KeyError):
                return None
        return None
