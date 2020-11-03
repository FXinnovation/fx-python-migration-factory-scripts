#!/usr/bin/env sh

INSTALL_CRON=false
DOC=/usr/local/share/applications/migration_factory
CONFIG=/etc/migration_factory
ENDPOINT_FILE=endpoints.json
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

display_help() {
  echo "install.sh"
  echo " "
  echo "options:"
  echo "-h, --help                show brief help"
  echo "--cron                    setup cron to make sure scripts as the same a version control"
  exit 0
}

check_arguments() {
  while test $# -gt 0; do
    case "$1" in
    -h | --help)
      display_help
      ;;
    --cron)
      shift
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

sudo cp scripts/* /usr/local/bin/
sudo mkdir -p $CONFIG

if [ -f "$CONFIG/$ENDPOINT_FILE.new" ]; then
    cmp --silent $ENDPOINT_FILE "$CONFIG/$ENDPOINT_FILE.new" || cp $ENDPOINT_FILE "$CONFIG/$ENDPOINT_FILE.new"
else
  if [ -f "$CONFIG/$ENDPOINT_FILE" ]; then
    cmp --silent $ENDPOINT_FILE "$CONFIG/$ENDPOINT_FILE" || cp $ENDPOINT_FILE "$CONFIG/$ENDPOINT_FILE.new"
  else
    cp $ENDPOINT_FILE "$CONFIG/$ENDPOINT_FILE"
  fi
fi

sudo mkdir -p $DOC
sudo cp config/0-import-tags.csv config/0-Migration-intake-form.csv $DOC

if [ "$INSTALL_CRON" = true ] ; then
    crontab -l > install_mf_script
    echo "*/10 * * * * $DIR/install.sh" >> install_mf_script
    crontab install_mf_script
    rm install_mf_script
fi
