# Environment Variable: timeLimit = integer (60, 90, etc.) days
# Lambda Permissions
# IAM: List - ListUsers

import boto3
import datetime
import os
from dateutil.tz import tzutc
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    inactive_90_days()

# Create list of Users who were last active 90+ days ago.    
def inactive_90_days():
    inactiveTime = datetime.datetime.now(tzutc()) - datetime.timedelta(days=int(os.environ['timeLimit']))
    users = []
    client = boto3.client('iam')
    response = client.list_users()
    for user in response['Users']: # For each user item in Users list
        if 'PasswordLastUsed' in user: # If PasswordLastUsed has no value then user has no password or password not used since October 20, 2014.
            if user['PasswordLastUsed'] <= inactiveTime: # If password older than inactive time add to list.
                users.append(user['UserName'])
                users.append(user['PasswordLastUsed'])
            else:
                print('All Users Active')
    # If users list is not empty, print.
    if users:
        print(users)
