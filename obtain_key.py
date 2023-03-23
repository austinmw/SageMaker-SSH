import argparse
import base64
import json
import os
import subprocess

import boto3
import yaml
from botocore.exceptions import ClientError
import paramiko

from ssh_utils import SSHConfig, private_to_public_key

parser = argparse.ArgumentParser(description='Retrieve or remove a parameter from SSM Parameter Store')
parser.add_argument('action', choices=['get', 'remove'], help='Action to perform: "get" to retrieve the parameter or "remove" to delete the key file')
args = parser.parse_args()

# Get outputs
with open('outputs.json') as file:
    outputs = json.load(file)
region = outputs['KeyStack']['Region']
key_name = outputs['KeyStack']['MyKeyPairName']
key_parameter_name = outputs['KeyStack']['MyKeyPairParameterName']
key_filename = key_name + '.pem'
key_filepath = os.path.expanduser(os.path.join('~', '.ssh', key_filename))
bastion_ip = outputs['BastionStack']['PublicIP']
notebook_instance_name = outputs['SageMakerStack']['SageMakerNotebookName']
notebook_url = outputs['SageMakerStack']['SageMakerNotebookURL']

# Create a Boto3 client for the SSM service
ssm = boto3.client('ssm', region_name=region)

# Instantiate an SSHConfig object
ssh_config_file = os.path.expanduser(os.path.join('~', '.ssh', 'config'))
config = SSHConfig(ssh_config_file)


if args.action == 'get':
    try:
        # Retrieve the parameter value
        response = ssm.get_parameter(
            Name=key_parameter_name,
            WithDecryption=True,
        )
        param_value = response['Parameter']['Value']

        # Print the parameter value
        #print(f'The value of parameter {key_parameter_name} is:\n{param_value}')

        # Write the key to a file and set permissions
        with open(key_filename, 'w') as f:
            f.write(param_value)
        subprocess.run(['sudo', 'mv', key_filename, key_filepath])
        subprocess.run(['sudo', 'chmod', '400', key_filepath])
        print(f'Wrote key to file: {key_filepath}')

        # Get public key
        public_key_str = private_to_public_key(key_filepath)

        # Create a Boto3 EC2 client
        ec2 = boto3.client('ec2')

        # Get the NetworkInterfaceId from the SageMaker notebook instance
        sagemaker = boto3.client('sagemaker')

        # Get the NetworkInterfaceId from the SageMaker notebook instance
        network_interface_id = sagemaker.describe_notebook_instance(NotebookInstanceName=notebook_instance_name)['NetworkInterfaceId']

        # Describe the network interface and get its PrivateIpAddress
        response = ec2.describe_network_interfaces(NetworkInterfaceIds=[network_interface_id])
        sagemaker_ip = response['NetworkInterfaces'][0]['PrivateIpAddress']

        # Add a new bastion host
        new_host_bastion = {
            'Hostname': bastion_ip,
            'User': 'ec2-user',
            'ForwardAgent': 'yes',
            'IdentityFile': key_filepath,
            'ForwardX11': 'yes',
        }

        # Add a new notebook host
        new_host_notebook = {
            'Hostname': sagemaker_ip,
            'User': 'ec2-user',
            'UserKnownHostsFile': '/dev/null',
            'StrictHostKeyChecking': 'no',
            'ProxyCommand': 'ssh -W %h:%p ec2-user@ec2-bastion',
            'IdentityFile': key_filepath,
            'LocalForward': '6006 localhost:6006', # Tensorboard
            'ForwardX11': 'yes',
        }

        # Add the hosts to the SSH config
        config.add_host("ec2-bastion", **new_host_bastion)
        config.add_host("sagemaker-notebook", **new_host_notebook)

        # Print the new hosts
        config.print_host("ec2-bastion")
        config.print_host("sagemaker-notebook")

        # Output the connection command
        #public_ip_str = bastion_ip.replace(".", "-")
        #connect_str = f"ssh -i '~/.ssh/{key_name}.pem' ec2-user@ec2-{public_ip_str}.compute-1.amazonaws.com"
        connect_str = f"ssh ec2-bastion"
        print(f"\033[36m{connect_str}\033[0m")

        # Get the public key
        public_key_str = private_to_public_key(key_filepath)

        # Print the instructions
        green = '\033[32m'
        reset = '\033[0m'
        print(f'{green}Step 1. Open the Notebook instance at:\n{notebook_url}\n')
        print(f'Step 2. Paste the following contents into the file ssh/authorized_keys:\n{public_key_str}\n')
        print(f'Step 3. Open a terminal in the notebook and run the following command:\ncopy-ssh-keys\n')
        print(f'Step 4. Connect to the notebook instance:\nssh sagemaker-notebook{reset}\n')
        print(f'Step 5: Open VS Code, go to the Remote Explorer tab, click the plus sign next to SSH, and enter the following:\nsagemaker-notebook\n')

    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            print(f'Parameter {key_parameter_name} not found.')
        else:
            print(f'Error retrieving parameter {key_parameter_name}: {e}')

elif args.action == 'remove':
    try:
        # Remove the key file
        os.remove(key_filepath)
        print(f'Removed key file: {key_filepath}')
        # Remove the hosts from the SSH config
        config.delete_host('ec2-bastion')
        config.delete_host('sagemaker-notebook')
        print('Removed hosts from SSH config')

    except OSError as e:
        print(f'Error running remove: {e}')
else:
    print(f'Invalid action: {args.action}')