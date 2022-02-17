mkdir -p charms/samplecharm/
cd charms/samplecharm/
mkdir hooks lib mod src
touch src/charm.py
touch actions.yaml metadata.yaml config.yaml
chmod +x src/charm.py
ln -s ../src/charm.py hooks/upgrade-charm
ln -s ../src/charm.py hooks/install
ln -s ../src/charm.py hooks/start
git clone https://github.com/canonical/operator mod/operator
git clone https://github.com/charmed-osm/charms.osm mod/charms.osm
ln -s ../mod/operator/ops lib/ops
ln -s ../mod/charms.osm/charms lib/charms