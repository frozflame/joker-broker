#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.cast.syntax import fmt_function_path


class CheckZone(object):
    def __init__(self, checker):
        self._checker = checker
        self._entries = []

    def register(self, *funcs):
        func = None
        for func in funcs:
            entry = func, tuple(), dict()
            self._entries.append(entry)
        return func

    def register_with_params(self, *args, **kwargs):
        def _decorator(*funcs):
            func = None
            for func in funcs:
                entry = func, args, kwargs
                self._entries.append(entry)
            return func
        return _decorator

    def conduct_checks(self, clear=True):
        for func, args, kwargs in self._entries:
            retval = func(*args, **kwargs)
            if self._checker(retval):
                continue
            p = fmt_function_path(func)
            m = 'introspect failed at {}'.format(p)
            raise RuntimeError(m)
        if clear:
            self._entries = []


default_zone = CheckZone(bool)


def register(*funcs):
    return default_zone.register(*funcs)


def register_with_params(*args, **kwargs):
    return default_zone.register_with_params(*args, **kwargs)


def conduct_checks(clear=True):
    return default_zone.conduct_checks(clear=clear)


