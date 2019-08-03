from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigException
from multiconf.decorators import named_as, nested_repeatables
from multiconf.envs import EnvFactory


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
        super().__init__(mc_key=mc_key)

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
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            FaultyRoot()


def test_triple_property_error_repeatable_config_item():
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with GoodRoot():
                FaultyRepeatable('aa')


def test_triple_property_error_repeatable_and_simple_config_item():
    with raises(ConfigException) as exinfo:
        @mc_config(ef, load_now=True)
        def config(_):
            with FaultyRoot():
                FaultyRepeatable('bb')
