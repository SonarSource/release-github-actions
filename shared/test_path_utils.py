import os
import sys
import tempfile
import unittest

from shared.path_utils import safe_path


class TestSafePath(unittest.TestCase):
    def test_valid_path_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'properties.txt')
            self.assertEqual(safe_path(p, base=d), os.path.realpath(p))

    def test_traversal_exits(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit) as cm:
                safe_path('../../etc/passwd', base=d)
            self.assertEqual(cm.exception.code, 1)


if __name__ == '__main__':
    unittest.main()
