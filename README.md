# python-migration-factory-scripts

Linux and Windows compliant scripts for the migration factory. 

## Pre-requisites

1. Install python3
1. Install python3 modules requests, paramiko and boto3
1. Install pwsh 7
1. Install gssntlmssp

## Installation

1. Copy the folder `scripts/` on a folder of your choice
1. Modify the file `FactoryEndpoints.json` to add the user and login API
1. Enjoy !

## NOTE

* This works only on Linux
* `0-AddProxy-Windows.py` and `4-Shutdown-all-servers.py` are not working for now. 
