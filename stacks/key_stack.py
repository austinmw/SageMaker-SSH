import os
import sys

import paramiko
import yaml
from aws_cdk import Aws, CfnOutput, Fn, RemovalPolicy, SecretValue, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_deployment as s3_deployment
from aws_cdk import aws_sagemaker as sagemaker
from aws_cdk import aws_ssm as ssm
from constructs import Construct


# Get configs
with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
key_name = config["ssh"]["key_name"]

# Get configs
account_id = Aws.ACCOUNT_ID
region = Aws.REGION

class KeyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a new key pair
        key_pair = ec2.CfnKeyPair(self, 'MyKeyPair',
                                  key_name=key_name,
                                  key_type='rsa')

        # Output the name of the key pair
        CfnOutput(self, "MyKeyPairName",
                  value=key_pair.key_name,
                  export_name="keypair-name")

        # Output the key pair Parameter Store name
        CfnOutput(self, "MyKeyPairParameterName",
                  value=f"/ec2/keypair/{key_pair.attr_key_pair_id}",
                  export_name="keypair-parameter-name")

        CfnOutput(self, "AccountID", value=account_id)
        CfnOutput(self, "Region", value=region)
