#!/usr/bin/env python
import sys
import subprocess
import json

def run_command(work_dir, command):
    """
    Run a command on OS
    :param work_dir: working directory
    :param command: command itself
    :return: str: output of the command
    """
    session = subprocess.Popen(command.split(' '), stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=work_dir)
    stdout, stderr = session.communicate()
    if stderr != '':
        print 'Impossivel executar o comando %s\n Erro: %s' % (command, stderr)
        return None
    else:
        return stdout

def git_diff_output(repo_path):
    """
    Return the output of git diff after a fetch
    :param: repo_path: str: Path to the repository
    :return: str
    """
    command = "/usr/bin/git diff --name-only origin/master"
    return run_command(repo_path, command)

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

def create_inventory(modfied_servers):
    dict = {
        "group": {
            "hosts" : modfied_servers
        },
        "vars": {
            "ansible_ssh_user": "root",
        }
    }
    return dict

def parse_ansible_command(modified_hosts):
    """
    Parse the ansible command to run only on modified hosts
    :param modified_hosts: []
    :return:
    """
    #Ansible
    if modified_hosts:
        start_cmd = "ansible-playbook modified-hosts.yml -l nrpe"
        extra_vars = "--extra-vars '{\"modified_hosts\":["
        for host in modified_hosts:
            extra_vars += "\"%s\"," % host
        # Removing the last column
        end_cmd = " %s]}'" % extra_vars[0:-1]
        return start_cmd + end_cmd
    else:
        return None

def main(args):
    path = args[0]
    run_command(path, "git fetch --all")
    output = git_diff_output(path)
    if output:
        modified_servers = parse_modified_servers(output)
        print modified_servers
        ansible_cmd = parse_ansible_command(modified_servers)
        print ansible_cmd
        if ansible_cmd:
            get = run_command('/etc/ansible/roles/remote-config/', ansible_cmd)
            print get
        # There is modified files but not servers.
        else:
            print "Nothing to refresh"
    #There is no files with modifications
    else:
        print "Nothing to refresh"
    run_command(path, "git reset --hard origin/master")

if __name__ == '__main__':
    main(sys.argv[1:])