#!/usr/bin/env sh

tmp_folder=/tmp/migration_factory_fxinnovation
doc=/usr/local/share/applications/migration_factory
config=/etc/migration_factory

mkdir -p $tmp_folder
curl -L https://scm.dazzlingwrench.fxinnovation.com/fxinnovation-public/python-migration-factory-scripts/archive/2.0.0.zip -o $tmp_folder/migration.zip
cd $tmp_folder
unzip -o migration.zip
cd python-migration-factory-scripts
sudo cp scripts/* /usr/local/bin/
sudo rm -f /usr/local/bin/0-import-tags.csv
sudo rm -f /usr/local/bin/0-Migration-intake-form.csv
sudo mkdir -p $config
sudo cp endpoints.json $config
sudo mkdir -p $doc
sudo cp scripts/0-import-tags.csv 0-Migration-intake-form.csv $doc
rm -rf $tmp_folder
