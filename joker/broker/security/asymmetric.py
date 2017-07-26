#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.cast import want_bytes
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


class RSAKeyPair(object):
    """
    Experimental! Take your own risk.
    """

    _crypt_padding = padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA1()),
        algorithm=hashes.SHA1(), label=None)

    def __init__(self, rsa_key=None):
        if rsa_key is None:
            rsa_key = self.gen_private_key()
        try:
            self.public_key = rsa_key.public_key()
        except AttributeError:
            self.public_key = rsa_key
            self.private_key = None
        else:
            self.private_key = rsa_key

    @classmethod
    def from_openssh_public_key(cls, content):
        rsa_key = cls.loads_public_key(want_bytes(content))
        return cls(rsa_key)

    @classmethod
    def from_openssh_private_key(cls, content, password):
        rsa_key = cls.loads_private_key(want_bytes(content), password)
        return cls(rsa_key)

    def encrypt(self, message):
        message = want_bytes(message)
        return self.public_key.encrypt(message, self._crypt_padding)

    def decrypt(self, ciphertext):
        if self.private_key is None:
            raise ValueError('cannot decrypt without a private key')
        return self.private_key.decrypt(ciphertext, self._crypt_padding)

    @staticmethod
    def gen_private_key():
        """
        :return: an _RSAPrivateKey instance
        """
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.asymmetric import rsa
        return rsa.generate_private_key(
            backend=default_backend(),
            public_exponent=65537,
            key_size=2048
        )

    @staticmethod
    def loads_private_key(bs, password=None):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        return serialization.load_pem_private_key(
            bs, password=password, backend=default_backend())

    @staticmethod
    def loads_public_key(bs):
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives import serialization
        return serialization.load_ssh_public_key(bs, default_backend())

    @staticmethod
    def dumps_private_key(rsa_key):
        """
        :param rsa_key: an _RSAPrivateKey instance
        :return: a str instance
        """
        from cryptography.hazmat.primitives import serialization
        return rsa_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ).decode()

    @staticmethod
    def dumps_public_key(rsa_key):
        """
        :param rsa_key: an _RSAPublicKey instance
        :return: a str instance
        """
        return rsa_key.public_key().public_bytes(
            serialization.Encoding.OpenSSH,
            serialization.PublicFormat.OpenSSH
        ).decode()


__all__ = ['RSAKeyPair']
