import sys

from pytest import raises, xfail

if __name__ == '__main__':
    import os
    here = os.path.dirname(__file__)
    sys.path.insert(0, os.path.join(here, '..'))

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException
from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory


major_version = sys.version_info[0]

ef = EnvFactory()
prod = ef.Env('prod')


@named_as('root')
@nested_repeatables('reps')
class FaultyRoot(ConfigItem):
    @property
    def aa(self):
        return self.no_such_attr

    @property
    def bb(self):
        return self.no_such_attr

    @property
    def cc(self):
        return self.no_such_attr


@named_as('root')
@nested_repeatables('reps')
class GoodRoot(ConfigItem):
    pass


@named_as('reps')
class FaultyRepeatable(RepeatableConfigItem):
    def __init__(self, mc_key):
        super(FaultyRepeatable, self).__init__(mc_key=mc_key)

    @property
    def aa(self):
        return self.no_such_attr

    @property
    def bb(self):
        return self.no_such_attr

    @property
    def cc(self):
        return self.no_such_attr


def test_triple_property_error_config_item():
    if major_version >= 3:
        xfail("TODO")

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            FaultyRoot()


def test_triple_property_error_repeatable_config_item():
    if major_version >= 3:
        xfail("TODO")

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with GoodRoot():
                FaultyRepeatable('aa')


def test_triple_property_error_repeatable_and_simple_config_item():
    if major_version >= 3:
        xfail("TODO")

    with raises(ConfigException) as exinfo:
        @mc_config(ef)
        def _(_):
            with FaultyRoot():
                FaultyRepeatable('bb')


if __name__ == '__main__':
    test_triple_property_error_config_item()
