import getpass

import yaml
from aws_cdk import Aws, CfnOutput, Fn, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sagemaker as sagemaker
from constructs import Construct

# Get configs
account_id = Aws.ACCOUNT_ID
region = Aws.REGION

with open("config.yaml") as file:
    config = yaml.load(file, Loader=yaml.SafeLoader)
notebook_name = config["notebook"]["name"]
append_username = config["notebook"]["append_username"]
instance_type = config["notebook"]["instance_type"]
volume_size = config["notebook"]["volume_size"]
lifecycle_name = config["lifecycle"]["name"]

if append_username:
    username = getpass.getuser()
    notebook_name = f"{notebook_name}-{username}"


# Define SageMaker notebook stack
class SageMakerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get VPC, subnet, and security group IDs from the Bastion stack
        Fn.import_value("MyVPC-VPCID")
        subnet_id = Fn.import_value("MyVPC-PrivateSubnet2")
        security_group_id = Fn.import_value("MyVPC-SecurityGroup2")

        # Create role with the required policies and trust relationships
        role = iam.Role(
            self,
            "BastionSageMakerExecutionRole",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("sagemaker.amazonaws.com"),
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSStepFunctionsFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonS3FullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AWSCodeCommitFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "IAMReadOnlyAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMReadOnlyAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonEC2ContainerRegistryFullAccess"
                ),
            ],
        )
        # Print the RoleARN
        CfnOutput(self, "RoleARN", value=role.role_arn)

        # Create a SageMaker notebook instance
        notebook = sagemaker.CfnNotebookInstance(
            self,
            "SageMakerNotebook",
            notebook_instance_name=notebook_name,
            instance_type=instance_type,
            volume_size_in_gb=volume_size,
            role_arn=role.role_arn,
            subnet_id=subnet_id,
            security_group_ids=[security_group_id],
            lifecycle_config_name=lifecycle_name,
        )

        # Output SageMaker notebook instance name
        CfnOutput(
            self,
            "SageMakerNotebookName",
            value=notebook.notebook_instance_name,
        )

        # Output SageMaker Notebook Jupyter Lab URL
        CfnOutput(
            self,
            "SageMakerNotebookURL",
            value=f"https:/{region}.console.aws.amazon.com/sagemaker/home?"
            f"region={region}#/notebook-instances/openNotebook/"
            f"{notebook.notebook_instance_name}?view=lab",
        )
