# -------------------------------
# Author: Alejandro Martin Herve
# Version: 1.0.0
# -------------------------------
# Main Program

# Pasos del contructor:
# 1. Cargar solicitud
# 2. Adaptar solicitud a template OSM
# 3. Convertir los templates de vnf y ns en paquetes .gz
# 4. Cargar paquetes vnf y ns
# *. Cargar credenciales de acceso OSM
# 5. Crear conexion con Openstack para el proyecto que se vaya a desplegar
#   - Cargar variables de entorno desde el archivo openstack_access.yaml para realizar la conexión con el proyecto especifico de openstack
#   - Comprobar que el proyecto a desplegar existe, sino añadir opcion de crearlo
#   - Añadir conexion con vim si no existe
# 6. Comprobar que las imagenes del paquete cargado se encuentran en Openstack
#   - Si no se encuentran subirlas
# 7. Instanciar ns
# 8. Añadir mirroring si es solicitado
# 9. Comprobar funcionamiento.

# TODO: Add support for passing ssh public keys [Not a priority]

from yaml import load, Loader
import os
import glob
import click
import pickle

from loader import PackageTool
from _osmclientv2 import OSMClient
# from _osmclient import OSMClient
from os_client import OpenstackClient

from utils import Config
import settings


@click.group()
@click.pass_context
@click.option("--scenario", required=True, type=str, help="Name of the scenario template to build (Template must exist in templates/scenarios folder)")
def cli_mw(ctx, scenario):
    ctx.obj["scenario"] = scenario

@cli_mw.command(short_help="Build scenario template")
@click.pass_context
def build(ctx):
    # Create scenario packages
    scenario = ctx.obj["scenario"]
    pkg = PackageTool(scenario)
    try:
        pkg.build_scenario()
        ctx.obj["pkg"] = pkg
        with open(os.path.join(settings.TEMP_DIR, scenario), "wb") as package_fd:
            pickle.dump(pkg, package_fd)
    except FileNotFoundError:
        raise(f"Scenario {scenario} has not been constructed")
    except Exception as error:
        pkg.clean_scenario_folder()
        raise(error.args)

def load_scenario(scenario):
    path = os.path.join(settings.TEMP_DIR, scenario)
    if os.path.exists(path):
        with open(path, "rb") as package_fd:
            pkg = pickle.load(package_fd)
        os.remove(path)
    return pkg

@cli_mw.command(short_help="Deploy already build scenario")
@click.option("--create-vim/--no-create-vim", default=True, help="Create VIM conecction if it does not exist")
@click.pass_context
def deploy(
    ctx,
    create_vim,
    osm_config_file=settings.OSM_ACCESS_FILE,
    os_config_file=settings.OS_ACCESS_FILE,
):
    scenario = ctx.obj['scenario']

    pkg = load_scenario(scenario)
    pkg.create_project_pkgs()
    
    # Load osm and openstack access credentials and validate config files
    osm_config = Config(osm_config_file, _type="OSM")
    os_config = Config(os_config_file, _type='Openstack')

    # Create osmclient instance
    osm_client = OSMClient(osm_config)
    
    # Create openstack client instance
    os_client = OpenstackClient(**os_config.config)
    os_client.connect()
    
    # Check VIM conection
    vim_name = os_config.OS_PROJECT_NAME
    osm_client.vim.create(os_config)

    for sw_image in pkg.images:
        if not os_client.image_exists(sw_image):
            print(f'Image {sw_image} does not exist on VIM and need to be uploaded')
            # Check if image exist inside the scenario/<scenario>/image folder
            image_path = image_is_available(sw_image)
            if image_path:
                print("Uploading image, this process could take a while.")
                img_obj = os_client.create_new_image(sw_image, image_path[0])
            else:
                raise(Exception(f"Image {sw_image} not found in image folder"))

    # Create VNFD package
    for vnfpkg in pkg.vnfpkgs:
        vnfdid =osm_client.vnfd.create(vnfpkg)
        
    # Create NSD package
    nsd_name = osm_client.nsd.create(pkg.nspkg)

    # Instantiate NS
    osm_client.ns.create(scenario, vim_name)
        
    if pkg.mirroring:
        print("Creating Mirroring...")
        list(map(os_client.create_mirror, pkg.mirror))

    # Close clients conections
    osm_client.close()
    os_client.close()

def image_is_available( image ):
    image_path = glob.glob(os.path.join(settings.IMAGES_DIR, image+"*"))
    return image_path

# def destroy(scenario):
#     # Delete network service from OSM
#     nslcm_id = osm_client.get_id(scenario, "nslcm")

if __name__ == '__main__':
    cli_mw(obj={})
    # deploy('hackfest_custom', create_vim=True)
    # destroy('hackfest_custom')
