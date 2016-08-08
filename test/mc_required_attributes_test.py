# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from .utils.utils import config_error, replace_ids, lineno, total_msg, assert_lines_in, file_line, py3_local
from .utils.messages import mc_required_current_env_expected, mc_required_other_env_expected, exception_previous_object_expected_stderr
from .utils.messages import config_error_mc_required_current_env_expected, config_error_mc_required_other_env_expected


from .. import ConfigRoot, ConfigItem, MC_REQUIRED, ConfigException

from ..envs import EnvFactory

def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')


_g_expected = """{
    "__class__": "root #as: 'project', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "abc"
}"""



def test_required_attributes_inherited_ok():
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory):
            super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    class root2(root):
        def __init__(self, selected_env, env_factory):
            super(root2, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.someattr2 = MC_REQUIRED
            self.someotherattr2 = MC_REQUIRED

    with root2(prod, ef) as cr:
        cr.anattr = 1
        cr.anotherattr = 2
        cr.someattr2 = 3
        cr.someotherattr2 = 4

    assert cr.anattr == 1
    assert cr.anotherattr == 2
    assert cr.someattr2 == 3
    assert cr.someotherattr2 == 4


def test_required_attributes_inherited_missing(capsys):
    class root(ConfigRoot):
        def __init__(self, selected_env, env_factory):
            super(root, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.anattr = MC_REQUIRED
            self.anotherattr = MC_REQUIRED

    class root2(root):
        def __init__(self, selected_env, env_factory):
            super(root2, self).__init__(selected_env=selected_env, env_factory=env_factory)
            self.someattr2  = MC_REQUIRED
            self.someotherattr2 = MC_REQUIRED

    with raises(ConfigException) as exinfo:
        with root2(prod, ef) as cr:
            errorline1 = lineno() + 1
            cr.setattr('anattr', prod=1)
            errorline2 = lineno() + 1
            cr.setattr('someattr2', prod=3)
            errorline3 = lineno() + 1
            cr.setattr('someotherattr2', pp=4)
            errorline_exit = lineno()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, None, serr,
        file_line(errorline1),
        config_error_mc_required_other_env_expected.format(attr='anattr', env=pp),
        file_line(errorline2),
        config_error_mc_required_other_env_expected.format(attr='someattr2', env=pp),
        file_line(errorline3),
        config_error_mc_required_current_env_expected.format(attr='someotherattr2', env=prod),
        file_line(errorline_exit),
        config_error_mc_required_other_env_expected.format(attr='anotherattr', env=pp),
        config_error_mc_required_current_env_expected.format(attr='anotherattr', env=prod),
    )


def test_multiple_required_attributes_missing_for_configitem(capsys):
    with raises(ConfigException) as exinfo:
        class root(ConfigRoot):
            pass

        class item(ConfigItem):
            def __init__(self):
                super(item, self).__init__()
                self.abcd = MC_REQUIRED
                self.efgh = MC_REQUIRED
                self.ijkl = MC_REQUIRED

        with root(prod, ef):
            with item() as ii:
                errorline1 = lineno() + 1
                ii.setattr('efgh', prod=7)
                errorline_exit = lineno()

    _sout, serr = capsys.readouterr()
    assert_lines_in(
        __file__, None, serr,
        file_line(errorline1),
        config_error_mc_required_other_env_expected.format(attr='efgh', env=pp),
        file_line(errorline_exit),
        config_error_mc_required_other_env_expected.format(attr='abcd', env=pp),
        config_error_mc_required_current_env_expected.format(attr='abcd', env=prod),
        config_error_mc_required_other_env_expected.format(attr='ijkl', env=pp),
        config_error_mc_required_current_env_expected.format(attr='ijkl', env=prod),
    )


def test_error_freezing_previous_sibling__validation(capsys):
    class inner(ConfigItem):
        def __init__(self):
            super(inner, self).__init__()
            self.a = MC_REQUIRED

    with raises(Exception) as exinfo:
        with ConfigRoot(prod, ef):
            errorline1 = lineno() + 1
            inner()
            errorline2 = lineno() + 1
            inner()

    _sout, serr = capsys.readouterr()
    print(serr)
    assert_lines_in(
        __file__, None, serr,
        file_line(errorline1),
        config_error_mc_required_other_env_expected.format(attr='a', env=pp),
        config_error_mc_required_current_env_expected.format(attr='a', env=prod),
    )

    assert serr.endswith(exception_previous_object_expected_stderr % dict(
        module='mc_required_attributes_test', py3_local=py3_local()))
    assert total_msg(2) in str(exinfo.value)
