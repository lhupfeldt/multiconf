# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, re
from typing import Optional

from .lines_in import lines_in as generic_lines_in

major_version = sys.version_info[0]
minor_version = sys.version_info[1]


def local_func():
    """Return extra string for representation of a test-funtion-local function or class.

    This allows for easy renaming of test functions with no impact on expected result string.
    """

    frame = sys._getframe(1)
    return frame.f_code.co_name + '.<locals>.'


def line_num():
    frame = sys._getframe(1)
    return frame.f_lineno


def next_line_num(minor_version_offsets: Optional[dict[int, int]] = None):
    """Get the line number the call to this function.

    Arguments:
        minor_version_offsets: An offset to apply for the specified Python minor version.
            This is necessary because of differences in reported linenumbers for decorators.
            The offset applies to the specified minor version and any version (max 20) smaller than that.
    """

    offset = 0
    if minor_version_offsets:
        assert major_version == 3
        for check_minor_version in range(minor_version, minor_version + 20):
            offset = minor_version_offsets.get(check_minor_version, None)
            if offset is not None:
                break
        else:
            offset = 0

    frame = sys._getframe(1)
    return frame.f_lineno + 1 + offset


def lazy(*args):
    return lambda: args[0](*args[1:])


def _config_msg(error_type, file_name, line_nummber, *lines):
    if not file_name.endswith('.py'):
        # file_name  may end in .pyc!
        file_name = file_name[:-1]

    line_msg = f'File "{file_name}", line {line_nummber}\n'
    emsg = ""
    for line in lines:
        emsg += line_msg
        emsg += error_type + ': ' + line + '\n'
    return emsg


def config_error(file_name, line_nummber, *line):
    return _config_msg('ConfigError', file_name, line_nummber, *line)


def config_warning(file_name, line_nummber, *line):
    return _config_msg('ConfigWarning', file_name, line_nummber, *line)


def api_error(file_name, line_nummber, *line):
    return _config_msg('MultiConfApiError', file_name, line_nummber, *line)


def total_msg(total_num_errors):
    ww, err = ('were', 'errors') if total_num_errors > 1 else ('was', 'error')
    return f"There {ww} {total_num_errors} {err} when defining item: "


def file_line(error_file_name, error_line_num):
    """Return string with file/line info formatted like in error messages."""
    return f'File "{error_file_name}", line {error_line_num}'


def start_file_line(error_file_name, error_line_num):
    """Helper for 'assert lines_in'.

    Return string with file/line info formatted like in error messages and prefixed with '^' for start-of-line.
    """

    return '^' + file_line(error_file_name, error_line_num)


def lines_in(text, *expected_lines):
    return generic_lines_in(text, None, *expected_lines)


# Handle variable ids and source file line numbers in json/repr output


_replace_multiconf_file_line_msg_regex = re.compile(r'File "[^"]+/multiconf/([^/]+).py", line [0-9]+')
def replace_multiconf_file_line_msg(string):
    return _replace_multiconf_file_line_msg_regex.sub(r'File "fake_multiconf_dir/\1.py", line 999', string)


_replace_ids_regex = re.compile(r'("__id__"|, id| #id): [0-9]+("?)')
_replace_refs_regex = re.compile(r'"#ref (self, |later, |)id: [0-9]+')
_replace_named_as_regex = re.compile(r" #as: '[^,]+',")
_replace_address_regex = re.compile(r" at 0x[^>]*>")
def replace_ids(json_string, named_as=True, address=False):
    json_string = _replace_ids_regex.sub(r'\1: 0000\2', json_string)
    if named_as:
        json_string = _replace_named_as_regex.sub(r" #as: 'xxxx',", json_string)
    if address:
        json_string = _replace_address_regex.sub(r" at 0x0000>", json_string)
    return _replace_refs_regex.sub(r'"#ref \1id: 0000', json_string)


_replace_builder_ids_regex = re.compile(r"""\.builder\.[0-9]+(["'])""")
def replace_ids_builder(json_string, named_as=True, address=False):
    json_string = _replace_builder_ids_regex.sub(r'.builder.0000\1', json_string)
    return replace_ids(json_string, named_as, address)


_compact_ids_regex = re.compile(r'("),\n *"__id__": ([0-9]+),')
_compact_calculated_regex = re.compile(r': "?([^"$]+)"?(,\n *"[a-zA-Z0-9_]+ #value for .* provided by @property": true|),\n *"([a-zA-Z0-9_]+) #(calculated|static)": true')
def to_compact(json_string):
    # There is no named_as in the non-compact format, just insert
    json_string = _compact_ids_regex.sub(r" #as: 'xxxx', id: \2\1,", json_string)
    return _compact_calculated_regex.sub(r': "\1 #\4"\2', json_string)


#    "item": false,
#    "item #Excluded: <class 'multiconf.test.include_exclude_test.item'>": true

_compact_excluded_regex = re.compile(r""": false,\n *"([a-zA-Z0-9_]*) #Excluded: <class '([.xa-zA-Z0-9_]*)'>": true""")
def to_compact_excluded(json_string):
    json_string = to_compact(json_string)
    return _compact_excluded_regex.sub(r""": "false #Excluded: <class '\2'>""" + '"', json_string)
