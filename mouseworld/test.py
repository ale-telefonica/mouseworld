from jinja2 import Environment, PackageLoader, select_autoescape

file_loader = PackageLoader("mouseworld")
env = Environment(loader=file_loader, autoescape=select_autoescape(), trim_blocks=True, lstrip_blocks=True)
nsd = env.get_template("nsd.yaml.j2")
nsd_params = {
    "name": "hackfest_basic",
    "vnfs": [{"id":"hackfest_basic"}, {"id":"hackfest_basic"}],
    "external_networks": [{"id":"management_network"}, {"id":"internet"}]
}

nsd = env.get_template("vnfd.yaml.j2")


print(nsd.render(nsd_params))