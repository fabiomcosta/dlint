# -*- coding: utf-8 -*-
from __future__ import unicode_literals, absolute_import

from django.core.management.base import BaseCommand
from django.template.base import TOKEN_BLOCK, TOKEN_VAR, TemplateSyntaxError

from dlint.finder import TemplateFinder


class Command(BaseCommand):

    def handle(self, *args, **options):

        template_finder = TemplateFinder()
        sources = list(template_finder.items())

        print 'Found {} templates'.format(len(sources))
        print 'analysing unused load templatetag libraries...'

        for source in sources:

            # if no load tags
            # continue to next template
            if not source.load_tokens:
                continue

            used_filters = set()
            used_tags = set()

            for token in source.tokens:

                filter_functions_in_expression = []

                if token.token_type == TOKEN_VAR:
                    # {{ val|filter }}

                    filter_expression = source.parser.compile_filter(token.contents)
                    filter_functions_in_expression = [f[0] for f in filter_expression.filters]

                elif token.token_type == TOKEN_BLOCK:
                    # tags like if, for, etc can use filters anywhere
                    # ex: {% if array1|length == array2|length %}

                    # to see if there are filters there
                    contents = token.split_contents()

                    tag_name = contents[0]
                    used_tags.add(tag_name)

                    # the tag_name will never have a filter
                    # so we dont check it
                    for content in contents[1:]:
                        try:
                            filter_expression = source.parser.compile_filter(content)
                            filter_functions_in_expression += [f[0] for f in filter_expression.filters]
                        except TemplateSyntaxError:
                            # while trying to get the filters used on
                            # {% if array1|length == array2|length %}
                            # we will try to compile '==', which will throw
                            # an TemplateSyntaxError, that will be ignored.
                            pass

                else:
                    continue

                # verify the used filters inside this token
                for filter_function in filter_functions_in_expression:
                    name = getattr(filter_function, '_decorated_function', filter_function).__name__
                    used_filters.add(name)

            unused_filters = source.loaded_filters.difference(used_filters)
            unused_tags = source.loaded_tags.difference(used_tags)

            # TODO make this an option, of course
            show_warnings = False

            # TODO separate this into a reporter class
            # that will be a list that will generate outputs
            # so we can generate the stdout reporter and a
            # jenkins xml reporter

            if (len(unused_filters) + len(unused_tags)) > 0:
                print '{}:'.format(source.source)

                for lib_name, lib_content in source.loaded_libs.items():

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
