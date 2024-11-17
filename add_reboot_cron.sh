#!/bin/bash

CRON_ENTRY="@reboot /home/dlinano/workspace/traffic-light/app_start.sh >> /home/dlinano/workspace/traffic-light/app_start.log 2>&1"
if crontab -l | grep -q "$CRON_ENTRY"; then
    echo "Cron entry already exists."
else
    (crontab -l ; echo "$CRON_ENTRY") | crontab -
    echo "Cron entry added successfully."
fi