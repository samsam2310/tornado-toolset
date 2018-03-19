# -*- coding: utf-8 -*-
""" tornado tool set test
Run test - |python -m tornadotoolset.test|
"""

import argparse
import fnmatch
import os
import sys
import unittest

CLEAR_ENVIRONS = []

for env in CLEAR_ENVIRONS:
    os.environ[env] = ''

os.environ['DB_HOST'] = os.getenv('TEST_DB_HOST', 'localhost:27017')
os.environ['DB_NAME'] = os.getenv('TEST_DB_NAME', 'UnitTestDB')

TEST_MODULES = [
    'tornadotoolset.test.pymonorm_test',
]


def main():
    parser = argparse.ArgumentParser(description='Run the test.')
    parser.add_argument(
        '-v',
        '--verbosity',
        action='store',
        choices=[0, 1, 2],
        default=1,
        dest='verbosity',
        help='The verbosity mode.',
        type=int)
    parser.add_argument(
        '--filter',
        action='store',
        default='*',
        dest='filter',
        help='The filter.')
    args = parser.parse_args()

    test_set = fnmatch.filter(TEST_MODULES, args.filter)
    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromNames(test_set))
    unittest.TextTestRunner(verbosity=args.verbosity).run(suite)


if __name__ == '__main__':
    main()
