#!/usr/bin/env python3
# coding: utf-8

import logging
import os
import warnings

from sqlalchemy import Table, MetaData, engine_from_config
from sqlalchemy.exc import SAWarning
from sqlalchemy.orm import scoped_session, sessionmaker

_logger = logging.getLogger(__name__)


class SQLInterface(object):
    def __init__(self, sqlalchemy_options):
        self.pid = os.getpid()
        self.engine = engine_from_config(sqlalchemy_options, prefix='')
        if self.engine.url.get_backend_name() == 'postgresql':
            self.metadata = MetaData(bind=self.engine, schema='public')
        else:
            self.metadata = MetaData(bind=self.engine)
        self.session_klass = scoped_session(sessionmaker(bind=self.engine))

    def just_after_fork(self):
        """
        http://docs.sqlalchemy.org/en/latest/core/pooling.html#using-\
        connection-pools-with-multiprocessing
        """
        if self.pid != os.getpid():
            self.engine.dispose()
            self.pid = os.getpid()

    @classmethod
    def from_default(cls):
        sqlalchemy_options = {
            'url': 'sqlite:///',
            'echo': False,
        }
        return cls(sqlalchemy_options)

    @classmethod
    def from_conf(cls, conf_section):
        """
        :param conf_section: (dict or None)
        :return:
        """
        url = conf_section.get('url')
        sqlalchemy_options = {
            'url': conf_section.get('url'),
            'echo': conf_section.get('echo', False),
        }
        if not url.startswith('sqlite:'):
            sqlalchemy_options['client_encoding'] = \
                conf_section.get('client_encoding', 'utf-8')
        return cls(sqlalchemy_options)

    @staticmethod
    def dataset_connect():
        pass

    @property
    def tables(self):
        return self.metadata.tables

    def get_table(self, table_name, schema=None):
        # SQLAlchemy document:
        # http://docs.sqlalchemy.org/en/latest/core/reflection.html
        # once loaded, new calls to Table # with the same name
        # will not re-issue any reflection queries.
        # So, sqlalchemy has done relation cache already!
        metadata = self.metadata
        with warnings.catch_warnings():
            mreg = '.*Predicate.*partial.*index.*reflection.*'
            warnings.filterwarnings('ignore', category=SAWarning, message=mreg)
            return Table(table_name, metadata, schema=schema, autoload=True)

    def get_session(self):
        return self.session_klass()

    def execute(self, *args, **kwargs):
        return self.engine.execute(*args, **kwargs)
