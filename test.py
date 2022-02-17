from jinja2 import Environment, PackageLoader
import os
# import settings


# os.chdir(os.path.dirname(settings.BASE_PATH))
print(os.getcwd())
file_loader = PackageLoader("mouseworld")
env = Environment(loader=file_loader)
template = env.get_template("vnfd.yaml.j2")
print(template)