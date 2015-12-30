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
    return stderr.read(), stdout.read()
    # error_lines = stderr.read()
    # if error_lines:
    # print error_lines
    #     return error_lines
    # else:
    #     return stdout.read()


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
    command = "git rev-list %s..%s" % (old[0:7], new[0:7])
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


def get_retry_filename(commits_list):
    """
    Return the name of the retry file name
    :param commits_list: []: List of all commits SHA1
    :return:
    """
    last_commit_sha1 = commits_list[-1]
    return last_commit_sha1[0:7] + '.tmp'


def remove_retry_file(conn, file_name):
    """
    Remove the retry file
    :param conn: SSHClient: Paramiko connection
    :param file_name: str: File name of the retry file
    :return: None
    """
    command = "rm -rf /tmp/%s" % file_name
    print "Running %s" % command
    stderr, stdout = run_paramiko_command(conn, command)
    if stderr:
        print "Nao foi possivel remover o arquivo de retry: /tmp/%s" % file_name
        print stderr

def write_retry_file(conn, modified_servers, file_name):
    """
    Write a retry file inside the controller host
    :param conn: Paramiko connection
    :param modified_servers: []: List of all modified servers
    :param file_name: str: Name of the retry file
    :return: None
    """
    modified_into_string = "\n".join(modified_servers)
    command = "echo -e \"%s\" > /tmp/%s" % (modified_into_string, file_name)
    stderr, stdout = run_paramiko_command(conn, command)
    # Since am writing there'll be only output if paramiko receives some stderr
    if stderr:
        print "Nao foi possivel escrever o arquivo de retry no controller. Valide o caminho"
        print stderr
        exit(2)


def execute_test_playbook(conn, file_name):
    """
    Executes a simple playbook to test conectivity with the modified servers
    :param conn: SSHClient: Paramiko connection
    :param file_name: str: File name of the retry file
    :return:
    """
    cmd = "ansible-playbook /etc/ansible/roles/remote-config/remote-config.yml --check -l @/tmp/%s" % file_name
    stderr, stdout = run_paramiko_command(conn, cmd)
    exit_status = 0
    if stderr:
        print "Ocorreu algum problema ao tentar executar o playbook de teste de conectividade, leia o output:\n"
        print stderr
        exit_status = 2
    if 'unreachable=1' in stdout:
        print "Alguns hosts falharam no teste.\nEste push sera negado. Verifique os erros no output. \nPode ser erro" \
              " de conectividade com o controller ou algo que esta errado nas configuracoes do remote-config.\n" \
              "Veja o output abaixo:"
        print stdout
        exit_status = 2
    if exit_status == 2:
        # I'll try to remove, but, if I couldn't there's no problem
        remove_retry_file(conn, file_name)
    return exit_status


# modified_servers = ['artemis', 'nova-nfe', 'other-server']
# conn = create_connection()
# commit_list = ['1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340']
# file_name = get_retry_filename(commit_list)
# write_retry_file(conn, modified_servers, file_name)
# execute_test_playbook(conn)


def main(args):
    # Setup variables
    ref, old, new = (args)
    commit_list = rev_list_sha1(new, old)
    modified_servers = get_all_modified_servers(commit_list)
    file_name = get_retry_filename(commit_list)
    conn = create_connection()
    write_retry_file(conn, modified_servers, file_name)
    exit_status = execute_test_playbook(conn, file_name)
    exit(exit_status)


if __name__ == '__main__':
    main(sys.argv[1:])