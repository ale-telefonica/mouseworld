# -------------------------------
# Author: Alejandro Martin Herve
# Version: 1.0.0
# -------------------------------
# Openstack API interaction
from schema import SCHEMA
    
class Tap_Service(SCHEMA, object):
    """
    TAAS_Service schema class
    Class that contains the specific endpoints
    to execute TAAS_Service actions.

    :POST /v2.0/taas/tap_services
    Json Request:
    {
    "tap_service": {
        "description": "Test_Tap",
        "name": "Test",
        "port_id": "c9beb5a1-21f5-4225-9eaf-02ddccdd50a9",
        "tenant_id": "97e1586d580745d7b311406697aaf097"
        }
    }

    :GET /v2.0/taas/tap_services/ | GET /v2.0/taas/tap_services/{tap_service_uuid}
    """
    GET_SCHEMA = "taas/tap_services"
    CREATE_SCHEMA = "taas/tap_services"


class Tap_Flow(SCHEMA, object):
    """
    TAAS_Flow schema class
    Class that contains the specific endpoints
    to execute TAAS_Flow actions.

    :POST /v2.0/taas/tap_flows
    Json Request:
    {
    "tap_flow": {
        "description": "Test_flow1",
        "direction": "BOTH",
        "name": "flow1",
        "source_port": "775a58bb-e2c6-4529-a918-2f019169b5b1",
        "tap_service_id": "69bd12b2-0e13-45ec-9045-b674fd9f0468",
        "tenant_id": "97e1586d580745d7b311406697aaf097",
        "vlan_filter": "9,18-27,36,45,54-63"
        }
    }

    :GET /v2.0/taas/tap_flows | GET /v2.0/taas/tap_flows/{tap_flow_uuid}
    """
    GET_SCHEMA = "taas/tap_flows"
    CREATE_SCHEMA = "taas/tap_flows"