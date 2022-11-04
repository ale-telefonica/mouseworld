"""
-------------------------------
Author: Alejandro Martin Herve
Version: 1.0.0
-------------------------------
Main Program
"""
import logging
from dataclasses import dataclass
from yaml import load, Loader

import settings


class Config(object):
    def __init__(self, config_file, _type=None):
        self.type = _type
        with open(config_file, encoding="utf-8") as configfd:
            self.config = load(configfd, Loader)

        self.validate_config_file()

    def validate_config_file(self):
        """
        Validate if OSM or Openstack configurtation have the correct
        key params acording with settings file
        """
        if self.type == "OSM":
            validator = settings.OSM_ACCESS_FILE_FILEDS
        elif self.type == "Openstack":
            validator = settings.OS_ACCESS_FILE_FILEDS
        for key in self.config:
            if key not in validator:
                raise(Exception(
                    f"{self.type} configuration file fields are incorrect. Please fix it using de format specified in settings."))
        return True

    def __getattr__(self, __name: str):
        return self.config[__name]


@dataclass
class IterJ:
    """
    Data structure to traverse json objects

    Access dict using the nomenclature iterj.key.key..., where iterj is the child 
    object of class IterJ, adn key, the dictionary key you want to acess.

    Access elements of list by using the nomenclature iterj.i<index>, where index
    is a number representing then index of the values you want access.

    To access the final result the value attribute must be called
    Example: iterj.key.i1.key.obj

    :param: obj: Json object to traverse
    """
    obj: dict

    def __getattr__(self, key):
        if isinstance(self.obj, list):
            value = self.obj[int(key[1])]
        elif isinstance(self.obj, str) and key != "value":
            return self.obj
        else:
            value = self.obj[key]
        return IterJ(value)

    def __getitem__(self, key):
        return IterJ(self.obj[key])


class Logger:
    """
    Handle logging info
    """

    def __init__(self, logger_name):
        self.root_logger = logger_name.split(".")[0]
        self.logger_name = logger_name
        self.logger = logging.getLogger(self.logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logging_settings = settings.LOGGING
        self.create_handlers()

    @staticmethod
    def create_formatter(formatter_info):
        formatter = logging.Formatter(formatter_info["format"])
        return formatter

    def create_handlers(self):
        handlers = self.logging_settings["loggers"][self.root_logger]["handlers"]
        for handler in handlers:
            handler_info = self.logging_settings["handlers"][handler]
            handler_instance = handler_info["cls"]()
            handler_instance.setLevel(handler_info["level"])
            
            formatter_name = handler_info["formatter"]
            formatter_info = self.logging_settings["formatters"][formatter_name]
            formatter = self.create_formatter(formatter_info)

            handler_instance.setFormatter(formatter)
            self.logger.addHandler(handler_instance)
    
    def debug(self, msg):
        self.logger.debug(msg)
    
    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)
    
    def error(self, msg):
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.critical(msg)
