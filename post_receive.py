#!/usr/bin/env python
import sys
import subprocess
import json
from paramiko import SSHClient
import paramiko


def create_connection():
    """
    Starts a connection to the controller host
    :return:
    """
    host = "10.200.0.127"
    user = "root"
    pwd = "oracle"
    client = SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(hostname=host, username=user, password=pwd, look_for_keys=False, allow_agent=False)
    except:
        print "Impossivel conectar com o controller"
        exit(3)
    return client

def run_paramiko_command(client, command, work_dir=None):
    if work_dir:
        command = "cd %s;%s" % (work_dir, command)
    stdin, stdout, stderr = client.exec_command(command)
    error_lines = stderr.readlines()
    if error_lines:
        print error_lines
    else:
        return stdout.read()


def git_diff_output(repo_path, conn):
    """
    Return the output of git diff after a fetch
    :param: repo_path: str: Path to the repository
    :return: str
    """
    command = "/usr/bin/git diff --name-only origin/master"
    #return run_command(repo_path, command)
    return run_paramiko_command(conn, command, repo_path)


def parse_modified_servers(diff_output):
    """
    Return a list of servers modified
    :param diff_output: str: output of git diff
    :return: []: List of servers
    """
    modfied_servers = []
    for line in diff_output.split('\n'):
        got_list = line.strip().split('/')
        if len(got_list) >= 2:
            modfied_servers.append(got_list[0])
    return modfied_servers


def parse_ansible_command(modified_hosts):
    """
    Parse the ansible command to run only on modified hosts
    :param modified_hosts: []
    :return:
    """
    #Ansible
    if modified_hosts:
        start_cmd = "ansible-playbook /etc/ansible/roles/remote-config/modified-hosts.yml -l nrpe"
        extra_vars = "--extra-vars '{\"modified_hosts\":["
        for host in modified_hosts:
            extra_vars += "\"%s\"," % host
        # Removing the last column
        end_cmd = " %s]}'" % extra_vars[0:-1]
        return start_cmd + end_cmd
    else:
        return None


def main():
    path = "/remote-configs"
    conn = create_connection()
    run_paramiko_command(conn, "git fetch --all", path)
    #run_command(path, "git fetch --all")
    output = git_diff_output(path, conn)
    if output:
        modified_servers = parse_modified_servers(output)
        ansible_cmd = parse_ansible_command(modified_servers)
        if ansible_cmd:
            print run_paramiko_command(conn, ansible_cmd)
        # There is modified files but not servers.
        else:
            print "Nothing to refresh"
    #There is no files with modifications
    else:
        print "Nothing to refresh"
    print run_paramiko_command(conn, "git reset --hard origin/master", path)

if __name__ == '__main__':
   main()
