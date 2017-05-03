#!/usr/bin/env python3
# coding: utf-8

from __future__ import division, print_function

from joker.broker import check


@check.instanciate_with_foolproof
class Event(check.AttrEchoer):
    prefix = 'event'
    unauthorized = ''  # assign whatever
    undefined_fault = ''


def test_path_formatters():
    vals = [
        check.format_class_path(dict),
        check.format_class_path(Event),
        check.format_class_path(check.CheckZone),
        check.format_function_path(dict.pop),
        check.format_function_path(check.CheckZone.register),
        check.format_function_path(check.register),
        check.format_function_path(lambda: 1),
    ]
    for v in vals:
        print(v)


if __name__ == '__main__':
    test_path_formatters()
