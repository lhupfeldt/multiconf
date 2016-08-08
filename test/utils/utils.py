# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re
from pytest import fail  # pylint: disable=no-name-in-module


def py3_local(extra_class_levels=''):
    """Return extra string for python 3 representation of a test-funtion-local function or class.

    This is different from the python 2 representation which has no information about parent classes or functions.

    Arguments:
        extra_class_levels (str): If the function or class is nested inside a class inside the test function
    """
    if sys.version_info[0] < 3:
        return ''

    frame = sys._getframe(1)
    return frame.f_code.co_name + '.<locals>.' + extra_class_levels


py3_tc = 'type' if sys.version_info[0] < 3 else 'class'


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


def total_msg(total_num_errors):
    ww, err = ('were', 'errors') if total_num_errors > 1 else ('was', 'error')
    return "There {ww} {num_errors} {err} when defining item: ".format(ww=ww, num_errors=total_num_errors, err=err)


def file_line(error_line_num):
    """Helper method for 'assert_lines_in' with multiple errors on different lines.

    'assert_lines_in' will replace the 'file_name'.
    """

    return '^File "%(file_name)s", line {error_line_num}'.format(error_line_num=error_line_num)


def assert_lines_in(file_name, line_num, text, *expected_lines):
    """Assert that `*expected_lines` occur in order in the lines of `text`.

    Args:
        file_name (str): Test file name, should be set to '__file__'
        line_num (int): Line number of failure. You can find the line number by using 'lineno()'
            Use this  together with the pattern %(lnum)s as first element in 'expected_lines', if all errors
            are from the same line.
            If errors are from different lines, set this to None, and instead use the 'file_line' function to
            insert patterns in 'expected_lines'.

        text (str): The text to find *expected_lines in
        *expected_lines (str, RegexObject (hasattr `match`) or sequence): For each `expected_line` in expected_lines:
            If an expected_line is a tuple or a list, any item in the sequence is handled as an individual
            expected_line, which may be matched in any order, but not out of order with the surrounding expected_lines,
            as described below:

            If `expected_line` has a match method it is called and must return True for a line in `text`.
            Otherwise, if the `expected_line` starts with '^', a line in `text` must start with `expected_line[1:]`
            Otherwise `expected line` must simply occur in a line in `text`

    The following pattern will be replaced in all expected_lines which are not regex:
    '%(file_name)s' replaced with: file_name
    '%(lnum)s' replaced with: 'File "%(file_name)s", line %(line_num)d'
    '%(type_or_class)s replaced with 'type' if python version < '3' else 'class'
    """

    def _check_match(expected, line):
        if hasattr(expected, 'match') and expected.match(line):
            return True

        if expected.startswith('^') and line.startswith(expected[1:]):
            return True

        if expected in line:
            return True

        return False

    def _report_failure(expected):
        if hasattr(expected, 'match'):
            fail("\n\nThe regex:\n\n" + repr(expected.pattern) + "\n\n    --- NOT MATCHED or OUT OF ORDER in ---\n\n" + text)

        if expected.startswith('^'):
            fail("\n\nThe text:\n\n" + repr(expected[1:]) + "\n\n    --- NOT FOUND, OUT OF ORDER or NOT AT START OF LINE in ---\n\n" + text)

        fail("\n\nThe text:\n\n" + repr(expected) + "\n\n    --- NOT FOUND OR OUT OF ORDER IN ---\n\n" + text)

    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]

    file_line_replace = dict(
        file_name=file_name,
        type_or_class=py3_tc
    )
        
    if line_num is not None:
        file_line_replace['lnum'] = 'File "%(file_name)s", line %(line_num)d' % dict(file_name=file_name, line_num=line_num)

    def _fix_one_expected(expected):
        return expected % file_line_replace if not hasattr(expected, 'match') else expected

    fixed_expected = []
    for expected in expected_lines:
        if isinstance(expected, (tuple, list)):
            if len(expected) == 1:
                # Single element, insert instead of sequence
                fixed_expected.append(_fix_one_expected(expected[0]))
                continue
            unordered = []
            for unordered_expected in expected:
                unordered.append(_fix_one_expected(unordered_expected))
            fixed_expected.append(unordered)
            continue
        fixed_expected.append(_fix_one_expected(expected))

    max_index = len(fixed_expected)
    index = 0

    for line in text.split('\n'):
        expected = fixed_expected[index]

        if isinstance(expected, (tuple, list)):
            new_expected = []
            for unordered_expected in expected:
                if _check_match(unordered_expected, line):
                    continue
                new_expected.append(unordered_expected)
            fixed_expected[index] = new_expected if len(new_expected) > 1 else new_expected[0]
            continue

        if _check_match(expected, line):
            index += 1
            if index == max_index:
                return

    if isinstance(expected, (tuple, list)):
        for expected in new_expected:
            # TODO: only reports first element
            _report_failure(expected)
    _report_failure(expected)


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


_compact_ids_regex = re.compile(r'("),\n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': "?([^"]+)"?,\n *"([a-zA-Z0-9_]*) #(calculated|static)": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #\3"', json_string)


#    "item": false,
#    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true

_compact_excluded_regex = re.compile(r""": false,\n *"([a-zA-Z0-9_]*) #Excluded: <class '([.xa-zA-Z0-9_]*)'>": true""")
def to_compact_excluded(json_string):
    json_string = to_compact(json_string)
    return _compact_excluded_regex.sub(r""": "false #Excluded: <class '\2'>""" + '"', json_string)
