# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys, os.path
from collections import namedtuple

class ConfigBaseException(Exception):
    pass


class ConfigException(ConfigBaseException):
    pass


class NoAttributeException(ConfigBaseException):
    pass


class InvalidUsageException(ConfigBaseException):
    pass


def _user_file_line(up_level_start=1):
    frame = sys._getframe(up_level_start)
    while 1:
        filename = frame.f_globals['__file__']
        if os.path.basename(os.path.dirname(filename)) != 'multiconf':
            break
        frame = frame.f_back

    return filename if filename[-1] == 'y' else filename[:-1], frame.f_lineno


def _error_msg(num_errors, message, up_level=2, error_type='ConfigError'):
    print >> sys.stderr, 'File "%s", line %d' % _user_file_line(up_level+1)
    print >> sys.stderr, error_type + ':', message
    return num_errors + 1


def _warning_msg(message, up_level=2):
    _error_msg(0, message, up_level=up_level+1, error_type='ConfigWarning')
