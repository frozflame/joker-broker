#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function
import os
import yaml
from collections import OrderedDict


def impose_order(dic, order):
    items = []
    for k in order:
        items.append((k, dic.get(k)))
    remained = set(dic) - set(order)
    for k in remained:
        items.append((k, dic[k]))
    return OrderedDict(items)


userdir_path = os.path.expanduser('~/.joker')

default_conf = {
    'cache': {
        'type': 'redis',
        'url': 'redis://127.0.0.1:6379/0',
    },
    'primary': {
        'echo': 0,
        'type': 'sql',
        'url': 'postgresql://127.0.0.1:5432/postgres',
    },
    'secret': {
        'type': 'secret',
        'extensions': ['~/.joker/credents/secret.json'],
    },
    'standby': {
        'type': 'sql',
        'echo': 0,
        'url': 'postgresql://127.0.0.1:5432/postgres'
    }
}

sections = [
    'cache', 'primary', 'standby', 'secret',
]


def represent_odict(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, represent_odict)


def make_userdir(path=userdir_path):
    # silently return if path exists as a dir
    if not os.path.isdir(path):
        os.mkdir(path, mode=int('700', 8))


def dump_as_yamlfile(path, data, order):
    if os.path.exists(path):
        raise FileExistsError(path)
    s = yaml.dump(impose_order(data, order))
    with open(path, 'w') as fout:
        fout.write(s)


def dump_default_conf(path=None):
    if path is None:
        make_userdir()
        path = os.path.join(userdir_path, 'broker.yml')
    dump_as_yamlfile(path, default_conf, sections)

