from post_receive import *
import unittest
import os
import shutil
import unittest
import mock
from mock import PropertyMock

class TestModifiedServers(unittest.TestCase):
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

    def test_parse_modified_servers(self):
        test_old_way = " host1/file1 \n \
             host2/file1 \n \
             host3/file1 \n \
             host4/file1"
        got = parse_modified_servers(test_old_way)
        expected = []
        self.assertEqual(expected, got)
        test_new_way = "client1/host1/file1 \n \
            client2/host3/file11231 \n \
            host2/file1 \n \
            file1 \n \
            client3/host2/file1321"
        expected = ['host1', 'host3', 'host2']
        got = parse_modified_servers(test_new_way)
        self.assertEqual(expected, got)