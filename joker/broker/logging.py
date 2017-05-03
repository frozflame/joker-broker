#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function
import logging


class LoggerBroker(object):
    """
    mostly just do this in each module:
        lbroker = LoggerBroker(__name__)

    and use like:
        lbroker.logger.info('data loaded')
    """

    primary_logger_name = ''

    def __init__(self, name):
        self.name = name

    @classmethod
    def config_logger(cls, name, log_level, path=None):
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.handlers = []
        if path:
            handler = logging.FileHandler(path)
        else:
            handler = logging.StreamHandler()
        handler.setLevel(log_level)

        fmt = '%(asctime)s [%(process)d] [%(levelname)s] %(message)s'
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)

    @property
    def logger(self):
        return logging.getLogger(self.primary_logger_name or self.name)


