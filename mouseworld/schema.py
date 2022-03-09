class SCHEMA(object):
    """
    Metaclass that specify the general methods to query the different 
    resources in OSM and Openstack APIs.
    """
    CONTENT_TYPE = {
        "Content-type":"application/json"
        }

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
        return self._http_handler.post(self.CREATE_SCHEMA, self.CONTENT_TYPE, data, *args, **kwargs).json()

    def delete(self, id, *args, **kwargs):
        return self._http_handler.delete(f'{self.GET_SCHEMA}/{id}')