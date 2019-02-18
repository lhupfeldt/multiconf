# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

# pylint: disable=E0611
from pytest import raises

from multiconf import mc_config, ConfigItem, ConfigBuilder, ConfigException, ConfigDefinitionException
from multiconf.decorators import nested_repeatables
from multiconf.envs import EnvFactory

from .utils.utils import config_error, line_num, next_line_num, lines_in, local_func, start_file_line, file_line
from .utils.messages import exception_previous_object_expected_stderr
from .utils.messages import mc_required_expected
from .utils.tstclasses import BuilderWithAA


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


def test_value_not_assigned_to_all_envs_in_builder(capsys):
    errorline = [None]

    class B(BuilderWithAA):
        def mc_build(self):
            pass

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with B() as bb:
                errorline[0] = next_line_num()
                bb.setattr('aa', prod="hello")

    _sout, serr = capsys.readouterr()
    assert serr == ce(errorline[0], mc_required_expected.format(attr='aa', env=pprd))


def test_exception_in___exit___must_print_ex_info_and_raise_original_exception_if_any_pending_builder(capsys):
    with raises(Exception) as exinfo:
        class root(ConfigItem):
            pass

        class inner(ConfigBuilder):
            def mc_build(self):
                raise Exception("in build")

        @mc_config(ef, load_now=True)
        def config(_):
            with root():
                with inner():
                    raise Exception("in with")

    _sout, serr = capsys.readouterr()
    assert serr == ""
    assert str(exinfo.value) == 'in with'


def test_error_freezing_previous_sibling__build(capsys):
    errorline = [None]

    class inner(ConfigBuilder):
        def mc_build(self):
            raise Exception("Error in build")

    with raises(Exception) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            errorline[0] = next_line_num()
            inner(1)
            inner(2)

    _sout, serr = capsys.readouterr()
    exp = exception_previous_object_expected_stderr % dict(module='definition_errors_builder_test', local_func=local_func())
    assert serr == exp
    assert str(exinfo.value) == "Error in build"


def test_builder_does_not_accept_nested_repeatables_decorator(capsys):
    with raises(ConfigDefinitionException) as exinfo:
        errorline = next_line_num() + 1
        @nested_repeatables('a')
        class _inner(ConfigBuilder):
            def mc_build(self):
                _a = 1

    _sout, serr = capsys.readouterr()
    exp = file_line(__file__, errorline) + "\nConfigError: Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder.\n"
    assert serr == exp
    assert str(exinfo.value) == "Decorator '@nested_repeatables' is not allowed on instance of ConfigBuilder."


def test_build_override_underscore_mc_error(capsys):
    errorline = line_num() + 3
    class B(ConfigBuilder):
        def mc_build(self):
            self.setattr("_mca", default="Hello", mc_force=True)

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            B()

    _sout, serr = capsys.readouterr()
    msg = "Trying to set attribute '_mca' on a config item. Atributes starting with '_mc' are reserved for multiconf internal usage."
    assert serr == ce(errorline, msg)


def _check_no_env(errorline, capsys):
    _sout, serr = capsys.readouterr()
    assert lines_in(
        serr,
        start_file_line(__file__, errorline),
        "^ConfigError: No Env or EnvGroup names specified.",
        # TODO, should we expect multiple errors here?
        # start_file_line(__file__, errorline),
        # config_error_mc_required_expected.format(attr='aa', env=pprd),
    )


def test_setattr_no_envs(capsys):
    # ConfigBuilder
    class B(BuilderWithAA):
        def mc_build(self):
            pass

    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with B() as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa')

    _check_no_env(errorline[0], capsys)


def test_setattr_no_envs_set_unknown(capsys):
    # ConfigBuilder
    class B(ConfigBuilder):
        def mc_build(self):
            pass

    errorline = [None]

    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with B() as ci:
                errorline[0] = next_line_num()
                ci.setattr('aa', mc_set_unknown=True)

    _check_no_env(errorline[0], capsys)


def test_setattr_mc_keyword_call_only():
    # ConfigBuilder
    class B(ConfigBuilder):
        def mc_build(self):
            pass

    with raises(TypeError) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with B() as ci:
                ci.setattr('aa', True, default=1)

    assert "setattr() takes 2 positional arguments but 3 were given" in str(exinfo.value)
