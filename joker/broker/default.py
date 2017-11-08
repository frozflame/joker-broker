#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import os
from collections import OrderedDict

import yaml
from joker.cast.locational import under_joker_dir

default_conf_path = under_joker_dir('broker.yml')


def represent_odict(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.add_representer(OrderedDict, represent_odict)


def impose_order(dic, order):
    items = []
    for k in order:
        items.append((k, dic.get(k)))
    remained = set(dic) - set(order)
    for k in remained:
        items.append((k, dic[k]))
    return OrderedDict(items)


def get_default_conf():
    url = 'sqlite:///' + under_joker_dir('lite.db')
    default_conf = {
        'cache': {
            'type': 'fakeredis',
            'url': 'redis://127.0.0.1:6379/0',
        },
        'primary': {
            'echo': 0,
            'type': 'sql',
            'url': url,
        },
        'standby': {
            'type': 'sql',
            'echo': 0,
            'url': url,
        },
        'lite': {
            'type': 'sql',
            'echo': 0,
            'url': url,
        },
        'secret': {
            'type': 'secret',
            'extensions': [],
        },
    }
    sections = ['cache', 'lite', 'primary', 'standby', 'secret']
    return impose_order(default_conf, sections)


def dump_as_yamlfile(path, data):
    if os.path.exists(path):
        raise FileExistsError(path)
    s = yaml.dump(data, default_flow_style=False)
    with open(path, 'w') as fout:
        fout.write(s)


def dump_default_conf(path=default_conf_path):
    dump_as_yamlfile(path, get_default_conf())


def setup_joker_dir():
    from joker.cast.locational import make_joker_dir
    make_joker_dir()
    dump_default_conf()


if __name__ == '__main__':
    setup_joker_dir()

