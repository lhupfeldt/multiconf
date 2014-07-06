# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re
from pytest import fail  # pylint: disable=no-name-in-module

def lineno():
    frame = sys._getframe(1)
    return frame.f_lineno


def lazy(*args):
    return lambda: args[0](*args[1:])


def _config_msg(error_type, file_name, line_num, *lines):
    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]

    line_msg = 'File "{file_name}", line {line_num}'.format(file_name=file_name, line_num=line_num) + '\n'
    emsg = ""
    for line in lines:
        emsg += line_msg
        emsg += error_type + ': ' + line + '\n'
    return emsg


def config_error(file_name, line_num, *line):
    return _config_msg('ConfigError', file_name, line_num, *line)


def config_warning(file_name, line_num, *line):
    return _config_msg('ConfigWarning', file_name, line_num, *line)


def api_error(file_name, line_num, *line):
    return _config_msg('MultiConfApiError', file_name, line_num, *line)


def assert_lines_in(file_name, line_num, text, *expected_lines):
    """Assert that `*expected_lines` occur in order in the lines of `text`.

    Args:
        file_name (str): Test file name, should be set to '__file__'
        line_num (int): Line number of failure, find the line number by using 'lineno()'
        text (str): The text to find *expected_lines in
        *expected_lines (str or RegexObject (hasattr `match`)): For each `expected_line` in expected_lines:
            If `expected_line` has a match method it is called and must return True for a line in `text`.
            Otherwise, if the `expected_line` starts with '^', a line in `text` must start with `expected_line[1:]`
            Otherwise `expected line` must simply occur in a line in `text`

    The following pattern will be replaced in all expected_lines which are not regex:
    '%(file_name)s' replaced with: file_name
    '%(lnum)s' replaced with: 'File "%(file_name)s", line %(line_num)d'
    """

    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]
    file_line_replace = dict(
        lnum='File "%(file_name)s", line %(line_num)d' % dict(file_name=file_name, line_num=line_num),
        file_name=file_name,
    )

    fixed_expected = []
    for expected in expected_lines:
        fixed_expected.append(expected % file_line_replace if not hasattr(expected, 'match') else expected)

    max_index = len(fixed_expected)
    index = 0

    for line in text.split('\n'):
        expected = fixed_expected[index]

        if hasattr(expected, 'match'):
            if expected.match(line):
                index += 1
                if index == max_index:
                    return
            continue

        if expected.startswith('^'):
            if line.startswith(expected[1:]):
                index += 1
                if index == max_index:
                    return
            continue

        if expected in line:
            index += 1
            if index == max_index:
                return

    if hasattr(expected, 'match'):
        fail("\n\nThe regex:\n\n" + repr(expected.pattern) + "\n\n    --- NOT MATCHED or OUT OF ORDER in ---\n\n" + text)

    if expected.startswith('^'):
        fail("\n\nThe text:\n\n" + repr(expected[1:]) + "\n\n    --- NOT FOUND, OUT OF ORDER or NOT AT START OF LINE in ---\n\n" + text)

    fail("\n\nThe text:\n\n" + repr(expected) + "\n\n    --- NOT FOUND OR OUT OF ORDER IN ---\n\n" + text)


# Handle variable ids and source file line numbers in json/repr output


_replace_user_file_line_tuple_regex = re.compile(r"\('[^,()]+/([^/]+)_test.py', [0-9]+\)")
def replace_user_file_line_tuple(string):
    return _replace_user_file_line_tuple_regex.sub(r"('fake_dir/\1_test.py', 999)", string)


_replace_user_file_line_msg_regex = re.compile(r'File "[^"]+/([^/]+)_test.py", line [0-9]+')
def replace_user_file_line_msg(string, line_no=999):
    return _replace_user_file_line_msg_regex.sub(r'File "fake_dir/\1_test.py", line %s' % line_no, string)

_replace_multiconf_file_line_msg_regex = re.compile(r'File "[^"]+/multiconf/([^/]+).py", line [0-9]+')
def replace_multiconf_file_line_msg(string):
    return _replace_multiconf_file_line_msg_regex.sub(r'File "fake_multiconf_dir/\1.py", line 999', string)

_replace_ids_regex = re.compile(r'("__id__"|, id| #id): [0-9]+("?)')
_replace_refs_regex = re.compile(r'"#ref (self, |later, |)id: [0-9]+')
_replace_named_as_regex = re.compile(r" #as: '[^,]+',")
def replace_ids(json_string, named_as=True):
    json_string = _replace_ids_regex.sub(r'\1: 0000\2', json_string)
    if named_as:
        json_string = _replace_named_as_regex.sub(r" #as: 'xxxx',", json_string)
    return _replace_refs_regex.sub(r'"#ref \1id: 0000', json_string)


_replace_builder_ids_regex = re.compile(r"""\.builder\.[0-9]+(["'])""")
def replace_ids_builder(json_string, named_as=True):
    json_string = _replace_builder_ids_regex.sub(r'.builder.0000\1', json_string)
    return replace_ids(json_string, named_as)


_compact_ids_regex = re.compile(r'("), \n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': "?([^"]+)"?, \n *"([a-zA-Z0-9_]*) #calculated": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #calculated"', json_string)


#    "item": false,
#    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true

_compact_excluded_regex = re.compile(r""": false, \n *"([a-zA-Z0-9_]*) #Excluded: <class '([.xa-zA-Z0-9_]*)'>": true""")
def to_compact_excluded(json_string):
    json_string = to_compact(json_string)
    return _compact_excluded_regex.sub(r""": "false #Excluded: <class '\2'>""" + '"', json_string)
