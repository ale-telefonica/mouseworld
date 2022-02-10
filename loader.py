from yaml import load, Loader
import tarfile
import os.path
from settings import SCENARIOS_DIR

def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))
    return output_filename

def extract_sw_image(vnf):
    with open(os.path.join(vnf, os.path.basename(vnf)+'d.yaml')) as vnfd:
        vnfd_yaml = load(vnfd, Loader)
    sw_image = vnfd_yaml['vnfd']['sw-image-desc'][0]['image']
    return sw_image

def create_project_pkgs(project):
    vnf = os.path.join(SCENARIOS_DIR, project, project + '_vnf')
    ns = os.path.join(SCENARIOS_DIR, project, project + '_ns')
    sw_image = extract_sw_image(vnf)
    vnfpkg = make_tarfile(vnf+'.tar.gz', vnf)
    nspkg = make_tarfile(ns+'.tar.gz', ns)
    return sw_image, vnfpkg, nspkg


if __name__=='__main__':
    create_project_pkgs('hackfest_basic')