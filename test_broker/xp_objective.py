#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.broker import get_resource_broker
from joker.broker.objective import DeclBase
from sqlalchemy import Column, Sequence, String, Integer, func
from sqlalchemy.dialects.postgresql import (
    BIGINT, TEXT, TIMESTAMP,
)
from joker.broker.objective import Toolbox

tms = func.now()
seq = Sequence('_seq_users_id', schema='auth')


class User(DeclBase):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'auth'}
    id = Column(BIGINT, seq, primary_key=True)
    username = Column(String(127))
    password = Column(String(255))
    email = Column(String(127))
    phone = Column(String(15))
    avatar = Column(TEXT)
    gender = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=tms)
    updated_at = Column(TIMESTAMP, server_default=tms, onupdate=tms)


sample_users_data = [
    {
        'username': 'jack',
        'password': 'jackpwd',
        'email': 'jack@imetro.io',
        'phone': '13100001234',
        'gender': 0,
        'avatar': '/img/avatar/default.png',
    },
    {
        'username': 'mandy',
        'password': 'vincentpwd',
        'email': 'vincent@imetro.io',
        'phone': '13200001234',
        'gender': 0,
        'avatar': '/img/avatar/default.png',
    }
]


def insert_sample_users():
    for udic in sample_users_data:
        user = User(**udic)
        session.add(user)
    session.commit()


def table_create():
    meta = DeclBase.metadata
    meta.bind = rb.primary.engine

    meta.bind.execute('CREATE SCHEMA IF NOT EXISTS auth;')
    meta.bind.execute('CREATE SCHEMA IF NOT EXISTS asset;')
    meta.create_all()
    insert_sample_users()


if __name__ == '__main__':
    rb = get_resource_broker()
    session = rb.get_session()
    toolbox = Toolbox(session, rb.cache)
    # table_create()
    # insert_sample_users()

