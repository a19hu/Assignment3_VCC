#!/bin/bash

THRESHOLD=75
INSTANCE_NAME="autoscale-mac"
ZONE="us-central1-a"
LB_BACKEND="autoscale-backend"

while true; do
    CPU_USAGE=$(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')
    echo "Current CPU Usage: $CPU_USAGE%"

    if (( $(echo "$CPU_USAGE > $THRESHOLD" | bc -l) )); then
        echo "CPU usage high, launching cloud instance..."
        gcloud compute instances create $INSTANCE_NAME \
            --machine-type=e2-medium \
            --image-family=ubuntu-2004-lts \
            --image-project=ubuntu-os-cloud \
            --zone=$ZONE

        gcloud compute backend-services add-backend $LB_BACKEND \
            --instance-group=$INSTANCE_NAME \
            --global

        break
    fi

    sleep 30
done
