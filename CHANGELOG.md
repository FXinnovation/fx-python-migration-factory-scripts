## 6.8.0

 * feat: Added the PSModule AWSPowerShell
 * feat: Added the 2nd vmware script to uninstall the tools by removing files and registry entries

## 6.7.2

  * fix: (delete_wave) makes sure the script does not crash even if wave ID is absent

## 6.7.1

* fix: download agent file without proxy

## 6.7.0

* refactor: Use enironment variable fetch static method
* feat: (library) Add `ENV_VAR_WINDOWS_USERNAME` and `ENV_VAR_WINDOWS_PASSWORD`

## 6.6.0

* feat: adds config.yml configuration file
* feat: adds notification library with Teams implementation
* feat: adds ConfigLoader class to load configuration
* feat: notifies at the end of the agent installation

## 6.5.3

* fix: makes sure CSV reader util can read multi line CSV
* fix: disable cache for GET requests immediatly after POSTS/PUTs
* fix: makes sure wave in MF is deleted properly
* fix: makes sure project in CloudEndure is deleted properly
* fix: makes sure project structure is deleted
* fix: do not throw error if wave-name does not exists for import CSV
* fix: fixes import CSV created_waves dict population
* fix: fixes import CSV created_apps dict population
* refactor: splits MF deletes in 3 steps for easier debugging

## 6.5.2

* fix: (library) Missing EOL separator for CSV import
* fix: (install-windows) Wrong list in powershell script
* fix: wrong constant call + add more verbose output

## 6.5.1

* fix: (import-tags) Wrong lower method usage when searching `server_id`

## 6.5.0

* feat: (prepare-wave) Generate CSV skeleton for tags
* refactor: (import-tgs) Improved import tags
* fix: Use `pip` module in install script
* doc: Update config example files

## 6.4.0

* feat: Add uninstall script for cloudamize

## 6.3.0

* refactor: remove endpoints.json and use EndpointLoader class
* doc: remove deprecated notice on endpoints.json

## 6.2.0

* feat: makes mf_delete_project only need wave_name
* feat: adds delete folder structure mf_delete_project
* fix: fixes import CSV scripts (wave and app creation skipped)
* fix: fixes import CSV scripts wrong blueprint

## 6.1.1

* fix: use subnet to get VPC ID for security group

## 6.1.0

* feat: adds requirements.txt file for pip dependencies
* feat: install dependencies in installation script

## 6.0.0

* feat: (library) adds MessageBag to store messages to log
* feat: (library) adds AWSValidator to validate common AWS resource names
* feat: (import-csv) Validates most of the fields of the CSV file
* feat: (import-csv) Adds CSV Intak data class
* feat(BREAKING): (library) MigrationFactoryRequester methods can now guess URL from URI automatically
* refactor: (import-csv) changes script to use the cloud_migration_requester
* refactor(BREAKING): changes input CSV headers fields to be all snake_case
* doc: link to technical documentation
* doc: better explain the intent of this repository
* fix: makes sure SG IDs are pre-filled with `mf_prepare_wave`

## 5.6.0

* feat: Add `mf_delete_project` script
* feat: Add `response_type` parameter to Request class
* feat: Add method to return directly the MF endpoint URL
* refactor: store endpoint loader object in `mf_prepare_wave`
* refactor: Move endpoints constant key to EndpointLoader class
* chore: Add pre-commit config and run it
* chore: Add Jenkinsfile pipeline

## 5.5.0

* feat: (library) Simplifies endpoint loader
* feat: (library) Reorganizes mf_library file into an actual python module
* feat: adds CE project creation in the `mf_prepare_wave` script
* feat: move local `_get_defaults` to the config object and improve it
* feat: adds Requester as a decorator on requests object for enhanced logging

## 5.4.0

* feat: adds Windows install AWS cli script
* feat: adds Windows uninstall AWS cli script
* feat: adds Windows install SSM agent script
* feat: adds Windows uninstall VMWare tools script

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
