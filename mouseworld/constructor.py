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
# TODO: Add function that create scenario folder structure and config template for that scenario base on general template
# TODO: Añadir opcion en caso de que una vnf tenga varias vdus con imagenes distintas cada una

from yaml import load, Loader
import os

import loader
from _osmclient import OSMClient
from os_client import OpenstackClient

import settings


class Config(object):
    def __init__(self, config_file, config_path, _type=None):
        self.type = _type
        with open(os.path.join(config_path, config_file)) as configfd:
            self.config = load(configfd, Loader)

        self.validate_config_file()

    def validate_config_file(self):
        if self.type == "OSM":
            validator = settings.OSM_ACCESS_FILE_FILEDS
        elif self.type == "Openstack":
            validator = settings.OS_ACCESS_FILE_FILEDS
        for key in self.config:
            if key not in validator:
                raise(Exception(
                    f"{self.type} configuration file fields are incorrect. Please fix it using de fields specified in settings."))
        return True

    def __getattr__(self, __name: str):
        return self.config[__name]


def image_is_available(scenario, image):
    image_path = os.path.join(
        settings.SCENARIOS_DIR,
        scenario,
        'images',
        image,
    )
    return os.path.exists(image_path), image_path


def main(
    scenario: str,
    osm_config_file=settings.OSM_ACCESS_FILE,
    os_config_file=settings.OS_ACCESS_FILE,
    config_dir=settings.CONFIG_DIR,
    create_vim=True
):
    # TODO: En el futuro en lugar de llamar create_projects_pkgs, llamar una funcion
    # que parsee template generico a osm templates, empaquete y devuelva el camino
    # a los paquetes ns y vnf

    sw_images, vnfpkg, nspkg = loader.create_project_pkgs(scenario)

    # Load osm and openstack access credentials and validate config files

    osm_config = Config(osm_config_file, config_dir, _type="OSM")
    os_config = Config(os_config_file, config_dir, _type='Openstack')

    # Create osmclient instance

    osm_client = OSMClient(**osm_config.config)

    # Create openstack client instance

    os_client = OpenstackClient(**os_config.config)
    os_client.connect()

    # Check if there is a vim conection with the specified name

    if not osm_client.vim_exists(os_config.OS_PROJECT_NAME):
        # Create vim conection
        print(
            f"Vim conection <{os_config.OS_PROJECT_NAME}> does not exist, and will be created")
        if create_vim:
            vimid = osm_client.create_vim(os_config)['id']
        else:
            raise(Exception(
                f"Vim conection <{os_config.OS_PROJECT_NAME}> does not exist, please create it on OSM."))
    else:
        vimid = osm_client.get_vim_id(os_config.OS_PROJECT_NAME)[0]
        
    for sw_image in sw_images:
        if not os_client.image_exists(sw_image):
            print(f'Image {sw_image} does not exist on VIM and need to be uploaded')
            # Check if image exist inside the vnf/image folder on the scenario
            image_exist, image_path = image_is_available(scenario, sw_image)
            if image_exist:
                print("Uploading image, this process could take a while.")
                os_client.create_new_image(sw_image, image_path)
            else:
                raise(Exception(f"Image {sw_image} not found in image folder"))

    # Create VNF package
    vnfdid = osm_client.create_vnfd_pkg(vnfpkg, scenario)

    # Create NS package

    nsdid = osm_client.create_nsd_pkg(nspkg, scenario)

    # Instantiate NS
    nsid = osm_client.create_ns_instance(scenario, nsdid, vimid, wait=True)

    ns_info = osm_client.nslcm().show(nsid)

    # Close clients conections
    osm_client.close()
    os_client.close()


if __name__ == '__main__':
    main('hackfest_basic', create_vim=True)
