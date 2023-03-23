#!/usr/bin/env bash

echo "Setting up ssh with bastion..."

# copy-ssh-keys script

# Create the .ssh directory in the /home/ec2-user directory and change the owner to the ec2-user user.
mkdir -p /home/ec2-user/.ssh && chown ec2-user:ec2-user /home/ec2-user/.ssh

# Overwrite the copy-ssh-keys file with the provided content.
cat > /usr/bin/copy-ssh-keys <<'EOF'
#!/usr/bin/env bash

set -e

# Create an empty authorized_keys file in the SageMaker/ssh directory and change the owner to the ec2-user user.
touch /home/ec2-user/SageMaker/authorized_keys
chown ec2-user:ec2-user /home/ec2-user/SageMaker/authorized_keys

# Copy the authorized_keys file to the /home/ec2-user/.ssh directory.
cp /home/ec2-user/SageMaker/authorized_keys /home/ec2-user/.ssh/authorized_keys
EOF

# Change the permissions of the copy-ssh-keys file to executable.
chmod +x /usr/bin/copy-ssh-keys

# Change the owner of the copy-ssh-keys file to the ec2-user user.
chown ec2-user:ec2-user /usr/bin/copy-ssh-keys

# Execute the copy-ssh-keys script.
copy-ssh-keys
