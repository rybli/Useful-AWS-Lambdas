# Need to have 1 Environment Variables: ageLimit
# ageLimit - NumberOfDays(int)

# Lambda Permissions
# CloudWatch Logs: Write - CreateLogStream, PutLogEvents, CreateLogGroup
# IAM: - ListUsers, ListAccessKeys, UpdateAccessKey

import boto3
import os
import datetime
from dateutil.tz import tzutc

client = boto3.client('iam')

def lambda_handler(event, context):
    rotate_keys()

def list_users():
    users = []
    for user in client.list_users()['Users']:
        users.append(user['UserName'])
    return users

def active_access_keys():
    maxAge = datetime.datetime.now(tzutc()) - datetime.timedelta(days=int(os.environ['ageLimit']))
    access_keys = []
    for user in list_users():
        for key in client.list_access_keys(UserName=user)['AccessKeyMetadata']:
            if key['Status'] == 'Active':
                if key['CreateDate'] <= maxAge:
                    access_keys.append(key['AccessKeyId'])
    return access_keys
    
def rotate_keys():
    for key in active_access_keys():
        client.update_access_key(AccessKeyId=key, Status='Inactive')
