# -------------------------------
# Author: Alejandro Martin Herve
# Version: 1.0.0
# -------------------------------
# General Schema
from schema import SCHEMA
    
class Nsd(SCHEMA, object):
    """
    NSD schema class
    Class that contains the specific endpoints
    to execute nsd actions.
    """
    GET_SCHEMA = "nsd/v1/ns_descriptors"
    CREATE_SCHEMA = "nsd/v1/ns_descriptors_content"
    CONTENT_TYPE = {
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
    CONTENT_TYPE = {
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


class Vims(SCHEMA, object):
    """
    VIM schema class
    Class that contains the specific endpoints
    to execute vim actions.
    """
    GET_SCHEMA = "admin/v1/vims"
    CREATE_SCHEMA = "admin/v1/vim_accounts"


class Auth(SCHEMA, object):
    """
    Auth schema class
    Class that contains the specific endpoints
    to execute authorization actions.
    """
    GET_SCHEMA = "admin/v1/tokens"
    CREATE_SCHEMA = "admin/v1/tokens"