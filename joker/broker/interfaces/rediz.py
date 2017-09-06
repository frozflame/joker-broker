#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import json

from fakeredis import FakeStrictRedis
from joker.cast.serialize import JSONEncoderExtended
from redis import StrictRedis


class RedisInterfaceMixin(object):
    def json_set(self, name, obj, **kwargs):
        value = json.dumps(obj, cls=JSONEncoderExtended)
        self.set(name, value, **kwargs)

    def json_get(self, name):
        value = self.get(name)
        if value is None:
            return None
        if not isinstance(value, str):
            value = value.decode('utf-8')
        return json.loads(value)

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

    @classmethod
    def __from_conf_deprecated(cls, conf_section):
        redis_options = {
            'host': conf_section.get('host'),
            'port': str(conf_section.get('port', 6379)),
            'decode_responses': conf_section.get('decode_responses', False),
            'db': conf_section.get('db', 0),
        }
        return cls(**redis_options)


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

    @classmethod
    def from_url(cls, url, **kwargs):
        return cls()
