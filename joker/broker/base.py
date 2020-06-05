#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, unicode_literals

import datetime
import json
from abc import ABC
from decimal import Decimal

import sqlalchemy.exc
from joker.cast import represent
from sqlalchemy import Table, select, tuple_, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.inspection import inspect


def flatten(tup):
    if isinstance(tup, tuple) and len(tup) == 1:
        return tup[0]
    return tup


def unflatten(obj):
    if isinstance(obj, tuple):
        return obj
    return obj,


def commit_or_rollback(session):
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise


class Toolkit(object):
    @staticmethod
    def _get_resource_broker():
        raise NotImplementedError

    def __init__(self, rb=None):
        """
        :type rb: joker.broker.access.ResourceBroker
        :param rb:
        """
        if not rb:
            rb = self._get_resource_broker()
        self.rb = rb


class StandardToolkit(Toolkit, ABC):
    """
    Base class for Viewmodels
        just remove the need to pass session obj for every func
    """

    def __init__(self, rb=None, session=None):
        """
        :type rb: joker.broker.access.ResourceBroker
        :param rb:
        :type session: sqlalchemy.orm.Session
        :param session:
        """
        Toolkit.__init__(self, rb)
        self.cache = self.rb.cache
        if session is None:
            self.session = self.rb.get_session()
            self._using_private_session = True
        else:
            self.session = session
            self._using_private_session = False

    def __del__(self):
        if not self._using_private_session:
            return
        try:
            self.session.close()
        except Exception:
            pass

    def commit_or_rollback(self):
        commit_or_rollback(self.session)

    def persist(self, *items):
        """
        :param items: a series of DeclBase derived instance
        """
        for o in items:
            self.session.add(o)
        self.commit_or_rollback()
        if self.cache is not None:
            kvpairs = [(x.cache_key, x.serialize()) for x in items]
            self.cache.set_many(kvpairs)

    def bulk_insert(self, target, records):
        if not isinstance(target, Table):
            target = target.__table__
        return self.rb.primary.engine.execute(target.insert(), records)


Toolbox = StandardToolkit


class DeclBase(declarative_base()):
    __abstract__ = True
    representation_columns = []

    def __repr__(self):
        if self.representation_columns:
            return represent(self, self.representation_columns)
        fields = [c.name for c in self.get_table().primary_key]
        return represent(self, fields)

    @classmethod
    def get_table(cls):
        return getattr(cls, '__table__')

    def get_identity(self, flat=True):
        identity = inspect(self).identity
        if flat:
            identity = flatten(identity)
        return identity

    @classmethod
    def format_cache_key(cls, ident):
        c = cls.__name__
        t = cls.get_table().name
        x = '_'.join(str(i) for i in unflatten(ident))
        return '{}:{}:{}'.format(c, t, x)

    @property
    def cache_key(self):
        return self.format_cache_key(self.get_identity(flat=False))

    def save(self, session, cache=None):
        if cache is not None:
            cache.set(self.cache_key, self.serialize())
        session.add(self)
        commit_or_rollback(session)

    @classmethod
    def load(cls, ident, session, cache=None):
        if cache is not None:
            string = cache.get(cls.format_cache_key(ident))
            if string:
                return cls.unserialize(string)
        return session.query(cls).get(ident)

    @classmethod
    def load_many(cls, idents, session, cache=None):
        idents = [unflatten(it) for it in idents]

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
            tbl = cls.get_table()
            cond = tuple_(*tbl.primary_key).in_(remainders)
            query = session.query(cls).filter(cond)
            for o in query.all():
                results[o.get_identity(flat=False)] = o
        return [results.get(it) for it in idents]

    def as_json_serializable(self, fields=None):
        result = {}
        names = {c.name for c in self.get_table().columns}
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

    @classmethod
    def create_all_tables(cls, engine):
        if not cls.__abstract__:
            raise TypeError('only available on base classes')
        meta = cls.metadata
        for schema in {t.schema for t in meta.tables.values()}:
            sql = 'CREATE SCHEMA IF NOT EXISTS "{}";'.format(schema)
            engine.execute(sql)
        meta.create_all(bind=engine)

    @classmethod
    def find(cls, cond, session, form='o', start=0, limit=1000, order=None):
        """
        :type cond: whereclause / dict
        :param cond: e.g. {'name': 'alice', 'gender': 'female'}

        :type session: sqlalchemy.orm.Session
        :param session:

        :type form: str
        :param form: ('o', 'p', 'd' or 'i') form of each record found
        'o' for model object (the bound class of this method),
        'd' for dict
        'r' for sqlalchemy.engine.result.RowProxy,
        'i' for identity (primary key value)
        'p' for sqlalchemy.engine.result.RowProxy, deprecated

        :type start: int
        :param start: pagination offset, int, default 0
        :type limit: int
        :param limit: pagination limit, int, default 1000
        :param order: sqlalchemy clauses
        """
        allowed_forms = {'o', 'r', 'd', 'i', 'p'}
        if form not in allowed_forms:
            msg = 'form must be chosen from {}'.format(allowed_forms)
            raise ValueError(msg)

        tbl = getattr(cls, '__table__')
        if not order:
            order = tuple(tbl.primary_key)
        elif not isinstance(order, (tuple, list)):
            order = order,

        # reduce db bandwidth cost if only pk is required
        if form == 'i':
            stmt = select(tbl.primary_key)
        else:
            stmt = tbl.select()

        if isinstance(cond, dict):
            expressions = list()
            for k, v in cond.items():
                expressions.append(getattr(tbl.c, k) == v)
            cond = and_(*expressions)

        stmt = stmt.where(cond)
        stmt = stmt.order_by(*order)

        if start:
            stmt = stmt.offset(start)
        if limit:
            stmt = stmt.limit(limit)

        try:
            rows = list(session.execute(stmt))
        except sqlalchemy.exc.SQLAlchemyError:
            session.rollback()
            raise

        if form == 'i':
            return [flatten(tuple(r)) for r in rows]
        if form == 'o':
            return [cls(**dict(r)) for r in rows]
        if form == 'd':
            return [dict(r) for r in rows]
        if form == 'p':
            import warnings
            warnings.warn("form='p' is deprecated, use 'r' instead")
        return rows
