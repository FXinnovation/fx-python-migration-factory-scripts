#!/bin/bash

### --------------------------------------------------------------------
###   install-ssm-agent.sh | © 2021 FXInnovation
### --------------------------------------------------------------------
###   Script which will install SSM Agent
### --------------------------------------------------------------------
###   This code is for the use of "© 2021 FXInnovation" only.
###   Individuals using this code without authority, or in violation
###   of copyright are subject to investigation. Any evidence of
###   copyright infringement will be reported to law enforcement officials.
### --------------------------------------------------------------------

REDHAT_VERSION=$(cat /etc/redhat-release | awk -F'[^0-9]*' '$0=$2')
REGION=us-east-1

if [ "${REDHAT_VERSION}" -ge 7 ]
then
    sudo yum install -y /tmp/amazon-ssm-agent-redhat7.rpm
    sudo systemctl start amazon-ssm-agent
    sudo systemctl enable amazon-ssm-agent
elif [[ "${REDHAT_VERSION}" -lt 7 ]]
then
    sudo yum install -y /tmp/amazon-ssm-agent-redhat6.rpm
    sudo start amazon-ssm-agent
else
    echo "Could not install SSM agent: unknown version of redhat: ${REDHAT_VERSION}"
fi
