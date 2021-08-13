# Create Report of access keys of Admin and Service accounts that are 60 and 365 days or older, respectively.

# Lambda Permissions
# IAM: ListGroups
# IAM: GetGroup
# IAM: ListAccessKeys

import boto3
import datetime
from dateutil.tz import tzutc
from collections import defaultdict

# Set up IAM client
iam_client = boto3.client('iam')

def lambda_handler(event, context):
    access_key_report()

# Grab list of user in the service_account group, and Administrators group
def get_users_from_group():
    # Set up service and user account lists
    service_accounts = []
    user_accounts = []
    
    # For every group, grab username and append to appropriate list
    groups = iam_client.list_groups()
    for group in groups["Groups"]:
        for user in iam_client.get_group(GroupName=group["GroupName"])["Users"]:
            # If user in Admin group, create username[[Access Keys]] key,value for dictionary
            if group["GroupName"] == "Administrators":
                user_accounts.append(user["UserName"])
            # If user in Service Account group, create username[[Access Keys]] key,value for dictionary
            elif group["GroupName"] == "service_accounts":
                service_accounts.append(user["UserName"])
            else:
                print("User not in Administrators or service_accounts gorup.")
    return user_accounts, service_accounts

def active_access_keys():
    users, services = get_users_from_group()
    # Set user_Max_Age allowed for user access key age. In this case 60 days.
    user_Max_Age = datetime.datetime.now(tzutc()) - datetime.timedelta(days=int(60))
    # Set service_MaX-Age allowed for user access key age. In this case 365 days.
    service_Max_Age = datetime.datetime.now(tzutc()) - datetime.timedelta(days=int(365))
    
    user_access_keys = defaultdict(list)
    service_access_keys = defaultdict(list)
    
    # Audit User Account Access keys
    for user in users:
        for key in iam_client.list_access_keys(UserName=user)['AccessKeyMetadata']:
            if key['Status'] == 'Active':
                if key['CreateDate'] <= user_Max_Age:
                    user_access_keys[user].append(key['AccessKeyId'])
    
    # Audit Service Account Acccess keys                
    for service in services:
        for key in iam_client.list_access_keys(UserName=service)['AccessKeyMetadata']:
            if key['Status'] == 'Active':
                if key['CreateDate'] <= service_Max_Age:
                    service_access_keys[user].append(key['AccessKeyId'])
    
    return user_access_keys, service_access_keys
    
# Create final report of access keys that are over their maximum allowable age.
def access_key_report():
    users, services = active_access_keys()
    final_report = ""
    if users:
        # Append user with keys to report.
        final_report += "User Accounts\n"
        for key in dict(users):
            final_report += f'{key} has the following access key(s) older than 60 days: {dict(users)[key]}\n'
    if services:
        # Append services with keys to report.
        final_report += '\nService Accounts\n'
        for key in dict(services):
            final_report += f'{key} has the following access key(s) older than 60 days: {dict(services)[key]}\n'
    
    return final_report
