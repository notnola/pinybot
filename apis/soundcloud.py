""" Contains functions to fetch info from api.soundcloud.com """
import util.web

API_KEY = '4ce43a6430270a1eea977ff8357a25a3'

SEARCH_URL = 'http://api.soundcloud.com/tracks/?filter=streamable&q={1}&limit=25&client_id={0}'

TRACK_DETAILS_URL = 'http://api.soundcloud.com/tracks/{1}?client_id={0}'

# kind: top (top 50), trending (new & hot)
# genre: soundcloud&3Agenres%3Agenres%3A[type]:
# types: all-music, all-audio, alternativerock, ambient, classical, country, danceedm, dancehall, deephouse, disco,
#       drumbass, dubstep, electronic, folksignersongwriter, hiphoprap, house, indie, jazzblues, latin, metal,
#       piano, pop, rbsoul, reggae, reggaeton, rock, soundtrack, techno, trance, trap, triphop, world, audiobooks,
#       business, comedy, entertainment, learning, newspolitics, religionspirtuality, science, sports, storytelling,
#       technology
# limit: 10, 20 (how many songs to receive)
# http://stackoverflow.com/questions/35688367/access-soundcloud-charts-with-api
CHART_DETAILS_URL = 'https://api-v2.soundcloud.com/charts?kind={1}&genre=soundcloud%3Agenres%3A{2}&client_id={0}' \
                    '&limit={3}'

CHART_DETAILS_PARAMETERS = {
    'kinds': ['top', 'trending'],
    'genres': [
        'all-music', 'all-audio', 'alternativerock', 'ambient', 'classical', 'country', 'danceedm', 'dancehall',
        'deephouse', 'disco', 'drumbass', 'dubstep', 'electronic', 'folksingersongwriter', 'hiphoprap', 'house',
        'indie', 'jazzblues', 'latin', 'metal', 'piano', 'pop', 'rbsoul', 'reggae', 'reggaeton', 'rock', 'soundtrack',
        'techno', 'trance', 'triphop', 'world', 'audiobooks', 'business', 'comedy', 'entertainment', 'learning',
        'newspolitics', 'religionspirtuality', 'science', 'sports', 'storytelling', 'technology'
    ]
}


def search(search_term):
    """ Searches SoundCloud's API for a track matching the search term.

    :param search_term: The search term to search for.
    :type search_term: str
    :return: 'type=soundCloud', 'video_id', 'video_time', 'video_title' or None on no match or error.
    :rtpe: dict
    """
    if search_term:
        url = SEARCH_URL.format(API_KEY, util.web.quote(search_term))
        response = util.web.http_get(url=url, json=True)

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


def chart_search(kind=None, genre=None, limit=20):
    """
    Allows us to search the charts list functionality on SoundCloud to return lists based on the kind of music,
    i.e. top 50 or new & hot and also the genre of the music e.g. dance, house etc.

    The amount of results to be returned can also be configured but is set to return by default to 20 entries.

    :param kind:
    :type kind: str
    :param genre:
    :type genre: str
    :param limit:
    :type limit: int

    :return: dict{'type=soundcloud', 'video_id', 'video_time', 'video_title'}, etc. (length of the list depends
             on the limit set to retrieve) or None on no match or error.
    :rtype: list
    """
    if kind is None or genre not in CHART_DETAILS_PARAMETERS['kinds']:
        kind = CHART_DETAILS_PARAMETERS['kinds'][1]

    if genre is None or genre not in CHART_DETAILS_PARAMETERS['genres']:
        genre = CHART_DETAILS_PARAMETERS['genres'][0]

    url = CHART_DETAILS_URL.format(API_KEY, kind, genre, limit)
    response = util.web.http_get(url, json=True)

    if response['json'] is not None:
        chart_items = []
        collections = response.json()['collection']
        for track_num in range(len(collections)):
            try:
                track_id = collections[track_num]['track']['id']
                track_time = collections[track_num]['track']['duration']
                track_title = collections[track_num]['track']['title'].encode('ascii', 'ignore')
                chart_items.append(
                    {
                        'type': 'soundCloud',
                        'video_id': track_id,
                        'video_time': track_time,
                        'video_title': track_title
                    }
                )
            except (IndexError, KeyError) as ex:
                print(ex)

        return chart_items
    else:
        return None


def track_info(track_id):
    """

    :param track_id:
    :type track_id: str
    :return: 'type=soundCloud', 'video_id', 'video_time', 'video_title', 'user_id'
    :rtype: dict
    """
    if track_id:
        url = TRACK_DETAILS_URL.format(API_KEY, track_id)
        response = util.web.http_get(url=url, json=True)

        if response['json'] is not None:
            try:
                user_id = response['json'][0]['user_id']
                track_time = response['json'][0]['duration']
                track_title = response['json'][0]['title'].encode('ascii', 'ignore')
                return {
                    'type': 'soundCloud',
                    'video_id': track_id,
                    'video_time': track_time,
                    'video_title': track_title,
                    'user_id': user_id
                }
            except (IndexError, KeyError):
                return None
        return None


# def soundcloud_resolve(sc_url):
#     pass


# def soundcloud_user_search(user_name):
#     if user_name:
#         url = 'http://api.soundcloud.com/all/?q=%s&client_id=%s' % (user_name, API_KEY)
#     pass


# def soundcloud_user_info_by_id(user_id):
#     url = 'http://api.soundcloud.com/all/%s?client_id=%s' % (user_id, API_KEY)
#     pass
