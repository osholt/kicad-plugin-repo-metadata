from unittest import TestCase
from unittest.mock import patch
from io import StringIO
from validate.util import verify, getsha


class TestUtil(TestCase):
    def test_verify_false(self):
        verify.FAILURES = 0
        with patch('sys.stdout', new=StringIO()) as fake_out:
            verify.verify(False, "abcde")
            self.assertIn("abcde", fake_out.getvalue())
            self.assertEqual(verify.get_failures(), 1)

    def test_verify_true(self):
        verify.FAILURES = 0
        with patch('sys.stdout', new=StringIO()) as fake_out:
            verify.verify(True, "abcde")
            self.assertEqual(fake_out.getvalue(), "")
            self.assertEqual(verify.get_failures(), 0)

    @patch("sys.exit")
    def test_verify_exit_false(self, exit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            verify.verify_exit(False, "abcde")
            self.assertIn("abcde", fake_out.getvalue())
            exit.assert_called_with(1)

    @patch("sys.exit")
    def test_verify_exit_true(self, exit):
        with patch('sys.stdout', new=StringIO()) as fake_out:
            verify.verify_exit(True, "abcde")
            self.assertEqual(fake_out.getvalue(), "")
            exit.assert_not_called()

    def test_sha(self):
        self.assertEqual(
            getsha.getsha256("test/data/package/resources/icon.png"),
            "e4d24fdf36babc82360cb6fc05c88cfba73acca6ced04ab7a6df37399b943c84")
