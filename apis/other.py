# -*- coding: utf-8 -*-

""" Provides functions to search/explore various APIs. """

# Some examples include that of:
#   World-weather-online,
#   Urban-dictionary,
#   ip-api and api.icndb,
# Includes BeautifulSoup parsed APIs/website functions.

import random
import unicodedata
import urllib

from utilities import web, string_utili

try:
    from bs4 import BeautifulSoup
    bs4_present = True
except (ImportError, BeautifulSoup):
    bs4_present = False

ONE_LINER_TAGS = ['age', 'alcohol', 'animal', 'attitude', 'beauty', 'black', 'car', 'communication',
                  'dirty', 'doctor', 'drug', 'family', 'fighting', 'flirty', 'food', 'friendship', 'happiness',
                  'health', 'insults', 'intelligence', 'IT', 'kids', 'life', 'love', 'marriage', 'men', 'mistake',
                  'money', 'motivational', 'motorcycle', 'new', 'people', 'political', 'puns', 'retirement', 'rude',
                  'sarcastic', 'school', 'sport', 'stupid', 'success', 'time', 'travel', 'work']


def urban_dictionary_search(search):
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
    api_key = ''  # Place the API key necessary here.
    if api_key:
        weather_api_url = 'http://api.worldweatheronline.com/free/v2/weather.ashx?q=%s&format=json&key=%s' %\
                          (city.strip(), api_key)
        response = web.http_get(weather_api_url, json=True)

        if response['json'] is not None:
            try:
                pressure = response['json']['data']['current_condition'][0]['pressure']
                temp_celsius = response['json']['data']['current_condition'][0]['temp_C']
                temp_fahrenheit = response['json']['data']['current_condition'][0]['temp_F']
                query = response['json']['data']['request'][0]['query'].encode('ascii', 'ignore')

                cloud_cover = response['json']['data']['current_condition'][0]['cloudcover']
                sunrise = response['json']['data']['weather'][0]['astronomy'][0]['sunrise']
                sunset = response['json']['data']['weather'][0]['astronomy'][0]['sunset']
                weather_info = '*Queried location:* %s. *Temperature:* %sC (%sF), *Pressure:* %s millibars, ' \
                               '*Cloud cover:* %s%%, *Sunrise:* %s, *Sunset:* %s.' % \
                               (query, temp_celsius, temp_fahrenheit, pressure, cloud_cover, sunrise, sunset)
                return weather_info
            except (IndexError, KeyError) as ex:
                print(ex)
                return None
        else:
            return None
    else:
        return False


def who_is(ip):
    """
    Searches ip-api for information about a given IP address.
    :param ip: str the ip to search for.
    :return: str information or None on error.
    """
    url = 'http://ip-api.com/json/%s' % ip.strip()
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


# TODO: Implement categories, and character name functionality.
def chuck_norris():
    """
    Finds a random Chuck Norris joke/quote from http://www.icndb.com/api/ .
    NOTE:  The API also has category specifications, i.e. categories are either 'nerdy'/'explicit' set
           via the web-form '?limitTo'. The character names can also be altered via passing the web-form
           '?firstName=[name]' or '?lastName=[name]'.

    :return: str joke or None if 'joke' is not found.
    """
    url = 'http://api.icndb.com/jokes/random/?escape=javascript'
    response = web.http_get(url, json=True)

    if response['json'] is not None:
        if response['json']['type'] == 'success':
            return response['json']['value']['joke'].decode('string_escape')
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
    url = 'http://md5cracker.org/api/api.cracker.php?r=9327&database=md5cracker.org&hash=%s' % hash_str.strip()
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
    :return: joke str or None if no 'joke' is found.
    """
    url = 'http://api.yomomma.info/'
    response = web.http_get(url, json=True)

    if response['json'] is not None:
        return response['json']['joke'].decode('string_escape')
    else:
        return None


def online_advice():
    """
    Retrieves a random string of advice from the 'adviceslip' (http://adviceslip.com/) API.
    :return: advice str or None if 'advice' is not found.
    """
    url = 'http://api.adviceslip.com/advice'
    response = web.http_get(url, json=True)
    if response['json'] is not None:
        return response['json']['slip']['advice']
    else:
        return None


# TODO: Parse all the required necessary information returned from the API;
#       more clear output from function.
def duck_duck_go_search(search):
    """
    Search DuckDuckGo using their API (https://duckduckgo.com/api).

    :param search: The search term str to search for.
    :return: definition str or None on no match or error.
    """
    duck_duck_go_api = 'http://api.duckduckgo.com/?q=%s&ia=answer&format=json&no_html=1' % \
                       urllib.quote_plus(search.strip())
    response = web.http_get(duck_duck_go_api, json=True)

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
    :return: str title, rating, and short a description.
    """
    omdb_url = 'http://www.omdbapi.com/?t=%s&plot=short&r=json' % search.strip()
    response = web.http_get(omdb_url, json=True)

    if response['json'] is not None:
        try:
            title = response['json']['Title']
            plot = response['json']['Plot']
            imdb_id = response['json']['imdbID']
            imdb_rating = response['json']['imdbRating']
            if len(plot) > 159:
                plot_chunks = string_utili.chunk_string(plot, 70)
                plot_formatted = ''
                for i in range(0, 2):
                    plot_formatted += ('\n' + plot_chunks[i])
            else:
                plot_formatted = plot

            omdb_info = '*Title:* %s\nDetails: %s\n*Rating:* %s\n*More Info:* http://www.imdb.com/title/%s' % \
                        (title, plot_formatted, imdb_rating, imdb_id)

            return omdb_info
        except (KeyError, IndexError) as ex:
            print(ex)
            return None
    else:
        return None


# TODO: Implement Jservice trivia.
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


# TODO: Parse this correctly.
def longman_dictionary(lookup_term):
    """
    Looks up a particular headword on the Pearson Longman Dictionary API
    (http://http://developer.pearson.com/apis/dictionaries) and returns an appropriate definition.

    NOTE: The API is free for up to 4,000,000 calls per month. We are using the 'entries' API endpoint
          located by using http://api.pearson.com/v2/dictionaries/entries?headword=[headword here].

    :param lookup_term: str the term to search for a dictionary reference.
    :return:
    """
    dictionary_url = 'http://api.pearson.com/v2/dictionaries/entries?headword=%s' % lookup_term.strip()
    response = web.http_get(dictionary_url, json=True)

    if response['json'] is not None:
        definitions = []
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


# These APIs require the use of Requests, BeautifulSoup, urllib2 and unicodedata.
# As a result of using HTML parsers, the code maybe subject to change over time to adapt with the server's pages.
def time_is(location):
    """
    Retrieves the time in a location by parsing the time element in the html from Time.is .
    :param location: str location of the place you want to find time (works for small towns as well).
    :return: time str or None on failure.
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

        post_url = 'http://time.is/' + location.replace(location[0], location[0].upper())
        time_data = web.http_get(post_url, header=header)
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


# TODO: Allow time to reply with AM/PM.
def google_time(location):
    """
    Retrieves the time in a location using Google.
    :param location: str location of the place you want to find time (Location must be a large town/city/country).
    :return: time str or None on failure.
    """
    if bs4_present:
        url = 'https://www.google.com/search?q=time%20in%20' + urllib.quote_plus(location)
        response = web.http_get(url)
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


def top40():
    """
    Retrieves the Top40 songs list from www.bbc.co.uk/radio1/chart/singles.
    :return: list (nested list) all songs including the song name and artist in the format
             [[songs name, song artist], etc.]].
    """
    if bs4_present:
        chart_url = 'http://www.bbc.co.uk/radio1/chart/singles'
        response = web.http_get(url=chart_url)

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
            for x in range(len(all_titles)):
                songs.append([all_titles[x], all_artists[x]])

            if len(songs) is not 0:
                return songs
    return None


def one_liners(tag=None):
    """
    Retrieves a one-liner from http://onelinefun.com/ (by selecting a random category).
    :param tag: str a specific tag name from which you want to choose a joke from.
    :return: str joke a one line joke/statement (depending on the specified category).
    """
    if bs4_present:
        url = 'http://onelinefun.com/'
        if tag is None:
            # Select a random tag from the list if one has not been provided.
            joke_tag = random.randint(0, len(ONE_LINER_TAGS) - 1)
            joke_url = url + ONE_LINER_TAGS[joke_tag] + '/'
        else:
            joke_url = url + str(tag) + '/'

        response = web.http_get(url=joke_url)
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
        response = web.http_get(etymonline_url)

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
