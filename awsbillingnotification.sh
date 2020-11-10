#!/bin/bash

set -x

from_email="$from_email"
to_email="$to_email"

max_estimated_charge_12_hour=$(aws --region us-east-1 cloudwatch get-metric-statistics \
 --namespace "AWS/Billing" \
 --metric-name "EstimatedCharges" \
 --dimension "Name=Currency,Value=USD" \
 --start-time $(date +"%Y-%m-%dT%H:%M:00" --date="-12 hours") --end-time $(date +"%Y-%m-%dT%H:%M:00") \
 --statistic Maximum \
 --period 60 \
 --output text | sort -r -k 3 | head -n 1 | cut -f 2)

 max_estimated_charge_before_last_12_hour=$(aws --region us-east-1 cloudwatch get-metric-statistics \
 --namespace "AWS/Billing" \
 --metric-name "EstimatedCharges" \
 --dimension "Name=Currency,Value=USD" \
 --start-time $(date +"%Y-%m-%dT%H:%M:00" \
 --date="-24 hours") \
 --end-time $(date +"%Y-%m-%dT%H:%M:00" --date="-12 hours") \
 --statistic Maximum \
 --period 60 \
 --output text | sort -r -k 3 | head -n 1 | cut -f 2)

bill=$(echo "$max_estimated_charge_12_hour $max_estimated_charge_before_last_12_hour" | awk '{print $1-$2}') \
ALERT=2
while :; do sleep 12h; echo "aws billing notification" | if [ ${bill%.*} -gt $ALERT ] ; then \
 aws ses send-email \
  --from "$from_email" \
  --destination "ToAddresses=<$to_email>" \
  --message "Subject={Data= Billing alert,Charset=utf8},Body={Text={Data=Last 12 hour AWS  bill `echo $cluster` `echo $bill`,Charset=utf8}}" \
  --region "us-east-1" ;fi; done
