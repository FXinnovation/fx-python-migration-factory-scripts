#!/bin/bash

### --------------------------------------------------------------------
###   install-cloudwatch-agent.sh | © 2021 FXInnovation
### --------------------------------------------------------------------
###   Script which will install cloudwatch agent
### --------------------------------------------------------------------
###   This code is for the use of "© 2021 FXInnovation" only.
###   Individuals using this code without authority, or in violation
###   of copyright are subject to investigation. Any evidence of
###   copyright infringement will be reported to law enforcement officials.
### --------------------------------------------------------------------

exec 1>>/tmp/migrate.log 2>&1
echo "`date -u` Installation of cloudwatch agent"

test -f /tmp/amazon-cloudwatch-agent-redhat.rpm && echo "package is present" ||  echo "package is not present"
sudo rpm -U /tmp/amazon-cloudwatch-agent-redhat.rpm
