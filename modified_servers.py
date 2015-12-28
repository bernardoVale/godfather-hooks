import subprocess

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
    output = run_command('/Users/bernardovale/hook-test', command)
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
        if len(got_list) >= 2:
            modfied_servers.append(got_list[0])
    return modfied_servers


def get_modified_servers_from_commit(commit_sha1):
    """
    Return all modified files on that commit
    :param commit_sha1: str
    :return: []: List of files modified from that commit
    """
    command = "git log -1 --name-only --pretty=format:'' %s" % commit_sha1
    output = run_command('/Users/bernardovale/hook-test', command)
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

#list_of_sha1 = rev_list_sha1('8833ac4ae091f4ef32ef0932e7f495131250542e', 'c22ab40a638595e39f012f77384f461d9d8e8f82')
#print get_all_modified_servers(list_of_sha1)