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
1. Modify the file `/etc/migration_factory/endpoints.yml` to add URL API;
1. Modify the file `/etc/migration_factory/defaults.yml` to give the defaults values by environments;
1. *optional* - Add an alias on your shell profile to run the script `mf_setup_environment` properly. `alias mf_setup_environment="source /usr/local/bin/mf_setup_environment"`
1. Enjoy !

## Defaults

A file containing default values will be installed. See [installation](#installation).
When environment in passed as an argument of any script, it will check dynamically that a key corresponding to the given environment exists in the defaults file.

## Environment variable

Here are all main environment variable:

* `MF_USERNAME`: The username used to log on the migration factory
* `MF_PASSWORD`: The password used to log on the migration factory
* `MF_CE_API_TOKEN`: The Cloud Endure API token
* `MF_AWS_ACCESS_KEY_ID`: The AWS access key id of the target account
* `MF_AWS_SECRET_ACCESS_KEY`: The AWS secret access key of the target account
* `MF_AWS_REGION`: The AWS region of the target account
* `MF_ENDPOINT_CONFIG_FILE`: The location of endpoint config file
* `MF_WINDOWS_USERNAME`: The Windows username to connect to source host
* `MF_WINDOWS_PASSWORD`: The Windows password to connect to source host
* `MF_LINUX_USERNAME`: The linux username to connect to source host
* `MF_LINUX_PASSWORD`: The linux password to connect to source host
* `MF_LINUX_PRIVATE_KEY_PASSPHRASE`: The linux passphrase for the private key file to connect to source host
* `MF_LINUX_PRIVATE_KEY_FILE`: This linux private key file to connect to source host


Also supported for edge cases:

* `MF_CONFIG_FILE`: Path of the YAML main configuration file
* `MF_ENDPOINT_CONFIG_FILE`: Path of the YAML configuration file containing endpoints configuration
* `MF_DEFAULTS_CONFIG_FILE`: Path of the YAML configuration file containing default values and environments

You can also use the command `source mf_setup_environment` to set all these environment variables

## Technical documentation

See [this repository wiki](https://github.com/FXinnovation/fx-python-migration-factory-scripts/wiki).

## Versioning
This repository follows [Semantic Versioning 2.0.0](https://semver.org/)

## Git Hooks
This repository uses [pre-commit](https://pre-commit.com/) hooks.

### Usage

```
pre-commit install
pre-commit run -a
```

## Commit Messages

This repository follows the [afcmf](https://github.com/FXinnovation/fx-pre-commit-afcmf) standard for it's commit messages.

## NOTE

* This works only on Linux
* `0-AddProxy-Windows.py` is not working for now.

## Process of Migration Factory Removal

#### History

We would like to get rid of the AWS Migration Factory because of the following reasons:

1. AWS refused to handle feature updates of the Migration Factory.
FX had an official meeting with them and the official Migration Factory project manager said it will not be possible to add any features.
E.g. Private IPs addresses or GP3 are not supported and thus these scripts are made unuseful if we want to use these features.

1. As an alternative, FX could get the Migration Factory code and maintain it themselves.
We believe that is too much work to do that, especially since we already decided to support the current scripts.
Also, lambdas for Migration Factory are very badly written and would require a lot of rework.
For instance, a lot of portion of the lambdas code uses now deprecated python 2.X.

1. Migration Factory gives very few features above the scripts of this project, mainly two things: handling environments (dev and prod) for security groups and subnets and an interface for cutover/test to cloudendure API.Factory
For such little improvement, Migration Factory is a very heavy product that contains: lambdas, CloudFront distribution, API gateway, dynamoDB… Incurring costs, maintenance and complexity in our scripts code.
Moreover, we believe such features are not very complex to implement in our current scripts.

1. Migration Factory brings added complexity when a new feature is released in cloudendure, as it is a middleware.
It becomes harder to debug issues, requires time to wait for Migration Factory updates.

1. As stated in previous point, Migration Factory uses a lot of product from AWS, thus it costs money.

#### Plan

Each of the steps should be its own pull request.
These steps are optimized for a quick change first, clean after approach without sacrifice of the code quality in the end.

##### Prepare - no feature change

1. Optional (but recommended): update all the scripts calling the Migration Factory API directly without using `mf.migration_factory`.
At the end of this step, every script should use the `mf.migration_factory`.
This will greatly simplify the jobs to come after.

1. Add support for a DB storage locally, e.g. sqlite.
Update the installation script to install/configure the chosen DBMS.
Update `requirements.txt` to add support for the chosen DBMS

1. Adapt code to uses local DB storage.
Update the code of `mf.migration_factory`.
Each call to the AWS Migration Factory must stay for now, but each function should duplicated the create/update/delete operations in the local DB system.
You will probably need to create new library classes to handle inserts/updates/deletes for the DB system.
Import this library in `mf.migration_factory` libs.
Do not make any changes in any scripts, except the ones calling migration factory directly (not necessary if you did the first step).

##### Remove Dependency - feature change

1. Change launch `mf.migration_factory.MigrationFactoryRequester.launch_target()`.
This method will talk to the cloudEndure API directly, using local DB data.
Test extensively.

##### Cleaning for future maintenance

1. Remove all code making requests to Migration Factory in `mf.migration_factory`.
Except the term, no requests to Migration Factory should be done by any scripts after this step.

1. Move/Rename `mf.migration_factory` lib classes/method to a new namespace named `mf.core_database` (or a better name if you think about one).
Update all the scripts to use this new classes instead of the "old" calls to `mf.migration_factory`.
At the end of this step, the terms "Migration Factory" to refer to AWS Migration Factory should have entirely disappeared from the code.

1. Update this README to remove these instructions.
Remove any trace of MigrationFactory on any client, by running a destroy of the MF CloudFormation stack.
