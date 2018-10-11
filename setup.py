#!/usr/bin/env python
from __future__ import absolute_import, unicode_literals

from distutils.core import setup

setup(
    name='GenbankParser',
    version='0.1-alpha',
    description='Unofficial parser for ncbi GenBank data.',
    author='Jonas I. Liechti',
    packages=['gbparse', 'gbparse.content_parser'],
    install_requires=['configparser', 'requests'],
    data_files=[
        ('config', ['gbparse/config.cfg']),
        ]
    )
