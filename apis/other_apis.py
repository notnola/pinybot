# -*- coding: utf-8 -*-
""" Provides functions to search/explore various APIs """

# Some examples include: World-weather-online, Urban-dictionary, ip-api and api.icndb & many others.
# Includes BeautifulSoup parsed APIs/website functions.

import web_request
import unicodedata
import random

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

if BeautifulSoup is not None:
    try:
        import wikipedia  # Reliant on BeautifulSoup to being present.
    except ImportError:
        wikipedia = None

# A storage area for API keys if required; add to this dictionary if you intend to use more keys.
API_KEYS = {'weather': ''}


def urbandictionary_search(search):
    """
    Searches Urban-dictionary's API for a given search term.
    :param search: str the search term str to search for.
    :return: str definition or None on no match or error.
    """

    urban_api_url = 'http://api.urbandictionary.com/v0/define?term=%s' % search.strip()
    response = web_request.get_request(urban_api_url, json=True)

    if response:
        try:
            definition = response['content']['list'][0]['definition'].strip()
            # print definition
            definition_parts = definition.split('\n')
            one_definition = definition_parts[0].replace('\r', '')
            return one_definition.encode('ascii', 'ignore')
        except KeyError:
            return None
        except IndexError:
            return None
    else:
        return None


# TODO: Expose time in location.
def weather_search(city):
    """
    Searches World-weather-online's API for weather data for a given city.
    NOTE: You must have a working API key from the website to be able to use this function and also be aware of the
          API call restrictions on the API key for your account.
    :param city: The city str to search for.
    :return: weather data str or None on no match or error.
    """

    city = str(city).strip()
    # A valid API key from the API_KEYS dictionary.
    api_key = API_KEYS['weather']
    if api_key:
        weather_api_url = 'http://api.worldweatheronline.com/free/v2/weather.ashx?' \
                          'q=%s&format=json&key=%s' % (city, api_key)

        response = web_request.get_request(weather_api_url, json=True)

        if response['content'] is not None:
            try:
                data = response['content']['data']
                query = data['request'][0]['query'].encode('ascii', 'ignore')
                pressure = data['current_condition'][0]['pressure']
                cloud_cover = data['current_condition'][0]['cloudcover']
                temp_celsius = data['current_condition'][0]['temp_C']
                temp_fahrenheit = data['current_condition'][0]['temp_F']
                sunrise = data['weather'][0]['astronomy'][0]['sunrise']
                sunset = data['weather'][0]['astronomy'][0]['sunset']
                result = query + '. Temperature: ' + temp_celsius + 'C (' + temp_fahrenheit + 'F), Pressure: ' + \
                         pressure + ' millibars, Cloud cover: ' + cloud_cover + '%, Sunrise: ' + sunrise + \
                         ', Sunset: ' + sunset
                return result
            except (IndexError, KeyError):
                return None
    else:
        return False


def whois(ip):
    """
    Searches ip-api for information about a given IP.
    :param ip: str the ip str to search for.
    :return: str information str or None on error.
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
            info = country + ', ' + city + ', ' + region + ', *Zipcode*: ' + zipcode + '  *ISP*: ' + isp + '/' + org
            return info
        except KeyError:
            return None
    else:
        return None


# TODO: Implement categories, and character name functionality.
def chuck_norris():
    """
    Finds a random Chuck Norris joke/quote from http://www.icndb.com/api/ .
    The API also has category specifications, i.e. categories are either "nerdy"/"explicit" set via webform "?limtTo".
    The character names can also be altered via passing the webform "?firstName=[name]" or "?lastName=[name]".
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


def online_advice():
    """
    Retrieves a random string of advice from an API.
    :return: advice str or None on failure.
    """

    url = 'http://api.adviceslip.com/advice'
    json_data = web_request.get_request(url, json=True)
    if json_data['content']:
        advice = json_data['content']['slip']['advice'].decode('ascii', 'ignore')
        return str(advice)
    else:
        return None


# TODO: Needs a more clearer and succinct output.
def duckduckgo_search(search):
    """
    Search DuckDuckGo using their API - https://duckduckgo.com/api .
    NOTE: This is currenly limited to definition as of now.
    :param search: The search term str to search for.
    :return: definition str or None on no match or error.
    """

    if str(search).strip():
        ddg_api = 'https://api.duckduckgo.com/?q=%s&format=json' % search
        response = web_request.get_request(ddg_api, json=True)

        definitions = []
        if response:
            # Return up to 2 definition results.
            for x in range(2):
                definition = response['content']['RelatedTopics'][x]['Text']
                # The search word is stripped from the definition result by default.
                definitions.append(definition.encode('ascii', 'ignore').strip(search))
            return definitions
    else:
        return None


# TODO: The functions use needs to be redefined and needs to be referred to the original library.
def wiki_search():  # search=None
    """
    Requires Wikipedia module;  pip install wikipedia.
    :return: Wikipedia summary or None if nothing found.
    """
    # :param search: str The search term to search for.

    if BeautifulSoup is not None:
        if wikipedia is not None:
            raise NotImplementedError('Wikipedia functionality is yet to be integrated properly.')
            # wiki_content = wikipedia.summary(search, sentences=2)
            # return wiki_content
        else:
            return False


def omdb_search(search):
    """
    Query the OMDb API - https://omdbapi.com/.
    :param search: str search term.
    :return: str title, rating, and short description.
    """
    if str(search).strip():
        omdb_url = 'http://www.omdbapi.com/?t=%s&plot=short&r=json' % search
        response = web_request.get_request(omdb_url, json=True)

        if response:
            try:
                title = response['content']['Title']
                plot = response['content']['Plot']
                imdbid = response['content']['imdbID']
                imdbrating = response['content']['imdbRating']
                if len(plot) >= 160:
                    plot_parts = plot.split('.')
                    omdb_info = '*Title:* ' + title + '\nDetails: ' + plot_parts[0] + '\n*Rating: *' + imdbrating +\
                                '\n*More Info:*  http://www.imdb.com/title/' + imdbid
                else:
                    omdb_info = '*Title:* ' + title + '\n' + plot + '\n*Rating:*' + imdbrating +\
                                '\n*More Info:*  http://www.imdb.com/title/' + imdbid
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
    Retrieves the time in a location by parsing the time element in the html from Time.is .
    :param location: str location of the place you want to find time (works for small towns as well).
    :return: time str or None on failure.
    """

    if BeautifulSoup:
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:42.0) Gecko/20100101 Firefox/42.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Connection': 'close',
            'Referer': 'http://time.is/',
            'Host': 'time.is'
        }

        post_url = 'http://time.is/' + location.replace(location[0], location[0].upper())
        time_data = web_request.get_request(post_url, header=header)
        time_html = time_data['content']
        soup = BeautifulSoup(time_html, "html.parser")

        time = ''
        try:
            for hit in soup.findAll(attrs={'id': 'twd'}):
                time = hit.contents[0].strip()
        except Exception:
            pass

        return time
    else:
        return None


# TODO: Allow time to reply with AM/PM.
def google_time(location):
    """
    Retrieves the time in a location using Google.
    :param location: str location of the place you want to find time (Location must be a large town/city/country).
    :return: time str or None on failure.
    """

    if BeautifulSoup is not None:
        to_send = location.replace(' ', '%20')
        url = 'https://www.google.com/search?q=time%20in%20' + to_send
        raw = web_request.get_request(url)
        if raw['status_code'] is 200:
            raw_content = raw['content']
            soup = BeautifulSoup(raw_content, 'html.parser')
            raw_info = None

            try:
                for hit in soup.findAll(attrs={'class': 'vk_c vk_gy vk_sh card-section _MZc'}):
                    raw_info = hit.contents
            except Exception:
                return None

            if raw_info is not None:
                location = str(raw_info[5].getText()).strip()
                time = str(raw_info[1].getText()).strip()
                return [location, time]
            else:
                return None
        else:
            return None
    else:
        return None


def top40():
    """
    Retrieves the Top40 songs list from www.bbc.co.uk/radio1/chart/singles.
    :return: list (nested list) all songs including the song name and artist in the format
             [[songs name, song artist], etc.]].
    """

    if BeautifulSoup is not None:
        chart_url = 'http://www.bbc.co.uk/radio1/chart/singles'
        raw = web_request.get_request(url=chart_url)
        html = raw['content']
        soup = BeautifulSoup(html, "html.parser")
        raw_titles = soup.findAll("div", {"class": "cht-entry-title"})
        raw_artists = soup.findAll("div", {"class": "cht-entry-artist"})

        all_titles = []
        all_artists = []

        for x in xrange(len(raw_titles)):
            individual_title = unicodedata.normalize('NFKD', raw_titles[x].getText()).encode('ascii', 'ignore')
            all_titles.append(individual_title)

        for x in xrange(len(raw_artists)):
            individual_artist = unicodedata.normalize('NFKD', raw_artists[x].getText()).encode('ascii', 'ignore')
            individual_artist = individual_artist.lstrip()
            individual_artist = individual_artist.rstrip()
            all_artists.append(individual_artist)

        songs = []
        for x in xrange(len(all_titles)):
            songs.append([all_titles[x], all_artists[x]])

        if len(songs) > 0:
            return songs
        else:
            return None
    else:
        return None


tags = ['age', 'alcohol', 'animal', 'attitude', 'beauty', 'black', 'blonde', 'car', 'communication',
        'dirty', 'doctor', 'drug', 'family', 'fat', 'fighting', 'flirty', 'food', 'friendship', 'happiness',
        'health', 'insults', 'intelligence', 'IT', 'kids', 'life', 'love', 'marriage', 'men', 'mistake', 'money',
        'motivational', 'motorcycle', 'new', 'people', 'political', 'puns', 'retirement', 'rude', 'sarcastic',
        'sex', 'school', 'sport', 'stupid', 'success', 'time', 'travel', 'women', 'work']


def one_liners(tag=None):
    """
    Retrieves a one-liner from http://onelinefun.com/ (by choosing a random category).
    :param tag: str a specific tag name from which you want to choose a
                    joke from.
    :return: joke: str a one line joke/statement (depending on category).
    """

    if BeautifulSoup is not None:
        url = 'http://onelinefun.com/'
        if tag:
            joke_url = url + str(tag) + '/'
        else:
            global tags

            # Select a random tag from the list if one has not been provided
            joke_tag = random.randint(0, len(tags) - 1)
            joke_url = url + tags[joke_tag] + '/'

        raw = web_request.get_request(url=joke_url)
        if raw['status_code'] is 200:
            html = raw['content']
            soup = BeautifulSoup(html, "html.parser")
            jokes = soup.findAll("p")
            if jokes:
                all_jokes = []

                for x in xrange(len(jokes)):
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


def etymonline(search):
    """
    Searches the etymology of words/phrases using the Etymonline website.

    :param search: str the word/phrase you want to search for.
    :return: dict the results from the search.
    """
    if BeautifulSoup is not None:
        url = 'http://etymonline.com/index.php?term=%s&allowed_in_frame=0'
        search_parts = search.split(' ')
        search_term = '+'.join(search_parts)
        post_url = url % search_term

        raw = web_request.get_request(url=post_url)
        if raw['status_code'] is 200:
            html = raw['content']
            soup = BeautifulSoup(html, "html.parser")
            quotes = soup.findAll("dd", {"class": "highlight"})
            # There are several quotes/term results returned, we only want
            # the first one, alternatively a loop can be setup.
            # Represent the tags as a string, since we do not have specific identification.
            # Unicode characters in this process will be represented as their respective values.
            if len(quotes) is not 0:
                quote = quotes[0].getText()
                quotes = quote.split('\r\n\r\n')
                # There are more than one set of quotes parsed, you may iterate over this too in order to return a
                # greater set of results.
                return u"" + quotes[0]  # Result is returned in unicode.
            else:
                return None
        else:
            return None
    else:
        return None

