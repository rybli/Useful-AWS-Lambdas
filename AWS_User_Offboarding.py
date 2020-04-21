# Need to have 2 Environment Variables: DeactivaceUser, DryRun
# DeactivateUser - AWS Username
# DryRun - True/False

# Lambda Permissions
# CloudWatch Logs: Write - CreateLogStream, PutLogEvents, CreateLogGroup
# IAM: List - GetLoginProfile, ListAccessKeys, ListAttachedUserPolicies, ListGroupsForUser, ListMFADevices, ListUserPolicies
# IAM: Read - GetUser
# IAM: Write - DeactivateMFADevice, DeleteLoginProfile, DeleteVirtualMFADevice, RemoveUserFromGroup, UpdateAccessKey
# IAM: Permissions management - DeleteUserPolicy, DetachUserPolicy

import boto3
import os
from botocore.exceptions import ClientError

DeactivateUser = os.environ['DeactivateUser']
DryRun = bool(os.environ['DryRun'].lower() != 'false')

def lambda_handler(event, context):
    iam_client = boto3.client('iam')
    response = iam_client.get_user(UserName=DeactivateUser)
    print(response)
    
    try:
        # Make Keys inactive
        response = iam_client.list_access_keys(UserName=DeactivateUser)
        for key in response['AccessKeyMetadata'] :
            if key['Status'] == "Active":
                if DryRun == False:
                    print('Key test')
                    #response = iam_client.update_access_key(UserName=DeactivateUser, AccessKeyId=key['AccessKeyId'], Status='Inactive')
                print("User=%s removed AccessKey=%s" % (DeactivateUser, key['AccessKeyId']))

        # Remove users from all Groups
        user_groups = iam_client.list_groups_for_user(UserName=DeactivateUser)
        for g in user_groups['Groups']:
            if DryRun == False:
                print('Group test')
                #response = iam_client.remove_user_from_group(GroupName=g['GroupName'], UserName=DeactivateUser)
            print("User=%s removed from Group=%s" % (DeactivateUser, g['GroupName']))
        
        # Remove user MFA Device
        user_mfa_devices = iam_client.list_mfa_devices(UserName=DeactivateUser)
        for d in user_mfa_devices['MFADevices']:
            if DryRun == False:
                print('MFA test')
                #response = iam_client.deactivate_mfa_device(SerialNumber=d['SerialNumber'], UserName=DeactivateUser)
            print("User=%s deactivated MFA=%s" % (DeactivateUser, d['SerialNumber']))
            if DryRun == False:
                print('Dig MFA test')
                #response = iam_client.delete_virtual_mfa_device(SerialNumber=d['SerialNumber'])
            print("Removed MFA=%s" % (d['SerialNumber']))
        
        # Remove user inline policies
        user_inline_policies = iam_client.list_user_policies(UserName=DeactivateUser)
        for i_policy in range(len(user_inline_policies['PolicyNames'])):
            print("User=%s removed inline policies=%s" % (DeactivateUser, user_inline_policies['PolicyNames'][i_policy]))
            if DryRun == False:
                print('Inline Policy test')
                #response = iam_client.delete_user_policy(UserName=DeactivateUser,PolicyName=user_inline_policies['PolicyNames'][i_policy])

        # Remove user managed policies
        user_managed_policies = iam_client.list_attached_user_policies(UserName=DeactivateUser)
        for m_policy in user_managed_policies['AttachedPolicies']:
            print("arn:", m_policy['PolicyArn'])
            if DryRun == False:
                print('Managed Policy test')
                #response = iam_client.detach_user_policy(UserName=DeactivateUser,PolicyArn=m_policy['PolicyArn'])
            print("User=%s removed managed policy=%s" % (DeactivateUser, m_policy['PolicyArn']))
            
        # Deactivate Console Access
        if DryRun == False:
            print('Console test')
            #response = iam_client.get_login_profile(UserName=DeactivateUser)
            if response['LoginProfile']['UserName']:
                #response = iam_client.delete_login_profile(UserName=DeactivateUser)
                print("User:%s login profile deleted" % (DeactivateUser))
            else:
                print("User:%s login profile does not exist" % (DeactivateUser))

    except ClientError as e:
        raise
