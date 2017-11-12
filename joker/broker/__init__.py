#!/usr/bin/env python3
# coding: utf-8

from joker.broker.access import ResourceBroker


__version__ = '0.1.6'


def get_resource_broker(path=None):
    from joker.broker.default import default_conf_path
    return ResourceBroker.create(path or default_conf_path)
