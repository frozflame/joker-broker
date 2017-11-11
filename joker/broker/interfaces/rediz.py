#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import json

from fakeredis import FakeStrictRedis
from joker.cast.serialize import JSONEncoderExtended
from redis import StrictRedis


def pass_(*args, **kwargs):
    # TODO: move to joker.cast
    return args, kwargs


def want_str(s, *args, **kwargs):
    """
    :param s:
    :param args: positional arguments passed to s.decode(..)
    :param kwargs: key word arguments passed to s.decode(..)
    :return:
    """
    if not isinstance(s, str):
        return s.decode(*args, **kwargs)
    return s


class RedisInterfaceMixin(object):
    def json_set(self, name, obj, **kwargs):
        value = json.dumps(obj, cls=JSONEncoderExtended)
        self.set(name, value, **kwargs)

    def json_set_many(self, pairs, **kwargs):
        """
        :param pairs: a series of 2-tuples
        :param kwargs:
        """
        pipe = getattr(self, 'pipeline')()
        for name, obj in pairs:
            value = json.dumps(obj, cls=JSONEncoderExtended)
            pipe.set(name, value, **kwargs)
        pipe.execute()

    def json_get(self, name):
        value = self.get(name)
        if value is None:
            return None
        return json.loads(want_str(value, 'utf-8'))

    def json_get_many(self, names):
        pipe = getattr(self, 'pipeline')()
        names = list(names)
        for name in names:
            pipe.get(name)
        values = pipe.execute()
        if not values:
            return [None for _ in names]
        objects = []
        for v in values:
            if v is None:
                objects.append(None)
            else:
                v = want_str(v, 'utf-8')
                objects.append(json.loads(v))
        return objects

    def get(self, name):
        raise NotImplementedError

    def set(self, name, value, **kwargs):
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
    pass


class FakeRedisInterface(FakeStrictRedis, RedisInterfaceMixin):
    pass


class NullRedisInterface(RedisInterfaceMixin):
    def __init__(self, *a, **kw):
        pass

    def get(self, name):
        pass

    def set(self, name, value, **kwargs):
        pass

    def pipeline(self, *args, **kwargs):
        pass_(args, kwargs)
        return self

    @classmethod
    def from_url(cls, url, **kwargs):
        return cls()

    def execute(self):
        """syntax sugar"""
        pass

