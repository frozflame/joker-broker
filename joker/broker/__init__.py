#!/usr/bin/env python3
# coding: utf-8


__version__ = '0.0.13'


def setup_joker_dir():
    from joker.cast.locational import make_joker_dir
    from joker.broker.userdefault import dump_default_conf
    make_joker_dir()
    dump_default_conf()


def get_resource_broker(path=None):
    from joker.broker.access import ResourceBroker
    from joker.broker.userdefault import default_conf_path
    return ResourceBroker.create(path or default_conf_path)


if __name__ == '__main__':
    setup_joker_dir()
