# coding: utf-8
"""
Tests for django-rest-easy. So far not ported from proprietary code.
"""
from __future__ import unicode_literals

import unittest


class NullTest(unittest.TestCase):
    """
    Null test to check travis build.
    """
    def test_null(self):
        """
        As above.
        """
        self.assertTrue(True)  # pylint: disable=redundant-unittest-assert

if __name__ == '__main__':
    unittest.main()
