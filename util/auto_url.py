# -*- coding: utf-8 -*-

""" Auto Url (retrieval of the main title of a page)"""

# Original idea developed from Sopel-IRC: https://github.com/sopel-irc/sopel/
# Original template: Aida (Autotonic): https://github.com/Autotonic/
# Modified by GoelBiju: https://github.com/GoelBiju/

# TODO: Adjust to work with the other libraries.
import requests
import re

# Set initial title tags/quoted title via regex.
title_tag_data = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
quoted_title = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)

# Set the maximum amount of bytes to be parsed from the request.
max_bytes = 655360


# Default chunk size is 512 but can be modified to 1024 for higher speeds if you have a higher download rate.
def auto_url(url, restrict_domain=None, chunk_size=512, decode_unicode=True):
    """
    Automatic URL method to request the title of a web-page.

    :param url: str the URL of the web-page to request the title for.
    :param restrict_domain: str the web domain to check for in the url, if the domain is not present then
                            auto URL will not process the URL e.g. "www.google.com" or simply a keyword "google".
    :param chunk_size: int the chunk size to read the stream in.
    :param decode_unicode: bool True/False if unicode decoding should be performed.
    :return title: str the title of the web-page that was requested or None if no title was found.
    """
    # Try checking if a restriction on the URL domain is applied or not.
    if restrict_domain is not None:
        if restrict_domain not in url:
            return None

    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }

    try:
        response = requests.get(url, headers=header, stream=True)
    except (Exception, requests.RequestException) as ex:
        print(ex)
        return None

    content = u''
    try:
        # TODO: Remove part of this since it isn't actually helpful.
        # With decode_unicode=True the unicode output will be given as a whole e.g. [u'\u2605'].
        # Whilst without this, each character in the unicode would be saved as an individual character
        # as an example: [u'\xe2'][u'\x98'][u'\x85'].
        for byte in response.iter_content(chunk_size, decode_unicode):
            byte = byte.strip()
            for char in byte:
                # Produce a comma separated decimal and then turn it into unicode using the integer.
                csd = ord(char)
                individual = unichr(csd)
                # Append to the unicode content.
                content += u'' + individual

            if '</title>' in content or len(content) > max_bytes:
                break

    # Keep a check on any unprecedented unicode errors.
    except UnicodeDecodeError:
        return None
    finally:
        # We need to close the connection because we have not read all the data.
        # web._request_session.close()
        response.close()

    # Clean up the title.
    content = title_tag_data.sub(r'<\1title>', content)
    content = quoted_title.sub('', content)

    start = content.find('<title>')
    end = content.find('</title>')

    if start is not -1 or end is not -1:
        raw_title = content[start + 7:end]
        clean_title = raw_title.strip()[:200]
        title = ' '.join(clean_title.split())

        return title or None
    else:
        return None
