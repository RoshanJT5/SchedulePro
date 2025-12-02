from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from typing import Any, Dict, List
from flask import abort

from pymongo import MongoClient, ASCENDING
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from typing import Any, Dict, List


class _Session:
    def __init__(self, db):
        self._db = db
        self._added = []
        self._deleted = []

    def add(self, obj):
        self._added.append(obj)

    def delete(self, obj):
        self._deleted.append(obj)

    def flush(self):
        # First process deletions recorded by db.session.delete(obj)
        for obj in list(self._deleted):
            try:
                coll = self._db[_get_collection_name(obj.__class__)]
                obj_id = getattr(obj, 'id', None)
                if obj_id is not None:
                    coll.delete_one({'id': obj_id})
                else:
                    # If no integer id, try to remove by _id or by matching dict
                    if hasattr(obj, '_id'):
                        coll.delete_one({'_id': obj._id})
                    else:
                        coll.delete_many(obj.to_dict())
            except Exception:
                pass

        # write added objects to DB and assign integer id if model uses 'id'
        for obj in list(self._added):
            obj._save(self._db)

    def commit(self):
        # for simplicity, flush does the persistence
        self.flush()
        self._added.clear()
        self._deleted.clear()


class _DB:
    def __init__(self):
        self.client: MongoClient | None = None
        self._db = None
        self.session = None
        self.engine = None

    def init_app(self, app):
        uri = app.config.get('MONGO_URI', 'mongodb://localhost:27017')
        dbname = app.config.get('MONGO_DBNAME', 'timetable')
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=8000)
            # Force DNS & initial server selection
            self.client.admin.command('ping')
        except Exception as e:
            print(f"[Mongo Init] Primary URI failed ({e}); falling back to localhost.")
            fallback = 'mongodb://localhost:27017'
            self.client = MongoClient(fallback)
        self._db = self.client[dbname]
        self.session = _Session(self._db)
        self.engine = None

    def create_all(self):
        # No-op for MongoDB; ensure indexes where needed
        pass

    def drop_all(self):
        # No-op
        pass


db = _DB()


def _get_collection_name(cls):
    return cls.__name__.lower()


def _get_next_id(db, name: str) -> int:
    counters = db['__counters__']
    res = counters.find_one_and_update({'_id': name}, {'$inc': {'seq': 1}}, upsert=True, return_document=True)
    return int(res['seq'])


class ColumnRef:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return self.name


class ModelMeta(type):
    def __getattr__(cls, item):
        # Provide class-level helpers:
        # - `Model.query` should return a Query(model) so callers can do
        #    Model.query.count(), Model.query.first(), etc.
        # - other unknown attributes are treated as column references
        if item == 'query':
            return Query(cls)
        return ColumnRef(item)


class Query:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self._filter = {}
        self._sort = None

    def filter_by(self, **kwargs):
        self._filter.update(kwargs)
        return self

    def order_by(self, *attrs):
        # Support calling order_by(Model.field, Model.other) or order_by('field')
        sorts = []
        for attr in attrs:
            if isinstance(attr, str):
                sorts.append((attr, ASCENDING))
            elif hasattr(attr, 'name'):
                sorts.append((attr.name, ASCENDING))
            else:
                # fallback: try to use str()
                sorts.append((str(attr), ASCENDING))
        self._sort = sorts if sorts else None
        return self

    def all(self):
        coll = db._db[_get_collection_name(self.model_cls)]
        cursor = coll.find(self._filter)
        if self._sort:
            cursor = cursor.sort(self._sort)
        return [self.model_cls(**doc) for doc in cursor]

    def first(self):
        coll = db._db[_get_collection_name(self.model_cls)]
        doc = coll.find_one(self._filter)
        if not doc:
            return None
        return self.model_cls(**doc)

    def count(self):
        coll = db._db[_get_collection_name(self.model_cls)]
        return coll.count_documents(self._filter)

    def delete(self, *args, **kwargs):
        # Accept extra SQLAlchemy-specific args (e.g., synchronize_session)
        coll = db._db[_get_collection_name(self.model_cls)]
        return coll.delete_many(self._filter)

    def get(self, id_value):
        coll = db._db[_get_collection_name(self.model_cls)]
        doc = coll.find_one({'id': id_value})
        if not doc:
            return None
        return self.model_cls(**doc)

    def get_or_404(self, id_value):
        obj = self.get(id_value)
        if obj is None:
            abort(404)
        return obj


class BaseModel(metaclass=ModelMeta):
    def __init__(self, **kwargs):
        # support both Mongo _id and integer id
        # Set all provided keys as attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

    # `query` is provided at the class level by `ModelMeta.__getattr__` so
    # callers can use `SomeModel.query.count()` or `SomeModel.query.first()`.

    def to_dict(self) -> Dict[str, Any]:
        d = self.__dict__.copy()
        # remove internal fields
        return d

    def _save(self, mongo_db):
        coll = mongo_db[_get_collection_name(self.__class__)]
        # ensure integer id sequence
        if getattr(self, 'id', None) is None:
            self.id = _get_next_id(mongo_db, _get_collection_name(self.__class__))
        data = self.to_dict()
        coll.replace_one({'id': self.id}, data, upsert=True)


# --- Model definitions ---


class User(BaseModel):
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(getattr(self, 'password_hash', ''), password)

    def __repr__(self):
        return f'<User {getattr(self, "username", None)} ({getattr(self, "role", None)})>'


class Course(BaseModel):
    def __repr__(self):
        return f'<Course {getattr(self, "code", None)}>'


class Faculty(BaseModel):
    def __repr__(self):
        return f'<Faculty {getattr(self, "name", None)}>'


class Room(BaseModel):
    def __repr__(self):
        return f'<Room {getattr(self, "name", None)}>'


class Student(BaseModel):
    def __repr__(self):
        return f'<Student {getattr(self, "student_id", None)}>'


class StudentGroup(BaseModel):
    def __repr__(self):
        return f'<StudentGroup {getattr(self, "name", None)}>'


class PeriodConfig(BaseModel):
    def __repr__(self):
        return f'<PeriodConfig {getattr(self, "periods_per_day", None)} periods, {getattr(self, "period_duration_minutes", None)} min>'


class BreakConfig(BaseModel):
    def __repr__(self):
        return f'<BreakConfig {getattr(self, "break_name", None)}>'


class TimeSlot(BaseModel):
    def __repr__(self):
        return f'<TimeSlot {getattr(self, "day", None)} P{getattr(self, "period", None)}>'


class TimetableEntry(BaseModel):
    def __repr__(self):
        return f'<TimetableEntry {getattr(self, "course_id", None)}-{getattr(self, "faculty_id", None)}-{getattr(self, "room_id", None)}-{getattr(self, "student_group", None)}>'
    pass

