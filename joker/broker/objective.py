#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, unicode_literals

import datetime
import json
from decimal import Decimal

from joker.cast import represent
from sqlalchemy import tuple_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect


def _unflatten(obj):
    if isinstance(obj, tuple):
        return obj
    return obj,


def _flatten(tup):
    if isinstance(tup, tuple) and len(tup) == 1:
        return tup[0]
    return tup


class Toolbox(object):
    """
    Base class for Viewmodels
        just remove the need to pass session obj for every func
    """
    def __init__(self, resource_broker, session=None):
        """
        :type resource_broker: joker.broker.access.ResourceBroker
        :param resource_broker:
        :type session: sqlalchemy.orm.Session
        :param session:
        """
        self.rb = resource_broker
        self.cache = resource_broker.cache
        if session is None:
            self.session = resource_broker.get_session()
        else:
            self.session = session

    def persist(self, *items):
        """
        :param items: a series of DeclBase derived instance
        """
        for o in items:
            self.session.add(o)
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

        if self.cache is not None:
            kvpairs = [(x.cache_key, x.serialize()) for x in items]
            self.cache.set_many(kvpairs)


class DeclBase(declarative_base()):
    __abstract__ = True

    def __repr__(self):
        fields = [c.name for c in self.__table__.primary_key]
        return represent(self, fields)

    def get_identity(self, flat=True):
        identity = inspect(self).identity
        if flat:
            identity = _flatten(identity)
        return identity

    @classmethod
    def format_cache_key(cls, ident):
        c = cls.__name__
        t = cls.__table__.name
        x = '_'.join(str(i) for i in _unflatten(ident))
        return '{}:{}:{}'.format(c, t, x)

    @property
    def cache_key(self):
        return self.format_cache_key(self.get_identity(flat=False))

    @classmethod
    def load(cls, ident, session, cache=None):
        if cache is not None:
            string = cache.get(cls.format_cache_key(ident))
            if string:
                return cls.unserialize(string)
        return session.query(cls).get(ident)

    @classmethod
    def load_many(cls, idents, session, cache=None):
        idents = [_unflatten(it) for it in idents]

        if cache is not None:
            names = [cls.format_cache_key(it) for it in idents]
            values = cache.get_many(names)
            pairs = zip(idents, values)
            results = {it: v for (it, v) in pairs if it is not None}
            remainders = [it for it in idents if it not in results]
        else:
            results = dict()
            remainders = idents

        if remainders:
            tbl = cls.__table__
            cond = tuple_(*tbl.primary_key).in_(remainders)
            query = session.query(cls).filter(cond)
            for o in query.all():
                results[o.get_identity(flat=False)] = o
        return [results.get(it) for it in idents]

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

    def serialize(self):
        dikt = self.as_json_serializable()
        return json.dumps(dikt)

    @classmethod
    def unserialize(cls, string, asdict=False):
        dikt = json.loads(string)
        params = {}
        for key, val in dikt.items():
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
        if asdict:
            return params
        return cls(**params)


__all__ = ['DeclBase', 'Toolbox']
