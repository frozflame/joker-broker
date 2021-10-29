#!/usr/bin/env python3
# coding: utf-8

import importlib

import volkanic
from volkanic.introspect import find_all_plain_modules


class GlobalInterface(volkanic.GlobalInterface):
    package_name = 'joker.broker'


gi = GlobalInterface()
dotpath_prefixes = [
    'joker.broker.',
    'tests.',
]


def _check_prefix(path):
    for prefix in dotpath_prefixes:
        if path.startswith(prefix):
            return True
    return False


def test_module_imports():
    pdir = gi.under_project_dir()
    for dotpath in find_all_plain_modules(pdir):
        if _check_prefix(dotpath):
            print('importing', dotpath)
            importlib.import_module(dotpath)


if __name__ == '__main__':
    test_module_imports()
