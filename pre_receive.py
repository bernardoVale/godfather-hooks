#!/usr/bin/env python
import subprocess
import sys
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
        return error_lines
    else:
        return stdout.read()

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

def rev_list_sha1(new, old):
    """
    Return a list of sha1 commits from those two intervals of a revision_list
    :param new: sha1 of the new commit
    :param old: sha1 of the newest commit pushed
    :param
    :return: [] : List of SHA1
    """
    commit_list = []
    # Only the first 6 characters are needed
    command = "git rev-list %s..%s" % (old[0:6], new[0:6])
    output = run_command('/var/opt/gitlab/git-data/repositories/bernardo.vale/hookoso.git', command)
    # The run command method was fine!
    if output:
        for commit in output.strip().split('\n'):
            # Each commit SHA1 has exacly 40 characters
            if len(commit.strip()) == 40:
                commit_list.append(commit.strip())
    else:
        # There's no commit to be parsed
        return []
    return commit_list

def parse_modified_servers(diff_output):
    """
    Return a list of servers modified
    :param diff_output: str: output of git diff
    :return: []: List of servers
    """
    modfied_servers = []
    for line in diff_output.split('\n'):
        got_list = line.strip().split('/')
        if len(got_list) >= 3:
            modfied_servers.append(got_list[1])
    return modfied_servers


def get_modified_servers_from_commit(commit_sha1):
    """
    Return all modified files on that commit
    :param commit_sha1: str
    :return: []: List of files modified from that commit
    """
    command = "git log -1 --name-only --pretty=format:'' %s" % commit_sha1
    output = run_command('/var/opt/gitlab/git-data/repositories/bernardo.vale/hookoso.git', command)
    modified_files = []
    if output:
        modified_files = parse_modified_servers(output)
    else:
        return None
    return modified_files

def get_all_modified_servers(commit_sha1_list):
    """

    :param commit_sha1_list: List of SHA1 commits
    :return: []: List of all modified servers
    """
    modified_servers = []
    for commit_sha1 in commit_sha1_list:
        commit_modified_servers = get_modified_servers_from_commit(commit_sha1)
        # This is used to remove duplicates
        modified_servers = list(set(modified_servers) | set(commit_modified_servers))

    return modified_servers

def write_retry_file(conn, modified_servers):
    """
    Write a retry file inside the controller host
    :param conn: Paramiko connection
    :param modified_servers: []: List of all modified servers
    :return:
    """
    modified_into_string = "\n".join(modified_servers)
    command = "echo -e \"%s\" > /tmp/retryme.retry" % modified_into_string
    output = run_paramiko_command(conn, command)
    #Since am writing there'll be only output if paramiko receives some stderr
    if output:
        print "Nao foi possivel escrever o arquivo de retry no controller. Valide o caminho"
        exit(3)

def execute_test_playbook(conn):
    cmd = "ansible-playbook /etc/ansible/ping.yml -l @/tmp/retryme.retry"
    output = run_paramiko_command(conn, cmd)
    if 'unreachable=1' in output:
        print "Alguns hosts falharam no teste de conectividade.\nEste push sera negado. Remova as modificacoes" \
              " referentes a este host ou reestabeleca a conectividade entre o controller.\nVeja o output abaixo:"
        print output
        exit(3)

# modified_servers = ['artemis', 'nova-nfe', 'server-oracle']
# conn = create_connection()
# write_retry_file(conn, modified_servers)
# execute_test_playbook(conn)
def main(args):
    # Setup variables
    ref, old, new = (args)
    commit_list = rev_list_sha1(new, old)
    print commit_list
    modified_servers = get_all_modified_servers(commit_list)
    conn = create_connection()
    write_retry_file(conn, modified_servers)
    execute_test_playbook(conn)

if __name__ == '__main__':
   main(sys.argv[1:])