from yaml import load, Loader
import settings

class Config(object):
    def __init__(self, config_file, _type=None):
        self.type = _type
        with open(config_file) as configfd:
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


class IterJ(dict):
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

    def __getitem__(self, key):
        return IterJ(self.value[key])