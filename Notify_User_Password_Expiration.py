# AWS Lambda to check for Console users with expired or expiring Console Passwords.
# Requires an SNS Topic to be created and Subscribed to for report delivery.

# Lambda Permissions
# IAM: GenerateCredentialReport
# IAM: GetCredentialReport
# SNS: Publish

import boto3
import datetime
import csv
import dateutil.parser
from time import sleep
from botocore.exceptions import ClientError

iam_client = boto3.client('iam')

def lambda_handler(event, context):
    sns_client = boto3.client('sns')
    max_age = get_max_password_age(iam_client)
    # Send Expiring Passwords Report to SNS Topic.
    sns_client.publish(
        TopicArn='<SNS TOPIC ARN>',
        Message=check_if_expiring(get_credential_report(iam_client), max_age)
        )
    

# Download Credential Report
def get_credential_report(iam_client):
    resp = iam_client.generate_credential_report()
    # Try to download report, if not retry.
    if resp['State'] == 'COMPLETE':
        try: 
            response = iam_client.get_credential_report()
            credential_report_csv = response['Content'].decode('utf-8') # decode otherwise downloads in bytes, not str.
            reader = csv.DictReader(credential_report_csv.splitlines())
            credential_report = []
            for row in reader:
                credential_report.append(row)
            return(credential_report) # Return Credential Report to be parsed.
        except ClientError as e:
            print("Unknown error getting Report: " + str(e))
    else:
        sleep(2)
        return get_credential_report(iam_client)

def check_if_expiring(credential_report, max_age):
    REPORT_SUMMARY = ""
    expired_message = "\n\tYour Password is {} days post expiration. Your permissions have been revoked. "
    for row in credential_report:
        if row['password_enabled'] != "true": continue # Skip IAM Users without passwords

        # Process their password
        password_expires = days_till_expire(row['password_last_changed'], max_age)
        if password_expires <= 0:
            REPORT_SUMMARY = REPORT_SUMMARY + "\n{}'s Password expired {} days ago".format(row['user'], password_expires * -1)
        elif password_expires < max_age:
            REPORT_SUMMARY = REPORT_SUMMARY + "\n{}'s Password will expire in {} days".format(row['user'], password_expires)
    return REPORT_SUMMARY
    
# Get Max Password Age from AWS Console Password Policy
def get_max_password_age(iam_client):
    try: 
        response = iam_client.get_account_password_policy()
        return response['PasswordPolicy']['MaxPasswordAge']
    except ClientError as e:
        print("Unexpected error in get_max_password_age: %s" + e.message) 
        
def days_till_expire(last_changed, max_age):
    # Ok - So last_changed can either be a string to parse or already a datetime object.
    # Handle these accordingly
    if type(last_changed) is str:
        last_changed_date=dateutil.parser.parse(last_changed).date()
    elif type(last_changed) is datetime.datetime:
        last_changed_date=last_changed.date()
    else:
        return -99999
    expires = (last_changed_date + datetime.timedelta(get_max_password_age(iam_client))) - datetime.date.today()
    return(expires.days)
