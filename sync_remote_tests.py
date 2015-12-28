import os
import shutil
import unittest
import mock
from mock import PropertyMock
from sync_remote import git_diff_output
from sync_remote import parse_modified_servers
from sync_remote import *

class TestSyncRemote(unittest.TestCase):
    """
    Tests related to sync remote script
    """

    def setUp(self):
        self.test_output_success = " host1/file1 \n \
             host2/file1 \n \
             host3/file1 \n \
             host4/file1"
        self.output_none = ""
        pass

    def tearDown(self):
        pass

    def test_get_diff_output(self):
        with mock.patch('sync_remote.run_command', return_value=self.test_output_success) as m:
            output = git_diff_output("mock_dir")
            self.assertEqual(output, self.test_output_success)
            m.return_value = None
            output_empty = git_diff_output("mock_dir")
            self.assertEqual(output_empty, None)

    def test_parse_modified_servers_sucess(self):
        output = parse_modified_servers(self.test_output_success)
        expected = ['host1', 'host2', 'host3', 'host4']
        self.assertEqual(output, expected)

    def test_parse_modified_servers_without_modification(self):
        output = parse_modified_servers(self.output_none)
        expected = []
        self.assertEqual(output, expected)
        output =  parse_modified_servers("")
        self.assertEqual(output, expected)

    def test_parse_modified_servers_with_non_servers(self):
        """
        Testa se o script vai adicionar a lista arquivos que nao sao de um server
        especifico
        :return:
        """
        test_output_success = " host1/file1 \n \
             host2/file1 \n \
             file1 \n \
             host4/file1 \n \
             file2"
        expected = ['host1', 'host2', 'host4']
        output = parse_modified_servers(test_output_success)
        self.assertEqual(expected, output)

    def test_run_ansible_playbook(self):
        modified_servers = ['capa', 'capudo']
        expected = "/usr/bin/ansible-playbook /etc/ansible/roles/remote-config/modified-hosts.yml -l nrpe --extra-vars '{\"modified_hosts\":[\"capa\",\"capudo\"]}'"
        got = parse_ansible_command(modified_servers)
        self.assertEqual(expected, got)

    def test_run_ansible_playbook_without_modified_servers(self):
        modified_servers = []
        expected = None
        got = parse_ansible_command(modified_servers)
        self.assertEqual(expected, got)