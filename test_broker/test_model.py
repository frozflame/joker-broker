#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.broker.model import AbstractModel
from joker.broker import get_resource_broker


class User(AbstractModel):
    table = 'public.users'

    @classmethod
    def get_resource_broker(cls):
        return get_resource_broker()


def test_model():
    pass
