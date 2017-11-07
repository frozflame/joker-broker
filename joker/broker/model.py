#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import weakref
from sqlalchemy import select


class AbstractModel(object):
    """
    Will be DEPRECATED!
    Just use SQLAlchemy's ORM
    requiring implementation of get_resource_broker method

    class bound attributes
    - _loaded_instances
    - table
    - primary_key
    - delete(..)
    - get_resource_broker()  -- NotImplementedError
    - get_table()
    - generate_pk()
    - format_cache_key(..)

    instance bound attributes
    - _changed
    - _initial
    - _permanent
    - pk
    - permanent
    - mark_parmanent()
    - load(..)
    - save()
    - data
    - as_json_serializable()
    - get(..)
    - []
    - _insert()
    - _update()
    - _update_cache()
    """
    # override these per model/table
    table = ''
    primary_key = 'id'

    _loaded_instances = weakref.WeakValueDictionary()

    __slots__ = ['_changed', '_initial', '_permanent']

    def __init__(self, *args, **kwargs):
        # http://stackoverflow.com/a/19566973/2925169
        data = dict(*args, **kwargs)
        AbstractModel.__dict__['_changed'].__set__(self, dict())
        AbstractModel.__dict__['_initial'].__set__(self, data)
        AbstractModel.__dict__['_permanent'].__set__(self, False)

    @classmethod
    def get_resource_broker(cls):
        raise NotImplementedError

    def __repr__(self):
        clsname = self.__class__.__name__
        return '{}({})'.format(clsname, self.data)

    def __contains__(self, key):
        return (key in self._initial) or (key in self._changed)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def __getitem__(self, key):
        if key in self._changed:
            return self._changed[key]
        return self._initial[key]

    def __setitem__(self, key, value):
        self._changed[key] = value

    def __delitem__(self, key):
        # del from both self._initial and self._changed
        del_count = 0
        if key in self._initial:
            del self._initial[key]
            del_count += 1
        if key in self._changed:
            del self._changed[key]
            del_count += 1
        if not del_count:
            m = "'{}'".format(key)
            raise KeyError(m)

    def __getattr__(self, key):
        p = getattr(self.__class__, key, None)
        if isinstance(p, property):
            if p.fget is None:
                raise AttributeError("can't get attribute")
            p.fget(self)
        else:
            return self.get(key)

    def __setattr__(self, key, value):
        p = getattr(self.__class__, key, None)
        if isinstance(p, property):
            if p.fset is None:
                raise AttributeError("can't set attribute")
            p.fset(self, value)
        else:
            self._changed[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            c = self.__class__.__name__
            m = "'{}' object has no attribute '{}'".format(c, key)
            raise AttributeError(m)

    @property
    def pk(self):
        kls = self.__class__
        return self.get(kls.primary_key)

    @pk.setter
    def pk(self, value):
        if value == self.pk:
            return
        kls = self.__class__
        self[kls.primary_key] = value

    @pk.deleter
    def pk(self):
        """
        Delete pk without raising an error
        """
        kls = self.__class__
        try:
            del self[kls.primary_key]
        except KeyError:
            pass

    @property
    def permanent(self):
        """
        True only if both conditions are satisfied

        [1]     M.load(), M.save() or manually set _permanent True
        [2]     primary key value not changed

        :return: True/False
        """
        k = self.__class__.primary_key
        if k in self._changed:
            return False
        return self._permanent

    @permanent.setter
    def permanent(self, value):
        value = bool(value)
        AbstractModel.__dict__['_permanent'].__set__(self, value)
        kls = self.__class__
        if value:
            k = kls.primary_key
            v = self._changed.pop(k, None)
            if v is not None:
                self._initial[k] = v
            kls._loaded_instances[kls, self.pk] = self
        else:
            del kls._loaded_instances[kls, self.pk]

    @permanent.deleter
    def permanent(self):
        self.permanent = False

    def mark_permanent(self):
        """merely syntax sugar"""
        self.permanent = True
        return self

    @classmethod
    def generate_pk(cls):
        # keep pylint from complaining
        return None and 0

    @property
    def data(self):
        p = self._initial.copy()
        p.update(self._changed)
        return p

    def __iter__(self):
        return self.data

    def as_json_serializable(self):
        return self.data

    @classmethod
    def get_table(cls, interface='primary'):
        if isinstance(interface, str):
            rb = cls.get_resource_broker()
            interface = rb[interface]
        if '.' in cls.table:
            schema, table = cls.table.split('.', 2)
        else:
            schema, table = None, cls.table
        return interface.get_table(table, schema=schema)

    @classmethod
    def format_cache_key(cls, pk):
        return '{}:{}:{}'.format(cls.__name__, cls.table, pk)

    @classmethod
    def load(cls, pk, interface='primary'):
        # try to load from weakref
        try:
            return cls._loaded_instances[cls, pk]
        except KeyError:
            pass

        # try to load from cache
        key = cls.format_cache_key(pk)
        rb = cls.get_resource_broker()
        props = rb.cache.json_get(key)
        if props is not None:
            return cls(**props).mark_permanent()

        tbl = cls.get_table(interface)
        pkc = getattr(tbl.c, cls.primary_key)
        stmt = tbl.select()
        stmt = stmt.where(pkc == pk)
        resultproxy = stmt.execute()
        row = resultproxy.fetchone()
        resultproxy.close()

        if row is None:
            return

        o = cls(**dict(row))
        o.update_cache()
        return o.mark_permanent()

    @classmethod
    def find(cls, kvpairs, interface='primary', **kwargs):
        """
        :param kvpairs: dict,\
            e.g. {'name': 'alice', 'gender': 'female'}
        :param interface: str
        :param kwargs: see parameters

        :parameter many: bool.
            If true, return a list of objects instead of the 1st one
        :parameter pkonly: bool
            If true, return only the value of primary key

        :parameter start: int
        :parameter limit: int

        :return:
        """
        tbl = cls.get_table(interface)

        # compatible to old version
        many = kwargs.get('many') or kwargs.get('multi')
        pkonly = kwargs.get('pkonly')

        # pagination
        limit = kwargs.get('limit')
        offset = kwargs.get('offset')

        # reduce db bandwidth cost if only pk is required
        if pkonly:
            stmt = select([getattr(tbl.c, cls.primary_key)])
        else:
            stmt = tbl.select()

        for k, v in kvpairs.items():
            stmt = stmt.where(getattr(tbl.c, k) == v)

        if many:
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
        else:
            stmt = stmt.limit(1)

        rows = list(stmt.execute())

        if pkonly:
            objects = [getattr(r, cls.primary_key) for r in rows]
        else:
            objects = [cls(**dict(r)) for r in rows]
            for o in objects:
                o.update_cache()
                o.mark_permanent()

        if many:
            return objects
        try:
            return objects[0]
        except IndexError:
            return None

    def _insert(self, interface):
        tbl = self.get_table(interface)
        kls = self.__class__

        # set pk if generate_pk provides not-None pk
        if self.pk is None:
            pk = self.generate_pk()
            if pk is not None:
                self._initial[kls.primary_key] = pk
                # self.pk = pk  -- wrong!

        # insert with all fields (_initial + _changed)
        rp = tbl.insert().execute(self.data)

        # set pk from db response
        pk = rp.inserted_primary_key[0]
        self._initial[kls.primary_key] = pk
        # self.pk = pk -- wrong!

    def _update(self, interface):
        if not self._changed:
            return

        kls = self.__class__
        tbl = self.get_table(interface)
        pkc = getattr(tbl.c, kls.primary_key)

        # update changed fields only
        stmt = tbl.update().values(**self._changed)
        stmt = stmt.where(pkc == self.pk)
        stmt.execute()

    def save(self, interface='primary'):
        if self.permanent:
            self._update(interface)
        else:
            self._insert(interface)
        self.update_cache()
        return self.mark_permanent()

    def update_cache(self):
        # TODO: expire key in cache
        pk = self.pk
        if pk is not None:
            key = self.format_cache_key(pk)
            rb = self.get_resource_broker()
            rb.cache.json_set(key, self.data)
        return self

    @classmethod
    def delete_cache(cls, *pklist):
        names = [cls.format_cache_key(pk) for pk in pklist]
        rb = cls.get_resource_broker()
        rb.cache.delete(*names)

    @classmethod
    def delete(cls, *pklist, **kwargs):
        for pk in pklist:
            o = cls._loaded_instances.get((cls, pk))
            if o is not None:
                o.permament = False
        interface = kwargs.get('interface', 'primary')
        tbl = cls.get_table(interface)
        pkc = getattr(tbl.c, cls.primary_key)
        stmt = tbl.delete().where(pkc.in_(pklist))
        stmt.execute()
        cls.delete_cache(*pklist)

