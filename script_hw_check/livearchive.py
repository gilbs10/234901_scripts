""" 
OnlineJudgeConnection implementation: Allows the submission of problems to ICPC/UVa online judges
Eden Saig (edens@cs) - 2015-2017
"""

import re
from bs4 import BeautifulSoup
import http.cookiejar
import urllib.request
import urllib.parse

class OnlineJudgeConnection(object):
    def __init__(self, username, password, verbose=True):
        # http related
        self._cj = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self._cj))
        self._opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')]
        self._verbose = verbose
        # log in
        login_result = self._log_in(username, password)

    def _get_url(self, url, data=None):
        if not url.startswith('http'):
            url = self.base_url + url
        if data is not None:
            data = urllib.parse.urlencode(data).encode('ascii')
        r = self._opener.open(url, data)
        return r
        
    def _get_soup(self, url, data=None):
        r = self._get_url(url, data)
        html_data = r.read()
        return BeautifulSoup(html_data,'html.parser')

    def _log_in(self, username, password):
        " Log into the website "
        s=self._get_soup(self.base_url)
        # fill login form
        login_form = self._get_login_form(s)
        form_inputs = login_form.find_all('input')
        login_data = {inp['name']: inp.get('value') for inp in form_inputs
                      if 'name' in inp.attrs}
        login_data['username'] = username
        login_data['passwd'] = password
        # submit and return
        login_action=login_form['action']
        login_result=self._get_soup(login_action, login_data)
        self._check_login_result(login_result)
        return login_result

    def quick_submit(self, problem_id, code_str, language='C++'):
        s = self._get_soup('index.php?option=com_onlinejudge&Itemid=25')
        submit_form = self._get_submit_form(s)
        form_inputs = submit_form.find_all('input')
        submit_data = {inp['name']: inp.get('value') for inp in form_inputs
                       if 'name' in inp}
        # fill submit form
        #submit_data.pop('codeupl')
        submit_data['localid'] = str(problem_id)
        submit_data['language'] = '5' # C++11
        submit_data['code'] = code_str
        # submit and return
        form_action = submit_form['action']
        result = self._get_url(form_action, submit_data)
        result_urlparams = urllib.parse.parse_qs(
            urllib.parse.urlparse(result.geturl()).query
        )
        result_message = result_urlparams['mosmsg'][0]
        if self._verbose:
            print('Submitting %s:' % problem_id, result_message)
        problem_id_st = re.findall('\d+',result_message)
        if problem_id_st:
            return int(problem_id_st[0])
        else:
            raise RuntimeError(result_message)

    def my_submissions(self, limit=100, page=0):
        s = self._get_soup('index.php?option=com_onlinejudge&Itemid=9&limit=%d&limitstart=%d' \
                           % (limit, limit*page) )
        rows = self._get_my_submissions_rows(s)
        titles = [td.text for td in rows[0].find_all('td','title')]
        titles[0] = 'Submission ID'
        titles[1] = 'Problem ID'
        data = {}
        for row in rows[1:]:
            row_data = {title: td.text for title,td
                        in zip(titles, row.find_all('td'))}
            if 'Verdict' not in row_data:
                raise ValueError('Row data is missing')
            data[int(row_data['Submission ID'])] = row_data
        return data


class LiveArchiveConnection(OnlineJudgeConnection):
    base_url = 'https://icpcarchive.ecs.baylor.edu/'

    def _get_login_form(self,s):
        return s.find_all('form','cbLoginForm')[0]

    def _check_login_result(self, login_result):
        if not login_result.find_all('span',id='mod_login_greeting'):
            raise RuntimeError('Login Error')
        elif self._verbose:
            print('Livearchive logged in:', \
                  login_result.find_all('span',id='mod_login_greeting')[0].text)

    def _get_submit_form(self,s):
        return s.find_all('td','maincontent')[0].form

    def _get_my_submissions_rows(self,s):
        return s.find_all('td','maincontent')[0].table.find_all('tr')


class UVAConnection(OnlineJudgeConnection):
    base_url = 'https://onlinejudge.org/'

    def _get_login_form(self,s):
        return s.find_all('form',id='mod_loginform')[0]

    def _check_login_result(self, login_result):
        if not login_result.find_all('a',string='Logout'):
            raise RuntimeError('Login Error')
        elif self._verbose:
            print('UVA Logged in')

    def _get_submit_form(self,s):
        return s.find_all('div',id='col3_content_wrapper')[0].form

    def _get_my_submissions_rows(self,s):
        return s.find_all('div',id='col3_content_wrapper')[0].table.find_all('tr')

    
