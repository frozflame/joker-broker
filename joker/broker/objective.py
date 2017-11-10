#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, unicode_literals

import datetime
from decimal import Decimal

from joker.cast import represent
from sqlalchemy.ext.declarative import declarative_base


class DeclBase(declarative_base()):
    __abstract__ = True

    def __repr__(self):
        fields = [c.name for c in self.__table__.primary_key]
        return represent(self, fields)

    @classmethod
    def format_cache_key(cls, pk):
        c = cls.__name__
        t = cls.__table__.name
        return '{}:{}:{}'.format(c, t, pk)

    @property
    def cache_key(self):
        return self.format_cache_key(self.id)

    @classmethod
    def load(cls, ident, session, cache=None):
        if cache is not None:
            serialized = cache.json_get(cls.format_cache_key(ident))
            if serialized:
                return cls.unserialize_from(serialized)
        return session.query(cls).get(ident)

    @classmethod
    def load_many(cls, idents, session, cache=None):
        return [cls.load(x, session, cache=cache) for x in idents]

    def as_json_serializable(self, fields=None):
        result = {}
        names = {c.name for c in self.__table__.columns}
        if fields is None:
            fields = names
        else:
            fields = set(fields).intersection(names)

        for key in fields:
            val = getattr(self, key)
            if isinstance(val, datetime.datetime):
                result[key] = {
                    "__type__": "datetime",
                    "value": val.strftime("%Y-%m-%d %H:%M:%S"),
                }
            elif isinstance(val, datetime.date):
                result[key] = {
                    "__type__": "date",
                    "value": val.strftime("%Y-%m-%d"),
                }
            elif isinstance(val, Decimal):
                result[key] = {
                    "__type__": "Decimal",
                    "value": str(val),
                }
            else:
                result[key] = val
        return result

    @classmethod
    def unserialize_from(cls, dic):
        params = {}
        for key, val in dic.items():
            if isinstance(val, dict) and '__type__' in val:
                if val["__type__"] == "datetime":
                    a = val['value'], "%Y-%m-%d %H:%M:%S"
                    params[key] = datetime.datetime.strptime(*a)
                elif val["__type__"] == "date":
                    a = val['value'], "%Y-%m-%d"
                    params[key] = datetime.datetime.strptime(*a).date()
                elif val["__type__"] == "Decimal":
                    params[key] = Decimal(val["value"])
            else:
                params[key] = val
        return cls(**params)


__all__ = ['DeclBase']
