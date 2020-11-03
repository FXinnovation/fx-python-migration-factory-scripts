#!/usr/bin/env sh

INSTALL_CRON=false
DOC=/usr/local/share/applications/migration_factory
CONFIG_DESTINATION_PATH=/etc/migration_factory
ENDPOINT_FILE=endpoints.json
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

check_arguments "$@"

git reset --hard HEAD
git checkout master
git pull --rebase origin master

sudo cp scripts/* /usr/local/bin/
sudo mkdir -p "$CONFIG_DESTINATION_PATH"

if [ -f "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE.new" ]; then
    cmp --silent "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE.new" || cp "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE.new"
else
  if [ -f "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE" ]; then
    cmp --silent "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE" || cp "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_PATH/$ENDPOINT_FILE.new"
  else
    cp "config/$ENDPOINT_FILE" "$CONFIG_DESTINATION_FILE/$ENDPOINT_FILE"
  fi
fi

sudo mkdir -p "$DOC"
sudo cp config/0-import-tags.csv config/0-Migration-intake-form.csv "$DOC"

if [ "$INSTALL_CRON" = true ] ; then
    if [ `crontab -l | grep -q "*/10 * * * * $DIR/$0"` ] ; then
        crontab -l > install_mf_script
        echo "*/10 * * * * $DIR/$0" >> install_mf_script
        crontab install_mf_script
        rm install_mf_script
    fi
fi
