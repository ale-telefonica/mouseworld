# -------------------------------
# Author: Alejandro Martin Herve
# Version: 1.0.0
# -------------------------------
# OSM API schema


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
        return self._http_handler.post(self.CREATE_SCHEMA, self.EXTRA_HEADER, data).json()

    def delete(self, id, *args, **kwargs):
        return self._http_handler.delete(f'{self.GET_SCHEMA}/{id}')

    
class Nsd(SCHEMA, object):
    """
    NSD schema class
    Class that contains the specific endpoints
    to execute nsd actions.
    """
    GET_SCHEMA = "nsd/v1/ns_descriptors"
    CREATE_SCHEMA = "nsd/v1/ns_descriptors_content"
    EXTRA_HEADER = {
        "Content-type":"application/gzip"
        }


class Vnfd(SCHEMA, object):
    """
    VNFD schema class
    Class that contains the specific endpoints
    to execute vnfd actions.
    """
    GET_SCHEMA = "vnfpkgm/v1/vnf_packages"
    CREATE_SCHEMA = "vnfpkgm/v1/vnf_packages_content"
    EXTRA_HEADER = {
        "Content-type":"application/gzip"
        }


class Nslcm(SCHEMA, object):
    """
    NS instantiation schema class
    Class that contains the specific endpoints
    to execute ns instances actions.
    """
    GET_SCHEMA = "nslcm/v1/ns_instances"
    CREATE_SCHEMA = "nslcm/v1/ns_instances_content"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }


class Vims(SCHEMA, object):
    """
    VIM schema class
    Class that contains the specific endpoints
    to execute vim actions.
    """
    GET_SCHEMA = "admin/v1/vims"
    CREATE_SCHEMA = "admin/v1/vim_accounts"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }


class Auth(SCHEMA, object):
    """
    Auth schema class
    Class that contains the specific endpoints
    to execute authorization actions.
    """
    GET_SCHEMA = "admin/v1/tokens"
    CREATE_SCHEMA = "admin/v1/tokens"
    EXTRA_HEADER = {
        "Content-type":"application/json"
        }