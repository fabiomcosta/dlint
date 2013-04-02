# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import codecs
from collections import defaultdict

from django.conf import settings
from django.template.base import TemplateSyntaxError, TOKEN_BLOCK
from django.template.debug import DebugLexer
from django.template.defaulttags import load as load_tag
from django.utils.functional import cached_property

from dlint.parser import Parser


class Template(object):

    def __init__(self, source):
        self.source = source
        self.source_file = codecs.open(source, 'r', settings.FILE_CHARSET)
        self._setup_load_properties()

    def __repr__(self):
        return '<{module}.{name} source={source}>'.format(
            module=self.__module__,
            name=self.__class__.__name__,
            source=self.source
        )

    @cached_property
    def tokens(self):
        '''
        returns a list with all the tokens in this template.
        '''
        source_content = self.source_file.read()
        lexer = DebugLexer(source_content, None)
        return lexer.tokenize()

    @cached_property
    def load_tokens(self):
        '''
        returns a list with all the load templatetag tokens in this template.
        '''
        return [t for t in self.tokens
            if t.token_type == TOKEN_BLOCK and t.contents.split()[0] == 'load']

    @cached_property
    def parser(self):
        '''
        returns an instance of a parser for this template.
        '''
        return Parser(self.tokens)

    def _setup_load_properties(self):
        # loaded_libs will be a dict like this:
        # {
        #   'library_name': {
        #     'filters': set(),
        #     'tags': set(),
        #   },
        #   ...
        # }
        self.loaded_libs = defaultdict(lambda: defaultdict(set))
        self.loaded_filters = set()
        self.loaded_tags = set()

        for load_token in self.load_tokens:
            try:
                load_tag(self.parser, load_token)
            except TemplateSyntaxError as e:
                raise TemplateSyntaxError('Error while loading modules from {}:\n{}'.format(self, e))

            last_library_loaded = self.parser.last_library_loaded

            # since there is no secure way to get the
            # templatetag module from the tag itself,
            # we have to do this to map
            # the tag to their module

            # takes care of both
            # {% load a b c from d.e %}
            # {% load a.d %}
            load_token_contents = load_token.contents.split()
            library_name = load_token_contents[-1]

            library_filters = last_library_loaded.filters.keys()
            library_tags = last_library_loaded.tags.keys()

            self.loaded_libs[library_name]['filters'].update(library_filters)
            self.loaded_libs[library_name]['tags'].update(library_tags)

            self.loaded_filters.update(library_filters)
            self.loaded_tags.update(library_tags)
