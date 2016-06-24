# -*- coding: utf-8 -*-

""" Auto Url (retrieval of the main title of a page)"""

# Original by Aida (Autotonic): https://github.com/Autotonic/
# Modified by TechWhizZ199: https://github.com/TechWhizZ199/

import requests
import re

# Set initial title tags/quoted title via regex.
title_tag_data = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
quoted_title = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)

# Set the maximum amount of bytes to be parsed from the request.
max_bytes = 655360  # Let's not break eh?


# Default chunk size is 512 but can be modified to 1024 for higher speeds if you have a higher download rate.
def auto_url(url, chunk_size=512, decode_unicode=True):
    """
    Auto Url method to request the title of a webpage.

    :param url: str the URL of the webpage to request the title for.
    :param chunk_size: int the chunk size to read the stream in.
    :param decode_unicode: bool True/False if unicode decoding should be performed.
    :return: str the title of the webpage that was requested.
    """
    
    header = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    response = requests.get(url, stream=True, headers=header)

    try:
        content = ''
        # With decode_unicode=True the unicode output will be given as a whole
        # e.g. [u'\u2605']. Whilst without this each character in the unicode would be saved as an indivual unicode
        # character e.g. [u'\xe2'][u'\x98'][u'\x85']. True is default.
        for byte in response.iter_content(chunk_size, decode_unicode):
            csd = ''
            for char in byte:
                # Produce a comma separated decimal and then turn it into unicode using the integer.
                csd = ord(char)
                individual = unichr(csd)
                # Append to the string or if it is unicode.
                try:
                    content += str(individual)
                except:
                    # 'str([individual)' (without quotes) instead will show the raw unicode in
                    # the title, without it being parsed by the interpreter.
                    content += individual
            if '</title>' in content or len(content) > max_bytes:
                break
    except UnicodeDecodeError:  # Keep a check on any unprecedented unicode errors.
        return
    finally:
        # Need to close the connection because we have not read all the data.
        response.close()

    # Clean up the title a bit
    content = title_tag_data.sub(r'<\1title>', content)
    content = quoted_title.sub('', content)

    start = content.find('<title>')
    end = content.find('</title>')
    if start == -1 or end == -1:
        return
    title = (content[start + 7:end])
    title = title.strip()[:200]

    title = ' '.join(title.split())
    return title or None

