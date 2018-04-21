# -*- coding: utf-8 -*-
""" tornado tool set test
Run test - |python -m backend.test|
"""

import argparse
import fnmatch
import os
import sys
import unittest


# Add module to test.
TEST_MODULES = []


CLEAR_ENVIRONS = ['DB_USER', 'DB_PWD', 'DB_REPLSE']

for env in CLEAR_ENVIRONS:
    os.environ[env] = ''

os.environ['DB_HOST'] = os.getenv('TEST_DB_HOST', 'localhost:27017')
os.environ['DB_NAME'] = os.getenv('TEST_DB_NAME', 'UnitTestDB')


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
    res = unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
