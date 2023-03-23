from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def private_to_public_key(private_key_path):
    """Convert a private key to a public key.

    Parameters
    ----------
    private_key_path : str
        The path to the private key file.

    Returns
    -------
    public_key : str
        The public key in OpenSSH format.
    """
    # Read the private key from the file
    with open(private_key_path, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    # Get the public key
    public_key = private_key.public_key()

    # Serialize the public key in OpenSSH format
    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    )

    # Print the public key string
    public_key_str = public_key_bytes.decode("utf-8") + " bastion-ssh-key"
    return public_key_str


class SSHConfig:
    """
    A class for parsing and modifying SSH config files.

    Parameters
    ----------
    filename : str
        The path to the SSH config file.

    Methods
    -------
    add_host(host, **kwargs)
        Adds a new host to the config file with the given keyword arguments.
    delete_host(host)
        Deletes a host from the config file.
    print_config()
        Prints the entire SSH config file.
    lookup_host(host)
        Returns a dictionary with the configuration for the specified host.
    print_host(host)
        Prints the configuration for the specified host.
    """

    def __init__(self, filename):
        self.filename = filename
        self.config = self._read_config()

    def _read_config(self):
        """Reads the SSH config file and returns a dictionary."""
        config = {}
        with open(self.filename, "r") as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith("Host"):
                    host = lines[i].strip().split()[1]
                    config[host] = {}
                    i += 1
                    while i < len(lines) and not lines[i].startswith("Host"):
                        line = lines[i].strip()
                        if line:
                            # Check that line has at least 2 words before trying to split it
                            if len(line.split()) >= 2:
                                key, value = line.split(maxsplit=1)
                                config[host][key] = value
                        i += 1
                else:
                    i += 1
        return config

    def _write_config(self):
        """Writes the updated ssh config to the file."""
        with open(self.filename, "w") as f:
            for host, config in self.config.items():
                f.write(f"Host {host}\n")
                for key, value in config.items():
                    f.write(f"    {key} {value}\n")
                f.write("\n")

    def add_host(self, host, **kwargs):
        """Adds a new host to the config file."""
        if host in self.config:
            print(f"Host {host} already exists in config.")
            #raise ValueError(f"Host {host} already exists in config.")
        self.config[host] = kwargs
        self._write_config()

    def delete_host(self, host):
        """Deletes a host from the config file."""
        if host not in self.config:
            print(f"Host {host} not found in config.")
            #raise ValueError(f"Host {host} not found in config.")
        del self.config[host]
        self._write_config()

    def print_config(self):
        """Prints the entire ssh config file."""
        with open(self.filename, "r") as f:
            print(f.read())

    def lookup_host(self, host):
        """Returns the configuration for a specific host."""
        if host not in self.config:
            raise ValueError("Host not found in config.")
        return self.config[host]

    def print_host(self, host):
        """Prints the configuration for a specific host."""
        host_info = self.lookup_host(host)
        print(f"Host {host}")
        for key, value in host_info.items():
            print(f"    {key} {value}")


if '__main__' == __name__:
    # Set the path to your ssh config file
    ssh_config_file = '/home/your-username/.ssh/config'

    # Add a new bastion host
    new_host_bastion = {
        'Hostname': '54.147.242.140',
        'User': 'ec2-user',
        'ForwardAgent': 'yes',
        'IdentityFile': '/Users/austinmw/Desktop/ssh-key.pem',
        'ForwardX11': 'yes',
    }

    # Add a new notebook host
    new_host_notebook = {
        'Hostname': '10.0.2.213',
        'User': 'ec2-user',
        'UserKnownHostsFile': '/dev/null',
        'StrictHostKeyChecking': 'no',
        'ProxyCommand': 'ssh -W %h:%p ec2-user@bastion',
        'IdentityFile': '/Users/austinmw/Desktop/ssh-key.pem',
        'LocalForward': '8501 localhost:8501', # Streamlit
        'LocalForward': '6006 localhost:6006', # Tensorboard
        'ForwardX11': 'yes',
    }

    # Create an instance of the SSHConfig class
    config = SSHConfig(ssh_config_file)

    #config.add_host("bastion", **new_host_bastion)
    #config.add_host("vscode", **new_host_notebook)

    # # Lookup a specific host's configuration
    # host = config.lookup_host("bastion")
    # print(host)

    # # Print a specific host's configuration
    # config.print_host("bastion")

    #config.delete_host("bastion")
    #config.delete_host("vscode")

    # Print the entire config
    config.print_config()

