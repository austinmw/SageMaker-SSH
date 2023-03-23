import os

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
instance_type = config["ec2"]["instance_type"]
lifecycle_name = config["lifecycle"]["name"]

# Define Bastion stack
class BastionStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Get the keypair name from the KeyStack
        keypair_name = Fn.import_value("keypair-name")

        # Create a VPC with two subnets
        vpc = ec2.Vpc(self, "MyVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                )
            ]
        )

        # Create the security groups
        sg1 = ec2.SecurityGroup(self, "SG1",
            vpc=vpc,
            allow_all_outbound=False,
            security_group_name="sg1"
        )

        sg2 = ec2.SecurityGroup(self, "SG2",
            vpc=vpc,
            allow_all_outbound=True,
            security_group_name="sg2"
        )

        # Add the rules to the security groups
        sg1.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="SSH access from anywhere"
        )
        sg1.add_egress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(22),
            description="SSH access to subnet 2"
        )

        sg2.add_ingress_rule(
            peer=sg1,
            connection=ec2.Port.tcp(22),
            description="SSH access from subnet 1"
        )

        # Export the resources
        CfnOutput(self, "SageMakerVPC",
            value=vpc.vpc_id,
            export_name="MyVPC-VPCID"
        )

        CfnOutput(self, "SageMakerSubnet",
            value=vpc.private_subnets[0].subnet_id,
            export_name="MyVPC-PrivateSubnet2"
        )

        CfnOutput(self, "SageMakerSecurityGroup",
            value=sg2.security_group_id,
            export_name="MyVPC-SecurityGroup2"
        )


        # Create an EC2 instance
        ec2_instance = ec2.Instance(
            self, "MyEc2Instance",
            instance_type=ec2.InstanceType(instance_type),
            machine_image=ec2.MachineImage.latest_amazon_linux(),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_group=sg1,
            key_name=keypair_name,
        )
        # Output the instance ID
        CfnOutput(self, "InstanceID", value=ec2_instance.instance_id)

        # Allocate and associate an Elastic IP
        elastic_ip = ec2.CfnEIP(self, "MyEIP")
        eip_assoc = ec2.CfnEIPAssociation(
            self, "MyEIPAssociation",
            instance_id=ec2_instance.instance_id,
            eip=elastic_ip.ref
        )
        CfnOutput(self, "PublicIP", value=elastic_ip.attr_public_ip)

        # Read lifecycle scripts' contents
        with open("lifecycle/on-create.sh") as f:
            oncreate_content = f.read()
        with open("lifecycle/on-start.sh") as f:
            onstart_content = f.read()
 
        # Create a SageMaker lifecycle configuration resource
        lifecycle_config = sagemaker.CfnNotebookInstanceLifecycleConfig(
            self,
            "MyLifecycleConfig",
            notebook_instance_lifecycle_config_name=lifecycle_name,
            on_create=[sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
                content=Fn.base64(oncreate_content)
            )],
            on_start=[sagemaker.CfnNotebookInstanceLifecycleConfig.NotebookInstanceLifecycleHookProperty(
                content=Fn.base64(onstart_content)
            )],
        )
        # Output the lifecycle config name
        CfnOutput(self, "MIDIFLifecycleConfig",
                      value=lifecycle_config.notebook_instance_lifecycle_config_name)

