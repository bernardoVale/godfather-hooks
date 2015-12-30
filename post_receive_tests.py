from post_receive import *
import unittest
import os
import shutil
import unittest
import mock
from mock import patch, Mock
from mock import PropertyMock
import paramiko
from paramiko import SSHClient
from time import sleep

class TestPostRecieve(unittest.TestCase):
    """
    Test related to the post-receive hook
    """
    @patch('paramiko.SSHClient.connect', Mock)
    def setUp(self):
        self.fake_conn = mock
        pass

    def tearDown(self):
        pass

    def test_get_file_name(self):
        mocked_result = "1ffaaf3187a85176e984025690e428ab2f5a2296"
        expected = "/tmp/1ffaaf3.tmp"
        with mock.patch('post_receive.get_last_commit', return_value=mocked_result) as m:
            got = get_file_name()
            self.assertEqual(expected, got)

    def test_get_file_name_with_err(self):
        mocked_result = None
        with mock.patch('post_receive.get_last_commit', return_value=mocked_result) as m:
            with self.assertRaises(SystemExit) as cm:
                get_file_name()
            self.assertEqual(cm.exception.code, 2)

    def test_execute_playbook_non_successful(self):
        stdout = ""
        stderr = "standard error, don't care"
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            with self.assertRaises(SystemExit) as cm:
                run_playbook(self.fake_conn, 'dontcare.tmp')
            self.assertEqual(cm.exception.code, 2)

    def test_update_repo_success(self):
        stdout = ""
        stderr = ""
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            with mock.patch('time.sleep') as m_sleep:
                try:
                    update_controller_repo(self.fake_conn, '/remote-configs')
                except SystemExit:
                    self.assertTrue(False)
                except:
                    self.assertTrue(True)

                self.assertFalse(m_sleep.called)

    def test_update_repo_failure_one_time(self):
        mocked_results = [('first time with error', ''), ('', '')]
        with mock.patch('post_receive.run_remote_command', side_effect=mocked_results) as m:
            with mock.patch('time.sleep') as m_sleep:
                try:
                    update_controller_repo(self.fake_conn, '/remote-configs')
                except SystemExit:
                    self.assertTrue(False)
                except:
                    self.assertTrue(True)

            # Make sure sleep was called
            self.assertTrue(m_sleep.called)

    def test_update_repo_failure_three_times(self):
        mocked_results = [('first time with error', ''), ('second too', ''), ('third too', '')]
        with mock.patch('post_receive.run_remote_command', side_effect=mocked_results) as m:
            with mock.patch('time.sleep') as m_sleep:
                with self.assertRaises(SystemExit) as cm:
                    update_controller_repo(self.fake_conn, '/remote-configs')
                self.assertEqual(cm.exception.code, 2)
            # Ensuring that sleep was called three times
            calls = [mock.call(1), mock.call(1), mock.call(1)]
            m_sleep.assert_has_calls(calls)
            # Make sure sleep was called
            self.assertTrue(m_sleep.called)

    def test_update_repo_failure_make_sure_dont_try_four_times(self):
        mocked_results = [('first time with error', ''), ('second too', ''), ('third too', ''), ('it will', 'ignore')]
        with mock.patch('post_receive.run_remote_command', side_effect=mocked_results) as m:
            with mock.patch('time.sleep') as m_sleep:
                with self.assertRaises(SystemExit) as cm:
                    update_controller_repo(self.fake_conn, '/remote-configs')
                self.assertEqual(cm.exception.code, 2)
            # Ensuring that sleep was called three times
            calls = [mock.call(1), mock.call(1), mock.call(1)]
            m_sleep.assert_has_calls(calls)
            # Make sure sleep was called
            self.assertTrue(m_sleep.called)
        #Make sure git fetch was called three times
        std_call = [mock, 'git fetch --all', '/remote-configs']
        calls = [mock.call(*std_call),
                 mock.call(*std_call),
                 mock.call(*std_call)]
        m.assert_has_calls(calls)

    def test_reset_repo_failure(self):
        stdout = ""
        stderr = "This is an error"
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            with self.assertRaises(SystemExit) as cm:
                reset_controller_repo(self.fake_conn, '/remote-configs')
            self.assertEqual(cm.exception.code, 2)
            #Also assert that method was called
            self.assertTrue(m.called)

    def test_reset_repo_success(self):
        stdout = ""
        stderr = ""
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            try:
                reset_controller_repo(self.fake_conn, '/remote-configs')
            except SystemExit:
                self.assertTrue(False)
            except:
                self.assertTrue(True)
            #Also assert that method was called
            self.assertTrue(m.called)

    def test_retry_file_exists(self):
        stdout = ""
        stderr = ""
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            got = retry_file_exists(self.fake_conn, '/tmp/dontcare.tmp')
            self.assertTrue(got)

    def test_retry_file_does_not_exists(self):
        stdout = ""
        stderr = "This is an error"
        mocked_result = (stderr, stdout)
        with mock.patch('post_receive.run_remote_command', return_value=mocked_result) as m:
            got = retry_file_exists(self.fake_conn, '/tmp/dontcare.tmp')
            self.assertFalse(got)