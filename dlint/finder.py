# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import codecs
from os import walk
from os.path import join, sep

from django.conf import settings
from django.template import loader
from django.template.base import TemplateDoesNotExist, TOKEN_BLOCK
from django.template.debug import DebugLexer
from django.template.loaders import (
    app_directories,
    filesystem,
    #eggs,
)


class TemplateFinder(object):

    class LoaderNotSupportedException(Exception):
        pass

    @property
    def template_source_loaders(self):
        if not hasattr(self, '_template_source_loaders') or\
                loader.template_source_loaders is None:

            # initializes the template_loader.template_source_loaders property
            # https://github.com/django/django/blob/master/django/template/loader.py#L113
            try:
                loader.find_template('')
            except TemplateDoesNotExist:
                pass

            self._template_source_loaders = loader.template_source_loaders

        return self._template_source_loaders

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
                ignored_app_paths = [join(sep, app.replace('.', sep), sep) for app in ignored_apps]

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

    def get_template_source_paths(self):
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

    def get_template_tokens(self, source):
        '''
        returns a list of all the tokens in source.
        '''
        source_file = codecs.open(source, 'r', settings.FILE_CHARSET)
        source_content = source_file.read()
        lexer = DebugLexer(source_content, None)
        return lexer.tokenize()

    def get_load_template_tokens(self, source):
        '''
        returns a list of all the tokens from the load templatetag.
        '''
        tokens = self.get_template_tokens(source)
        return [t for t in tokens
            if t.token_type == TOKEN_BLOCK and t.contents.split()[0] == 'load']
