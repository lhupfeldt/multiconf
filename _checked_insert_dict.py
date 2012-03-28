# Copyright 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# This code is free for anybody to use

from collections import namedtuple
from attrdict import AttrDict
import inspect

class InsertException(Exception):
    pass


class CheckedInsertDictGroup():
    def __init__(self, fail_fast = True):
        self.fail_fast = fail_fast
        self.members = []
        self.validation_enabled = False
        self.check_confs = {}
        self.env_confs = {}
        self.errors = 0

    def insert(self, env, key, value):
        #print 'insert:', env, key, value
        #print self.check_confs
        for member in self.members:
            #print 'member._env.name:', member._env.name

            # Validate that we are not overriding values from different groups or re-specifying env
            if member._env in env:
                #print 'member:', member
                conf = self.check_confs.get(member._env)
                #print 'conf:', conf
                if conf and key in conf:
                    #print 'member._env:', member._env
                    if not self.fail_fast:
                        self.errors += 1
                    raise InsertException("A value is already specified for: " + repr(env) + '.' + key + '=' + repr(value) + ", previous value: " + repr(member._env) + '.' + key + '=' + repr(conf[key]))

        self.check_confs.setdefault(env, {})[key] = value
        for single_env in env.envs():
            self.env_confs.setdefault(single_env, {})[key] = value


class CheckedInsertDict(AttrDict):
    """
    Only allows a single insert of an attribute to any of the dicts in the dict_group.
    Allows attribute-style access.
    """
    def __init__(self, dict_group, env, attrs={}):
        super(CheckedInsertDict, self).__init__(attrs)
        self._dict_group = dict_group
        self._env = env
        self._dict_group.members.append(self)

    def __setitem__(self, key, value):
        if key[0] != '_':
            try:
                self._dict_group.insert(self._env, key, value)
            except InsertException as ex:
                if self._dict_group.fail_fast:
                    raise
                Traceback = namedtuple('Traceback', 'filename, lineno, function, code_context, index')
                tb = Traceback(*inspect.stack()[1][1:])
                print tb
                print 'File "' + tb.filename + '", line', tb.lineno
                print 'ConfigError: ', ex.message
            return

        # This is for updating private attributes in __init__ only
        super(CheckedInsertDict, self).__setitem__(key, value)

        # TODO Adjust exception
        # TODO Save line number for error message

    __setattr__ = __setitem__
