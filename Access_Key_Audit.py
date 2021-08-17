# Service Accounts: If Access Key is older than 365 days, make inactive
# User Accounts: If Access Key is older than 60 days, make inactive

# Lambda Permissions
# IAM: ListGroups
# IAM: GetGroup
# IAM: ListAccessKeys
# IAM: UpdateAccessKey

import boto3
import datetime
from dateutil.tz import tzutc
from collections import defaultdict

# Set up IAM client
iam_client = boto3.client('iam')

def lambda_handler(event, context):
    print(access_key_report()) # Print the report
    disable_outdated_keys() # Disable keys that are outdated

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
            if key['Status'] == 'Active' and key['CreateDate'] <= user_Max_Age:
                user_access_keys[user].append(key['AccessKeyId'])
    
    # Audit Service Account Acccess keys                
    for service in services:
        for key in iam_client.list_access_keys(UserName=service)['AccessKeyMetadata']:
            if key['Status'] == 'Active' and key['CreateDate'] <= service_Max_Age:
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
            final_report += f'{key} has the following access key(s) older than 365 days: {dict(services)[key]}\n'

    return final_report
    
# Loop through entries in active_access_keys() function and set each key to 'Inactive'.
def disable_outdated_keys():
    for entry in active_access_keys():
        for user, keys in dict(entry).items():
            for key in keys:
                iam_client.update_access_key(UserName=user, AccessKeyId=key, Status='Inactive')
                print(f'Set {user}\'s key: {key} to Inactive.')
