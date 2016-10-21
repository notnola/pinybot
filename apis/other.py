# -*- coding: utf-8 -*-
""" Provides functions to search/explore various APIs """

# Some examples include: World-weather-online, Urban-dictionary, ip-api and api.icndb & many others.
# Includes BeautifulSoup parsed APIs/website functions.

import random
import unicodedata

from utilities import web, string_utili

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

ONE_LINER_TAGS = ['age', 'alcohol', 'animal', 'attitude', 'beauty', 'black', 'blonde', 'car', 'communication',
                  'dirty', 'doctor', 'drug', 'family', 'fat', 'fighting', 'flirty', 'food', 'friendship', 'happiness',
                  'health', 'insults', 'intelligence', 'IT', 'kids', 'life', 'love', 'marriage', 'men', 'mistake',
                  'money', 'motivational', 'motorcycle', 'new', 'people', 'political', 'puns', 'retirement', 'rude',
                  'sarcastic', 'sex', 'school', 'sport', 'stupid', 'success', 'time', 'travel', 'women', 'work']


def urbandictionary_search(search):
    """
    Searches Urban-dictionary's API for a given search term.
    :param search: str the search term str to search for.
    :return: str definition or None on no match or error.
    """
    urban_api_url = 'http://api.urbandictionary.com/v0/define?term=%s' % search.strip()
    response = web.http_get(urban_api_url, json=True)
    if response['json'] is not None:
        try:
            definition = response['json']['list'][0]['definition'].strip()
            return definition.encode('ascii', 'ignore')
        except (KeyError, IndexError) as ex:
            print(ex)
            return None
    else:
        return None


# TODO: Expose time in location.
def weather_search(city):
    """
    Searches World-weather-online's API for weather data for a given city.
    NOTE: You must have a working API key from the website to be able to use this function and also be aware of the
          API call restrictions on API access for your account.
    :param city: The city str to search for.
    :return: weather data str or None on no match or error.
    """
    city = str(city).strip()
    api_key = ''
    if api_key:
        weather_api_url = 'http://api.worldweatheronline.com/free/v2/weather.ashx?q=%s&format=json&key=%s' %\
                          (city, api_key)
        response = web.http_get(weather_api_url, json=True)
        if response['json'] is not None:
            try:
                pressure = response['json']['data']['current_condition'][0]['pressure']
                temp_c = response['json']['data']['current_condition'][0]['temp_C']
                temp_f = response['json']['data']['current_condition'][0]['temp_F']
                query = response['json']['data']['request'][0]['query'].encode('ascii', 'ignore')

                cloud_cover = response['json']['data']['current_condition'][0]['cloudcover']
                sunrise = response['json']['data']['weather'][0]['astronomy'][0]['sunrise']
                sunset = response['json']['data']['weather'][0]['astronomy'][0]['sunset']
                weather_info = '*Queried location:* %s. *Temperature:* %sC (%sF), *Pressure:* %s millibars, ' \
                               '*Cloud cover:* %s%%, *Sunrise:* %s, *Sunset:* %s.' % \
                               (query, temp_c, temp_f, pressure, cloud_cover, sunrise, sunset)
                return weather_info
            except (IndexError, KeyError) as ex:
                print(ex)
                return None
    else:
        return False


def whois(ip):
    """
    Searches ip-api for information about a given IP address.
    :param ip: str the ip str to search for.
    :return: str information str or None on error.
    """
    if str(ip).strip():
        url = 'http://ip-api.com/json/%s' % ip
        response = web.http_get(url, json=True)
        if response['json'] is not None:
            city = response['json']['city']
            country = response['json']['country']
            isp = response['json']['isp']
            org = response['json']['org']
            region = response['json']['regionName']
            zipcode = response['json']['zip']
            ip_info = country + ', ' + city + ', ' + region + ', *Zipcode*: ' + zipcode + '  *ISP*: ' + isp + '/' + org
            return ip_info
        else:
            return None
    else:
        return None


# TODO: Implement categories, and character name functionality.
def chuck_norris():
    """
    Finds a random Chuck Norris joke/quote from http://www.icndb.com/api/ .
    The API also has category specifications, i.e. categories are either "nerdy"/"explicit" set via webform "?limtTo".
    The character names can also be altered via passing the webform "?firstName=[name]" or "?lastName=[name]".
    :return: str or None on failure.
    """
    url = 'http://api.icndb.com/jokes/random/?escape=javascript'
    response = web.http_get(url, json=True)
    if response['json'] is not None:
        if response['json']['type'] == 'success':
            joke = response['json']['value']['joke'].decode('string_escape')
            return joke
        else:
            return None
    else:
        return None


def hash_cracker(hash_str):
    """
    Using md5cracker.org to crack md5 hashes with.
    :param hash_str: str the md5 hash to crack.
    :return: dict{'status', 'result', 'message'} or None on error.
    """
    url = 'http://md5cracker.org/api/api.cracker.php?r=9327&database=md5cracker.org&hash=%s' % hash_str
    response = web.http_get(url, json=True)
    if response['json'] is not None:
        return {
            'status': response['json']['status'],
            'result': response['json']['result'],
            'message': response['json']['message']
        }
    else:
        return None


def yo_mama_joke():
    """
    Retrieves a random 'Yo Mama' joke from an API.
    :return: joke str or None on failure.
    """
    url = 'http://api.yomomma.info/'
    response = web.http_get(url, json=True)
    if response['json'] is not None:
        joke = response['json']['joke'].decode('string_escape')
        return joke
    else:
        return None


def online_advice():
    """
    Retrieves a random string of advice from an API.
    :return: advice str or None on failure.
    """
    url = 'http://api.adviceslip.com/advice'
    response = web.http_get(url, json=True)
    if response['json'] is not None:
        advice = response['json']['slip']['advice']
        return advice
    else:
        return None


# TODO: Needs a more clearer and succinct output.
def duckduckgo_search(search):
    """
    Search DuckDuckGo using their API - https://duckduckgo.com/api .
    NOTE: This is currently limited to definition as of now.
    :param search: The search term str to search for.
    :return: definition str or None on no match or error.
    """
    if str(search).strip():
        ddg_api = 'https://api.duckduckgo.com/?q=%s&format=json' % search
        response = web.http_get(ddg_api, json=True)

        if response['json'] is not None:
            definitions = []
            # Return up to 2 definitions.
            for x in range(2):
                definition = response['json']['RelatedTopics'][x]['Text']
                # The search word is stripped from the definition by default.
                definitions.append(definition.encode('ascii', 'ignore').strip(search))
            return definitions
        else:
            return None
    else:
        return None


def omdb_search(search):
    """
    Query the OMDb API - https://omdbapi.com/.
    :param search: str search term.
    :return: str title, rating, and short description.
    """
    if str(search).strip():
        omdb_url = 'http://www.omdbapi.com/?t=%s&plot=short&r=json' % search
        response = web.http_get(omdb_url, json=True)

        if response['json'] is not None:
            try:
                title = response['json']['Title']
                plot = response['json']['Plot']
                imdbid = response['json']['imdbID']
                imdbrating = response['json']['imdbRating']
                if len(plot) > 159:
                    plot_chunks = string_utili.chunk_string(plot, 70)
                    plot_formatted = ''
                    for i in range(0, 2):
                        plot_formatted += ('\n' + plot_chunks[i])
                else:
                    plot_formatted = plot

                omdb_info = '*Title:* %s\nDetails: %s\n*Rating:* %s\n*More Info:* http://www.imdb.com/title/%s' % \
                            (title, plot_formatted, imdbrating, imdbid)

                return omdb_info
            except (KeyError, IndexError) as ex:
                print(ex)
                return None
        else:
            return None
    else:
        return None


def longman_dictionary(lookup_term):
    """
    Looks up a particular headword on the Pearson Longman Dictionary API -
    http://http://developer.pearson.com/apis/dictionaries and returns an appropriate definition response.

    NOTE: The API is free for up to 4,000,000 calls per month.
    :param lookup_term: str the term to search for a dictionary reference.
    :return
    """
    # http://api.pearson.com/v2/dictionaries/entries?headword=key
    dictionary_url = 'http://api.pearson.com/v2/dictionaries/entries?headword=%s' % lookup_term
    response = web.http_get(dictionary_url, json=True)

    if response['json'] is not None:
        return response['json']['results']


# These APIs require the use of Requests, BeautifulSoup, urllib2 and unicodedata. As a result of using HTML parsers,
# the code maybe subject to change over time to adapt with the server's pages.
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
        time_data = web.http_get(post_url, header=header)
        time_html = time_data['content']
        soup = BeautifulSoup(time_html, "html.parser")
        time = str

        try:
            for hit in soup.findAll(attrs={'id': 'twd'}):
                time = hit.contents[0].strip()
        except Exception as ex:
            print(ex)
            return None

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
        response = web.http_get(url)
        if response['content'] is not None:
            raw_content = response['content']
            soup = BeautifulSoup(raw_content, 'html.parser')
            raw_info = None

            try:
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
        response = web.http_get(url=chart_url)
        if response['content'] is not None:
            html = response['content']
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


def one_liners(tag=None):
    """
    Retrieves a one-liner from http://onelinefun.com/ (by choosing a random category).
    :param tag: str a specific tag name from which you want to choose a joke from.
    :return: joke: str a one line joke/statement (depending on category).
    """
    if BeautifulSoup is not None:
        url = 'http://onelinefun.com/'
        if tag:
            joke_url = url + str(tag) + '/'
        else:
            # Select a random tag from the list if one has not been provided
            joke_tag = random.randint(0, len(ONE_LINER_TAGS) - 1)
            joke_url = url + ONE_LINER_TAGS[joke_tag] + '/'

        response = web.http_get(url=joke_url)
        if response['content'] is not None:
            html = response['content']
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
        get_url = url % search_term
        response = web.http_get(get_url)

        if response['content'] is not None:
            html = response['content']
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
                return u'' + quotes[0]  # Result is returned in unicode.
            else:
                return None
        else:
            return None
    else:
        return None


# TODO: Jservice trivia.
def jservice_trivia():
    """
    Returns a random Jeopardy question from the http://jservice.io/ API.
    :return: dict{'title', 'value', 'question', 'answer', jeopardy_airdate'} or None on error.
    """
    base_url = 'http://jservice.io/'
    get_url = base_url + 'api/random'
    response = web.http_get(get_url, json=True)
    if response['json'] is not None:
        return {
            'title': response['json'][0]['category']['title'],
            'value': response['json'][0]['value'],
            'question': response['json'][0]['question'],
            'answer': response['json'][0]['answer'],
            'jeopardy_airdate': response['json'][0]['airdate']
        }
    else:
        return None
