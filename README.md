# python-migration-factory-scripts

Linux and Windows compliant scripts for [the AWS Migration Factory](https://docs.aws.amazon.com/solutions/latest/aws-cloudendure-migration-factory-solution/welcome.html).

These scripts replace and add many features above [the scripts given by AWS](https://github.com/awslabs/aws-cloudendure-migration-factory-solution/blob/master/source/automation-scripts.zip) for the migration execution server.

## Pre-requisites

1. Install `python3`, `gssntlmssp`, `pwsh 7` with your OS package manager.

## Installation

You need to have git and curl install on the machine.

1. Clone this repository;
1. Move to into it;
1. Run `# install.sh` (careful, needs root permissions). You can use `--cron` to force scripts installation regularly, making sure VCS and server have the same code;
1. Modify the file `/etc/migration_factory/endpoints.json` to add URL APIs (This is deprecated, and will be remove soon in futur version. This is replace by `endpoint.yml`. For now, both are used);
1. Modify the file `/etc/migration_factory/endpoints.yml` to add URL APIs;
1. Modify the file `/etc/migration_factory/defaults.yml` to give the defaults values by environments;
1. *optional* - Add an alias on your shell profile to run the script `mf_setup_environment` properly. `alias mf_setup_environment="source /usr/local/bin/mf_setup_environment"`
1. Enjoy !

## Defaults

A file containing default values will be installed. See [installation](#installation).
When environment in passed as an argument of any script, it will check dynamically that a key corresponding to the given environment exists in the defaults file.

## Environment variable

Here are all supported environment variable:

* `MF_USERNAME`: The username used to log on the migration factory
* `MF_PASSWORD`: The password used to log on the migration factory
* `MF_CE_API_TOKEN`: The Cloud Endure API token
* `MF_AWS_ACCESS_KEY_ID`: The AWS access key id of the target account
* `MF_AWS_SECRET_ACCESS_KEY`: The AWS secret access key of the target account
* `MF_AWS_REGION`: The AWS region of the target account
* `MF_ENDPOINT_CONFIG_FILE`: The location of endpoint config file
* `MF_WINDOWS_USERNAME`: The Windows username to connect to source host
* `MF_WINDOWS_PASSWORD`: The Windows password to connect to source host

You can also use the command `source mf_setup_environment` to set all these environment variables

## Technical documentation

See [this repository wiki](https://scm.dazzlingwrench.fxinnovation.com/fxinnovation-public/python-migration-factory-scripts/wiki).

## Versioning
This repository follows [Semantic Versioning 2.0.0](https://semver.org/)

## Git Hooks
This repository uses [pre-commit](https://pre-commit.com/) hooks.

### Usage

```
pre-commit install
pre-commit install -t commit-msg
```

## Commit Messages

This repository follows the [afcmf](https://scm.dazzlingwrench.fxinnovation.com/fxinnovation-public/pre-commit-afcmf) standard for it's commit messages.

## NOTE

* This works only on Linux
* `0-AddProxy-Windows.py` is not working for now.
