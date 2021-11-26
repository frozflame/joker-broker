#!/usr/bin/env python3
# coding: utf-8

from joker.cast import represent
from joker.cast.syntax import noop
from joker.interfaces.redis import RedisExtended


class RedisInterface(RedisExtended):
    @classmethod
    def from_conf(cls, conf_section):
        redis_options = dict(conf_section)
        redis_options.pop('type', '')
        url = redis_options.pop('url', None)
        if url is None:
            return cls(**redis_options)
        return cls.from_url(url, **redis_options)


class NullRedisInterface:
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
    def from_url(cls, *_args, **_kwargs):
        return cls()

    def rekom_getsetnx(self, *_args, **kwargs):
        pass
