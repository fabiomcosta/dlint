#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from setuptools import setup, find_packages
from .dlint import __version__


setup(
    name='dlint',
    version=__version__,
    description='Checks for bad practices and wasted resources on django-specific code',
    keywords='django lint dlint statical analysis',
    author='fabiomcosta',
    author_email='fabiomcosta@gmail.com',
    url='https://github.com/fabiomcosta/dlint',
    packages=find_packages(),
)
