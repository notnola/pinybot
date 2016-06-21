# -*- coding: utf-8 -*-

import os
import random
import time
import web_request
import html_reload


def htmloutput(webserver_url, PATH, html_message=''):
    """
    
    :param webserver_url:
    :param PATH:
    :param html_message:
    """
    if os.path.exists(PATH + 'recaptcha_data/recaptcha.txt'):
        print 'file exists, removing it'
        os.remove(PATH + 'recaptcha_data/recaptcha.txt')
    print 'creating new recaptcha text file'
    r = open(PATH + 'recaptcha_data/recaptcha.txt', 'w+')
    print 'opened new file'
    r.writelines(html_message)
    print 'wrote lines'
    r.close()
    print 'closed file succesfully, now reloading the index page appropriately'
    html_reload.main(webserver_url, PATH)


def recaptcha(proxy=None):
    """
    Check recaptcha. We will use our default browser to open the recaptcha challenge to solve.
    The return cookies is not used in the code, as request session will take care of it for us.
    
    :param proxy:
    :return: cookies dict (only used for debugging purposes)
    """
    t = str(random.uniform(0.9, 0.10))
    url = 'http://tinychat.com/cauth/captcha?%s' % t
    response = web_request.get_request(url, json=True, proxy=proxy)
    print response
    if response is not None:
        return response


def webserver_captcha(webserver_url, PATH):
    """
    Saving a recaptcha request (link) to the webserver's page.
    
    :param webserver_url:
    :param PATH:
    """
    new_recaptcha = recaptcha()
    print 'got new recaptcha'
    if new_recaptcha['content']['need_to_solve_captcha'] == 0:
        html_message = 'No need to solve a Recaptcha.'
        print html_message
        htmloutput(webserver_url, PATH, html_message)

    elif new_recaptcha is None:
        html_message = 'An error occured whilst fetching the recaptcha, please try again later.'
        print html_message
        htmloutput(webserver_url, PATH, html_message)

    else:
        html_message = 'http://tinychat.com/cauth/recaptcha?token=%s' % new_recaptcha['content']['token']
        print html_message
        htmloutput(webserver_url, PATH, html_message)

        while True:
            time.sleep(60)
            new_recaptcha = recaptcha()
            if new_recaptcha['content']['need_to_solve_captcha'] == 0:
                html_message = 'Solved Recaptcha.'
                print html_message
                htmloutput(webserver_url, PATH, html_message)
                break

            elif new_recaptcha is None: #2
                html_message = 'An error occured..'
                print html_message
                htmloutput(webserver_url, PATH, html_message)

            else:
                html_message = 'http://tinychat.com/cauth/recaptcha?token=%s' % new_recaptcha['content']['token']
                print html_message
                htmloutput(webserver_url, PATH, html_message)
    return 'OK'


def main(webserver_url, PATH):
    print('Loading Recaptcha HTML page and updating files...') # To remove

    if len(PATH) is 0:
        # PATH = str(os.path.join(os.path.dirname(__file__))) + '/WEBSERVER'
        PATH = str(os.path.dirname(os.path.abspath(__file__)))
        print 'Set path to:', PATH

    print('requesting index page') # To remove
    OK = webserver_captcha(webserver_url, PATH)
    if OK != 'OK':
        html_message = 'An error occurred. Aborted (possibly?).'
        htmloutput(webserver_url, PATH, html_message)
        print('An error occured. Aborting...')
        quit()
