# Author: Alejandro Martin Herve
# Version: 1.0.0

# TODO: Remove decorator on every method and authenticate at the begining of
# object creation to reduce overhead.

"""
Documentación
"""

# Imports
import re
import os
import time
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
        self.instatiation_timeout = 300

    def _is_authenticated(method):
        # Decorator that ensures authentication for every request
        def wrapper(self):
            if self.auth_info:
                expires = self.auth_info["expires"]
                if expires > dt.now().timestamp():
                    return method(self)
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
        # Check if conection with VIM exist in OSM
        return name in (vim['name'] for vim in self.vims().list())

    def get_vim_id(self, name):
        return [vim['_id'] for vim in self.vims().list() if vim['name'] == name]

    def get_id(self, name, _type):
        # Get existing resources for the specified type and return only
        # the one that match the provided name.
        obj = getattr(self, _type)
        key = "name"
        if _type == "vnfd" or _type == "nsd":
            key = "id"
        
        for resource in obj().list():
            if name == resource[key]:
            # if re.match(f'{name}(.?)+', resource[key]):
                return resource["_id"]
        else:
            return None
    
    def create_pkg(self, pkg, _type):
        pkg_name = os.path.basename(pkg).strip("tar.gz")
        try:
            with open(pkg, 'rb') as stream:
                if _type == "nsd":
                    id = self.nsd().create(stream)['id']
                elif _type == "vnfd":
                    id = self.vnfd().create(stream)['id']
                return id
        except HTTPError as http_e:
            if http_e.args[0]['code'] == "CONFLICT":
                print("Package already exist, not creating")
                return self.get_id(pkg_name, _type)
            else:
                raise(http_e)
        except Exception as e:
            raise(e)

    def create_nsd_pkg(self, nspkg):
        print("Creating NS package...")
        return self.create_pkg(nspkg, 'nsd')

    def create_vnfd_pkg(self, vnfpkg):
        print("Creating VNF package...")
        return self.create_pkg(vnfpkg, 'vnfd')  

    def create_vim(self, os_config):
        # Method to assemble vim data
        # :os_config: Object of type Config
        # :return: json response with de result of the vim creation
        vim_data = {
            "name": f"{os_config.OS_PROJECT_NAME}",
            "description": f"OSM conection with Openstack <{os_config.OS_AUTH_URL}> in project <{os_config.OS_PROJECT_NAME}>",
            "vim_type": "openstack",
            "vim_url": os_config.OS_AUTH_URL,
            "vim_tenant_name": os_config.OS_PROJECT_NAME,
            "vim_user": os_config.OS_USERNAME,
            "vim_password": os_config.OS_PASSWORD,
            "config": {
                "management_network_name": OPENSTACK_MANAGEMENT_NETWORK,
                "disable_network_port_security": True
            }
        }
        return self.vims().create(json.dumps(vim_data))
    
    def create_ns_instance(self, scenario, nsdid, vimid, external_nets, wait=True):
        vlds = []
        for net in external_nets:
            net_mapping =  {"name": net, "vim-network-name": net} 
            vlds.append(net_mapping)

        data_instantiation = {
            "nsName": scenario,
            "nsdId": nsdid,
            "vimAccountId": vimid,
            "vld": vlds
        }

        nsid = self.nslcm().create(json.dumps(data_instantiation))['id']
        status = "STARTING"
        ns_info = {}
        print("Awaiting instatiation process to be completed")
        print("Instatiation state:",status)
        if wait == True:
            start = time.time()
            while True:
                if status == "READY":
                    return nsid
                elif status == "BROKEN":
                    raise(Exception("Error occur while instantiating network service"))

                ns_info = self.nslcm().show(nsid)
                if status != ns_info['nsState']:
                    status = ns_info['nsState']
                    print("Instatiation state:",status)
                # print(".", end=" ")
                
                now = time.time() - start
                if now >= self.instatiation_timeout:
                    raise TimeoutError("The instatiation process is taking to much time.")
                time.sleep(1)
        return nsid

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
    from mouseworld import Config
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