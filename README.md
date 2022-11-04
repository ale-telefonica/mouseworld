# Mouseworld
Software to automate Network Services deployments using Open Source Mano and Openstack in MouseWorld Lab

## Requirenments
1. Install osmcllient

### Snap Installation
```
sudo snap install osmclient
```

### Debian package installation
```
sudo sed -i "/osm-download.etsi.org/d" /etc/apt/sources.list
wget -qO - https://osm-download.etsi.org/repository/osm/debian/ReleaseTWELVE/OSM%20ETSI%20Release%20Key.gpg | sudo apt-key add -
sudo add-apt-repository -y "deb [arch=amd64] https://osm-download.etsi.org/repository/osm/debian/ReleaseTWELVE stable devops IM osmclient"
sudo apt-get update
sudo apt-get install -y python3-pip
sudo -H python3 -m pip install -U pip
sudo -H python3 -m pip install python-magic pyangbind verboselogs
sudo apt-get install python3-osmclient
```

2. Install python packages
```
pip install -r requirenments.txt
```

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
