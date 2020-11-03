# python-migration-factory-scripts

Linux and Windows compliant scripts for the migration factory. 

## Pre-requisites

1. Install python3
1. Install python3 modules requests, paramiko and boto3
1. Install pwsh 7
1. Install gssntlmssp

## Installation

You need to have git and curl install on the machine. 

1. Clone this repository;
1. Move to into it;
1. Run `install.sh`. You can use `--cron` to force scripts installation regularly, making sure VCS and server have the same code;
1. Modify the file `/etc/migration_factory/endpoints.json` to add the user and login API
1. *optional* - Add an alias on your shell profile to run the script `mf_setup_environment` properly. `alias mf_setup_environment="source /usr/local/bin/mf_setup_environment"`
1. Enjoy !

## Environment variable

Here are all supported environment variable: 

* `MF_USERNAME`: The username used to log on the migration factory
* `MF_PASSWORD`: The password used to log on the migration factory
* `MF_CE_API_TOKEN`: The Cloud Endure API token
* `MF_AWS_ACCESS_KEY_ID`: The AWS access key id of the target account
* `MF_AWS_SECRET_ACCESS_KEY`: The AWS secret acces key of the target account
* `MF_ENDPOINT_CONFIG_FILE`: The location of endpoint config file
* `MF_WINDOWS_USERNAME`: The Windows username to connect to source host
* `MF_WINDOWS_PASSWORD`: The Windows password to connect to source host

You can also use the command `source mf_setup_environment` to set all these environment variables

## NOTE

* This works only on Linux
* `0-AddProxy-Windows.py` is not working for now. 
