#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import base64
import hashlib
import os
import re

import six
from joker.cast import want_bytes, want_unicode


def guess_hash_algorithm(digest):
    algo_map = {
        ('bin', 16): 'md5',
        ('bin', 20): 'sha1',
        ('bin', 28): 'sha224',
        ('bin', 32): 'sha256',
        ('bin', 48): 'sha384',
        ('bin', 64): 'sha512',
        ('hex', 32): 'md5',
        ('hex', 40): 'sha1',
        ('hex', 56): 'sha224',
        ('hex', 64): 'sha256',
        ('hex', 96): 'sha384',
        ('hex', 128): 'sha512',
    }
    if isinstance(digest, six.binary_type):
        try:
            digest = digest.decode('utf-8')
        except Exception:
            return algo_map.get(('bin', len(digest)))
    if not re.match(r'[0-9A-Fa-f]+', digest):
        return
    return algo_map.get(('hex', len(digest)))


class HashedPath(object):
    """
    /data/web/config.ini;;f6da8154d73f954cdfebd04d6c76cff8
    for integrity-check purpose only
    """
    delimiter = ';;'

    def __init__(self, digest, algo, path):
        self.digest = digest
        self.algo = algo
        self.path = path

    @staticmethod
    def calc_hash(path, algo='md5'):
        blksize = 2 ** 20
        h = hashlib.new(algo)
        with open(path, 'rb') as fin:
            buf = fin.read(blksize)
            while buf:
                h.update(buf)
                buf = fin.read(blksize)
        return h.hexdigest()

    @classmethod
    def generate(cls, path, algo='md5'):
        try:
            digest = cls.calc_hash(path, algo)
        except IOError:
            digest = hashlib.new(algo, b'\0')
        return cls(digest, algo, path)

    @classmethod
    def parse(cls, h_path):
        if cls.delimiter not in h_path:
            return cls('', 'md5', h_path)
        path, digest = h_path.split(cls.delimiter, 2)
        algo = guess_hash_algorithm(digest)
        return cls(digest, algo, path)

    def __str__(self):
        return '{}{}{}'.format(self.path, self.delimiter, self.digest)

    def verify(self):
        if not self.digest:
            return True
        hx1 = self.generate(self.path, self.algo or 'md5')
        return hx1.digest == self.digest


class HashedPassword(object):
    def __init__(self, digest, algo, salt):
        self.digest = digest
        self.algo = algo
        self.salt = salt

    @staticmethod
    def gen_random_string(length):
        n = 1 + int(length * 0.625)
        return base64.b32encode(os.urandom(n)).decode()[:length]

    @classmethod
    def parse(cls, s):
        digest, algo, salt = s.split(':')
        return cls(digest, algo, salt)

    @classmethod
    def generate(cls, password, algo='sha512', salt=None):
        if salt is None:
            salt = cls.gen_random_string(16)
        p = want_bytes(password)
        s = want_bytes(salt)
        h = hashlib.new(algo, p + s)
        return cls(h.hexdigest(), algo, want_unicode(salt))

    def __str__(self):
        return '{}:{}:{}'.format(self.digest, self.algo, self.salt)

    def verify(self, password):
        hp1 = self.generate(password, self.algo, self.salt)
        return self.digest == hp1.digest


