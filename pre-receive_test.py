from pre_receive import *
import unittest
import os
import shutil
import unittest
import mock
from mock import PropertyMock

class TestPreReceive(unittest.TestCase):
    """
    Tests related to modified servers
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

    def test_list_sha1_list_ok(self):
        mocked_result = "1ffaaf3187a85176e984025690e428ab2f5a2296 \n \
536b9d6404b456cd5c9bba63cd2648d1d9053340"

        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = rev_list_sha1('1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340')
            expected = ['1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340']
            self.assertEqual(got, expected)

    def test_list_sha1_empty_line(self):
        mocked_result = "1ffaaf3187a85176e984025690e428ab2f5a2296 \n \
536b9d6404b456cd5c9bba63cd2648d1d9053340 \n \
                        "
        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = rev_list_sha1('1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340')
            #Blank lines shouldn't be parsed
            self.assertEqual(len(got), 2)

    def test_list_sha1_incorrect_line(self):
        mocked_result = "1ffaaf3187a85176e984025690e428ab2f5a2296 \n \
536b9d6404b456cd5c9bba63cd2648d1d9053340 \n \
                        dsadasdas"
        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = rev_list_sha1('1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340')
            #Blank lines shouldn't be parsed
            self.assertEqual(len(got), 2)

    def test_list_sha1_empty_list_of_commits(self):
        mocked_result = ""
        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = rev_list_sha1('1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340')
            expected = []
            self.assertEqual(got, expected)

    def test_get_modified_servers_from_commit(self):
        mocked_result = "capa/server1"
        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = get_modified_servers_from_commit('1ffaaf3187a85176e984025690e428ab2f5a2296')
            expected = ['capa']
            self.assertEqual(got, expected)

    def test_get_modified_servers_from_commit_that_arent_a_server(self):
        mocked_result = "capa"
        with mock.patch('pre_receive.run_command', return_value=mocked_result) as m:
            got = get_modified_servers_from_commit('1ffaaf3187a85176e984025690e428ab2f5a2296')
            expected = []
            self.assertEqual(got, expected)

    def test_get_modified_servers_from_commit_with_err(self):
        mocked_result = ""
        self.reiceve = 'pre_receive'
        with mock.patch('%s.run_command' % self.reiceve, return_value=mocked_result) as m:
            self.commit = get_modified_servers_from_commit('1ffaaf3187a85176e984025690e428ab2f5a2296')
            got = self.commit
            expected = None
            self.assertEqual(got, expected)
            
    def test_get_all_pre_receive(self):
        mocked_results = [['server1', 'server2'], ['server3']]
        list_of_commits = ['1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340']
        self.from_commit = 'get_modified_servers_from_commit'
        with mock.patch('pre_receive.%s' % self.from_commit, side_effect=mocked_results) as m:
            got = get_all_modified_servers(list_of_commits)
            expected = ["server1", "server2", "server3"]
            self.assertEqual(got, expected)

    def test_get_modified_servers_with_duplicates(self):
        mocked_results = [['server1', 'server2'], ['server2', 'server1']]
        list_of_commits = ['1ffaaf3187a85176e984025690e428ab2f5a2296', '536b9d6404b456cd5c9bba63cd2648d1d9053340']
        with mock.patch('pre_receive.get_modified_servers_from_commit', side_effect=mocked_results) as m:
            got = get_all_modified_servers(list_of_commits)
            expected = ["server1", "server2"]
            self.assertEqual(got, expected)
