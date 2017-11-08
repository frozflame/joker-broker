#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import os
import random
import weakref
from collections import defaultdict


def _import_requirements():
    """
    A dummy function to list all imports
    These imports are slow!
    """
    from joker.broker.security import HashedPath
    from joker.broker.interfaces.rediz import RedisInterface
    from joker.broker.interfaces.rediz import FakeRedisInterface
    from joker.broker.interfaces.rediz import NullRedisInterface
    from joker.broker.interfaces.sequel import SQLInterface
    from joker.broker.interfaces.static import deserialize_conf
    from joker.broker.interfaces.static import GeneralInterface
    from joker.broker.interfaces.static import SecretInterface
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
        self.standby_interfaces = []
        section_names = list(conf.keys())
        section_names.sort()

        for name in section_names:
            section = conf[name]
            typ = section.get('type')

            if not typ or typ == 'general':
                from joker.broker.interfaces.static import GeneralInterface
                self.interfaces[name] = GeneralInterface.from_conf(section)

            elif typ == 'secret':
                from joker.broker.interfaces.static import SecretInterface
                self.interfaces[name] = SecretInterface.from_conf(section)

            elif typ == 'sql':
                from joker.broker.interfaces.sequel import SQLInterface
                self.interfaces[name] = SQLInterface.from_conf(section)
                if name.lower().startswith('standby'):
                    self.standby_interfaces.append(self.interfaces[name])

            elif typ == 'redis':
                from joker.broker.interfaces.rediz import RedisInterface
                self.interfaces[name] = RedisInterface.from_conf(section)

            elif typ == 'fakeredis':
                from joker.broker.interfaces.rediz import FakeRedisInterface
                self.interfaces[name] = FakeRedisInterface.from_conf(section)

            elif typ == 'nullredis':
                from joker.broker.interfaces.rediz import NullRedisInterface
                self.interfaces[name] = NullRedisInterface.from_conf(section)

        if ('primary' in self.interfaces) and self.standby_interfaces:
                from sqlalchemy.orm import scoped_session, sessionmaker
                from joker.broker.interfaces.sequel import RoutingSession
                kwargs = {
                    'primary_engine': self.primary.engine,
                    'standby_engines': [x.engine for x in self.standby_interfaces],
                }
                factory = sessionmaker(class_=RoutingSession, **kwargs)
                self.session_klass = scoped_session(factory)
        else:
            self.session_klass = self.primary.session_klass

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
        from joker.broker.interfaces.sequel import SQLInterface
        for rb in cls.cached_instances.values():
            for res in rb.resources.values():
                if isinstance(res, SQLInterface):
                    res.just_after_fork()

    def __getitem__(self, interface_name):
        try:
            return self.interfaces[interface_name]
        except LookupError:
            msg = 'section "{}" not in your config file or mis-configured'
            msg = msg.format(interface_name)
            raise ResourceNotFoundError(msg)

    # The following code seems redundant,
    # but I cannot find a better way to ensure both IDE's grammar inferrence
    # and lazy import of Interface classes work well.

    def get_general_interface(self, name):
        try:
            return self[name]
        except KeyError:
            from joker.broker.interfaces.static import GeneralInterface
            gi = GeneralInterface.from_default()
            return self.interfaces.setdefault(name, gi)

    def get_secret_interface(self, name):
        try:
            return self[name]
        except KeyError:
            from joker.broker.interfaces.static import SecretInterface
            si = SecretInterface.from_default()
            return self.interfaces.setdefault(name, si)

    def get_sql_interface(self, name):
        try:
            return self[name]
        except KeyError:
            # fallback to in-memory SQLite;
            # also making this property type-inferrable.
            # slow to import, so import when needed
            from joker.broker.interfaces.sequel import SQLInterface
            si = SQLInterface.from_default()
            return self.interfaces.setdefault(name, si)

    def get_redis_interface(self, name):
        try:
            return self[name]
        except KeyError:
            # fallback to set-n-forget cache;
            # also making this property type-inferrable.
            # slow to import, so import when needed
            from joker.broker.interfaces.rediz import NullRedisInterface
            si = NullRedisInterface()
            return self.interfaces.setdefault(name, si)

    def get_session(self):
        """
        Get a RoutingSession instance, which is modified from
        http://docs.sqlalchemy.org/en/latest/orm/persistence_techniques.html
        #custom-vertical-partitioning
        """
        return self.session_klass()

    # some preset interfaces: general, secret, cache, primary, standby, lite
    @property
    def general(self):
        return self.get_general_interface('general')

    @property
    def secret(self):
        return self.get_secret_interface('secret')

    @property
    def primary(self):
        return self.get_sql_interface('primary')

    @property
    def standby(self):
        if self.standby_interfaces:
            return random.choice(self.standby_interfaces)
        return self.primary

    @property
    def lite(self):
        return self.get_sql_interface('lite')

    @property
    def cache(self):
        return self.get_redis_interface('cache')
