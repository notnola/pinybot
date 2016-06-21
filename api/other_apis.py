# -*- coding: utf-8 -*-

# Provides functions to search/explore various APIs i.e. urbandictionary,
# worldweatheronline , ip-api and api.icndb & many others
# Includes BeautifulSoup parsed APIs/websites functions

import web_request
import requests
import unicodedata
import random

try:
    from bs4 import BeautifulSoup
except:
    BeautifulSoup = None

if BeautifulSoup != None:
    try:
        import wikipedia # Is reliant on BeautifulSoup to be present
    except:
        wikipedia = None

# A storage for API keys if required; add to this dictionary if you intend to use
# more keys
API_KEYS = {'weather': ''}


def urbandictionary_search(search):
    """
    Searches Urban-dictionary's API for a given search term.
    :param search: The search term str to search for.
    :return: defenition str or None on no match or error.
    """

    if str(search).strip():
        urban_api_url = 'http://api.urbandictionary.com/v0/define?term=%s' % search
        response = web_request.get_request(urban_api_url, json=True)

        if response:
            try:
                definition = response['content']['list'][0]['definition']
                return definition.encode('ascii', 'ignore')
            except KeyError:
                return None
            except IndexError:
                return None
    else:
        return None


def weather_search(city):
    """
    Searches worldweatheronline's API for weather data for a given city.
    You must have a working API key to be able to use this function.
    :param city: The city str to search for.
    :return: weather data str or None on no match or error.
    """

    if str(city).strip():
        api_key = API_KEYS['weather']  # A valid API key.
        if not api_key:
            return 'Missing api key.'
        else:
            weather_api_url = 'http://api.worldweatheronline.com/free/v2/weather.ashx?' \
                              'q=%s&format=json&key=%s' % (city, api_key)

            response = web_request.get_request(weather_api_url, json=True)

            if response['content'] is not None:
                try:
                    pressure = response['content']['data']['current_condition'][0]['pressure']
                    temp_c = response['content']['data']['current_condition'][0]['temp_C']
                    temp_f = response['content']['data']['current_condition'][0]['temp_F']
                    query = response['content']['data']['request'][0]['query'].encode('ascii', 'ignore')
                    result = query + '. Temperature: ' + temp_c + 'C (' + temp_f + 'F) Pressure: ' + pressure + ' millibars'
                    return result
                except (IndexError, KeyError):
                    return None
    else:
        return None


def whois(ip):
    """
    Searches ip-api for information about a given IP.
    :param ip: The ip str to search for.
    :return: information str or None on error.
    """

    if str(ip).strip():
        url = 'http://ip-api.com/json/%s' % ip
        json_data = web_request.get_request(url, json=True)
        try:
            city = json_data['content']['city']
            country = json_data['content']['country']
            isp = json_data['content']['isp']
            org = json_data['content']['org']
            region = json_data['content']['regionName']
            zipcode = json_data['content']['zip']
            info = country + ', ' + city + ', ' + region + ', Zipcode: ' + zipcode + '  Isp: ' + isp + '/' + org
            return info
        except KeyError:
            return None
    else:
        return None


def chuck_norris():
    """
    Finds a random Chuck Norris joke/quote.
    :return: joke str or None on failure.
    """

    url = 'http://api.icndb.com/jokes/random/?escape=javascript'
    json_data = web_request.get_request(url, json=True)
    if json_data['content']['type'] == 'success':
        joke = json_data['content']['value']['joke'].decode('string_escape')
        return joke
    else:
        return None


def yo_mama_joke():
    """
    Retrieves a random 'Yo Mama' joke from an API.
    :return: joke str or None on failure.
    """

    url = 'http://api.yomomma.info/'
    json_data = web_request.get_request(url, json=True)
    if json_data['content']:
        joke = json_data['content']['joke'].decode('string_escape')
        return joke
    else:
        return None


def onlineadvice():
    """
    Retrieves a random piece of advice from an API.
    :return: adivce str or None on failure.
    """

    url = 'http://api.adviceslip.com/advice'
    json_data = web_request.get_request(url, json=True)
    if json_data['content']:
        advice = json_data['content']['slip']['advice'].decode('string_escape')
        return advice
    else:
        return None


def duckduckgo_search(search):
    """
    Search DuckDuckGo using their API - https://duckduckgo.com/api
    :param search: The search term str to search for.
    :return: definition str or None on no match or error.
    """

    if str(search).strip():
        ddg_api = 'https://api.duckduckgo.com/?q=%s&format=json' % search
        response = web_request.get_request(ddg_api, json=True)

        definitions = []
        if response:
            # Return up to 2 definition results
            for x in range(2):
                definition = response['content']['RelatedTopics'][x]['Text']
                definitions.append(definition.encode('ascii', 'ignore'))
            return definitions
    else:
        return None


def wiki_search(search):
    """
    Requires wikipedia,  pip install wikipedia
    :param search: The search term str to search for.
    :return: wikipedia summary or None if nothing found.
    """
    if BeautifulSoup != None:
        if wikipedia != None:
            wiki_content = wikipedia.summary(search, sentences=2)
            return wiki_content
        else:
            return False


def omdb_search(search):
    """
    Query the OMDb API - https://omdbapi.com/
    :param search: Search term
    :return: Title, rating, and short description
    """
    if str(search).strip():
        omdb_url = 'http://www.omdbapi.com/?t=%s&plot=short&r=json' % search
        response = web_request.get_request(omdb_url, json=True)

        if response:
            print response
            try:
                title = response['content']['Title']
                plot = response['content']['Plot']
                imdbid = response['content']['imdbID']
                imdbrating = response['content']['imdbRating']
                if len(plot) >= 160:
                    plot_parts = plot.split('.')
                    omdb_info ='*Title:* ' + title + '\n' + plot_parts[0] + '\n*Rating:*' + imdbrating + '\n*More Info:*  http://www.imdb.com/title/' + imdbid
                else:
                    omdb_info ='*Title:* ' + title + '\n' + plot + '\n*Rating:*' + imdbrating + '\n*More Info:*  http://www.imdb.com/title/' + imdbid
                return omdb_info
            except KeyError:
                return None
            except IndexError:
                return None
    else:
        return None


# These APIs require the use of Requests, BeautifulSoup, urllib2 and unicodedata.
# As a result of using HTML parsers, the code maybe subject to change over time
# to adapt with the server's pages.
def time_is(location):
    """
    Retrieves the time in a location by parsing the time element in the html from http://time.is/
    NOTE: This uses the normal 'requests' module.
    :param location: str location of the place you want to find time (works for small towns as well).
    :return: time str or None on failure.
    """

    if BeautifulSoup:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'http://time.is/',
        }

        try:
            post_url = 'http://time.is/' + str(location)
            time_data = requests.post(url=post_url, headers=header)
            time_html = time_data.content
            soup = BeautifulSoup(time_html, "html.parser")

            for hit in soup.findAll(attrs={'id': 'twd'}):
                time = hit.contents[0].strip()

            return time
        except:
            return None
    else:
        return None


def google_time(location):
    """
    Retrieves the time in a location using Google.
    :param location: str location of the place you want to find time (Location must be a large town/city/country).
    :return: time str or None on failure.
    """

    if BeautifulSoup != None:
        to_send = location.replace(' ', '%20')
        url = 'https://www.google.co.uk/search?q=time%20in%20' + str(to_send)
        raw = web_request.get_request(url)
        if raw['status_code'] == 200:
            raw_content = raw['content']
            soup = BeautifulSoup(raw_content, 'html.parser')
            raw_info = None

            try:
                for hit in soup.findAll(attrs={'class': 'vk_c vk_gy vk_sh card-section _MZc'}):
                    raw_info = hit.contents
            except:
                pass

            if raw_info is None:
                return None
            else:
                return [str(raw_info[1].getText()), str(raw_info[5].getText())]
        else:
            return None
    else:
        return None


def top40():
    """
    Retrieves the Top40 songs list from www.bbc.co.uk/radio1/chart/singles.
    :return: list (nested list) all songs including the song name and artist in the format [[songs name, song artist], etc.]].
    """

    if BeautifulSoup != None:
        chart_url = "http://www.bbc.co.uk/radio1/chart/singles"
        raw = web_request.get_request(url=chart_url)
        html = raw['content']
        soup = BeautifulSoup(html, "html.parser")
        raw_titles = soup.findAll("div", {"class": "cht-entry-title"})
        raw_artists = soup.findAll("div", {"class": "cht-entry-artist"})

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
        for x in range(len(all_titles)):
            songs.append([all_titles[x], all_artists[x]])

        if len(songs) > 0:
            return songs
        else:
            return None
    else:
        return None


tags = ['men', 'life', 'kids', 'money', 'mistake', 'sex', 'stupid', 'puns', 'new',
        'black', 'dirty', 'motivational', 'rude', 'time', 'fat', 'drug', 'blonde',
        'alcohol', 'ugly', 'communication', 'doctor', 'health', 'political',
        'IT', 'sarcastic', 'insults', 'racist', "age", 'intelligence', 'friendship',
        'fighting', 'happiness', 'love']


def oneliners(tag=None):
    """
    Retrieves a one-liner from http://onelinefun.com/ (by choosing a random category).
    :param tag (OPTIONAL): str a specific tag name from which you want to choose a
                               joke from.
    :return: joke: str a one line joke/statement (depending on category).
    """

    if BeautifulSoup != None:
        url = "http://onelinefun.com/"
        if tag:
            joke_url = url + str(tag) + "/"
        else:
            global tags

            # Select a random tag from the list if one has not been provided
            joke_tag = random.randint(0, len(tags) - 1)
            joke_url = url + tags[joke_tag] + "/"

        raw = web_request.get_request(url=joke_url)
        if raw['status_code'] == 200:
            html = raw['content']
            soup = BeautifulSoup(html, "html.parser")
            jokes = soup.findAll("p")
            if jokes:
                all_jokes = []

                for x in range(len(jokes)):
                    individual_joke = unicodedata.normalize('NFKD', jokes[x].getText()).encode('ascii', 'ignore')
                    all_jokes.append(individual_joke)

                if len(all_jokes) is not 0:
                    del all_jokes[0]
                    for x in range(6):
                        del all_jokes[len(all_jokes) - 1]

                    joke = str(all_jokes[random.randint(0, len(all_jokes) - 1)])

                    return joke
                else:
                    return None
            else:
                return None
        else:
            return None
    else:
        return None


