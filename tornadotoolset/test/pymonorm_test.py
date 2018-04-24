# -*- coding: utf-8 -*-

# Test the ORM module of pymongo

from datetime import datetime

import pymongo
import time
import unittest

from tornadotoolset.pymonorm import Collection, Field, get_database_from_env


def get_date_time():
    return datetime(2017, 8, 12)


class TestUser(Collection):
    _ORM_collection_name = 'TestUser'

    uid = Field(time.time, is_unique=True)
    name = Field()
    age = Field(default=18)
    birthday = Field(default=datetime(1997, 1, 12))
    created = Field(default=get_date_time)


class TestFoo(Collection):
    foo = Field()

    # This won't appear because `name` already in TestUser, and base on python
    # MRO, `name` in TestUser should be used instead of this one.
    name = Field()


class TestInherit(TestUser, TestFoo):
    _ORM_collection_name = 'TestInherit'


class MongoOrmTest(unittest.TestCase):

    def setUp(self):
        self._db = get_database_from_env()
        self._db.drop_collection(TestUser._ORM_collection_name)
        self._collection = self._db[TestUser._ORM_collection_name]
        self._fields = ['uid', 'name', 'age', 'birthday', 'created']
        self._test_user = TestUser(
            name='Bob', age=20, birthday=datetime(1997, 11, 2))

        if '_ORM_field_names' in TestUser.__dict__:
            del TestUser._ORM_field_names
        if '_ORM_field_names' in TestFoo.__dict__:
            del TestFoo._ORM_field_names

    def get_default_data(self, **kargs):
        data = {
            'age': 18,
            'birthday': datetime(1997, 1, 12),
            'created': get_date_time(),
        }
        data.update(kargs)
        return data

    def assert_mongo_data_equal(self, orm_object, data):
        self.assertEqual(orm_object['_id'], data['_id'])
        for field in self._fields:
            self.assertEqual(orm_object[field], data[field])

    def test_overwrite_collection_name(self):
        self.assertEqual(TestUser._ORM_collection_name, 'TestUser')

    def test_class_field(self):
        self.assertCountEqual(TestUser._get_field_names(), self._fields)

    def test_inherit_class_field(self):
        self.assertCountEqual(TestInherit._get_field_names(),
                              self._fields + ['foo'])

    def test_unique(self):
        # Create a instense to make TestUser call _get_field_names()
        _ = TestUser()
        index_fields = [
            idx['key'].keys()[0] for idx in self._collection.list_indexes()
        ]
        self.assertIn('uid', index_fields)

        alice = TestUser(uid=1, name='Alice')
        alice.save()
        bob = TestUser(uid=1, name='Bob')
        self.assertRaises(pymongo.errors.DuplicateKeyError, bob.save)

    def test_save(self):
        test_user = self._test_user
        test_user.save()
        test_user.save()  # call twice do nothing
        self.assert_mongo_data_equal(test_user,
                                     self._collection.find_one({
                                         'name': 'Bob'
                                     }))

        test_user['age'] = 17
        test_user.save()
        self.assert_mongo_data_equal(test_user,
                                     self._collection.find_one({
                                         'name': 'Bob'
                                     }))

    def test_delete(self):
        test_user = self._test_user
        with self.assertRaises(RuntimeError):
            test_user.delete()
        test_user.save()
        test_user.delete()
        self.assertIsNone(self._collection.find_one({'name': 'Bob'}))

    def test_find(self):
        self._test_user.save()
        bob = TestUser.find_one({'name': 'Bob'})
        self.assert_mongo_data_equal(bob,
                                     self._collection.find_one({
                                         'name': 'Bob'
                                     }))

        alice = TestUser(name='Alice', age=bob['age'])
        alice.save()
        query = {'age': bob['age']}
        self.assertEqual(TestUser.count(query), 2)
        self.assertEqual(
            len([x for x in TestUser.find_many(query, limit=1)]), 1)
        self.assertEqual(len([x for x in TestUser.find_many(query, skip=2)]), 0)
        self.assertEqual(
            next(TestUser.find_many(query, sort=[('name', 1)]))['name'],
            'Alice')
        self.assertEqual(
            next(TestUser.find_many(query, sort=[('name', -1)]))['name'], 'Bob')
        for found_user in TestUser.find_many(query):
            self.assertEqual(found_user['age'], bob['age'])

    def test_from_id(self):
        bob = self._test_user
        bob.save()
        self.assert_mongo_data_equal(TestUser.from_id(bob['_id']), bob)
        self.assert_mongo_data_equal(TestUser.from_id(str(bob['_id'])), bob)

    def test_upsert(self):
        # Upsert name of user whose name is Bob to Alice
        alice = TestUser(name='Alice')
        TestUser.upsert(alice, {'name': 'Bob'})
        test_query = TestUser.find_one({'name': 'Alice'})
        self.assertIsNotNone(test_query)
        self.assert_mongo_data_equal(
            test_query, {
                '_id': test_query['_id'],
                'uid': test_query['uid'],
                'name': alice['name'],
                'age': 18,
                'birthday': datetime(1997, 1, 12),
                'created': get_date_time(),
            })
        TestUser.find_one({'name': 'Alice'}).delete()

        bob = self._test_user
        bob.save()
        alice = TestUser(name='Alice')
        alice['age'] = 28
        alice['created'] = datetime(2017, 1, 7)
        TestUser.upsert(alice, {'name': 'Bob'})
        test_query = TestUser.find_one({'name': 'Alice'})
        self.assertIsNotNone(test_query)
        self.assert_mongo_data_equal(
            test_query, {
                '_id': bob['_id'],
                'uid': bob['uid'],
                'name': alice['name'],
                'age': alice['age'],
                'birthday': bob['birthday'],
                'created': datetime(2017, 1, 7),
            })

    def test_update(self):
        # Update name of user whose name is Bob to Alice
        alice = TestUser(name='Alice')
        TestUser.update(alice, {'name': 'Bob'})
        self.assertIsNone(TestUser.find_one({'name': 'Alice'}))

        bob = self._test_user
        bob.save()
        TestUser.update(alice, {'name': 'Bob'})
        test_query = TestUser.find_one({'name': 'Alice'})
        self.assertIsNotNone(test_query)
        self.assert_mongo_data_equal(
            test_query, {
                '_id': bob['_id'],
                'uid': bob['uid'],
                'name': 'Alice',
                'age': bob['age'],
                'birthday': bob['birthday'],
                'created': bob['created'],
            })
