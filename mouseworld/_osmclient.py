# Author: Alejandro Martin Herve
# Version: 1.0.0

# TODO: Remove decorator on every method and authenticate at the begining of
# object creation to reduce overhead.

"""
Documentación
"""

# Imports
# import os
import json
from datetime import datetime as dt

from settings import OPENSTACK_MANAGEMENT_NETWORK
import osm_api_schema as api
import _http

from requests.exceptions import HTTPError
from urllib3.exceptions import InsecureRequestWarning
import warnings
warnings.filterwarnings("ignore", category=InsecureRequestWarning) 


class OSMClient(object):
    """
    Small client to interact with OSM North Bound Interface
    """

    def __init__(self, **credentials):
        self.username = credentials["OSM_USER"]
        self.password = credentials["OSM_PASSWORD"]
        self.http_handler = None
        self.auth_info = None
        self.hostname = f'https://{credentials["OSM_URL"]}/osm'

    def _is_authenticated(method):
        # Decorator that ensures authentication for every request
        def wrapper(self):
            if self.auth_info:
                expires = self.auth_info["expires"]
                if expires > dt.now().timestamp():
                    return method(self)
            print("No authenticated")
            self.authenticate()
            return method(self)
        return wrapper

    def authenticate(self):
        # Method to authenticate agains de API
        data = {"username": self.username, "password": self.password}
        data = json.dumps(data)
        try:
            self.http_handler = _http.HTTP(
                self.hostname, user=self.username, password=self.password, schema="OSM")
            content = api.Auth(self.http_handler).create(data)
            if "id" in content:
                self.auth_info = content
                self.http_handler.auth_info = self.auth_info
                AUTH_HEADER = {
                    'Authorization': f'Bearer {self.http_handler.auth_info["id"]}'}
                self.http_handler.add_auth_header(AUTH_HEADER)
            else:
                raise Exception("Authentication error")
        except Exception as e:
            raise(e)

    def vim_exists(self, name):
        # Check if xonection with VIM exist in OSM
        return name in (vim['name'] for vim in self.vims().list())

    def get_vim_id(self, name):
        return [vim['_id'] for vim in self.vims().list() if vim['name'] == name]

    def get_id(self, name, _type):
        obj = getattr(self, _type)
        print(obj().list())
        # return [resource['_id'] for resource in obj().list() if resource['name'] == name]
    
    def create_pkg(self, pkg, _type, scenario):
        try:
            with open(pkg, 'rb') as stream:
                if _type == "nsd":
                    id = self.nsd().create(stream)['id']
                elif _type == "vnfd":
                    id = self.vnfd().create(stream)['id']
                return id
        except HTTPError as http_e:
            if http_e.args[0]['code'] == "CONFLICT":
                print("NS package already exist, not creating")
                return self.get_id(scenario, _type)
        except Exception as e:
            raise(e)

    def create_nsd_pkg(self, nspkg, scenario):
        print("Creating NS package...")
        return self.create_pkg(nspkg, 'nsd', scenario)

    def create_vnfd_pkg(self, nspkg, scenario):
        print("Creating VNF package...")
        return self.create_pkg(nspkg, 'vnfd', scenario)  

    def create_vim(self, os_config):
        # Method to assemble vim data
        # :os_config: Object of type Config
        # :return: json response with de result of the vim creation
        vim_data = {
            "name": os_config.OS_PROJECT_NAME,
            "description": f"OSM conection with Openstack project {os_config.OS_PROJECT_NAME}",
            "vim_type": "openstack",
            "vim_url": os_config.OS_AUTH_URL,
            "vim_tenant_name": os_config.OS_PROJECT_NAME,
            "vim_user": os_config.OS_USERNAME,
            "vim_password": os_config.OS_PASSWORD,
            "config": {
                "management_network_name": OPENSTACK_MANAGEMENT_NETWORK
            }
        }
        return self.vims().create(json.dumps(vim_data))
    
    def close(self):
        return self.delete_token().delete(self.auth_info["id"])

    @_is_authenticated
    def nsd(self):
        return api.Nsd(self.http_handler)
    
    @_is_authenticated
    def vnfd(self):
        return api.Vnfd(self.http_handler)

    @_is_authenticated
    def nslcm(self):
        return api.Nslcm(self.http_handler)
    
    @_is_authenticated
    def vims(self):
        return api.Vims(self.http_handler)

    @_is_authenticated
    def delete_token(self):
        return api.Auth(self.http_handler)

    _is_authenticated = staticmethod( _is_authenticated )

    


if __name__ == "__main__":
    from constructor import Config
    from settings import OS_ACCESS_FILE, CONFIG_DIR

    osm_config = Config(OS_ACCESS_FILE, CONFIG_DIR)
    client = OSMClient(**osm_config.config)
    client = OSMClient("admin", "admin", hostname="nbi.192.168.159.10.nip.io")
    
    ##################################################################
    '''
    NS instantiation process example:
    1- Upload vnfd package
    2- Upload nsd package
    3- Instantiate NS using ID of NSD
    '''
    # vnfpkg = "packages/hackfest.tar.gz"
    # nspkg = "packages/hackfest_ns.tar.gz"

    # vnf_fd = open(vnfpkg, 'rb')
    # print("Creating VNF ...")
    # vnfid = client.vnfd().create(vnf_fd)['id']
    # vnf_fd.close()
    # print("VNF created:", vnfid)

    # print("Creating NS ...")
    # ns_fd = open(nspkg, 'rb')
    # nsid = client.nsd().create(ns_fd)['id']
    # print("NS creation:\n {}".format(nsid))
    # ns_fd.close()
    # print("NS created:", nsid)

    # print("Instantiating NS ...")
    # data_instantiation = {
    #     "nsName": "hackfest-basic",
    #     "nsdId": f"{nsid}",
    #     "vimAccountId": "5d686eba-f3cc-4c19-9806-a1dd402eef11",
    #     }

    # print(client.nslcm().create(json.dumps(data_instantiation)))
    # print("NS instantiation in process")
    ###################################################################

    '''
    List NS deployed example:
    '''
    print(client.nsd().list())

    ###################################################################
    # Erase created token and close the conection with OSM
    client.close()