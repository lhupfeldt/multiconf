# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
from collections import namedtuple
import inspect

class ConfigBaseException(Exception):
    pass


class ConfigException(ConfigBaseException):
    pass


class NoAttributeException(ConfigBaseException):
    pass


class InvalidUsageException(ConfigBaseException):
    pass


_Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')


def _error_msg(num_errors, message):
    tb = _Traceback(*inspect.stack()[2][1:])
    print >> sys.stderr, 'File "' + tb.filename + '", line', tb.lineno
    print >> sys.stderr, 'ConfigError:', message
    return num_errors + 1


def _warning_msg(message):
    tb = _Traceback(*inspect.stack()[2][1:])
    print >> sys.stderr, 'File "' + tb.filename + '", line', tb.lineno
    print >> sys.stderr, 'ConfigWarning:', message
