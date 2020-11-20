## 5.3.0

* fix: wrong EnvironmentFetcher signature

## 5.2.0

* feat: Add `mf_launch_target` script to launch cutover and test targets using CLI
* fix: install script to use python3 command to install tools
* doc: update to integrate previous changes (missing pre-requisite library)

## 5.1.0

* feat: adds some post install scripts for Windows machines
* fix: fixes windows file copy on old Windows

## 5.0.0

* feat: (library) Makes Utils class methods static
* feat: (library) Makes EnvironmentVariableFetcher fetch class methods static
* feat: (library) Allow EnvironmentVariableFetcher fetch to return default value
* refactor: (library) sets default constants for config files
* feat: (library) adds MigrationFactoryAuthenticator class to login to Migration Factory
* feat: adds endpoints.yml as the new main endpoint file, making endpoints.json deprecated

## 4.1.0

* feat: (library) adds AWSServiceAccessor to get access to AWS services
* feat: (library) adds EnvironmentVariableFetcher to fetch environment variables and fallback to user input
* feat: adds MF_AWS_REGION environment variable
* feat: renames template files to exclude the `0-` prefix
* fix: (installation script) removes error when trying to copy .pyc files

## 4.0.0

* feat (BREAKING): Add iamRole support in CSV import

## 3.3.1

* fix: fixes installation script

## 3.3.0

* feat: changes .csv templates to add examples + defaults

## 3.2.0

* feat: `mf_import_intake_form` Add wave id in outputs
* fix: wrong path for powershell libraries
* fix: `mf_setup_environment` issue with backslashes
* refactor: `mf_setup_environment` de-duplicate code

## 3.1.0

* feat: improve installation script to handle cron creation
* feat: improve installation script to create a .new file
* feat: adds default.yml template

## 3.0.0

* refactor (BREAKING): Rename scripts

## 2.1.0

* feat: Add `mf_setup_environment` script

## 2.0.0

* feat (BREAKING): Default endpoint config file is now located in `/etc/migration_factory/`
* feat: Add environment variable support for all asked credentials
* feat: Add parameter to define where endpoint config file is locacted
* feat: Add install script
* chore: Change dos encoding file to unix

## 1.0.0

* feat: init
