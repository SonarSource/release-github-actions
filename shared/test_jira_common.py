import os
import sys
import unittest
from io import StringIO
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jira_common import CUSTOM_FIELDS, eprint, get_jira_instance, get_jira_url, JIRA_URL_PROD, JIRA_URL_SANDBOX
from jira.exceptions import JIRAError


class TestCustomFields(unittest.TestCase):
    def test_field_ids(self):
        # Behaviour-lock: these IDs are a contract with Jira, not free to change.
        self.assertEqual(CUSTOM_FIELDS['SHORT_DESCRIPTION'], 'customfield_10146')
        self.assertEqual(CUSTOM_FIELDS['LINK_TO_RELEASE_NOTES'], 'customfield_10145')
        self.assertEqual(CUSTOM_FIELDS['DOCUMENTATION_STATUS'], 'customfield_10147')
        self.assertEqual(CUSTOM_FIELDS['RULE_PROPS_CHANGED'], 'customfield_11263')
        self.assertEqual(CUSTOM_FIELDS['SONARLINT_CHANGELOG'], 'customfield_11264')


class TestEprint(unittest.TestCase):
    def test_writes_to_stderr(self):
        with patch('sys.stderr', new=StringIO()) as err:
            eprint("hello")
        self.assertEqual(err.getvalue(), "hello\n")


class TestGetJiraUrl(unittest.TestCase):
    def test_false_string_returns_prod(self):
        self.assertEqual(get_jira_url('false'), JIRA_URL_PROD)

    def test_empty_string_returns_prod(self):
        self.assertEqual(get_jira_url(''), JIRA_URL_PROD)

    def test_true_string_returns_sandbox(self):
        self.assertEqual(get_jira_url('true'), JIRA_URL_SANDBOX)

    def test_true_bool_returns_sandbox(self):
        self.assertEqual(get_jira_url(True), JIRA_URL_SANDBOX)

    def test_false_bool_returns_prod(self):
        self.assertEqual(get_jira_url(False), JIRA_URL_PROD)

    def test_none_returns_prod(self):
        self.assertEqual(get_jira_url(None), JIRA_URL_PROD)


class TestGetJiraInstance(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_credentials_exits(self):
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('false')
        self.assertEqual(cm.exception.code, 1)

    @patch.dict(os.environ, {'JIRA_USER': 'u', 'JIRA_TOKEN': 't'})
    @patch('jira.JIRA')
    def test_success_returns_client(self, mock_jira_class):
        mock_client = Mock()
        mock_jira_class.return_value = mock_client
        self.assertIs(get_jira_instance('false'), mock_client)

    @patch.dict(os.environ, {'JIRA_USER': 'u', 'JIRA_TOKEN': 't'})
    @patch('jira.JIRA')
    def test_success_uses_prod_url(self, mock_jira_class):
        mock_jira_class.return_value = Mock()
        get_jira_instance('false')
        mock_jira_class.assert_called_once_with(JIRA_URL_PROD, basic_auth=('u', 't'), get_server_info=True)

    @patch.dict(os.environ, {'JIRA_USER': 'u', 'JIRA_TOKEN': 't'})
    @patch('jira.JIRA')
    def test_success_uses_sandbox_url(self, mock_jira_class):
        mock_jira_class.return_value = Mock()
        get_jira_instance('true')
        mock_jira_class.assert_called_once_with(JIRA_URL_SANDBOX, basic_auth=('u', 't'), get_server_info=True)

    @patch.dict(os.environ, {'JIRA_USER': 'u', 'JIRA_TOKEN': 't'})
    @patch('jira.JIRA')
    def test_auth_failure_exits(self, mock_jira_class):
        mock_jira_class.side_effect = JIRAError(status_code=401, text='nope')
        with self.assertRaises(SystemExit) as cm:
            get_jira_instance('false')
        self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
