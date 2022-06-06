# HTTP handler to make requests

# Imports
import requests

class HTTP(object):
    """
    Class to interact with the OSM API

    :DEFAULT_HTTP_HEADER: Minimum header to use in every request
    """
    DEFAULT_HTTP_HEADER = {
        'Accept':  'application/json',
        }
    def __init__(self, url, user="", password="", schema=""):
        self._url = url
        self._user = user
        self._password = password
        self._http_header = self.DEFAULT_HTTP_HEADER
        self.auth_info = None
        self.schema = schema
    
    @property
    def authenticated(self):
        return self.auth_info is not None

    def add_auth_header(self, auth_header):
        self._http_header.update(auth_header)
        return

    def get(self, endpoint, *args, **kwargs):
        """
        Execute requests get method
        """
        response = requests.get('/'.join([self._url, endpoint]), headers=self._http_header, verify=False)
        
        if response.ok:  
            return response.json()
        else:
            raise requests.HTTPError("Status code:", response.status_code)

    def post(self, endpoint, content_type,  data, *args, **kwargs):
        """
        Execute requests post method
        """
        self._http_header.update(content_type)
        response = requests.post('/'.join([self._url, endpoint]), headers=self._http_header, data=data, verify=False)
        
        if response.ok:  
            return response
        else:
            raise requests.HTTPError(response.json())

    def delete(self, endpoint, *args, **kwargs):
        """
        Execute requests delete method
        """
        response = requests.delete('/'.join([self._url, endpoint]), headers=self._http_header, verify=False)
        if response.ok:  
            return response.json()
        else:
            raise requests.HTTPError("Status code:", response.status_code)