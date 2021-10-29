#!/usr/bin/env python3
# coding: utf-8

import logging
import time
from functools import cached_property

import orjson
from bson import ObjectId
from redis import Redis
from redis.client import PubSub

_logger = logging.getLogger(__name__)
_debug = _logger.debug


class TaskNotificationInterface(object):
    """Task queue, notification and synchronization with Redis"""

    def __init__(self, redis: Redis, prefix: str):
        self.redis = redis
        # f-string was introduced since 3.6
        self.prefix = f'{prefix}.{self.__class__.__name__}'
        self._queue_key = f'{self.prefix}.taskq'

    @cached_property
    def _dbnum(self) -> int:
        return self.redis.connection_pool.connection_kwargs.get('db', 0)

    def _fmt_result_key(self, task_id: str):
        return f'{self.prefix}.taskr.{task_id}'

    @cached_property
    def _queue_pubsub(self) -> PubSub:
        channel = f'__keyspace@{self._dbnum}__:{self._queue_key}'
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    def get_queue_pubsub(self):
        return self._queue_pubsub

    def get_result_pubsub(self, task_id: str = None):
        result_key = self._fmt_result_key(task_id)
        channel = f'__keyspace@{self._dbnum}__:{result_key}'
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    @staticmethod
    def _check_task_id(task_doc: dict):
        try:
            return task_doc['_id']
        except KeyError:
            task_id = str(ObjectId())
            return task_doc.setdefault('_id', task_id)

    def add(self, task_doc: dict):
        self._check_task_id(task_doc)
        task_bin = orjson.dumps(task_doc, default=str)
        self.redis.lpush(self._queue_key, task_bin)
        return task_doc['_id']

    def pull(self):
        task_bin = self.redis.rpop(self._queue_key)
        if not task_bin:
            return
        return orjson.loads(task_bin)

    def finish(self, task_id: str, result: dict, ex=3600):
        key = self._fmt_result_key(task_id)
        result_bin = orjson.dumps(result)
        self.redis.set(key, result_bin, ex=ex)

    def query(self, task_id: str):
        key = self._fmt_result_key(task_id)
        if result_bin := self.redis.get(key):
            return orjson.loads(result_bin)

    @staticmethod
    def _wait_for_channel_message(pubsub: PubSub, timeout, value: bytes):
        while timeout > 0:
            t = time.time()
            d = pubsub.get_message(timeout=timeout)
            _debug('pubsub.get_message() => %s', d)
            if d and d.get('type') == 'message' and d.get('data') == value:
                break
            timeout -= (time.time() - t)

    def wait_and_pull(self, timeout=60):
        _debug('TaskInterface.wait_and_pull(), %s', timeout)
        # IMPORTANT:
        # self.get_queue_pubsub() before self.pull() is required
        pubsub = self.get_queue_pubsub()
        if task_doc := self.pull():
            return task_doc
        self._wait_for_channel_message(pubsub, timeout, b'lpush')
        return self.pull()

    def wait_and_query(self, task_id: str, timeout=60):
        _debug('TaskInterface.wait_and_query(), %s, %s', task_id, timeout)
        # IMPORTANT:
        # self.get_result_pubsub() before self.query() is required
        pubsub = self.get_result_pubsub(task_id)
        if result := self.query(task_id):
            return result
        self._wait_for_channel_message(pubsub, timeout, b'set')
        return self.query(task_id)
