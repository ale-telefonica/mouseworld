'''
Client to interact with Openstack Xena API

TODO: Cambiar código para adpatarlo a la API de openstack.
For this client is only needed for now the compute:image schema
'''


class SCHEMA(object):
    """
    Metaclass that specify the general methods to query the different 
    resources in the OSM NBI API.
    """
    def __init__(self, http_handler):
        """
        Constructor
        :http_handler: Object of type _http.HTTP that contains
        the required information to access the API.
        """
        self._http_handler = http_handler

    def list(self, *args, **kwargs):
        return self._http_handler.get(self.GET_SCHEMA)

    def show(self, id, *args, **kwargs):
        return self._http_handler.get(f'{self.GET_SCHEMA}/{id}')

    def create(self, data, *args, **kwargs):
        return self._http_handler.post(self.CREATE_SCHEMA, self.EXTRA_HEADER, data)

    def delete(self, id, *args, **kwargs):
        return self._http_handler.delete(f'{self.GET_SCHEMA}/{id}')

class Compute(SCHEMA, object):
    """
    Compute schema class
    Class that contains the specific endpoints
    to execute compute actions.
    """
    GET_SCHEMA = "nsd/v1/ns_descriptors"
    CREATE_SCHEMA = "nsd/v1/ns_descriptors_content"
    EXTRA_HEADER = {
        "Content-type":"application/gzip"
        }
        

class Auth(SCHEMA, object):
    """
    Auth schema class
    Class that contains the specific endpoints
    to execute authorization actions.
    """
    GET_SCHEMA = "auth/tokens"
    CREATE_SCHEMA = "auth/tokens"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }

class Projects(SCHEMA, object):
    """
    Auth schema class
    Class that contains the specific endpoints
    to execute authorization actions.
    """
    GET_SCHEMA = "auth/tokens"
    CREATE_SCHEMA = "auth/tokens"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }

class TAAS(SCHEMA, object):
    """
    Auth schema class
    Class that contains the specific endpoints
    to execute authorization actions.
    """
    GET_SCHEMA = "auth/tokens"
    CREATE_SCHEMA = "auth/tokens"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }