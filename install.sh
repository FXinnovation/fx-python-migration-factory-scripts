#!/usr/bin/env sh

doc=/usr/local/share/applications/migration_factory
config=/etc/migration_factory

sudo cp scripts/* /usr/local/bin/
sudo mkdir -p $config
sudo cp endpoints.json $config
sudo mkdir -p $doc
sudo cp 0-import-tags.csv 0-Migration-intake-form.csv $doc
rm -rf $tmp_folder
