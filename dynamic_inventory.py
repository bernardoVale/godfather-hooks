#!/usr/bin/env python

import os
import sys
import argparse
import subprocess


try:
    import json
except ImportError:
    import simplejson as json

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

def get_modified_servers():
    path = "/Users/bernardovale/Documents/LB2/projects/testing"
    run_command(path, "git fetch --all")
    output = git_diff_output(path)
    modified_servers = []
    if output:
        modified_servers = parse_modified_servers(output)
    run_command(path, "git reset --hard origin/master")
    return modified_servers

class ExampleInventory(object):

    def __init__(self):
        self.inventory = {}
        self.read_cli_args()
        self.modified_servers = get_modified_servers()

        # Called with `--list`.
        if self.args.list:
            self.inventory = self.example_inventory()
        # Called with `--host [hostname]`.
        elif self.args.host:
            # Not implemented, since we return _meta info `--list`.
            self.inventory = self.empty_inventory()
        # If no groups or vars are present, return an empty inventory.
        else:
            self.inventory = self.empty_inventory()

        print json.dumps(self.inventory)

    # Example inventory for testing.
    def example_inventory(self):
        return {
            'group': {
                'hosts': self.modified_servers,
                'vars': {
                    'ansible_ssh_user': 'root'
                }
            }
        }

    # Empty inventory for testing.
    def empty_inventory(self):
        return {'_meta': {'hostvars': {}}}

    # Read the command line args passed to the script.
    def read_cli_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--list', action = 'store_true')
        parser.add_argument('--host', action = 'store')
        self.args = parser.parse_args()

# Get the inventory.
ExampleInventory()