# Mouseworld
Software to automate Network Services deployments using Open Source Mano and Openstack in MouseWorld Lab

## Configuration
Before running the program the config files must be filled:
- **openstack_access.yaml**: Openstack access information
- **osm_access.yaml**: OSM access information

## Usage
```
Usage: mouseworld.py [OPTIONS] COMMAND [ARGS]...

Options:
  --scenario TEXT  Name of the scenario template to build (Template must exist       
                   in templates/scenarios folder)  [required]
  --help           Show this message and exit.

Commands:
  build   Build scenario template
  deploy  Deploy already build scenario
```