"""
-------------------------------
Author: Alejandro Martin Herve
Version: 2.0.0
-------------------------------
Main Program
"""

# Pasos del contructor:
# 1. Cargar solicitud
# 2. Adaptar solicitud a template OSM
# 3. Convertir los templates de vnf y ns en paquetes .gz
# 4. Cargar paquetes vnf y ns
# *. Cargar credenciales de acceso OSM
# 5. Crear conexion con Openstack para el proyecto que se vaya a desplegar
#   - Cargar variables de entorno desde el archivo openstack_access.yaml para
#     realizar la conexión con el proyecto especifico de openstack
#   - Comprobar que el proyecto a desplegar existe, sino añadir opcion de crearlo
#   - Añadir conexion con vim si no existe
# 6. Comprobar que las imagenes del paquete cargado se encuentran en Openstack
#   - Si no se encuentran subirlas
# 7. Instanciar ns
# 8. Añadir mirroring si es solicitado
# 9. Comprobar funcionamiento.

# TODO: Add support for passing ssh public keys [Not a priority]


import os
import glob
import pickle
import click

import settings
from loader import PackageTool
# from _osmclientv2 import OSMClient
# from _osmclient import OSMClient
from os_client import OpenstackClient
from utils import Config, Logger



def load_scenario(scenario):
    """
    Load already built scenario
    """
    path = os.path.join(settings.TEMP_DIR, scenario)
    if not os.path.exists(path):
        print(f"""[!] Scenario {scenario} have not been built.\nBuild it using command:
        <mouseworld.py build --scenario {scenario}>
        """)
        exit()
    with open(path, "rb") as package_fd:
        pkg = pickle.load(package_fd)
    return pkg


def load_config(
    osm_config_file=settings.OSM_ACCESS_FILE,
    os_config_file=settings.OS_ACCESS_FILE
):
    """Load osm and openstack access credentials and validate config files"""
    osm_config = Config(osm_config_file, _type="OSM")
    os_config = Config(os_config_file, _type='Openstack')
    return osm_config, os_config


@click.group()
def cli_mw():
    pass


@cli_mw.command(short_help="Build scenario template")
@click.option("--scenario", "-s", required=True, type=str, help="Name of the scenario template to build (Template must exist in templates/scenarios folder)")
def build(scenario):
    # Create scenario packages
    pkg = PackageTool(scenario)
    try:
        pkg.build_scenario()
        with open(os.path.join(settings.TEMP_DIR, scenario), "wb") as package_fd:
            pickle.dump(pkg, package_fd)
    except FileNotFoundError as exc:
        print(f"Scenario {scenario} has not been constructed")
        raise exc
    except Exception as error:
        pkg.clean_scenario_folder()
        raise error


@cli_mw.command(short_help="Deploy already build scenario")
@click.option("--scenario", "-s", required=True, type=str, help="Name of the scenario to deploy (Scenario must be built before deploy it)")
def deploy(scenario):
    """Deploy already build scenario"""

    pkg = load_scenario(scenario)

    osm_config, os_config = load_config()

    # Create osm client instance
    osm_client = OSMClient(osm_config)

    # Create openstack client instance
    os_client = OpenstackClient(**os_config.config)
    os_client.connect()

    # Check VIM conection
    vim_name = os_config.OS_PROJECT_NAME
    osm_client.vim.create(os_config)

    # Check if image is available in VIM
    os_client.check_images(pkg.images)

    # Create VNFD package
    for vnfpkg in pkg.scenario_vnf_paths:
        osm_client.vnfd.create(vnfpkg)

    # Create NSD package
    nsd_name = osm_client.nsd.create(pkg.scenario_ns_path)

    # Instantiate NS
    osm_client.ns.create(nsd_name, scenario, vim_name)

    if pkg.mirroring:
        # Create mirroring
        print("Creating Mirroring...")
        list(map(os_client.create_mirror, pkg.mirror))

    # Close client conections
    os_client.close()

    print("[!] Finish")


@cli_mw.command(short_help="Destroy scenario")
@click.option("--scenario", "-s", required=True, type=str, help="Name of the scenario to destroy")
def destroy(scenario):
    """Destroy deployed scenario"""
    pkg = load_scenario(scenario)

    print(f"[!] Destroying scenario {scenario}")
    path = os.path.join(settings.TEMP_DIR, scenario)

    osm_config, _ = load_config()
    osm_client = OSMClient(osm_config)

    # Delete ns instance
    osm_client.ns.delete(scenario, wait=True)

    # Delete ns descriptor
    osm_client.nsd.delete(os.path.basename(pkg.scenario_ns_path))

    # Delete vnf descriptors
    for vnfpkg in pkg.scenario_vnf_paths:
        osm_client.vnfd.delete(os.path.basename(vnfpkg))

    # Remove scenario configuration
    os.remove(path)
    print(f"[!] Destroyed scenario <{scenario}>")


@cli_mw.command(short_help="List built scenarios")
def list_scenarios():
    """
    List the scenarios that have been build with this tool
    """
    scenarios = list(filter(lambda x: not x.endswith(".txt"),
                            glob.glob(os.path.join(settings.TEMP_DIR, "*"))))
    logger.debug(f"Scenarios {scenarios}")
    print("Scenarios:")
    if not scenarios:
        print("  Not scenarios have been built")
    for scenario in scenarios:
        print("- ", os.path.basename(scenario).strip(".yaml"))



if __name__ == '__main__':
    if settings.LOGGING_ACTIVATED:
        logger = Logger("mouseworld")
    cli_mw()
