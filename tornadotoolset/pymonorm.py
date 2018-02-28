# Pymongo ORM Base

from bson.objectid import ObjectId
from pymongo import MongoClient

import os

DB_HOST = os.environ.get('DB_HOST', 'localhost:27017').split(",")
DB_REPLSET = os.environ.get('DB_REPLSET', None)
DB_USER = os.environ.get('DB_USER', '')
DB_PWD = os.environ.get('DB_PWD', '')
DB_NAME = os.environ.get('DB_NAME', 'mealtime')
# The time out of MongoClient, in seconds.
DB_TIMEOUT = 2


def getDatabaseFromEnv(is_log_mode=False):
    if is_log_mode:
        print("Connect to DB: %s/%s" % (','.join(DB_HOST), DB_NAME))
        if DB_REPLSET:
            print("Replica Set: %s" % DB_REPLSET)
        if DB_USER:
            print("Login with user: %s" % DB_USER)
        else:
            print("Login without user.")
    if not DB_REPLSET and len(DB_HOST) > 1:
        print('Missing Replica set.')
        return None

    mongo_client = MongoClient(
        host=DB_HOST,
        replicaset=DB_REPLSET,
        serverSelectionTimeoutMS=DB_TIMEOUT)
    database = mongo_client[DB_NAME]

    if DB_USER != '':
        if not database.authenticate(DB_USER, DB_PWD):
            print('Database auth failed.')
            return None
    return database


class Field():
    def __init__(self, default=None):
        self._default = default

    def getDefault(self):
        default = self._default
        return default() if callable(default) else default


class Collection():
    _ORM_field_names = None
    _ORM_database_instance = getDatabaseFromEnv(True)
    # Need to be overwritten by subclass
    _ORM_collection = 'default'

    @classmethod
    def _getFieldNames(cls):
        if not cls._ORM_field_names:
            cls._ORM_field_names = [
                attr for attr in cls.__dict__
                if isinstance(getattr(cls, attr), Field)
            ]
        return cls._ORM_field_names

    @classmethod
    def _checkInstance(cls, val):
        if not isinstance(orm_object, cls):
            raise ValueError(
                'orm_object must be a isinstance of %s' % cls.__name__)

    @classmethod
    def getCollection(cls):
        return cls._ORM_database_instance[cls._ORM_collection]

    @classmethod
    def upsert(cls, orm_object, query):
        cls._checkInstance(orm_object)
        set_data, default_data = orm_object._getUpsertData()
        cls.getCollection().update_one(
            query, {"$set": set_data,
                    "$setOnInsert": default_data},
            upsert=True)

    @classmethod
    def update(cls, orm_object, query):
        cls._checkInstance(orm_object)
        data, _ = orm_object._getUpsertData()
        cls.getCollection().update_one(query, {"$set": set_data})

    @classmethod
    def _createFromPymongoResult(cls, result):
        if not result:
            return None

        data = {'_id': result['_id']}
        for attr in cls._getFieldNames():
            data[attr] = result.get(attr, None)
        orm_object = cls(**data)
        orm_object._syncServerData()
        return orm_object

    @classmethod
    def findOne(cls, **kargs):
        return cls._createFromPymongoResult(
            cls.getCollection().find_one(kargs))

    @classmethod
    def findMany(cls, skip=0, limit=0, sort=None, **kargs):
        for result in cls.getCollection().find(kargs):
            yield cls._createFromPymongoResult(result)

    @classmethod
    def getById(cls, object_id):
        if not isinstance(object_id, ObjectId):
            if not ObjectId.is_valid(key):
                return None
            object_id = ObjectId(object_id)
        return cls.findOne(_id=object_id)

    def __init__(self, *args, **kargs):
        self._local_data = None
        self._default_field = None
        self._server_data = {}
        self._initLocalData(kargs)

    def _initLocalData(self, kargs):
        data = {'_id': kargs.get('_id', None)}
        default_field = []
        for attr in self._getFieldNames():
            if attr in kargs:
                data[attr] = kargs[attr]
            else:
                default_field.append(attr)
                field = getattr(self.__class__, attr)
                data[attr] = field.getDefault()

        self._local_data = data
        self._default_field = default_field

    def _syncServerData(self):
        self._server_data = dict(self._local_data)

    def _getUpdateData(self):
        res_data = dict()
        for attr in self._local_data:
            if (attr not in self._server_data
                    or self._local_data[attr] != self._server_data[attr]):
                res_data[attr] = self._local_data[attr]
        res_data.pop('_id', None)

        return res_data

    def _getUpsertData(self):
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
        if key not in self._getFieldNames():
            raise KeyError('%s is not an attribute of %s.' %
                           (key, self.__class__.__name__))

        self._local_data[key] = val
        if key in self._default_field:
            self._default_field.remove(key)

    def _checkId(self):
        if not self._local_data.get('_id', None):
            raise RuntimeError('Missing _id field.')

    def save(self):
        update_data = self._getUpdateData()
        if not update_data:
            return
        if self._local_data.get('_id', None):
            self.getCollection().update_one({
                '_id': self._local_data['_id'],
            }, {'$set': update_data})
        else:
            insert_res = self.getCollection().insert_one(update_data)
            self._local_data['_id'] = insert_res.inserted_id
        self._syncServerData()

    def delete(self):
        self._checkId()
        self.getCollection().delete_one({'_id': self._local_data['_id']})
        self._local_data['_id'] = None
        self._server_data = {}
