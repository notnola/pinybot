# -*- coding: utf-8 -*-

import requests
import re
import urllib

# TODO Unicode support, example URL with unicode https://youtu.be/SJzyaXO53Sc DONE!
# TODO add exclusion_char to ignore URLs
#     exclusion_car = "!"

title_tag_data = re.compile('<(/?)title( [^>]+)?>', re.IGNORECASE)
quoted_title = re.compile('[\'"]<title>[\'"]', re.IGNORECASE)

max_bytes = 655360  # Let's not break eh?


def auto_url(url, chunk_size=512, decode_unicode=True): # Default chunk size is 512 but can be modified to 1024 for higher speed
    
    header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:44.0) Gecko/20100101 Firefox/44.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Referer': ' '
    }
    response = requests.get(url, stream=True, headers=header)
    try:
        content = ''
        for byte in response.iter_content(chunk_size, decode_unicode): # With decode_unicode=True the unicode output will be given as a whole
            csds = ''                                                  # e.g. [u'\u2605']. Whilst without this each character in the unicode would be
            for char in byte:                                          # saved as an indivual unicode character e.g. [u'\xe2'][u'\x98'][u'\x85']. True is default.
                #print(str(ord(char)))
                # Produce a comma separated decimal and then turn it into unicode using the integer
                csd = ord(char)
                individual = unichr(csd)
                #print individual
                # Append to the string or if it is unicode
                try:
                    content += str(individual)
                except:
                    content += individual # 'str([individual)' (without quotes) instead will show the raw unicode in the title, without it being parsed by the interpreter.
            if '</title>' in content or len(content) > max_bytes:
                break
    except UnicodeDecodeError: # Keep a check on any unprecedented unicode errors anyhow
        return # R.I.P.
    finally:
        # Need to close the connection because we have not read all the data
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
    #title = urllib.unquote(title.decode("utf8"))

    title = ' '.join(title.split())

    #title = urllib.unquote(urllib.quote(title.encode("utf_8"))).decode("utf_8")
    #print(title)
    #title = title.replace("&quot;", '"')


    return title or None

#print auto_url('https://github.com/oddballz/')