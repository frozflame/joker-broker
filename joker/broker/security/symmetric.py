#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.cast import want_bytes, want_unicode


class MultiFernetWrapper(object):
    _multifernets = dict()

    @classmethod
    def get_secret_keys(cls):
        # return a list of bytes objects
        raise NotImplementedError

    @classmethod
    def get_multifernet(cls):
        # import of cryptography is slow, so import when needed
        from cryptography.fernet import Fernet, MultiFernet
        try:
            return cls._multifernets[cls]
        except KeyError:
            pass
        fernets = [Fernet(sk) for sk in cls.get_secret_keys()]
        mf = MultiFernet(fernets)
        return cls._multifernets.setdefault(cls, mf)

    @classmethod
    def encrypt(cls, msg):
        mf = cls.get_multifernet()
        token = mf.encrypt(want_bytes(msg))
        return want_unicode(token)

    @classmethod
    def decrypt(cls, token, ttl=None):
        mf = cls.get_multifernet()
        msg = mf.decrypt(want_bytes(token), ttl=ttl)
        return want_unicode(msg)