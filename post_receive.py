#!/usr/bin/env python
import sys
import subprocess
import json
from paramiko import SSHClient
import paramiko
import time

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

def run_remote_command(client, command, work_dir=None):
    """
    Executes a command and return stdout and stderr
    :param client: SSHClient: a runnning ssh connection
    :param command: str: a bash command
    :param work_dir: str: A directory to start with
    :return: (str, str): Both stderr and stdout
    """
    if work_dir:
        command = "cd %s;%s" % (work_dir, command)
    stdin, stdout, stderr = client.exec_command(command)
    return stderr.read(), stdout.read()

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


def get_last_commit():
    """
    Return the last commit sha1 inside the repo.
    :return: str: Commit sha1
    """
    cmd = "git log --format=%H -n 1"
    path = "/var/opt/gitlab/git-data/repositories/infra/remote-configs.git"
    output = run_command(path, cmd)
    if output:
        return output.strip()

def get_file_name():
    """
    Return the name of the retry file
    :return: str: retry file and directory
    """
    commit_sha1 = get_last_commit()
    if commit_sha1:
        return "/tmp/%s.tmp" % commit_sha1[0:7]
    else:
        print "Nao foi possivel coletar o SHA1 do ultimo commit, verifique os erros acima"
        exit(2)

def run_playbook(conn, retry_file):
    """
    Ran the playbook remote-config with the retry_file especified
    :param conn: SSHClient: A paramiko connection to the controller host
    :param retry_file: str: The retry file with only the modified hosts
    :return: None
    """
    cmd = "ansible-playbook /etc/ansible/roles/remote-config/remote-config.yml -l @%s" % retry_file
    stderr, stdout = run_remote_command(conn, cmd)
    if stderr:
        print "Aconteceu algum problema na execucao do playbook remote-config.yml\nVerifique o erro abaixo:"
        print stderr
        # I don't want a git reset if the playbook stop with errors
        exit(2)
    print stdout

def update_controller_repo(conn, path):
    """
    Try to fetch git updates on the local repository (controller repo)
    :param conn: SSHClient: A running ssh connection
    :param path: str: Work dir of the repo
    :return:
    """
    keep_trying = 0
    stderr = stdout = ""
    # Sometimes fetch fails, I don't it to give up without 3 shoots
    while keep_trying < 3:
        stderr, stdout = run_remote_command(conn, "git fetch --all", path)
        if stderr:
            keep_trying += 1
            # If this is a connection problem, let's try again
            time.sleep(1)
        else:
            keep_trying = 0
            print stdout
            break
    # Failed miserable three times
    if keep_trying == 3:
        print "Nao foi possivel atualizar o repositorio %s\nVerifique o erro abaixo:" % path
        print stderr
        exit(2)


def retry_file_exists(conn, retry_file):
    """
    Make sure this file exists inside the controller host.
    The update hook does not write this file if there is no
    servers with modifications
    :param conn: SSHClient
    :param retry_file: str: retry file name and path
    :return: bool
    """
    cmd = "ls %s" % retry_file
    stderr, stdout = run_remote_command(conn, cmd)
    return True if stderr == "" else False

def reset_controller_repo(conn, path):
    """
    Run a git reset to get all updates from the last push
    :param conn: SSHClient: A running ssh connection
    :param path: str: Work dir of the repo
    :return:
    """
    # Reset controller repo with the just pushed files
    stderr, stdout = run_remote_command(conn, "git reset --hard origin/master", path)
    if stderr:
        print "Nao foi possivel resetar o repositorio %s\nVerifique o erro abaixo:" % path
        print stderr
        exit(2)
    # Print for logging
    print stdout


def main():
    path = "/remote-configs"
    conn = create_connection()
    # Failure it's handled on this command
    update_controller_repo(conn, path)
    # Reset to the latest update
    reset_controller_repo(conn, path)
    # Make sure there's a retry file. If it doesn't the update does not contain modified servers
    retry_file = get_file_name()
    # Last test. If the file exists run the playbook
    if retry_file_exists(conn, retry_file):
        # If we got here, everything it's ok, just run the playbook
        run_playbook(conn, retry_file)
    else:
        print "Nao existem servidores com modificacoes.\nRepositorio atualizado com sucesso!"

if __name__ == '__main__':
   main()
