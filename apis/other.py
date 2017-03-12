""" Contains functions to fetch info from different simple online APIs."""
import util.web

import random
import unicodedata
import urllib


try:
    from bs4 import BeautifulSoup
    bs4_present = True
except (ImportError, BeautifulSoup):
    bs4_present = False

ONE_LINER_TAGS = ['age', 'alcohol', 'animal', 'attitude', 'beauty', 'car', 'communication',
                  'dirty', 'doctor', 'drug', 'family', 'fighting', 'flirty', 'food', 'friendship', 'happiness',
                  'health', 'insults', 'intelligence', 'IT', 'kids', 'life', 'love', 'marriage', 'men', 'mistake',
                  'money', 'motivational', 'motorcycle', 'new', 'people', 'political', 'puns', 'retirement', 'rude',
                  'sarcastic', 'school', 'sport', 'stupid', 'success', 'time', 'travel', 'work']


def urbandictionary_search(search):
    """
    Searches Urban-Dictionary's API for a given search term.
    :param search: The search term str to search for.
    :return: definition str or None on no match or error.
    """
    if str(search).strip():
        urban_api_url = 'http://api.urbandictionary.com/v0/define?term=%s' % search
        response = util.web.http_get(url=urban_api_url, json=True)
        if response['json'] is not None:
            try:
                definition = response['json']['list'][0]['definition'].strip()
                return definition.encode('ascii', 'ignore')
            except (KeyError, IndexError):
                return None
    else:
        return None


def worldwide_weather_search(city):
    """
    Searches World-Weather-Online's API for weather data for a given city.
    You must have a working API key to be able to use this function.
    :param city: The city str to search for.
    :return: weather data str or None on no match or error.
    """
    if str(city).strip():
        api_key = '1a7c7025fa5dec52e070bbc5a7714'
        if not api_key:
            return 'Missing api key.'
        else:
            worldwide_api_url = 'http://api.worldweatheronline.com/free/v2/weather.ashx?' \
                              'q=%s&format=json&key=%s' % (city, api_key)

            response = util.web.http_get(url=worldwide_api_url, json=True)
            if response['json'] is not None:
                try:
                    pressure = response['json']['data']['current_condition'][0]['pressure']
                    temp_celsius = response['json']['data']['current_condition'][0]['temp_C']
                    temp_fahrenheit = response['json']['data']['current_condition'][0]['temp_F']
                    query = response['json']['data']['request'][0]['query'].encode('ascii', 'ignore')

                    cloud_cover = response['json']['data']['current_condition'][0]['cloudcover']
                    sunrise = response['json']['data']['weather'][0]['astronomy'][0]['sunrise']
                    sunset = response['json']['data']['weather'][0]['astronomy'][0]['sunset']

                    weather_online_information = '*Queried location:* %s. *Temperature:* %sC (%sF), ' \
                                                 '*Pressure:* %s millibars, Cloud cover:* %s%%, *Sunrise:* %s,' \
                                                 '*Sunset:* %s.' % (query, temp_celsius, temp_fahrenheit, pressure,
                                                                    cloud_cover, sunrise, sunset)
                    return weather_online_information
                except (IndexError, KeyError):
                    return None
    else:
        return None


def wunderground_weather_search(city):
    """

    Thanks to Aida (Autotonic) for writing this method.
    :param city:
    :return:
    """
    if str(city).strip():
        api_key = ''  # Place your API key for Wunderground weather here.
        if not api_key:
            return 'Missing API key.'
        else:
            wunderground_api_url = 'http://api.wunderground.com/api/%s/conditions/q/%s.json' % (api_key, city)

            response = util.web.http_get(url=wunderground_api_url, json=True)

            if response['json'] is not None:
                try:
                    display_location = response['json']['current_observation']['display_location']['full']
                    weather_observation = response['json']['current_observation']['weather']
                    temperature_observation = response['json']['current_observation']['temperature_string']
                    humidity_observation = response['json']['current_observation']['relative_humidity']

                    wunderground_information = '*%s*: %s | %s | Humidity: %s' % (display_location, weather_observation,
                                                                                 temperature_observation,
                                                                                 humidity_observation)
                    return wunderground_information
                except (IndexError, KeyError):
                    return None
    else:
        return None


def who_is(ip):
    """
    Searches ip-api for information about a given IP address.
    :param ip: The ip str to search for.
    :return: information str or None on error.
    """
    if str(ip).strip():
        ip_api_url = 'http://ip-api.com/json/%s' % ip
        response = util.web.http_get(url=ip_api_url, json=True)
        if response['json'] is not None:
            try:
                city = response['json']['city']
                country = response['json']['country']
                isp = response['json']['isp']
                org = response['json']['org']
                region = response['json']['regionName']
                zipcode = response['json']['zip']
                ip_info = country + ', ' + city + ', ' + region + ', *Zipcode*: ' + zipcode + '  *ISP*: ' + isp + '/' \
                          + org
                return ip_info
            except KeyError:
                return None
    else:
        return None


def chuck_norris():
    """
    Finds a random Chuck Norris joke/quote.
    :return: joke str or None on failure.
    """
    icdb_api_url = 'http://api.icndb.com/jokes/random/?escape=javascript'
    response = util.web.http_get(url=icdb_api_url, json=True)
    if response['json'] is not None:
        if response['json']['type'] == 'success':
            joke = response['json']['value']['joke'].decode('string_escape')
            return joke
        else:
            return None
    else:
        return None


def food_search(ingredient):
    """

    All credits for this method goes to Aida (Autotonic).
    :param ingredient:
    :return:
    """
    if str(ingredient).strip():
        api_key = ''  # Place your API key for the food2fork website here.
        if api_key:
            food2fork_api_url = 'http://food2fork.com/api/search?key=%s&q=%s' % (api_key, ingredient)
            response = util.web.http_get(url=food2fork_api_url, json=True)
            if response['json'] is not None:
                count = int(response['json']['count'])
                num = random.randint(0, count)
                title = response['json']['recipes'][num]['title']
                url = response['json']['recipes'][num]['f2f_url']
                recipe_information = '(%s/%s) *%s*: %s' % (num, count, title, url)
                return recipe_information
            else:
                return None
        else:
            return 'Missing API key.'
    else:
        return None


def online_advice():
    """
    Retrieves a random string of advice from the 'adviceslip' (http://adviceslip.com/) API.
    :return str: advice or None if 'advice' is not found.
    """
    adviceslip_api_url = 'http://api.adviceslip.com/advice'
    response = util.web.http_get(url=adviceslip_api_url, json=True)
    if response['json'] is not None:
        return response['json']['slip']['advice']
    else:
        return None


def duck_duck_go_search(search):
    """
    Search DuckDuckGo using their API (https://duckduckgo.com/api).
    :param search: The search term str to search for.
    :return results: list or None on no match or error.
    """
    duck_duck_go_api_url = 'http://api.duckduckgo.com/?q=%s&ia=answer&format=json&no_html=1' % \
                           urllib.quote_plus(search.strip())
    response = util.web.http_get(url=duck_duck_go_api_url, json=True)

    if response['json'] is not None:
        if response['json']['AnswerType'] == 'calc':
            results = response['json']['Answer']
        else:
            related_topics = response['json']['RelatedTopics']
            results = []
            for topic in range(len(related_topics)):
                if 'Text' in related_topics[topic]:
                    results.append(related_topics[topic]['Text'].replace(search, ('*%s*' % search), 1))
        return results
    return None


def omdb_search(search):
    """
    Query the OMDb API - https://omdbapi.com/.
    :param search: str search term.
    :return omdb_info: str title, rating, and short a description.
    """
    omdb_api_url = 'http://www.omdbapi.com/?t=%s&plot=short&r=json' % search.strip()
    response = util.web.http_get(url=omdb_api_url, json=True)

    if response['json'] is not None:
        try:
            title = response['json']['Title']
            plot = response['json']['Plot']
            imdb_id = response['json']['imdbID']
            imdb_rating = response['json']['imdbRating']
            # if len(plot) > 159:
            #     plot_chunks = string_utili.chunk_string(plot, 70)
            #     plot_chunks = plot[]
            #     plot_formatted = ''
            #     for i in range(0, 2):
            #         plot_formatted += ('\n' + plot_chunks[i])
            # else:
            #     plot_formatted = plot

            omdb_info = '*Title*: %s\n*Rating*: %s\n*Info*: http://www.imdb.com/title/%s\n' % \
                        (title, imdb_rating, imdb_id)

            return omdb_info, plot
        except (KeyError, IndexError):
            return None
    else:
        return None


def longman_dictionary(lookup_term):
    """
    Looks up a particular headword on the Pearson Longman Dictionary API
    (http://http://developer.pearson.com/apis/dictionaries) and returns an appropriate definition.
    NOTE: The API is free for up to 4,000,000 calls per month. We are using the 'entries' API endpoint
          located by using http://api.pearson.com/v2/dictionaries/entries?headword=[headword here].
    For all the searches we are using, we will use the Advanced American Dictionary (laad3 is what we use in the url
    for this dictionary).
    :param lookup_term: str the term to search for a dictionary reference.
    :return definitions: list of the definitions returned from the search.
    """
    dictionary_api_url = 'http://api.pearson.com/v2/dictionaries/laad3/entries?headword=%s' % lookup_term.strip()
    response = util.web.http_get(url=dictionary_api_url, json=True)

    if response['json'] is not None:
        definitions = []
        # TODO: Handle examples.
        for search_result in response['json']['results']:
            if 'senses' in search_result:
                for sense_num in range(len(search_result['senses'])):
                    if 'definition' in search_result['senses'][sense_num]:
                        definition = search_result['senses'][sense_num]['definition']
                        if type(definition) is not list:
                            definitions.append(definition)
        return definitions
    else:
        return None


# def bbc_radio_station_playlist(station):
#     """
#
#     :param station: The number of the station you want to fetch the playlist for:
#                     1 - BBC Radio One, 2 - BBC Radio Two, 3 - BBC Asian Network.
#
#     :type station: int
#     :return:
#     """
#     if station is 1:
#         station_playlist_url = 'http://www.bbc.co.uk/radio1/playlist.json'
#     elif station is 2:
#         station_playlist_url = 'http://www.bbc.co.uk/radio2/playlist.json'
#     elif station is 3:
#         station_playlist_url = 'http://www.bbc.co.uk/asiannetwork/playlist.json'
#     else:
#         return False
#
#     response = util.web.http_get(url=station_playlist_url, json=True)


def time_is(location):
    """
    Retrieves the time in a location by parsing the time element in the html from Time.is .
    :param location: str location of the place you want to find time (works for small towns as well).
    :return time: str or None on failure.
    """
    if bs4_present:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Connection': 'close',
            'Referer': 'http://time.is/',
            'Host': 'time.is'
        }

        time_url = 'http://time.is/' + location.replace(location[0], location[0].upper())
        time_data = util.web.http_get(url=time_url, header=header)
        time_html = time_data['content']
        soup = BeautifulSoup(time_html, 'html.parser')

        try:
            time = ''
            for hit in soup.findAll(attrs={'id': 'twd'}):
                time = hit.contents[0].strip()
        except Exception as ex:
            print(ex)
            time = None
        return time
    else:
        return None


def google_time(location):
    """
    Retrieves the time in a location using Google.
    :param location: str location of the place you want to find time (Location must be a large town/city/country).
    :return time: str or None on failure.
    """
    if bs4_present:
        google_search_url = 'https://www.google.com/search?q=time%20in%20' + urllib.quote_plus(location)
        response = util.web.http_get(url=google_search_url)
        if response['content'] is not None:
            raw_content = response['content']
            soup = BeautifulSoup(raw_content, 'html.parser')

            try:
                raw_info = None
                for hit in soup.findAll(attrs={'class': 'vk_c vk_gy vk_sh card-section _MZc'}):
                    raw_info = hit.contents
            except Exception as ex:
                print(ex)
                return None

            if raw_info is not None:
                location = str(raw_info[5].getText()).strip()
                time = str(raw_info[1].getText()).strip()
                return location, time
            else:
                return None
    return None


def official_charts():
    """
    Retrieves the Official Charts Top 40 Singles (http://www.officialcharts.com/charts/uk-top-40-singles-chart/)
    currently in time.
    :return official_charts: list of the artist and title of the tracks in the top 40 starting from first to the last.
    """
    if bs4_present:
        official_charts_url = 'http://www.officialcharts.com/charts/uk-top-40-singles-chart/'
        response = util.web.http_get(url=official_charts_url)

        if response['content'] is not None:
            html = response['content']
            soup = BeautifulSoup(html, 'html.parser')
            tracks = soup.findAll('div', {'class': 'track'})

            official_tracks = []
            for track in tracks:
                # Get the text from the track.
                title_artist = track.find('div', {'class': 'title'}).getText()
                title_name = track.find('div', {'class': 'artist'}).getText()

                # Get the track artist and name by stripping any spaces and storing them as titles into the list.
                track_artist = title_artist.strip()
                track_name = title_name.strip()
                official_tracks.append('%s - %s' % (track_artist.title(), track_name.title()))

            if len(official_tracks) is not 0:
                return official_tracks
            else:
                return False
    return None


def radio_top40_charts():
    """
    Retrieves the Top40 songs list from Radio One (www.bbc.co.uk/radio1/chart/singles).
    :return songs: list (nested list) all songs including the song name and artist in the format
                   [[songs name, song artist], etc.]] or None if we couldn't retrieve any content.
    """
    if bs4_present:
        radio_one_url = 'http://www.bbc.co.uk/radio1/chart/singles'
        response = util.web.http_get(url=radio_one_url)

        if response['content'] is not None:
            html = response['content']
            soup = BeautifulSoup(html, 'html.parser')
            raw_titles = soup.findAll('div', {'class': 'cht-entry-title'})
            raw_artists = soup.findAll('div', {'class': 'cht-entry-artist'})

            all_titles = []
            all_artists = []

            for x in range(len(raw_titles)):
                individual_title = unicodedata.normalize('NFKD', raw_titles[x].getText()).encode('ascii', 'ignore')
                all_titles.append(individual_title)

            for x in range(len(raw_artists)):
                individual_artist = unicodedata.normalize('NFKD', raw_artists[x].getText()).encode('ascii', 'ignore')
                individual_artist = individual_artist.lstrip()
                individual_artist = individual_artist.rstrip()
                all_artists.append(individual_artist)

            songs = []
            for song in range(len(all_titles)):
                songs.append('%s - %s' % (all_artists[song], all_titles[song]))

            if len(songs) is not 0:
                return songs
            else:
                return False
        else:
            return None
    else:
        return None


def capital_fm_latest():
    """
    Retrieves the track playing at the moment on the Capital FM radio station (http://www.capitalfm.com/).
    The function returns a music search term which can be used by the YouTube or SoundCloud API to load the song.
    :return music_term: str the current track that is playing and the track artist.
    """
    if bs4_present:
        last_played_url = 'http://www.capitalfm.com/radio/last-played-songs/'
        response = util.web.http_get(url=last_played_url)

        if response['content'] is not None:
            html = response['content']
            soup = BeautifulSoup(html, 'html.parser')

            now_playing_content = soup.find('div', {'class': 'now-playing__text-content'})

            raw_current_track = now_playing_content.find('span', {'itemprop': 'name', 'class': 'track'})
            raw_current_artist = now_playing_content.find('span', {'itemprop': 'byArtist', 'class': 'artist'})

            current_track = raw_current_track.getText().strip()
            current_artist = raw_current_artist.getText().strip()

            music_search_term = current_artist + ' - ' + current_track
            return music_search_term
        else:
            return None


def one_liners(tag=None):
    """
    Retrieves a one-liner from http://onelinefun.com/ (by selecting a random category).
    :param tag: str a specific tag name from which you want to choose a joke from.
    :return joke: str a one line joke/statement (depending on the specified category).
    """
    if bs4_present:
        onelinefun_url = 'http://onelinefun.com/'
        # TODO: Make this small section more clear.
        if tag is None:
            # Select a random tag from the list if one has not been provided.
            joke_tag = random.randint(0, len(ONE_LINER_TAGS) - 1)
            joke_url = onelinefun_url + ONE_LINER_TAGS[joke_tag] + '/'
        else:
            joke_url = onelinefun_url + str(tag) + '/'

        response = util.web.http_get(url=joke_url)
        if response['content'] is not None:
            html = response['content']
            soup = BeautifulSoup(html, 'html.parser')
            jokes = soup.findAll('p')
            if jokes:
                all_jokes = []

                for x in range(len(jokes)):
                    individual_joke = unicodedata.normalize('NFKD', jokes[x].getText()).encode('ascii', 'ignore')
                    all_jokes.append(individual_joke)

                if len(all_jokes) is not 0:
                    del all_jokes[0]
                    for x in range(6):
                        del all_jokes[len(all_jokes) - 1]

                    return str(all_jokes[random.randint(0, len(all_jokes) - 1)])
    return None


def etymonline(search):
    """
    Searches the etymology of words/phrases using the Etymonline website (http://etymonline.com/).
    :param search: str the word/phrase you want to search for.
    :return: str the quote from the the search result.
    """
    if bs4_present:
        etymonline_url = 'http://etymonline.com/index.php?term=%s&allowed_in_frame=0' % (search.replace(' ', '+'))
        response = util.web.http_get(url=etymonline_url)

        if response['content'] is not None:
            html = response['content']
            soup = BeautifulSoup(html, 'html.parser')
            quotes = soup.findAll('dd', {'class': 'highlight'})
            # There are several quotes/term results returned, we only want the first one,
            # alternatively a loop can be setup. Represent the tags as a string,
            # since we do not have specific identification. Unicode characters in this process
            # will be represented as their respective values.
            if len(quotes) is not 0:
                quote = quotes[0].getText()
                quotes = quote.split('\r\n\r\n')
                # There are more than one set of quotes parsed, you may iterate over this too in order to return a
                # greater set of results.
                return u'' + quotes[0]  # Result is returned as unicode.
    return None
