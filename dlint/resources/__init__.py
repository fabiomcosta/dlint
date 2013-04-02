#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from .template.finder import TemplateFinder

__all__ = ('templates',)

templates = TemplateFinder()
