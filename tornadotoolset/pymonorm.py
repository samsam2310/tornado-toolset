# -*- coding: utf-8 -*-
""" Pymongo ORM Base
Example:

User(Collection):
    # Collection name in mongodb
    _ORM_collection_name = 'user'

    uid = Field(time.time, is_unique=True)
    name = Field()
    age = Field(18)
    created = Field(datetime.utcnow)

user = User(name='Bob') # Create a user with default age 18.
user.save() # Save to mongodbs

user = User.find_one('Bob')
user.delete() # Delete bob
"""

from bson.objectid import ObjectId
from pymongo import MongoClient

import logging
import os

DB_HOST = os.environ.get('DB_HOST', 'localhost:27017').split(",")
DB_REPLSET = os.environ.get('DB_REPLSET', None)
DB_USER = os.environ.get('DB_USER', '')
DB_PWD = os.environ.get('DB_PWD', '')
DB_NAME = os.environ.get('DB_NAME', 'TestDB')
# The time out of MongoClient, in milliseconds.
DB_TIMEOUT = 2000


def get_database_from_env():
    logging.info("DB: Connect to DB: %s/%s" % (','.join(DB_HOST), DB_NAME))
    if DB_REPLSET:
        logging.info("DB: Replica Set: %s" % DB_REPLSET)
    if DB_USER:
        logging.info("DB: Login with user: %s" % DB_USER)
    else:
        logging.info("DB: Login without user.")
    if not DB_REPLSET and len(DB_HOST) > 1:
        logging.error('DB: Missing Replica set.')
        raise Exception('DB: Missing Replica set.')

    mongo_client = MongoClient(
        host=DB_HOST,
        replicaset=DB_REPLSET,
        serverSelectionTimeoutMS=DB_TIMEOUT)
    database = mongo_client[DB_NAME]

    if DB_USER != '' and not database.authenticate(DB_USER, DB_PWD):
        logging.error('DB: Database auth failed.')
        raise Exception('DB: Database auth failed.')
    return database


class Field():

    def __init__(self, default=None, is_unique=False):
        self._default = default
        self._is_unique = is_unique

    def get_default(self):
        default = self._default
        return default() if callable(default) else default

    def create_index(self, mongo_collection, field_name):
        # If index already exist then this has no effect
        if self._is_unique:
            logging.info('Create unique index: %s: %s' % (mongo_collection.name,
                                                          field_name))
            mongo_collection.create_index(field_name, unique=True)


class Collection():
    _ORM_database_instance = get_database_from_env()

    # Note: Overwrite this var to spesify the collection name.
    _ORM_collection_name = 'default'

    @classmethod
    def _get_field_names(cls):
        if not cls.__dict__.get('_ORM_field_names', None):
            cls._ORM_field_names = []
            for super_class in cls.mro():
                for attr in super_class.__dict__:
                    if attr in cls._ORM_field_names:
                        # Skip repeated field
                        continue
                    field = super_class.__dict__[attr]
                    if isinstance(field, Field):
                        field.create_index(cls.get_collection(), attr)
                        cls._ORM_field_names.append(attr)
        return cls._ORM_field_names

    @classmethod
    def _check_instance(cls, val):
        if not isinstance(val, cls):
            raise ValueError(
                'orm_object must be a isinstance of %s' % cls.__name__)

    @classmethod
    def get_collection(cls):
        return cls._ORM_database_instance[cls._ORM_collection_name]

    @classmethod
    def upsert(cls, orm_object, query):
        cls._check_instance(orm_object)
        set_data, default_data = orm_object._get_upsert_data()
        cls.get_collection().update_one(
            query, {
                "$set": set_data,
                "$setOnInsert": default_data
            },
            upsert=True)

    @classmethod
    def update(cls, orm_object, query):
        cls._check_instance(orm_object)
        set_data, _ = orm_object._get_upsert_data()
        cls.get_collection().update_one(query, {"$set": set_data})

    @classmethod
    def _create_from_pymongo_result(cls, result):
        if not result:
            return None

        data = {'_id': result['_id']}
        for attr in cls._get_field_names():
            data[attr] = result.get(attr, None)
        orm_object = cls(**data)
        orm_object._sync_server_data()
        return orm_object

    @classmethod
    def find_one(cls, *args, **kargs):
        return cls._create_from_pymongo_result(cls.get_collection().find_one(
            *args, **kargs))

    @classmethod
    def _get_cursor(cls, *args, **kargs):
        cursor = cls.get_collection().find(*args, **kargs)
        return cursor

    @classmethod
    def find_many(cls, *args, **kargs):
        for result in cls._get_cursor(*args, **kargs):
            yield cls._create_from_pymongo_result(result)

    @classmethod
    def count(cls, *args, **kargs):
        return cls._get_cursor(*args, **kargs).count()

    @classmethod
    def from_id(cls, object_id):
        if not isinstance(object_id, ObjectId):
            if not ObjectId.is_valid(object_id):
                return None
            object_id = ObjectId(object_id)
        return cls.find_one({'_id': object_id})

    def __init__(self, *args, **kargs):
        self._local_data = None
        self._default_field = None
        self._server_data = {}
        self._init_local_data(kargs)

    def _init_local_data(self, kargs):
        data = {'_id': kargs.get('_id', None)}
        default_field = []
        for attr in self._get_field_names():
            if attr in kargs:
                data[attr] = kargs[attr]
            else:
                default_field.append(attr)
                field = getattr(self.__class__, attr)
                data[attr] = field.get_default()

        self._local_data = data
        self._default_field = default_field

    def _sync_server_data(self):
        self._server_data = dict(self._local_data)

    def _get_update_data(self):
        res_data = dict()
        for attr in self._local_data:
            if (attr not in self._server_data or
                    self._local_data[attr] != self._server_data[attr]):
                res_data[attr] = self._local_data[attr]
        res_data.pop('_id', None)

        return res_data

    def _get_upsert_data(self):
        set_data = {}
        default_data = {}
        local_data = self._local_data
        for attr in local_data:
            if attr in self._default_field:
                default_data[attr] = local_data[attr]
            else:
                set_data[attr] = local_data[attr]
        set_data.pop('_id', None)
        return set_data, default_data

    def __getitem__(self, key):
        return self._local_data[key]

    def __setitem__(self, key, val):
        if key not in self._get_field_names():
            raise KeyError('%s is not an attribute of %s.' %
                           (key, self.__class__.__name__))

        self._local_data[key] = val
        if key in self._default_field:
            self._default_field.remove(key)

    def _check_id(self):
        if not self._local_data.get('_id', None):
            raise RuntimeError('Missing _id field.')

    def save(self):
        update_data = self._get_update_data()
        if not update_data:
            return
        if self._local_data.get('_id', None):
            self.get_collection().update_one({
                '_id': self._local_data['_id'],
            }, {'$set': update_data})
        else:
            insert_res = self.get_collection().insert_one(update_data)
            self._local_data['_id'] = insert_res.inserted_id
        self._sync_server_data()

    def delete(self):
        self._check_id()
        self.get_collection().delete_one({'_id': self._local_data['_id']})
        self._local_data['_id'] = None
        self._server_data = {}
