# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

import codecs
from collections import defaultdict
from os import walk
from os.path import join, sep

from django.conf import settings
from django.template import loader
from django.template.base import TemplateDoesNotExist, TemplateSyntaxError, TOKEN_BLOCK
from django.template.debug import DebugLexer
from django.template.defaulttags import load as load_tag
from django.template.loaders import (
    app_directories,
    filesystem,
    #eggs,
)
from django.utils.functional import cached_property

from dlint.parser import Parser


class TemplateFinder(object):

    class LoaderNotSupportedException(Exception):
        pass

    def items(self):
        for source in self.template_source_paths:
            yield Template(source)

    @cached_property
    def template_source_paths(self):
        '''
        returns a list with all the template file paths inside
        the folders returned by `self.get_template_folders()`
        '''
        folders = self.get_template_folders()

        sources = []

        for folder in folders:
            for root, dirs, files in walk(folder):
                sources += [join(root, name) for name in files]

        return sources

    @cached_property
    def template_source_loaders(self):
        # initializes the template_loader.template_source_loaders property
        # https://github.com/django/django/blob/master/django/template/loader.py#L113
        try:
            loader.find_template('')
        except TemplateDoesNotExist:
            pass

        return loader.template_source_loaders

    def get_template_folders(self):
        '''
        returns a list of all the template folders that
        are used by django to load template files.

        This list is based on the template loaders
        defined by the `TEMPLATE_LOADERS` setting.
        '''
        # this code sux badly, but I couldnt find a better way
        # to get all the files available to the builtin
        # template loaders
        folders = []

        for loader in self.template_source_loaders:

            if isinstance(loader, app_directories.Loader):

                ignored_apps = settings.DLINT_IGNORED_APPS
                ignored_app_paths = [(sep + app.replace('.', sep) + sep) for app in ignored_apps]

                all_app_dirs = app_directories.app_template_dirs
                app_dirs = []

                for app_dir in all_app_dirs:
                    if len([p for p in ignored_app_paths if p in app_dir]) > 0:
                        continue
                    app_dirs.append(app_dir)

                folders += app_dirs

            elif isinstance(loader, filesystem.Loader):
                folders += settings.TEMPLATE_DIRS

            else:
                raise self.LoaderNotSupportedException('The {!r} django template loader is not supported.'.format(loader))

        return folders


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
