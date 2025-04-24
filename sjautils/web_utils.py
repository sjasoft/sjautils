import requests

import http.client
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import validators

def is_url(what):
  return validators.url(what) == True


def url_soup(url, kind='html5'):
  return BeautifulSoup(requests.get(url).text, kind)

def get_server_status_code(url):
  """
  Download just the header of a URL and
  return the server's status code.
  """
  # http://stackoverflow.com/questions/1140661
  host, path = urlparse(url)[1:3]  # elems [1] and [2]
  try:
    conn = http.client.HTTPConnection(host)
    conn.request('HEAD', path)
    return conn.getresponse().status
  except Exception as e:
    return None


def check_url(url):
  """
  Check if a URL exists without downloading the whole file.
  We only check the URL header.
  """
  # see also http://stackoverflow.com/questions/2924422
  good_codes = [http.client.OK, http.client.FOUND, http.client.MOVED_PERMANENTLY]
  return get_server_status_code(url) in good_codes


class WebInterface(object):
  '''
  Purpose of this class is to provide restful calls to a webserver.  
  There are common patterns to consider including handling CSRF issues.
  Subclasses can specialize as needed or provide extra methods wrapping restful
  calls.
  '''
  def __init__(self, main_url, base_get, csrf_key='csrftoken'):
    '''
    General interaction with a single webserver across restful calls.
    :param main_url: the base url for getting to the webserver without trailing slash
    :param base_get: a GET target used only to obtain a csrf cookie from the server
    :param csrf_key: the cookie key the webserver uses for csrf return.  It can vary
    depending on type of server.  Here it is preset appropriately for DJANGO. 
    '''
    self._main_url = main_url
    self._session = requests.Session()
    self._csrf_key = csrf_key

  def _get_csrf(self, response):
    '''
    Gets the csrf token from a response.  Different backends 
    use different keys for that cookie.  Many types of backends
    require the csrf cookie to do a write method operations such as POST.
    
    :param response: the response to get the cookie from
    :return: 
    '''
    return response.cookies.get(self._csrf_key)

  def _setup_headers(self, base_get):
    response = self.get(base_get)
    self._session.headers['X-CSRFToken'] = self._get_csrf(response)

  def get(self, target, **query_params):
    return self._session.get(self.make_url(target), params=query_params)

  def make_url(self, target):
    return '/'.join([self._main_url, target])

  def post(self, target, json_data):
    url = self.make_url(target)
    return self._session.post(url, json=json_data)

  
