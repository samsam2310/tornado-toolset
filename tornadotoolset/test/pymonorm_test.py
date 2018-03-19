# -*- coding: utf-8 -*-

# Test the ORM module of pymongo

from datetime import datetime

import pymongo
import unittest

from tornadotoolset.pymonorm import Collection, Field, get_database_from_env


def get_date_time():
    return datetime(2017, 8, 12)


class TestUser(Collection):
    _ORM_collection_name = 'TestUser'

    name = Field()
    age = Field(default=18)
    birthday = Field(default=datetime(1997, 1, 12))
    created = Field(default=get_date_time)


class MongoOrmTest(unittest.TestCase):
    def setUp(self):
        self._db = get_database_from_env()
        self._db.drop_collection(TestUser._ORM_collection_name)
        self._collection = self._db[TestUser._ORM_collection_name]
        self._fields = ['name', 'age', 'birthday', 'created']
        self._test_user = TestUser(
            name='Bob', age=20, birthday=datetime(1997, 11, 2))

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
        self.assertEqual(
            len([x for x in TestUser.find_many(query, skip=2)]), 0)
        self.assertEqual(
            next(TestUser.find_many(query, sort=[('name', 1)]))['name'],
            'Alice')
        self.assertEqual(
            next(TestUser.find_many(query, sort=[('name', -1)]))['name'],
            'Bob')
        for found_user in TestUser.find_many(query):
            self.assertEqual(found_user['age'], bob['age'])

    def test_from_id(self):
        bob = self._test_user
        bob.save()
        self.assert_mongo_data_equal(TestUser.from_id(bob['_id']), bob)
        self.assert_mongo_data_equal(TestUser.from_id(str(bob['_id'])), bob)

    def test_upsert(self):
        alice = TestUser(name='Alice')
        TestUser.upsert(alice, {'name': 'Bob'})
        test_query = TestUser.find_one({'name': 'Alice'})
        self.assertIsNotNone(test_query)
        self.assert_mongo_data_equal(test_query,
                                     self.get_default_data(
                                         _id=test_query['_id'], name='Alice'))
        TestUser.find_one({'name': 'Alice'}).delete()

        bob = self._test_user
        bob.save()
        alice = TestUser(name='Alice')
        alice['age'] = 18
        alice['created'] = datetime(2017, 1, 7)
        TestUser.upsert(alice, {'name': 'Bob'})
        test_query = TestUser.find_one({'name': 'Alice'})
        self.assertIsNotNone(test_query)
        self.assert_mongo_data_equal(
            test_query, {
                '_id': test_query['_id'],
                'name': 'Alice',
                'age': 18,
                'birthday': bob['birthday'],
                'created': datetime(2017, 1, 7),
            })

    def test_update(self):
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
                '_id': test_query['_id'],
                'name': 'Alice',
                'age': bob['age'],
                'birthday': bob['birthday'],
                'created': bob['created'],
            })
