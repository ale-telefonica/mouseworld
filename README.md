# Mouseworld
Software to automate Network Services deployments using Open Source Mano and Openstack in MouseWorld Lab

## Requirenments
1. Install osmcllient

```
sudo snap install osmclient
```

2. Install python packages
pip install -r requirenments.txt

## Configuration
### Before running the program the configuration files must be filled
1. Access files:
- **openstack_access.yaml**: Openstack access information. Located inside the **config** directory
- **osm_access.yaml**: OSM access information. Located inside the **config** directory

2. The scenario template must be created under the **scenarios** directory, following the sintax of the example template *general_template.yaml*, located inside the **/templates/scenarios** folder.

## Usage

```
Usage: mouseworld.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  build           Build scenario template
  deploy          Deploy already build scenario
  destroy         Destroy scenario
  list-scenarios  List scenarios
```
