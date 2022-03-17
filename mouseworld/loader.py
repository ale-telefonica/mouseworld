import os
import glob
import shutil
import tarfile
import yaml
from os.path import getmtime, join
from yaml import load, Loader
from jinja2 import Environment, BaseLoader, TemplateNotFound

from settings import SCENARIOS_DIR, TEMPLATES_DIR


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
        self.scenario_ns_path = join(SCENARIOS_DIR, self.scenario, f'{self.scenario}_ns')
        self.scenario_vnf_paths = []
        file_loader = MouseworldLoader()
        self.env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)
        self.nsd = self.env.get_template("nsd.yaml.j2")
        self.vnfd = self.env.get_template("vnfd.yaml.j2")
        self.cloud_init = self.env.get_template("cloud_init.txt.j2")
        self.scenario_descriptor = load(self.env.get_template(f"{self.scenario}.yaml").render(), Loader)

    def build_scenario(self):
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
        self.vnfs2 = []
        self.images = set()
        self.nsd_path = join(self.scenario_ns_path, f'{self.scenario}_nsd.yaml' )

        self.create_folders()
        
        self.vnfd_paths = set()
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
            raise(Exception("Scenario folder odes not exit, no deleting"))

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
   