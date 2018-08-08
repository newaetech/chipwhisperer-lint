"""
test.py

Unit tests for server program
"""

import unittest
import subprocess
import os

class TestServerCLI(unittest.TestCase):
    def test_help(self):
        ret = subprocess.call('python server.py --help')
        self.assertEqual(ret, 0)
                
if __name__ == "__main__":
    unittest.main()