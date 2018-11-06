#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import random
from collections import OrderedDict

from fakeredis import FakeStrictRedis
from joker.cast import represent
from joker.cast.syntax import noop
from redis import StrictRedis


class RedisInterfaceMixin(object):
    def set_many(self, kvpairs, **kwargs):
        """
        :param kvpairs: a series of 2-tuples
        :param kwargs:
        """
        pipe = self.pipeline()
        for name, value in kvpairs:
            pipe.set(name, value, **kwargs)
        pipe.execute()

    def get_many(self, names):
        pipe = self.pipeline()
        for name in names:
            pipe.get(name)
        values = pipe.execute()
        if not values:
            return [None for _ in names]
        return values

    def rekom_getsetnx(self, name, value):
        # https://groups.google.com/d/msg/redis-db/QM15DH3SI6I/euJpdYJHTrcJ
        tmp_name = '_rekom_getsetnx_{}'.format(random.randint(1, 2 ** 60))
        pipe = self.pipeline()
        pipe.get(name)
        pipe.set(tmp_name, value)
        pipe.renamenx(tmp_name, name)
        pipe.delete(tmp_name)
        results = pipe.execute()
        return results[0]

    def get(self, name):
        raise NotImplementedError

    def set(self, name, value, **kwargs):
        raise NotImplementedError

    def pipeline(self, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_url(cls, url, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_conf(cls, conf_section):
        redis_options = dict(conf_section)
        redis_options.pop('type', '')
        url = redis_options.pop('url', None)
        if url is None:
            return cls(**redis_options)
        return cls.from_url(url, **redis_options)


class RedisInterface(StrictRedis, RedisInterfaceMixin):
    def __repr__(self):
        pool = getattr(self, 'connection_pool')
        kwargs = getattr(pool, 'connection_kwargs', {})
        params = OrderedDict([
            ('host', kwargs.get('host')),
            ('port', kwargs.get('port')),
            ('db', kwargs.get('db')),
        ])
        return represent(self, params)


class FakeRedisInterface(FakeStrictRedis, RedisInterfaceMixin):
    def __repr__(self):
        return represent(self, {'db': self._db_num})


class NullRedisInterface(RedisInterfaceMixin):
    get = noop
    set = noop
    # syntax sugar for pipeline
    execute = noop

    def __init__(self, *args, **kwargs):
        pass

    def __repr__(self):
        return represent(self, {})

    def __getattr__(self, _):
        return noop

    def pipeline(self, *_, **__):
        return self

    @classmethod
    def from_url(cls, url, **kwargs):
        return cls()
