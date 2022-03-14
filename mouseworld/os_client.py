import requests
import openstack
import json

import _http
import os_api as api


def http(service=""):
    def decorator(method):
        def wrapper(self):
            url = self._get_endpoint(service)
            self.http_handler = _http.HTTP(url, schema="Openstack")
            token = self.conn.identity.get_token()
            AUTH_HEADER = {'X-Auth-Token': token}
            self.http_handler.add_auth_header(AUTH_HEADER)
            return method(self)
        return wrapper
    return decorator


class OpenstackClient:
    """
    Client specific app to make specific request to Openstack API
    """
    def __init__(self, **credentials):
        # Load environmental variables
        # This credentials must be valid.
        self.USER = credentials["OS_USERNAME"]
        self.PASSWD = credentials["OS_PASSWORD"]
        self.USER_DOMAIN = credentials["OS_USER_DOMAIN_NAME"]
        self.PROJECT_DOMAIN = credentials["OS_PROJECT_DOMAIN_NAME"]
        self.AUTH_URL = credentials["OS_AUTH_URL"]
        self.PROJECT_NAME = credentials["OS_PROJECT_NAME"]

        self.http_handler = None

    def connect(self):
        # Connect to openstack API, using openstack sdk
        try:
            self.conn = openstack.connect(
                auth_url=self.AUTH_URL,
                username=self.USER,
                password=self.PASSWD,
                user_domain_id=self.USER_DOMAIN.lower(),
                project_domain_id=self.PROJECT_DOMAIN.lower(),
                project_name=self.PROJECT_NAME
            )
            self.token = self.conn.identity.get_token()
            self.__load_headers()
            
        except Exception as e:
            print(e)
            exit(1)
    
    
    def _get_endpoint(self, service_type:str) -> str:
        preendpoint = self.conn.endpoint_for(service_type)
        r = requests.get(preendpoint, headers=self.headers)
        if service_type == "compute" or  service_type == "identity": 
            endpoint = r.json()['version']['links'][0]["href"]
        else:
            endpoint = r.json()['versions'][0]['links'][0]["href"]
        return endpoint

    def __load_headers(self):
        self.headers = {'Content-type': 'application/json',  'X-Auth-Token': self.token}

    @property
    def projects(self) -> list:
        return [p.name for p in self.conn.identity.projects()]

    def create_project(self, project_name, description="Project created by OSM"):
        # In development
        # data = {
        #     "project": {
        #         "description": description,
        #         "domain_id": self.PROJECT_DOMAIN,
        #         "enabled": True,
        #         "is_domain": False,
        #         "name": project_name}
        raise NotImplemented

    def project_exist(self, project_name:str) -> bool:
        return project_name in self.projects
    
    def image_exists(self, name:str) -> bool:
        return True if self.conn.get_image_id(name) else False

    def create_new_image(self, name, filename=None, container_format='bare', disk_format='qcow2', server_name=None, from_server=False):
        if from_server:
            # This part is not going to be available yet because it takes a long time
            # depending on the server size to create the image. Image can only be created for now
            # from scratch
            
            # Create image from server
            # if not server_name:
            #     raise Error("If you are creating an image from a server you must provide a server name in your project")
            # server_id = self.conn.get_server_id(server_name)
            # image_obj = self.conn.compute.create_server_image(server_id, name)
            raise(NotImplemented)
        else:
            if not filename:
                raise(Exception("If you are not creating image from server, you must provide a file"))
            image_obj = self.conn.create_image(name, filename=filename, container_format=container_format, disk_format=disk_format)
        return image_obj

    def create_mirror(self, mirror):
        source = mirror['source']
        dest = mirror['dest']
        direction = mirror['direction']
        source_id = self._get_port_id(source)
        dest_id = self._get_port_id(dest)

        service_data = json.dumps({"tap_service":{
            "description": "Tap service created by Mouseworld",
            "name": dest,
            "port_id": dest_id,
        }})

        tap_service = self.tap_service().create(service_data)['tap_service']

        flow_data = json.dumps({"tap_flow":{
            "description": "Tap flow created by Mouseworld",
            "name": source,
            "source_port": source_id,
            "direction": direction,
            "tap_service_id": tap_service['id'],
        }})
        
        self.tap_flow().create(flow_data)


    def _get_port_id(self, port_name):
        port_id = (list(self.conn.network.ports(name=port_name, fields=['id'])))[0]
        return port_id.id

    @http("network")
    # This request goes over http not standard openstack sdk calls
    def tap_service(self):
        return api.Tap_Service(self.http_handler)
    
    @http("network")
    # This request goes over http not standard openstack sdk calls
    def tap_flow(self):
        return api.Tap_Flow(self.http_handler)
        
    def close(self):
        self.conn.close()
    


if __name__ == "__main__":
    # Test this setion
    from mouseworld import Config
    from settings import OS_ACCESS_FILE, CONFIG_DIR

    os_config = Config(OS_ACCESS_FILE, CONFIG_DIR, _type='Openstack')
    client = OpenstackClient(**os_config.config)

    client.connect()
    # print(client.image_exists("ubuntu2004"))


    # Test taap api
    # print(client.tap_service().list())
    # import requests
    # token = client.conn.identity.get_token()
    # net_endpoint = client._get_endpoint("network")
    # headers = {'Accept': "Application/json", 'X-Auth-Token': token}
    # r = requests.get("/".join([net_endpoint, "taas/tap_services"]), headers=headers)
    # print(r.json())
    client.close()
# USER = credentials["OS_USERNAME"]
# PASSWD = credentials["OS_PASSWORD"]
# USER_DOMAIN = credentials["OS_USER_DOMAIN_NAME"]
# PROJECT_DOMAIN = credentials["OS_PROJECT_DOMAIN_NAME"]
# AUTH_URL = credentials["OS_AUTH_URL"]
# PROJECT_NAME = credentials["OS_PROJECT_NAME"]