# -*- coding: utf-8 -*-
""" BaseTestCase for db testing
"""

from tornadotoolset.pymonorm import get_database_from_env

import unittest


class DBTestCase(unittest.TestCase):
    def setUp(self):
        self._db = get_database_from_env()
        self._db.client.drop_database(self._db.name)
