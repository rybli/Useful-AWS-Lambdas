# Must have SSM Agent installed on all machines
# Lambda Permissions Needed:
# EC2: List - DescribeInstances
# S3: Write - PutObject
# Systems Manager: List - ListInventoryEntries
# CloudWatch Logs: Write - CreateLogStream, PutLogEvents, CreateLogGroup

import boto3
import time
from datetime import datetime,timedelta

# Define filter
filter = [
    {
        'Name': 'tag:Deployment',
        'Values': ['DeploymentName']
    }
]

# Connect to aws resources
ec2 = boto3.resource('ec2')
ssm = boto3.client('ssm')
s3 = boto3.client('s3')

# Filename
bucket = "bucket-name"
fname = "path/to/folder/test1.csv"


def getSoftwareFromEntries(instanceId, entries):
    software_list = []
    
    for entry in entries:
        name = entry['Name']
        publisher = entry['Publisher']
        publisher = publisher.replace(',','')
        version = entry['Version'] 
        time = entry['InstalledTime']
        
        software_list.append(instanceId + "," + name + "," + version + "," + publisher + "," + time)
        
    return software_list

# Run the command generated from the get_command() function
def get_software():

     # Get a list of instances based on the filter
    response = ec2.instances.filter(Filters = filter)
    
    # Create empty list to populate with instances
    instances = []
    software_list = []
    
    # Populate the instances list
    for i in response:
        instances.append(i.id)

    # Find connected instances
    for i in instances:
        print(i)
        response = ssm.list_inventory_entries(InstanceId = i, TypeName = "AWS:Application")
        

        while response.get("NextToken"):
            ##print(response.get("NextToken"))
            software_list.extend(getSoftwareFromEntries(response.get("InstanceId"), response["Entries"]))
            response = ssm.list_inventory_entries(InstanceId = i, TypeName = "AWS:Application", NextToken = response.get("NextToken"))

        software_list.extend(getSoftwareFromEntries(response.get("InstanceId"), response["Entries"]))

    s3.put_object(Body='\n'.join(software_list), Bucket=bucket, Key=fname)
   
    
def lambda_handler(event, context):
    get_software()