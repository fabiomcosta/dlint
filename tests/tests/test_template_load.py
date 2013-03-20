# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from tempfile import NamedTemporaryFile

from django.template.base import TOKEN_BLOCK, TOKEN_VAR

import sure  # noqa
from mock import patch, Mock
from dlint.finder import TemplateFinder


def test_template_source_loaders_function_caches_correctly():
    template_finder = TemplateFinder()

    template_finder.should_not.have.property('_template_source_loaders')
    template_finder.template_source_loaders  # should create the cache property
    template_finder.should.have.property('_template_source_loaders')
    template_finder.template_source_loaders.should.equals(template_finder._template_source_loaders)


@patch('django.template.loader.template_source_loaders', None)  # forces the loaders to be reloaded
@patch('django.template.loader.settings')
def test_template_source_loaders_loads_loader_object_based_on_TEMPLATE_LOADERS_setting(settings):
    settings.TEMPLATE_LOADERS = ('django.template.loaders.filesystem.Loader',)

    template_finder = TemplateFinder()

    template_finder.template_source_loaders.should.have.length_of(1)
    template_finder.template_source_loaders[0].should.be.a('django.template.loaders.filesystem.Loader')


@patch('django.template.loader.template_source_loaders', None)  # forces the loaders to be reloaded
@patch('django.template.loader.settings')
def test_template_source_loaders_loads_loader_objects_based_on_TEMPLATE_LOADERS_setting(settings):
    settings.TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )

    template_finder = TemplateFinder()

    template_finder.template_source_loaders.should.have.length_of(2)
    template_finder.template_source_loaders[0]\
        .should.be.a('django.template.loaders.filesystem.Loader')
    template_finder.template_source_loaders[1]\
        .should.be.a('django.template.loaders.app_directories.Loader')


@patch('django.template.loader.template_source_loaders', None)  # forces the loaders to be reloaded
@patch('django.template.loader.settings')
@patch('dlint.finder.settings')
def test_get_template_folders_for_the_filesystem_loader(settings, settings_):
    settings_.TEMPLATE_LOADERS = settings.TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
    )
    settings_.TEMPLATE_DIRS = settings.TEMPLATE_DIRS = ('/some/dir/',)

    template_finder = TemplateFinder()

    template_finder.get_template_folders().should.equals(['/some/dir/'])


@patch('django.template.loader.template_source_loaders', None)  # forces the loaders to be reloaded
@patch('django.template.loader.settings')
@patch('django.template.loaders.app_directories.app_template_dirs', ['/anapp/dir/'])
def test_get_template_folders_for_the_app_directories_loader(settings):
    settings.TEMPLATE_LOADERS = (
        'django.template.loaders.app_directories.Loader',
    )

    template_finder = TemplateFinder()

    template_finder.get_template_folders().should.equals(['/anapp/dir/'])


@patch('django.template.loader.template_source_loaders', None)  # forces the loaders to be reloaded
@patch('django.template.loaders.eggs.Loader.__repr__', lambda self: 'eggsloader')
@patch('django.template.loader.settings')
def test_get_template_folders_with_an_unsuppored_template_loader(settings):
    settings.TEMPLATE_LOADERS = (
        'django.template.loaders.eggs.Loader',
    )

    template_finder = TemplateFinder()

    template_finder.get_template_folders.when.called_with()\
        .should.throw(
            template_finder.LoaderNotSupportedException,
            "The eggsloader django template loader is not supported."
        )


@patch('dlint.finder.walk', lambda f: [(f, ['dirs'], ['fa', 'fb'])])
@patch('dlint.finder.TemplateFinder.get_template_folders', lambda self: ['/folder'])
def test_get_template_source_paths_with_an_unsuppored_template_loader():
    template_finder = TemplateFinder()

    template_finder.get_template_source_paths()\
        .should.equals(['/folder/fa', '/folder/fb'])


@patch('dlint.finder.DebugLexer')
@patch('dlint.finder.codecs.open')
def test_get_template_tokens(_open, DebugLexer):
    template_finder = TemplateFinder()

    # write some content to a temporary file
    temp_file = NamedTemporaryFile(delete=False)
    temp_file.write('content')
    temp_file.close()

    # makes the open method return the temporary file
    _open.return_value = open(temp_file.name)

    # call the tested function
    template_finder.get_template_tokens(temp_file.name)

    # check if the function is handling the file as expected
    _open.assert_called_with(temp_file.name, 'r', 'utf-8')
    DebugLexer.assert_called_with('content', None)

    # remove the temporary file
    os.unlink(temp_file.name)


def test_get_template_tokens_should_return_only_load_tokens():
    class TestLoadToken(object):
        token_type = TOKEN_BLOCK
        contents = 'load module'

    class TestValueToken(object):
        token_type = TOKEN_VAR
        contents = 'value'

    class TestOtherBlockToken(object):
        token_type = TOKEN_BLOCK
        contents = 'tag'

    template_finder = TemplateFinder()

    # mock the function that will be called by
    # get_load_template_tokens
    load_token = TestLoadToken()
    template_finder.get_template_tokens = Mock(return_value=[
        load_token,
        TestValueToken(),
        TestOtherBlockToken(),
    ])

    template_finder.get_load_template_tokens('source.html')\
        .should.equals([load_token])
    template_finder.get_template_tokens.assert_called_with('source.html')
