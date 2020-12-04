#!/usr/bin/env sh

INSTALL_CRON=false
TEMPLATES_PATH=/usr/local/share/applications/migration_factory
CONFIG_DESTINATION_PATH=/etc/migration_factory
ENDPOINT_FILE=endpoints.yml
DEFAULTS_FILE=defaults.yml
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

set -e

display_help() {
  echo "$0"
  echo " "
  echo "options:"
  echo "-h, --help                show brief help"
  echo "--cron                    setup cron to make sure scripts as the same a version control"
  exit 0
}

check_arguments() {
  while test "$#" -gt 0; do
    case "$1" in
    -h | --help)
      display_help
      exit 0
      ;;
    --cron)
      INSTALL_CRON=true
      shift
      ;;
    *)
      print_error "\e[1m$1\e[22m is not a valid option."
      exit 1
      ;;
    esac
  done
}

install_without_override() {
  local source_file="$1"
  local destination_file="$2"

  if [ -f "$destination_file.new" ]; then
    cmp --silent "$source_file" "$destination_file.new" || cp "$source_file" "$destination_file.new"
  else
    if [ -f "$destination_file" ]; then
      cmp --silent "$source_file" "$destination_file" || cp "$source_file" "$destination_file.new"
    else
      cp "$source_file" "$destination_file"
    fi
  fi
}

check_arguments "$@"

pip install -r requirements.txt

cd "$DIR"
git reset --hard HEAD
git checkout master
git pull --rebase origin master

find scripts -type f -not -iname '*pyc' -exec install '{}' '/usr/local/bin/' ';'
sudo mkdir -p "$CONFIG_DESTINATION_PATH"

mkdir -p /usr/local/bin/mf
find scripts/mf -type f -not -iname '*pyc' -exec install '{}' '/usr/local/bin/mf/' ';'

install_without_override "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE"
install_without_override "config/$DEFAULTS_FILE" "$CONFIG_DESTINATION_PATH/$DEFAULTS_FILE"

# Deprecated - To remove once no scripts uses "endpoints.json" anymore
install_without_override "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/endpoints.json"

sudo mkdir -p "$TEMPLATES_PATH"
sudo cp config/*.csv "$TEMPLATES_PATH"

python3 ./tools/create_server_attributes

if [ "$INSTALL_CRON" = true ] ; then
    if [ $(crontab -l | grep -q "$DIR/$0" && echo 0 || echo 1) -eq 1 ] ; then
        crontab -l > install_mf_script
        echo "*/10 * * * * $DIR/$0" >> install_mf_script
        crontab install_mf_script
        rm install_mf_script
    fi
fi
