# -------------------------------
# Author: Alejandro Martin Herve
# Version: 2.0.0
# -------------------------------
# Interface with OSM using osmclient

# Built-in Import
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import os

# Project imports
from utils import Config
from settings import OPENSTACK_MANAGEMENT_NETWORK

# OSM library imports
from osmclient.common.exceptions import ClientException, NotFound
from osmclient.client import Client


class Type(Enum):
    """Artifacts Types"""
    
    NSD = "nsd"
    VNFD = "vnfd"
    VIM = "vim"
    NS = "ns"
    NST = "nst"


@dataclass
class Artifact(ABC):
    """Template base class that defines NSD, VNFD, NS, VIMS, etc

    :param conn: Object of type osmclient.client.Client
    :param artifact_type: Object of type Type that will be use to create the artifact object
    """
    conn: Client
    artifact_type: Type

    def __post_init__(self):
        # self.object reference the type of artifact created
        self.object = getattr(self.conn, self.artifact_type.value)

    def exist(self, name):
        try:
            object_data = self.object.get(name)
            return object_data
        except NotFound:
            return False
        # except Exception as e:
        #     print(f"Error getting {self.artifact_type.name}: ", e)
        #     exit(1)
    
    def create(self, path_to_descriptor: str, **kwargs):
        """Create descriptors (NSD, VNFD), other artifacts may implement it´s own create method"""
        name = os.path.basename(path_to_descriptor)
        if self.exist(name):
            print(f"{self.artifact_type.name} {name} already exist, not creating")
            return None
        
        try:
            nsdid = self.object.create(path_to_descriptor)
            return nsdid
        except Exception as e:
            print(f"Error creating {self.artifact_type.name}: ", e)
            exit(1)
    
    def delete(self, **kwargs):
        """Delete artifact object from OSM"""
        pass


@dataclass
class VIM(Artifact):
    """Class that define specific implementations for a VIM"""
    artifact_type: Type = Type.VIM

    def create(self, os_config, vim_type="openstack", **kwargs):
        if self.exist(os_config.OS_PROJECT_NAME):
            print(f"VIM {os_config.OS_PROJECT_NAME} already exist, not creating")
            return None
        
        vim_access = {
            'vim-url': os_config.OS_AUTH_URL, 
            'vim-tenant-name': os_config.OS_PROJECT_NAME, 
            'vim-username': os_config.OS_USERNAME,
            'vim-password':  os_config.OS_PASSWORD, 
            'vim-type': vim_type, 
            'description': f"OSM conection with Openstack <{os_config.OS_AUTH_URL}> in project <{os_config.OS_PROJECT_NAME}>"}
        
        config = {
                "management_network_name": OPENSTACK_MANAGEMENT_NETWORK,
                "disable_network_port_security": True}
        try:
            vimid = self.object.create(
                os_config.OS_PROJECT_NAME,
                vim_access,
                config)
            return vimid
        except KeyError:
            print(f"The fields specified to create VIM are incorrect: {vim_access}")
            exit(1)
        # except Exception as e:
        #     print("Error: ", e)
        #     exit(1)


@dataclass
class NSD(Artifact):
    """Class that define specific implementations for a NSD"""
    artifact_type: Type = Type.NSD


@dataclass
class VNFD(Artifact):
    """Class that define specific implementations for a VNFD"""
    artifact_type: Type = Type.VNFD


@dataclass
class NS(Artifact):
    """Class that define specific implementations for a NS"""
    artifact_type: Type = Type.NS
    
    def create(self, name, vim_account, wait=True, **kwargs):
        if self.exist(name):
            print(f"{self.artifact_type.name} already exist, not creating")
            return None

        try:
            nsid = self.object.create(name, name, vim_account, wait=wait)
            return nsid
        except Exception as e:
            print(f"Error creating {self.artifact_type.name}:", e)
            exit(1)
            

class OSMClient:
    """
    Interface to interact with OSM
    """

    def __init__(self, osm_config: Config):
        self.username = osm_config.OSM_USER
        self.password = osm_config.OSM_PASSWORD
        self.http_handler = None
        self.auth_info = None
        self.hostname = osm_config.OSM_URL
        self.instatiation_timeout = 300

        try:
            self.conn = Client(
                host=self.hostname, user=self.username, password=self.password, sol005=True)
        except ClientException as clientError:
            print("Client Exception: Error conecting with OSM NBI.\n", clientError)
            exit(1)

        # Adding interface to OSM client objects
        self.vim = VIM(self.conn) 
        self.nsd = NSD(self.conn)
        self.vnfd = VNFD(self.conn)
        self.ns = NS(self.conn)
        