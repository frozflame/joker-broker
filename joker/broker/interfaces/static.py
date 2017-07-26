#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import json
import os
from collections import OrderedDict

import yaml

from joker.broker.security import HashedPath


def deserialize_conf(path):
    ext = os.path.splitext(path)[1]
    if ext.lower() in {'.yml', '.yaml'}:
        return yaml.load(open(path))
    elif ext.lower() == '.json':
        return json.load(open(path))
    raise ValueError('unrecognizable extension: {}'.format(ext))


class IntegrityError(ValueError):
    pass


class StaticInterface(object):
    """
    A strict and immutable dict-like object
    """
    def __init__(self, data=None):
        self._data = dict(data or {})

    def __getattr__(self, name):
        return self.get(name)

    def __getitem__(self, name):
        return self.get(name)

    def get(self, name, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def _standardize(cls, conf_section):
        raise NotImplementedError

    @classmethod
    def _load_extension_from_file(cls, path):
        hp = HashedPath.parse(path)
        if not hp.verify():
            raise IntegrityError(path)
        return cls._standardize(deserialize_conf(hp.path))

    @classmethod
    def from_conf(cls, conf_section):
        extensions = conf_section.pop('extensions', [])
        data = cls._standardize(conf_section)
        for ext in extensions:
            data.update(cls._load_extension_from_file(ext))
        return cls(data)

    @classmethod
    def from_default(cls):
        return cls.from_conf(dict())


class GeneralInterface(StaticInterface):
    @classmethod
    def _standardize(cls, conf_section):
        return conf_section

    def get(self, name, *args, **kwargs):
        return self._data.get(name, *args, **kwargs)


class SecretInterface(StaticInterface):
    def get(self, name, version=None, *args, **kwargs):
        versions_dict = self._data.get(name)
        if not versions_dict:
            return
        if version:
            return versions_dict.get(version)
        return next(iter(versions_dict.values()))

    def get_binary(self, name):
        val = self.get(name)
        if val:
            return val.encode('utf-8')

    get_secret_key = get

    def get_secret_keys(self, name, binary=False):
        versions_dict = self._data.get(name)
        if not versions_dict:
            return
        if not binary:
            return list(versions_dict.values())
        return [x.encode('utf-8') for x in versions_dict.values()]

    @staticmethod
    def _sort_versions(versions_dict):
        versions = list(versions_dict.items())
        versions.sort(reverse=True)
        return OrderedDict(versions)

    @classmethod
    def _standardize(cls, conf_section):
        data = dict()
        for name, secret_keys in conf_section.items():
            if isinstance(secret_keys, str):
                secret_keys = dict(active=secret_keys)
            if isinstance(secret_keys, list):
                # the first (topmost) as active
                secret_keys = {-i: s for i, s in enumerate(secret_keys)}
            data[name] = cls._sort_versions(secret_keys)
        return data

