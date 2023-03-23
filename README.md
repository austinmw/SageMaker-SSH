# Connect Your Local VS Code IDE to a SageMaker Notebook Instance

**This CDK app allows you to connect a local VS Code IDE to a SageMaker Notebook Instance.**

It does this by creating a VPC and placing both the SageMaker notebook instance as well as a small EC2 instance inside it. The EC2 instance acts as a bastion, providing access to the SageMaker instance through the externally accessible EC2 instance.

## Getting Started

Open a terminal, and first make sure that you've previously ran `aws configure` so that your shell has proper access to your AWS account. You can test this access by running `aws s3 ls`.

Also note that an `~/.ssh/config` file should exist on your system. The deploy and tear down steps will modify this file to add/remove hosts.

Note that this app has only been tested on MacOS.

### Bootstrap the CDK
`make bootstrap`

### Configure the app
Edit the `config.yaml` file as necessary. The default settings are:
```yaml
region: default

ec2:
  instance_type: t2.micro

notebook:
  name: accessible-notebook
  append_username: true
  instance_type: ml.c5.xlarge
  volume_size: 30

lifecycle:
  name: bastion-lifecycle-config

ssh:
  key_name: bastion-ssh-key
```

### Deployment
`make`

After this runs, follow the steps printed in your console, which include opening the SageMaker notebook instance, and pasting the public key. This will allow SSH access to your notebook via `ssh sagemaker-notebook`, as well as VS Code access via the Remote Explorer tab.

### Tear down
`make clean`


## Acknowledgements

Thanks to the following blog post for inspiration and the SageMaker lifecycle script: https://modelpredict.com/sagemaker-ssh-setup/