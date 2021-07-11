#!/usr/bin/env python3
# coding: utf-8

import volkanic.environ
from redis import Redis
from volkanic.compat import cached_property


class GlobalInterface(volkanic.GlobalInterface):
    """
    joker.broker.GlobalInterface
        - is intended to be used by other projects
        - has no association with the joker-dir (~/.joker by default)
    joker.environ.GlobalInterface
        - is intended to be used by joker.* projects
        - associates with the joker-dir (~/.joker by default)
    """

    package_name = 'joker.broker'
    default_config = {
        "secret_keys": [
            'rfeee44ad365b6b1ec75c5621a0ad067371102854',
            'c6b93d1c2880daea891c8879c86d167c6678facf',
        ],
    }

    @cached_property
    def redis(self) -> Redis:
        return Redis(**self.conf.get('redis', {}))

    @cached_property
    def signer(self):
        from itsdangerous import Signer
        # secret_keys: should be a list to support key rotation
        return Signer(self.conf['secret_keys'])

    def under_data_dir(self, *paths, mkdirs=False) -> str:
        dirpath = self.conf['data_dir']
        if not mkdirs:
            return abs_path_join(dirpath, *paths)
        return abs_path_join_and_mkdirs(dirpath, *paths)

    def under_resources_dir(self, *paths):
        resources_dir = self.conf.get('resources_dir')
        if not resources_dir:
            resources_dir = self.under_project_dir('resources')
        if not os.path.isdir(resources_dir):
            raise NotADirectoryError(resources_dir)
        return abs_path_join(resources_dir, *paths)

    def get_temp_path(self, ext=''):
        name = os.urandom(17).hex() + ext
        return self.under_data_dir('tmp', name)
