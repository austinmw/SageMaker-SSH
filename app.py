import getpass
import json
import os

import aws_cdk as cdk
import yaml

from stacks.bastion_stack import BastionStack
from stacks.key_stack import KeyStack
from stacks.sagemaker_stack import SageMakerStack

# Get configs
with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
region = config["region"]

env = cdk.Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"] if region == "default" else region
    )

app = cdk.App()

# Generate a new SSH key pair using Paramiko
key = KeyStack(app, "KeyStack", env=env)

# Create a new EC2 instance using the key pair
bastion = BastionStack(app, "BastionStack", env=env)
bastion.add_dependency(key)

notebook = SageMakerStack(app, "SageMakerStack", env=env)
notebook.add_dependency(bastion)

# Add tags to stacks
for stack in [key, bastion, notebook]:
    cdk.Tags.of(stack).add("Creator", "CDK")
    cdk.Tags.of(stack).add("Description", "Dev stack")

app.synth()