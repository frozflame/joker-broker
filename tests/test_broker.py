#!/usr/bin/env python3
# coding: utf-8

import os
from joker.broker import ResourceBroker


def get_test_dir():
    return os.path.dirname(__file__)


def test_resource_broker():
    path = os.path.join(get_test_dir(), 'example_conf.json')
    rb = ResourceBroker.create(path)
    ResourceBroker.just_after_fork()
    print(rb)


if __name__ == '__main__':
    test_resource_broker()