#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

import os
import warnings

from sqlalchemy import Table, MetaData, engine_from_config
from sqlalchemy.exc import SAWarning


class SQLInterface(object):
    def __init__(self, sqlalchemy_options):
        self.pid = os.getpid()
        self.tables = dict()
        self.engine = engine_from_config(sqlalchemy_options, prefix='')
        if self.engine.url.get_backend_name() == 'postgresql':
            self.metadata = MetaData(bind=self.engine, schema='public')
        else:
            self.metadata = MetaData(bind=self.engine)

    def just_after_fork(self):
        """
        http://docs.sqlalchemy.org/en/latest/core/pooling.html\
        #using-connection-pools-with-multiprocessing
        """
        if self.pid != os.getpid():
            self.engine.dispose()
            self.pid = os.getpid()

    @classmethod
    def from_default(cls):
        sqlalchemy_options = {
            'url': 'sqlite://',
            'client_encoding': 'utf-8',
            'echo': False,
        }
        return cls(sqlalchemy_options)

    @classmethod
    def from_conf(cls, conf_section):
        """
        :param conf_section: (dict or None)
        :return:
        """
        sqlalchemy_options = {
            'url': conf_section.get('url'),
            'client_encoding': conf_section.get('client_encoding', 'utf-8'),
            'echo': conf_section.get('echo', False),
        }
        return cls(sqlalchemy_options)

    @staticmethod
    def dataset_connect():
        pass

    # def get_metadata(self, schema):
    #     if schema not in self.meta:
    #         metadata = MetaData(bind=self.engine, schema=schema)
    #         self.meta[schema] = metadata
    #     return self.meta[schema]

    def get_table(self, table_name, schema=None):
        # TODO: check if sqlalchemy has done relation cache already
        if (table_name, schema) not in self.tables:
            # metadata = self.get_metadata(schema)
            metadata = self.metadata
            with warnings.catch_warnings():
                mreg = '.*Predicate.*partial.*index.*reflection.*'
                warnings.filterwarnings('ignore', category=SAWarning, message=mreg)
                table = Table(table_name, metadata, schema=schema, autoload=True)
            self.tables[(table_name, schema)] = table
        return self.tables[(table_name, schema)]
