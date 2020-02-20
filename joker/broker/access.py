#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import os
import random
import weakref
from collections import defaultdict


def _factory():
    return defaultdict(_factory)


def compute_hash(path, algor='md5', chunksize=1024):
    """compute hash given a file pathname"""
    # similar to: joker.stream.utils.checksum
    import hashlib
    hashfunc = hashlib.new(algor)
    chunksize *= 1024
    with open(path, 'rb') as fin:
        chunk = fin.read(chunksize)
        while chunk:
            hashfunc.update(chunk)
            chunk = fin.read(chunksize)
    return hashfunc.hexdigest()


class Conf(defaultdict):
    cached_instances = weakref.WeakValueDictionary()

    def __init__(self, *args, **kwargs):
        super(Conf, self).__init__(_factory, *args, **kwargs)

    @classmethod
    def load(cls, path):
        # if loaded already, return it
        path = os.path.abspath(path)
        if path in cls.cached_instances:
            return cls.cached_instances[path]

        sha1 = compute_hash(path, 'sha1')
        if sha1 in cls.cached_instances:
            return cls.cached_instances[sha1]

        # parse from conf file
        from joker.broker.interfaces.static import deserialize_conf
        conf = cls(deserialize_conf(path))

        # Note: not cls.loaded_confs.
        # All sub-classes use the same dict
        Conf.cached_instances[path] = conf
        Conf.cached_instances[sha1] = conf
        return conf


class ResourceNotFoundError(Exception):
    pass


def _setup_general_interface(conf_section):
    from joker.broker.interfaces.static import GeneralInterface
    if conf_section is None:
        return GeneralInterface.from_default()
    return GeneralInterface.from_conf(conf_section)


def _setup_secret_interface(conf_section):
    from joker.broker.interfaces.static import SecretInterface
    if conf_section is None:
        return SecretInterface.from_default()
    return SecretInterface.from_conf(conf_section)


def _setup_sql_interface(conf_section):
    from joker.broker.interfaces.sequel import SQLInterface
    if conf_section is None:
        # fallback to in-memory SQLite;
        return SQLInterface.from_default()
    return SQLInterface.from_conf(conf_section)


def _setup_redis_interface(conf_section):
    from joker.broker.interfaces import redis
    if conf_section is None:
        # fallback to set-n-forget cache, i.e. nullreids
        return redis.NullRedisInterface()
    return redis.RedisInterface.from_conf(conf_section)


def _setup_fakeredis_interface(conf_section):
    from joker.broker.interfaces import redis
    if conf_section is None:
        # fallback to set-n-forget cache, i.e. nullreids
        return redis.NullRedisInterface()
    return redis.FakeRedisInterface.from_conf(conf_section)


def _setup_nullredis_interface(_):
    from joker.broker.interfaces.redis import NullRedisInterface
    return NullRedisInterface()


_interface_types = {
    'fakeredis': _setup_fakeredis_interface,
    'nullredis': _setup_nullredis_interface,
    'redis': _setup_redis_interface,
    'secret': _setup_secret_interface,
    'sql': _setup_sql_interface,
}


class ResourceBroker(object):
    cached_instances = weakref.WeakValueDictionary()

    def __init__(self, conf):
        """
        :param conf: (joker.broker.Conf)
        """
        # interfaces are slow to import, so import when needed
        self.conf = conf
        self.interfaces = {}
        self.session_klass = None
        self.standby_interfaces = []
        # why I did this?
        # section_names = list(conf.keys())
        # section_names.sort()

        for name, section in conf.items():
            typ = section.get('type')
            _setup = _setup_general_interface
            _setup = _interface_types.get(typ, _setup)
            interf = _setup(section)
            self.interfaces[name] = interf
            if name.lower().startswith('standby'):
                self.standby_interfaces.append(interf)

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

    def _get_interface(self, name, typ):
        try:
            return self.interfaces[name]
        except KeyError:
            interface = _interface_types.get(typ, _setup_general_interface)(None)
            self.interfaces[name] = interface
            return interface

    def get_session(self):
        """
        Get a RoutingSession instance, which is modified from
        http://docs.sqlalchemy.org/en/latest/orm/persistence_techniques.html
        #custom-vertical-partitioning
        """
        if self.session_klass is None:
            from joker.broker.interfaces.sequel import get_session_klass
            self.session_klass = \
                get_session_klass(self.primary, self.standby_interfaces)
        return self.session_klass()

    # some preset interfaces:
    # general, secret, primary, standby, lite, cache, kvstore
    @property
    def general(self):
        """:rtype: joker.broker.interfaces.static.GeneralInterface"""
        return self._get_interface('general', 'general')

    @property
    def secret(self):
        """:rtype: joker.broker.interfaces.static.SecretInterface"""
        return self._get_interface('secret', 'secret')

    @property
    def primary(self):
        """
        Intend to be a primary (master) RDB instance
        :rtype: joker.broker.interfaces.sequel.SQLInterface
        """
        return self._get_interface('primary', 'sql')

    @property
    def standby(self):
        """
        Intend to be a standby (slave) RDB instance
        :rtype: joker.broker.interfaces.sequel.SQLInterface
        """
        if self.standby_interfaces:
            return random.choice(self.standby_interfaces)
        return self.primary

    @property
    def cache(self):
        """
        Intend to be a volatile redis instance
        :rtype: joker.broker.interfaces.redis.RedisInterface
        """
        return self._get_interface('cache', 'redis')

    @property
    def store(self):
        """
        Intend to be a non-volatile (persisting) redis instance
        :rtype: joker.broker.interfaces.redis.RedisInterface
        """
        return self._get_interface('store', 'redis')
