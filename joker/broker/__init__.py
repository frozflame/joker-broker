#!/usr/bin/env python3
# coding: utf-8

__version__ = '0.5.0!'

from joker.broker.access import ResourceBroker
from joker.broker.environ import GlobalInterface


def get_resource_broker(path=None):
    from joker.broker.default import default_conf_path
    return ResourceBroker.create(path or default_conf_path)
