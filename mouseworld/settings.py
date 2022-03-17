import os

"""
This file record the necesary variables to be used in the scripts.
The purpose of this file is to isolate configuration from code in the way that
modifications in the configuration can be made without touching the code
"""

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_PATH, 'config')
SCENARIOS_DIR = os.path.join(BASE_PATH, 'scenarios')
TEMPLATES_DIR = os.path.join(BASE_PATH, 'templates')
LOG_DIR = os.path.join(BASE_PATH, 'logs')
IMAGES_DIR = os.path.join(BASE_PATH, 'images')
TEMP_DIR = os.path.join(BASE_PATH, 'temp')

# File that contains OSM access credentials
OSM_ACCESS_FILE = os.path.join(CONFIG_DIR, 'osm_access.yaml')

# File that contains Openstack access credentials
OS_ACCESS_FILE = os.path.join(CONFIG_DIR, 'openstack_access.yaml')

OS_ACCESS_FILE_FILEDS = [
    "OS_USERNAME",
    "OS_PASSWORD",
    "OS_PROJECT_NAME",
    "OS_USER_DOMAIN_NAME",
    "OS_PROJECT_DOMAIN_ID",
    "OS_PROJECT_DOMAIN_NAME",
    "OS_AUTH_URL",
    "OS_IDENTITY_API_VERSION",
]

OSM_ACCESS_FILE_FILEDS = [
    "OSM_USER",
    "OSM_PASSWORD",
    "OSM_URL",
]

OPENSTACK_MANAGEMENT_NETWORK = "management_network"
