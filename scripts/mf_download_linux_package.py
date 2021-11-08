#!/usr/bin/env python3

import paramiko


def execute_cmd(host, username, key, cmd, using_key):
    output = ''
    error = ''
    ssh = None
    try:
        ssh = open_ssh(host, username, key, using_key)
        if ssh is None:
            error = "Not able to get the SSH connection for the host " + host
            print(error)
        else:
            _, stdout, stderr = ssh.exec_command(cmd)
            for line in stdout.readlines():
                output = output + line
            for line in stderr.readlines():
                error = error + line
    except IOError as io_error:
        error = "Unable to execute the command " + cmd + " due to " + \
                str(io_error)
        print(error)
    except paramiko.SSHException as ssh_exception:
        error = "Unable to execute the command " + cmd + " due to " + \
                str(ssh_exception)
        print(error)
    finally:
        if ssh is not None:
            ssh.close()
    return output, error


def open_ssh(host, username, key_pwd, using_key):
    ssh = None
    try:
        if using_key:
            private_key = paramiko.RSAKey.from_private_key_file(key_pwd)
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=username, pkey=private_key)
        else:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=host, username=username, password=key_pwd)
    except IOError as io_error:
        error = "Unable to connect to host " + host + " with username " + \
                username + " due to " + str(io_error)
        print(error)
    except paramiko.SSHException as ssh_exception:
        error = "Unable to connect to host " + host + " with username " + \
                username + " due to " + str(ssh_exception)
        print(error)
    return ssh


def find_distribution(host, username, key_pwd, using_key):
    distribution = "linux"
    output, _ = execute_cmd(host, username, key_pwd, "cat /etc/*release",
                            using_key)
    if "ubuntu" in output:
        distribution = "ubuntu"
    elif "Red Hat" and "6." in output:
        distribution = "Red Hat 6"
    elif "Red Hat" and "7." in output:
        distribution = "Red Hat 7"
    elif "suse" in output:
        distribution = "suse"
    return distribution


def install_wget(host, username, key_pwd, using_key):
    ssh = None
    try:
        # Find the distribution
        distribution = find_distribution(host, username, key_pwd, using_key)
        print("")
        print("***** Installing wget *****")
        ssh = open_ssh(host, username, key_pwd, using_key)
        if distribution == "ubuntu":
            ssh.exec_command("sudo apt-get update")
            stdin, _, stderr = ssh.exec_command(
                "sudo DEBIAN_FRONTEND=noninteractive apt-get install wget")
        elif distribution == "suse":
            stdin, _, stderr = ssh.exec_command("sudo zypper install wget")
            stdin.write('Y\n')
            stdin.flush()
        else:
            # This condition works with centos, fedora and RHEL distributions
            stdin, _, stderr = ssh.exec_command("sudo yum install wget -y")
        # Check if there is any error while installing wget
        error = ''
        for line in stderr.readlines():
            error = error + line
        if not error:
            print("wget got installed successfully")
            # Execute the command wget and check if it got configured correctly
            _, _, stderr = ssh.exec_command("wget")
            error = ''
            for line in stderr.readlines():
                error = error + line
            if "not found" in error or "command-not-found" in error:
                print(
                    "wget is not recognized, unable to proceed! due to " + error)
        else:
            print("something went wrong while installing wget ", error)
    finally:
        if ssh is not None:
            ssh.close()


def check_python(host, username, key_pwd, using_key):
    _, error = execute_cmd(host, username, key_pwd, "python --version",
                           using_key)
    if error:
        return False
    else:
        return True


def check_python3(host, username, key_pwd, using_key):
    _, error = execute_cmd(host, username, key_pwd, "python3 --version",
                           using_key)
    if error:
        return False
    else:
        return True


def install_python3(host, username, key_pwd, using_key):
    ssh = None
    try:
        print("")
        print("***** Installing python3 *****")
        ssh = open_ssh(host, username, key_pwd, using_key)
        # Find the distribution
        distribution = find_distribution(host, username, key_pwd, using_key)
        if distribution == "ubuntu":
            ssh.exec_command("sudo apt-get update")
            command = "sudo DEBIAN_FRONTEND=noninteractive apt-get install " \
                      "python3"
            stdin, _, stderr = ssh.exec_command(command)
            stdin.write('Y\n')
            stdin.flush()
        elif distribution == 'suse':
            stdin, _, stderr = ssh.exec_command("sudo zypper install python3")
            stdin.write('Y\n')
            stdin.flush()
        elif distribution == "fedora":
            stdin, _, stderr = ssh.exec_command("sudo dnf install python3")
            stdin.write('Y\n')
            stdin.flush()
        else:  # This installs on centos
            ssh.exec_command("sudo yum install -y python3")
            _, _, stderr = ssh.exec_command("python --version")
        error = ''
        for line in stderr.readlines():
            error = error + line
        if not error:
            print("python got installed successfully")
        else:
            print(error)
    finally:
        if ssh is not None:
            ssh.close()


def download_ssm_agent(host, username, key_pwd, using_key):
    print("")
    print("")
    print("--------------------------------------------------------")
    print("- Downloading SSM Agent for:  " + host + " -")
    print("--------------------------------------------------------")
    try:
        output = None
        error = None
        distribution = find_distribution(host, username, key_pwd, using_key)
        if distribution == "Red Hat 6":
            command = "wget -O /tmp/amazon-ssm-agent-redhat6.rpm " \
                      "https://s3.us-east-1.amazonaws.com/amazon-ssm-us-east-1/3.0.1390.0/linux_amd64/amazon-ssm-agent.rpm"
            output, error = execute_cmd(host=host, username=username, key=key_pwd, cmd=command, using_key=using_key)
            if "not found" in error or "No such file or directory" in error:
                install_wget(host, username, key_pwd, using_key)
                output, error = execute_cmd(host=host, username=username, key=key_pwd, cmd=command, using_key=using_key)
        elif distribution == "Red Hat 7":
            command = "wget -O /tmp/amazon-ssm-agent-redhat7.rpm " \
                      "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm"
            output, error = execute_cmd(host=host, username=username, key=key_pwd, cmd=command, using_key=using_key)
            if "not found" in error or "No such file or directory" in error:
                install_wget(host, username, key_pwd, using_key)
    except Exception as e:
        error = 'Got exception! ' + str(e)
    if not error:
        print("***** SSM agent download completed successfully on "
              + host + "*****")
        return True
    else:
        print("Unable to download SSM Agent on " + host + " due to: ")
        print("")
        if output:
            print(output)
        print(error)
        return False


def download_cloudwatch_agent(host, username, key_pwd, using_key):
    print("")
    print("")
    print("--------------------------------------------------------")
    print("- Downloading Cloudwatch Agent for:  " + host + " -")
    print("--------------------------------------------------------")
    try:
        output = None
        error = None
        command = "wget -O /tmp/amazon-cloudwatch-agent-redhat.rpm " \
                  "https://s3.us-east-1.amazonaws.com/amazoncloudwatch-agent-us-east-1/redhat/amd64/latest/amazon-cloudwatch-agent.rpm"
        output, error = execute_cmd(host=host, username=username, key=key_pwd, cmd=command, using_key=using_key)
        if "not found" in error or "No such file or directory" in error:
            install_wget(host, username, key_pwd, using_key)
    except Exception as e:
        error = 'Got exception! ' + str(e)
    if not error:
        print("***** Cloudwatch agent download completed successfully on "
              + host + "*****")
        return True
    else:
        print("Unable to download Cloudwatch agent on " + host + " due to: ")
        print("")
        if output:
            print(output)
        print(error)
        return False
