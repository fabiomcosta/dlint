# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.template.defaulttags import load as load_tag
from django.template.base import TOKEN_BLOCK, TOKEN_VAR, FilterExpression, TemplateSyntaxError

from dlint.finder import TemplateFinder


class Command(BaseCommand):

    def handle(self, *args, **options):
        template_finder = TemplateFinder()
        sources = template_finder.items()

        #print 'Found {} templates'.format(len(sources))
        print 'analysing unused load templatetag libraries...'

        for source in sources:

            # if any load_nodes
            # lets check for unused templatetags lib
            if source.load_tokens:

                # loaded_libs will be a dict like this:
                # {
                #   'library_name': {
                #     'filters': set(),
                #     'tags': set(),
                #   },
                #   ...
                # }
                loaded_libs = defaultdict(lambda: defaultdict(set))
                loaded_filters = set()
                loaded_tags = set()

                for load_token in source.load_tokens:
                    try:
                        load_tag(source.parser, load_token)
                    except TemplateSyntaxError as e:
                        print 'Error while loading modules from {}'.format(source)
                        raise e

                    last_library_loaded = source.parser.last_library_loaded

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

                    loaded_libs[library_name]['filters'].update(library_filters)
                    loaded_libs[library_name]['tags'].update(library_tags)

                    loaded_filters.update(library_filters)
                    loaded_tags.update(library_tags)

                unused_filters = set()
                unused_tags = set()

                # verify if a filter is not being used by this template
                for filter_name in loaded_filters:

                    is_used = False

                    for token in source.tokens:
                        if token.token_type == TOKEN_VAR:
                            filter_expression = FilterExpression(token.contents, source.parser)
                            filter_functions_in_expression = [f[0] for f in filter_expression.filters]

                            # if TOKEN_VAR uses any filter
                            if filter_functions_in_expression:

                                filter_names = set()

                                for filter_function in filter_functions_in_expression:
                                    name = getattr(filter_function, '_decorated_function', filter_function).__name__
                                    filter_names.add(name)

                                is_used = filter_name in filter_names

                                if is_used:
                                    break

                    if not is_used:
                        unused_filters.add(filter_name)

                # verify if a tag is not being used by this template
                for tag_name in loaded_tags:

                    is_used = False

                    for token in source.tokens:
                        if token.token_type == TOKEN_BLOCK and token.contents.split()[0] == tag_name:
                            is_used = True
                            break

                    if not is_used:
                        unused_tags.add(tag_name)

                # TODO make this an option, of course
                show_warnings = False

                if (len(unused_filters) + len(unused_tags)) > 0:
                    print '{}:'.format(source.source)

                    for lib_name, lib_content in loaded_libs.items():

                        unused_filters_in_lib = lib_content['filters'].intersection(unused_filters)
                        unused_tags_in_lib = lib_content['tags'].intersection(unused_tags)

                        if (len(unused_filters_in_lib) + len(unused_tags_in_lib)) > 0:

                            if unused_filters_in_lib == lib_content['filters'] and \
                                    unused_tags_in_lib == lib_content['tags']:
                                print '  [E] {} library is completely unused in the file.'.format(lib_name)

                            elif show_warnings:
                                print '  [W] some modules of {} are not used:'.format(lib_name)

                                for unused_filter in unused_filters_in_lib:
                                    print '    [FILTER] {}'.format(unused_filter)

                                for unused_tag in unused_tags_in_lib:
                                    print '    [TAG] {}'.format(unused_tag)
