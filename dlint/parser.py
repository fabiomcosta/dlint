# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.template.debug import DebugParser


class Parser(DebugParser):

    last_library_loaded = None

    def add_library(self, library):
        super(self.__class__, self).add_library(library)
        self.last_library_loaded = library
