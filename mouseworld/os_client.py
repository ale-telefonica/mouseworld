import requests
import openstack

# import _http
# import os_api as api

# Authentication data in json format, in case of api update modify only this dict keeping the wildcars (<wildcard>)
# auth_data = {"auth": {"identity": {"methods": ["password"], "password": {"user": {"name": "<username>", "password": "<password>", "domain": {"id": "<user_domain_id>"}}}}, 
#                 "scope": { "project": {"domain": {"id": "<project_domain_id>"},"name": "<project_name>"}}}}

class OpenstackClient:
    """
    Client specific app to make specific request to Openstack API
    """
    def __init__(self, **credentials):
        # Load environmental variables
        # This credentials must be valid.
        self.USER = credentials["OS_USERNAME"]
        self.PASSWD = credentials["OS_PASSWORD"]
        self.USER_DOMAIN = credentials["OS_USER_DOMAIN_NAME"].lower()
        self.PROJECT_DOMAIN = credentials["OS_PROJECT_DOMAIN_ID"]
        self.AUTH_URL = credentials["OS_AUTH_URL"]
        self.PROJECT_NAME = credentials["OS_PROJECT_NAME"]

    def connect(self):
        # Connect to openstack API, using openstack sdk
        try:
            self.conn = openstack.connect(
                auth_url=self.AUTH_URL,
                username=self.USER,
                password=self.PASSWD,
                user_domain_id=self.USER_DOMAIN,
                project_domain_id=self.PROJECT_DOMAIN,
                project_name=self.PROJECT_NAME
            )
            self.token = self.conn.identity.get_token()
            
        except Exception as e:
            print(e)
    
        self.__load_headers()
    
    def __get_endpoint(self, service_type:str) -> str:
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
        return True if  self.conn.get_image_id(name) else False

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

    def close(self):
        self.conn.close()


if __name__ == "__main__":
    from constructor import Config
    from settings import OS_ACCESS_FILE, CONFIG_DIR

    os_config = Config(OS_ACCESS_FILE, CONFIG_DIR)
    client = OpenstackClient(**os_config.config)

    client.connect()
    print(client.image_exists("ubusntu2004"))
    client.close()