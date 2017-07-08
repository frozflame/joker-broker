#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import os
import weakref
from collections import defaultdict


def _import_requirements():
    """
    A dummy function to list all imports
    These imports are slow!
    """
    from joker.broker.security import HashedPath
    from joker.broker.interfaces.sql import SQLInterface
    from joker.broker.interfaces.static import deserialize_conf
    from joker.broker.interfaces.static import GeneralInterface
    from joker.broker.interfaces.static import SecretInterface
    from joker.broker.interfaces.redis import RedisInterface
    from joker.broker.interfaces.redis import FakeRedisInterface
    from joker.broker.interfaces.redis import NullRedisInterface
    return [
        GeneralInterface, SecretInterface, SQLInterface,
        RedisInterface, FakeRedisInterface, NullRedisInterface,
        HashedPath, deserialize_conf,
    ]


def default_factory():
    return defaultdict(default_factory)


class Conf(defaultdict):
    cached_instances = weakref.WeakValueDictionary()

    @classmethod
    def load(cls, path):
        # if loaded already, return it
        path = os.path.abspath(path)
        if path in cls.cached_instances:
            return cls.cached_instances[path]

        from joker.broker.security import HashedPath
        sha1 = HashedPath.calc_hash(path, 'sha1')
        if sha1 in cls.cached_instances:
            return cls.cached_instances[sha1]

        # parse from conf file
        from joker.broker.interfaces.static import deserialize_conf
        conf = cls(default_factory, deserialize_conf(path))

        # Note: not cls.loaded_confs.
        # All sub-classes use the same dict
        Conf.cached_instances[path] = conf
        Conf.cached_instances[sha1] = conf
        return conf


class ResourceNotFoundError(Exception):
    pass


class ResourceBroker(object):
    cached_instances = weakref.WeakValueDictionary()

    def __init__(self, conf):
        """
        :param conf: (joker.broker.Conf)
        """
        # interfaces are slow to import, so import when needed
        self.conf = conf
        self.interfaces = dict()

        for name, section in conf.items():
            type_ = section.get('type')
            if name == 'general':
                from joker.broker.interfaces.static import GeneralInterface
                self.interfaces[name] = GeneralInterface.from_conf(section)

            elif name == 'secret':
                from joker.broker.interfaces.static import SecretInterface
                self.interfaces[name] = SecretInterface.from_conf(section)

            elif type_ == 'sql':
                from joker.broker.interfaces.sql import SQLInterface
                self.interfaces[name] = SQLInterface.from_conf(section)

            elif type_ == 'redis':
                from joker.broker.interfaces.redis import RedisInterface
                self.interfaces[name] = RedisInterface.from_conf(section)

            elif type_ == 'fakeredis':
                from joker.broker.interfaces.redis import FakeRedisInterface
                self.interfaces[name] = FakeRedisInterface.from_conf(section)

            elif type_ == 'nullredis':
                from joker.broker.interfaces.redis import NullRedisInterface
                self.interfaces[name] = NullRedisInterface.from_conf(section)

    @classmethod
    def create(cls, path):
        conf = Conf.load(path)
        if id(conf) in cls.cached_instances:
            return cls.cached_instances[id(conf)]
        else:
            return cls(conf)

    @classmethod
    def just_after_fork(cls):
        """
        http://docs.sqlalchemy.org/en/latest/core/pooling.html\
        #using-connection-pools-with-multiprocessing
        """
        from joker.broker.interfaces.sql import SQLInterface
        for rb in cls.cached_instances.values():
            for res in rb.resources.values():
                if isinstance(res, SQLInterface):
                    res.just_after_fork()

    def __getitem__(self, interface_name):
        try:
            return self.interfaces[interface_name]
        except:
            msg = 'section "{}" not in your config file or mis-configured'
            msg = msg.format(interface_name)
            raise ResourceNotFoundError(msg)

    @property
    def general(self):
        try:
            return self['general']
        except KeyError:
            from joker.broker.interfaces.static import GeneralInterface
            gi = GeneralInterface.from_default()
            return self.interfaces.setdefault('general', gi)

    @property
    def secret(self):
        try:
            return self['secret']
        except KeyError:
            from joker.broker.interfaces.static import SecretInterface
            si = SecretInterface.from_default()
            return self.interfaces.setdefault('secret', si)
    
    @property
    def primary(self):
        try:
            return self['primary']
        except KeyError:
            # fallback to in-memory SQLite;
            # also making this property type-inferrable.
            # slow to import, so import when needed
            from joker.broker.interfaces.sql import SQLInterface
            si = SQLInterface.from_default()
            return self.interfaces.setdefault('primary', si)
    
    @property
    def standby(self):
        try:
            return self['standby']
        except KeyError:
            # fallback to in-memory SQLite;
            # also making this property type-inferrable.
            # slow to import, so import when needed
            from joker.broker.interfaces.sql import SQLInterface
            si = SQLInterface.from_default()
            return self.interfaces.setdefault('standby', si)
        
    @property
    def cache(self):
        try:
            return self['cache']
        except KeyError:
            # fallback to set-n-forget cache;
            # also making this property type-inferrable.
            # slow to import, so import when needed
            from joker.broker.interfaces.redis import NullRedisInterface
            si = NullRedisInterface()
            return self.interfaces.setdefault('cache', si)

