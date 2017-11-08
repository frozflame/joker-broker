#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, unicode_literals

import datetime
from decimal import Decimal

from sqlalchemy import MetaData
from sqlalchemy.ext.declarative import declarative_base

metadata = MetaData()
DeclarBase = declarative_base(metadata=metadata)


class NoncachedBase(DeclarBase):
    __abstract__ = True

    def __repr__(self):
        c = self.__class__.__name__
        a = hex(id(self))
        return '<{}(id={}) at {}>'.format(c, self.id, a)

    @classmethod
    def get_resource_broker(cls):
        from joker.broker import get_resource_broker
        return get_resource_broker()

    def as_json_serializable(self):
        result = {}
        for col in self.__table__.columns:
            key = col.name
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

    @classmethod
    def load(cls, ident):
        rb = cls.get_resource_broker()
        session = rb.get_session()
        return session.query(cls).get(ident)

    def save(self):
        pass


class CachedBase(NoncachedBase):
    __abstract__ = True

    @classmethod
    def format_cache_key(cls, pk):
        c = cls.__name__
        t = cls.__table__.name
        return '{}:{}:{}'.format(c, t, pk)

    @property
    def cache_key(self):
        return self.format_cache_key(self.id)
