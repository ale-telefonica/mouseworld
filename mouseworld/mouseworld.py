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
    osm_client = OSMClient(**osm_config.config)
    
    # Create openstack client instance
    os_client = OpenstackClient(**os_config.config)
    os_client.connect()
    
    # Check if there is a vim conection with the specified name
    if not (vim_data:=osm_client.vim.exist(os_config.OS_PROJECT_NAME)):
        print(
            f"VIM conection <{os_config.OS_PROJECT_NAME}> does not exist")
        if create_vim:
            print(f"Creating VIM <{os_config.OS_PROJECT_NAME}>")
            vimid = osm_client.vim.create(os_config)
        else:
            raise(Exception(
                f"Vim conection <{os_config.OS_PROJECT_NAME}> does not exist, please create it on OSM."))

    # if not osm_client.vim_exists(os_config.OS_PROJECT_NAME):
    #     # Create vim conection
    #     print(
    #         f"Vim conection <{os_config.OS_PROJECT_NAME}> does not exist, and will be created")
    #     if create_vim:
    #         vimid = osm_client.create_vim(os_config)['id']
    #     else:
    #         raise(Exception(
    #             f"Vim conection <{os_config.OS_PROJECT_NAME}> does not exist, please create it on OSM."))
    # else:
    #     vimid = osm_client.get_id(os_config.OS_PROJECT_NAME, "vims")

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
        vnfdid =osm_client.create_vnfd_pkg(vnfpkg)
        
    # Create NSD package
    nsdid = osm_client.create_nsd_pkg(pkg.nspkg)

    # Instantiate NS
    if not osm_client.get_id(scenario, "nslcm"):
        nsid = osm_client.create_ns_instance(scenario, nsdid, vimid, pkg.vnfs2, wait=True)
    else:
        print("A NS instance already exist, please rename new NS or delete old one")
        exit()
        
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
