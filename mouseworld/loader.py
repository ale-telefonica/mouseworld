import os
import glob
import shutil
import tarfile
import yaml
from os.path import getmtime, join
from yaml import load, Loader
from jinja2 import Environment, BaseLoader, TemplateNotFound

from settings import SCENARIOS_DIR, TEMPLATES_DIR


class Charm(object):

    def __init__(self, environ, vnf_path, charm_info):
        self.env = environ
        self.vnf_path = vnf_path
        self.charm_info = charm_info
        self.actions = self.env.get_template("actions.yaml.j2")
        self.proxycharm = self.env.get_template("charm.py.j2")
        self.metadata = self.env.get_template("metadata.yaml.j2")
        self.config = self.env.get_template("config.yaml.j2")
        # self.day1_2 = self.env.get_template("day1_2.yaml.j2")
        
        self.extract()
        self.setup()
        

    def parse_all(self):
        # Parse actions.yaml file
        with open(os.path.join(self.charm_dir, "actions.yaml"), 'w') as charm_action_file:
            charm_action_file.write(self.actions.render(self.variables))
        
        # Parse charms.yaml file
        with open(os.path.join(self.charm_dir, "src", "charm.py"), 'w') as charm_script:
            charm_script.write(self.proxycharm.render(self.variables))
            # os.chmod(os.path.join(self.charm_dir, "src", "charm.py"), 775)

        # Parse metadata.yaml file
        # with open(os.path.join(self.charm_dir, "metadata.yaml"), 'w') as metadata:
        #     metadata.write(self.metadata.render(self.variables))

        # Parse config.yaml file
        # with open(os.path.join(self.charm_dir, "config.yaml"), 'w') as config:
        #     config.write(self.config.render())


    def setup(self,):
        charm_files = tarfile.open(os.path.join(TEMPLATES_DIR, "charms", "charm_files.tar.gz"))
        charm_files.extractall(self.charm_dir)
        charm_files.close()
        
        # os.chdir(self.charm_dir)
        # os.makedirs(os.path.join(self.charm_dir, "hooks"), exist_ok=True)
        # os.makedirs(os.path.join(self.charm_dir, "lib"), exist_ok=True)
        # os.makedirs(os.path.join(self.charm_dir, "mod"), exist_ok=True)
        # os.makedirs(os.path.join(self.charm_dir, "src"), exist_ok=True)
        
        # with open(os.path.join(self.charm_dir, "src", "charm.py"), "w") as charm_file:
        #     charm_file.write("")
    
    # def clone_proxy_charm(self):

    #     os.chmod(os.path.join(self.charm_dir, "src", "charm.py"), 775)
        
    #     os.symlink("../src/charm.py", "hooks/upgrade-charm")
    #     os.symlink("../src/charm.py", "hooks/install")
    #     os.symlink("../src/charm.py", "hooks/start")
        
    #     os.system("git clone https://github.com/canonical/operator mod/operator")
    #     os.system("git clone https://github.com/charmed-osm/charms.osm mod/charms.osm")
       
    #     os.symlink("../mod/operator/ops", "lib/ops")
    #     os.symlink("../mod/charms.osm/charms", "lib/charms")

    def extract(self):
        self.charm_name = self.charm_info["name"]
        self.charm_dir = os.path.join(self.vnf_path, "charms", self.charm_name)
        name = self.charm_info['name']
        vnf = self.charm_info['vnf']
        target = self.charm_info['target']
        level = self.charm_info['level']
        charm_actions = self.charm_info['actions']
        username = self.charm_info['credentials']['cloud-config']['username']
        password = self.charm_info['credentials']['cloud-config']['password']

        self.variables = {
            "charm_name": name,
            "vnf": vnf,
            "target": target,
            "actions": charm_actions,
            "ssh_username": username,
            "ssh_password": password,
            "level": level
        }


class MouseworldLoader(BaseLoader):

    def __init__(self, path=TEMPLATES_DIR):
        self.path = path

    def get_source(self, environment, template):
        path = glob.glob(join(self.path, "**", template))
        if len(path) == 1: path = path[0]
        elif len(path) == 0:
            raise TemplateNotFound(template)
        else:
            raise Exception("Multiple files found for {}".format(template))
        mtime = getmtime(path)
        with open(path) as f:
            source = f.read()
        return source, path, lambda: mtime == getmtime(path)


class PackageTool(object):
    def __init__(self, scenario):
        self.scenario = scenario
        self.scenario_ns_path = os.path.join(SCENARIOS_DIR, self.scenario, f'{self.scenario}_ns')
        self.scenario_vnf_paths = []
        file_loader = MouseworldLoader()
        self.env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        self.nsd = self.env.get_template("nsd.yaml.j2")
        self.vnfd = self.env.get_template("vnfd.yaml.j2")
        self.cloud_init = self.env.get_template("cloud_init.txt.j2")
        self.scenario_descriptor = load(self.env.get_template(f"{self.scenario}.yaml").render(), Loader)

    def build_scenario(self):
        # Init variables
        name = self.scenario
        self.mirroring = False
        self.vnfs = self.scenario_descriptor['VNFs']
        cloudinit = self.scenario_descriptor['CloudInit']
        self.external_networks = [ n['id'] for n in self.scenario_descriptor['Networks'] if n['type'] == "external"]
        internal_networks = [ n['id'] for n in self.scenario_descriptor['Networks'] if n['type'] == "internal"]
        computes = self.scenario_descriptor['Compute']
        storages = self.scenario_descriptor['Storage']
        vdus = self.scenario_descriptor['Instances']
        vdus2 = []
        charms = []
        self.vnfs2 = []
        self.images = set()
        self.nsd_path = join(self.scenario_ns_path, f'{self.scenario}_nsd.yaml' )
        self.vnfd_paths = set()
        if 'Charms' in self.scenario_descriptor:
            charms = self.scenario_descriptor['Charms']
        
        # Create folder structure
        self.create_folders()
        
        # Assemble VNFs/VDUs
        for vnf in self.vnfs:
            vnf_external_net = []
            vnf_internal_net = []
            vnf_computes = []
            vnf_storages = []
            vnf['vdus'] = []
            scenario_vnf_path = join(SCENARIOS_DIR, self.scenario, f'{vnf["id"]}_vnf')
            path_to_vnf = join(scenario_vnf_path, f'{vnf["id"]}_vnfd.yaml')

            if path_to_vnf in self.vnfd_paths:
                continue

            self.scenario_vnf_paths.append(scenario_vnf_path)
            for vdu in vdus:
                if vdu['vnf'] == vnf['id']:
                    vdu['cloud-init'] = list(filter(lambda x: x["id"] == vdu["cloud-init"], cloudinit))[0]
                    vdu['compute'] = list(filter(lambda x: x["id"] == vdu["compute"], computes))[0]
                    vdu['storage'] = list(filter(lambda x: x["id"] == vdu["storage"], storages))[0]

                    vdu_externals_net = [n for n in vdu["networks"] if n in self.external_networks]
                    vdu_internals_net = [n for n in vdu["networks"] if n in internal_networks]
                    
                    vdu['external_networks'] = vdu_externals_net
                    vdu['internal_networks'] = vdu_internals_net
                    vnf_external_net.extend(vdu_externals_net)
                    vnf_internal_net.extend(vdu_internals_net)
                    
                    vdu_networks = []
                    vdu_networks.extend(vdu_externals_net)
                    vdu_networks.extend(vdu_internals_net)
                    vdu['networks'] = vdu_networks
                    vdus2.append(vdu)
                    self.images.add(vdu['image'])
                    
                    if not vdu['compute'] in vnf_computes:
                        vnf_computes.append(vdu['compute'])
                    if not vdu['storage'] in vnf_storages:
                        vnf_storages.append(vdu['storage'])

                    # Create cloud_init file
                    cloud_init_file = f'{vdu["id"]}_cloud_init.txt'
                    vdu['cloud_init_file'] = cloud_init_file
                    
                    cloud_init_info = vdu['cloud-init']['cloud-config']
                    content = self.cloud_init.render({"hostname": vdu['id']})
                    extra = yaml.safe_dump(cloud_init_info)
                    content = content + "\n" + extra

                    with open(join(scenario_vnf_path, 'cloud_init', cloud_init_file), 'w') as cloud_init:
                        cloud_init.write(content)
                        
                    vnf['vdus'].append(vdu)
                    
            vnf["external_networks"] = set(vnf_external_net)
            vnf["internal_networks"] = set(vnf_internal_net)
            vnf["computes"] = vnf_computes
            vnf["storages"] = vnf_storages

            vnf_params = {
                "vnf": vnf,
                "vdus": vdus2,
                "external_networks": self.external_networks,
                "internal_networks": internal_networks,
                "images": self.images,
                "description": vnf['description']
            }

            if charms:
                charm = list(filter(lambda x: x["vnf"] == vnf["id"], charms))
                
                if charm: 
                    vnf['charm'] = charm[0]
                    vnf['charm']['credentials'] = list(filter(lambda x: x["id"] == vnf['charm']["credentials"], cloudinit))[0]
                    _charm = Charm(self.env, scenario_vnf_path, vnf['charm'])
                    _charm.parse_all()
                    # _charm.clone_proxy_charm()
                    vnf_params['charm'] = _charm.variables
                    # print(vnf_params['charm'])

            with open(path_to_vnf, 'w') as vnf_descriptor:
                vnfd = self.vnfd.render(vnf_params)
                vnf_descriptor.write(vnfd)
                vnfd = load(vnfd, Loader)
            self.vnfd_paths.add(path_to_vnf)

            vnf["cps"] = vnfd["vnfd"]["ext-cpd"]
            self.vnfs2.append(vnf)
        
        nsd_params = {
            "name": name,
            "vnfs": self.vnfs2,
            "external_networks": self.external_networks,
            "description": self.scenario_descriptor['Project']['description']
        }
        with open(self.nsd_path, 'w') as ns_descriptor:
            ns_descriptor.write(self.nsd.render(nsd_params))

        # Setup mirroring if requested
        if "Mirroring" in self.scenario_descriptor:
            self.mirror = []
            self.mirroring = self.scenario_descriptor['Mirroring']
            services = self.mirroring['services']
            flows = self.mirroring['flows']
            for flow in flows:
                flow['service'] = list(filter(lambda x: x["id"] == flow["service"], services))[0]
                self.mirror.append(
                    {'source':f"{flow['instance_id']}_{flow['network_id']}",
                    'dest':f"{flow['service']['instance_id']}_{flow['service']['network_id']}",
                    "direction": flow['direction']}
                    )
        # Clean variable to save progress in serialized file
        self.clean_to_serialize()
        
    def clean_to_serialize(self):
        self.nsd = ""
        self.vnfd = ""
        self.cloud_init = ""
        self.env = ""

    def clean_scenario_folder(self):
        if os.path.exists(join(SCENARIOS_DIR, self.scenario)):
            shutil.rmtree(join(SCENARIOS_DIR, self.scenario))
        else:
            raise(Exception("Scenario folder does not exit, no deleting"))

    def create_folders(self):
        print("Creating project directory tree")
        folders = [
            f"{self.scenario_ns_path}", 
            ]
        for vnf in self.vnfs:
            folders.extend([
                f"{self.scenario}/{vnf['id']}_vnf/cloud_init",
                f"{self.scenario}/{vnf['id']}_vnf/charms"
            ])
        for folder in folders:
            os.makedirs(join(SCENARIOS_DIR, folder), exist_ok=True)

    def make_tarfile(self, output_filename, source_dir):
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        return output_filename

    def create_project_pkgs(self):
        self.vnfpkgs = []
        for vnf in self.scenario_vnf_paths:
            self.vnfpkgs.append(self.make_tarfile(vnf+'.tar.gz', vnf))
        self.nspkg = self.make_tarfile(self.scenario_ns_path+'.tar.gz', self.scenario_ns_path)


class IterJ:
    """
    Data structure to traverse json objects

    Access dict using the nomenclature iterj.key.key..., where iterj is the child 
    object of class IterJ, adn key, the dictionary key you want to acess.

    Access elements of list by using the nomenclature iterj.i<index>, where index
    is a number representing then index of the values you want access.

    To access the final result the value attribute must be called
    Example: iterj.key.i1.key.value
    
    :param: obj: Json object to traverse
    """
    def __init__(self, obj):
        self.obj = obj
        self.value = self.obj

    def __getattr__(self, key):
        if isinstance(self.obj, list):
            value = self.obj[int(key[1])]
        elif isinstance(self.obj, str) and key != "value":
            raise(TypeError(f"You are trying to access a string <{self.obj}> using key={key}"))
        else:
            value = self.obj[key]
        return IterJ(value)


if __name__=='__main__':
#     sw_image, vnfpkg, nspkg = create_project_pkgs('hackfest_cloudinit')
    pkg = PackageTool("Inspire5G")
    
    try:
        import pickle
        import settings
        pkg.build_scenario()
        # print(pkg.vnfs2)
        with open(os.path.join(settings.TEMP_DIR, "Inspire5G"), "wb") as package_fd:
            pickle.dump(pkg, package_fd)
    except Exception as exception:
        pkg.clean_scenario_folder()
        raise(exception)
   