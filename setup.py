#!/usr/bin/env python3
# coding: utf-8

import os
import re

from setuptools import setup, find_packages


# import joker; exit(1)
# DO NOT import your package from your setup.py


def readfile(filename):
    with open(filename) as f:
        return f.read()


# change this
package_name = 'broker'


def version_find():
    root = os.path.dirname(__file__)
    path = os.path.join(root, 'joker/{}/__init__.py'.format(package_name))
    regex = re.compile(
        r'''^__version__\s*=\s*('|"|'{3}|"{3})([.\w]+)\1\s*(#|$)''')
    with open(path) as fin:
        for line in fin:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            mat = regex.match(line)
            if mat:
                return mat.groups()[1]
    raise ValueError('__version__ definition not found')


config = {
    'name': "joker-{}".format(package_name),
    'version': version_find(),
    'description': 'access resources conveniently',
    'keywords': 'resource database access joker',
    'url': "https://github.com/frozflame/joker-{}".format(package_name),
    'author': 'frozflame',
    'author_email': 'frozflame@outlook.com',
    'license': "GNU General Public License (GPL)",
    'packages': find_packages(exclude=['test_*']),
    'namespace_packages': ["joker"],
    'zip_safe': False,
    'install_requires': readfile("requirements.txt"),
    'classifiers': [
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # ensure copy static file to runtime directory
    'include_package_data': True,
}

setup(**config)
