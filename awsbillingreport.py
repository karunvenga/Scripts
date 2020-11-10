#!/usr/bin/env python3

from config.config import Config
from aws.ses import SES
import argparse
import boto3
import datetime
import csv
import time


def billing_report():
    print("-------Billing Report-------")
    TO_EMAIL = Config().get_env('TO_EMAIL')
    TO_EMAIL_LIST = TO_EMAIL.split(",")
    FROM_EMAIL = Config().get_env('FROM_EMAIL')
    SES('us-east-1').send_mail(FROM_EMAIL,
                               TO_EMAIL_LIST,
                               "",
                               "",
                               "Note: It's an automated email, please send an email to f5cs_sre@f5.com in case of any discrepancy in the report.",
                               ["aws_billing_report.csv"])
parser = argparse.ArgumentParser()
parser.add_argument('--days', type=int, default=30)
args = parser.parse_args()
now = datetime.datetime.utcnow()
start = (now - datetime.timedelta(days=args.days)).strftime('%Y-%m-%d')
end = now.strftime('%Y-%m-%d')
cd = boto3.client('ce', 'us-east-1')
results = []
token = None
while True:
    if token:
        kwargs = {'NextPageToken': token}
    else:
        kwargs = {}
    data = cd.get_cost_and_usage(TimePeriod={'Start': start, 'End':  end}, Granularity='MONTHLY', Metrics=['UnblendedCost'], GroupBy=[{'Type': 'DIMENSION', 'Key': 'LINKED_ACCOUNT'}, {'Type': 'DIMENSION', 'Key': 'SERVICE'}], **kwargs)
    results += data['ResultsByTime']
    token = data.get('NextPageToken')
    if not token:
        break


b_out = open('aws_billing_report.csv', 'w+')
total = 0
writer = csv.writer(b_out)
writer.writerow(['TimePeriod', 'LinkedAccount', 'Service', 'Amount', 'Unit', 'Estimated'])
for result_by_time in results:
    for group in result_by_time['Groups']:
        amount = group['Metrics']['UnblendedCost']['Amount']
        unit = group['Metrics']['UnblendedCost']['Unit']
        date_obj = result_by_time['TimePeriod']['Start']
        mydate = datetime.datetime.strptime(date_obj,'%Y-%m-%d')
        out_list=[mydate.strftime("%B")]
        out_list.extend(group['Keys'])
        out_list.extend([amount, unit, result_by_time['Estimated']])
        total = float(amount) + total
        writer.writerow(out_list)
writer.writerow(["Total Cost","","",total,""])

b_out.close()
billing_report()

