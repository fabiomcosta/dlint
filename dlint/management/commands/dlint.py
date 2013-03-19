# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.core.management.base import BaseCommand
from django.template.defaulttags import load as load_tag
from django.template.base import TOKEN_BLOCK, TOKEN_VAR, FilterExpression, TemplateSyntaxError

from dlint.finder import TemplateFinder
from dlint.parser import Parser


class Command(BaseCommand):

    def handle(self, *args, **options):
        template_finder = TemplateFinder()
        sources = template_finder.get_template_source_paths()

        print 'Found {} templates'.format(len(sources))
        print 'analysing unused load templatetag libraries...'

        for source in sources:
            all_tokens = template_finder.get_template_tokens(source)
            load_tokens = template_finder.get_load_template_tokens(source)

            # if any load_nodes
            # lets check for unused templatetags lib
            if load_tokens:
                # TODO evaluate the use of Parser instead of DebugParser
                parser = Parser(all_tokens)

                loaded_tags = {}
                loaded_filters = {}

                for load_token in load_tokens:
                    try:
                        load_tag(parser, load_token)
                    except TemplateSyntaxError as e:
                        print 'Error while loading modules from {}'.format(source)
                        raise e

                    last_library_loaded = parser.last_library_loaded

                    # since there is no secure way to get the
                    # templatetag module from the tag itself,
                    # we have to do this to map
                    # the tag to their module

                    # takes care of both
                    # {% load a b c from d.e %}
                    # {% load a.d %}
                    load_token_contents = load_token.contents.split()
                    module_name = load_token_contents[-1]

                    for f in last_library_loaded.filters.keys():
                        loaded_filters[f] = module_name

                    for t in last_library_loaded.tags.keys():
                        loaded_tags[t] = module_name

                print '{}:'.format(source)

                unused_filters = set()
                unused_tags = set()

                # verify if a filter is not being used by this template
                for filter_name, module in loaded_filters.items():

                    is_used = False

                    for token in all_tokens:
                        if token.token_type == TOKEN_VAR:
                            filter_expression = FilterExpression(token.contents, parser)
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

                print '  Unused Filters:'
                for filter_name in unused_filters:
                    print '    {} loaded from "{}"'.format(filter_name, loaded_filters[filter_name])

                # verify if a tag is not being used by this template
                for tag_name, module in loaded_tags.items():

                    is_used = False

                    for token in all_tokens:
                        if token.token_type == TOKEN_BLOCK and token.contents.split()[0] == tag_name:
                            is_used = True
                            break

                    if not is_used:
                        unused_tags.add(tag_name)

                print '  Unused Tags:'
                for tag_name in unused_tags:
                    print '    {} loaded from "{}"'.format(tag_name, loaded_tags[tag_name])
