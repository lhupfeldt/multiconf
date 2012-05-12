import inspect
from collections import namedtuple

_Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')

def lineno():
    return _Traceback(*inspect.stack()[1][1:]).lineno

def lazy(*args):
    return lambda: args[0](*args[1:])

def config_error(file_name, line_num, *lines):
    emsg = ""
    for line in lines:
        emsg += 'File "{file_name}", line {line_num}'.format(file_name=file_name, line_num=line_num) + '\n'
        emsg += 'ConfigError: ' + line + '\n'
    return emsg
