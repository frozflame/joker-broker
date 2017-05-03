#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function
import inspect


def format_class_path(obj):
    if isinstance(obj, type):
        klass = obj
    else:
        klass = type(obj)
    m = getattr(klass, '__module__', None)
    q = getattr(klass, '__qualname__', None)
    n = getattr(klass, '__name__', None)
    name = q or n or ''
    if m:
        return '{}.{}'.format(m, name)
    return name


def format_function_path(func):
    if not inspect.ismethod(func):
        mod = getattr(func, '__module__', None)
        if mod is None:
            return func.__qualname__
        else:
            return '{}.{}'.format(mod, func.__qualname__)
    klass_path = format_class_path(func.__self__)
    return '{}.{}'.format(klass_path, func.__name__)


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
            p = format_function_path(func)
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


def instanciate(cls):
    return cls()


def instanciate_with_foolproof(cls):
    """
    The return class can be called again without error
    """
    if '__call__' not in cls.__dict__:
        cls.__call__ = lambda x: x
    return cls()


class AttrEchoer(object):
    """
    Resembles an enum type
    Reduces typos by using syntax based completion of dev tools
    
    Example:
        
        @instanciate_with_foolproof
        class Event(AttrEchoer):
            _prefix = 'event'
            bad_params = ''  # assign whatever
            unauthorized_access = ''  
            undefined_fault = ''
            ...
       
        # no error: 
        assert Event.unauthoried  == 'event.bad_params'
    """
    _prefix = '_root.'

    def __getattribute__(self, key):
        kls = type(self)
        if key in kls.__dict__ and key != '_prefix':
            if not kls._prefix:
                return key
            return '{}{}'.format(kls._prefix, key)
        return object.__getattribute__(self, key)

