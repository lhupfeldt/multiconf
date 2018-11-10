# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from pytest import raises

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigDefinitionException
from multiconf.decorators import named_as, nested_repeatables, repeatable_key
from multiconf.envs import EnvFactory

from .utils.utils import config_error, replace_ids
from .utils.tstclasses import ItemWithName


def ce(line_num, *lines):
    return config_error(__file__, line_num, *lines)


ef1_prod = EnvFactory()
prod1 = ef1_prod.Env('prod')

ef2_prod_dev2ct = EnvFactory()
pp2 = ef2_prod_dev2ct.Env('dev2ct')
prod2 = ef2_prod_dev2ct.Env('prod')


_g_expected = """{
    "__class__": "root #as: 'project', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "abc"
}"""

def test_named_as():
    @named_as('project')
    class root(ItemWithName):
        pass

    @mc_config(ef2_prod_dev2ct, load_now=True)
    def config(croot):
        with root() as proj:
            proj.name = 'abc'
        return proj

    cfg = config(prod2)
    assert replace_ids(repr(cfg.mc_config_result), named_as=False) == _g_expected


def test_nested_repeatables():
    @nested_repeatables('ritm1', 'ritm2')
    class root(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(croot):
        root()

    cr = config(prod1).root
    assert cr.ritm1 == {}
    assert cr.ritm2 == {}


def test_mc_key_value():
    @named_as('ritem')
    class Rr(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.aa = 0

    @repeatable_key(mc_key='single')
    class SingularRr(Rr):
        def __init__(self):
            super().__init__(mc_key=None)
            self.aa = 0

    @named_as('ritem')
    @repeatable_key(mc_key='single2')
    class Singular2(RepeatableConfigItem):
        aa = 2

    @nested_repeatables('ritem')
    class root(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with root() as cr:
            Rr('aa')
            Rr('bb')
            SingularRr()
            Singular2()

    cr = config(prod1).root
    assert 'aa' in cr.ritem
    assert 'bb' in cr.ritem
    assert 'single' in cr.ritem
    assert 'single2' in cr.ritem


def test_repeatable_key():
    @named_as('ritem')
    class Rr(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.aa = 0

    @repeatable_key(base_name='xxx')
    class AlternateKeyRr(Rr):
        def __init__(self, base_name='xxx'):
            super().__init__(mc_key=None)
            self.base_name = base_name

    @repeatable_key(base_name='zzz')
    class FixedKeyRr(Rr):
        def __init__(self):
            super().__init__(mc_key=None)

    @repeatable_key(base_name='qqq')
    class FixedKey2(AlternateKeyRr):
        def __init__(self):
            super().__init__(base_name='qqq')

    @nested_repeatables('ritem')
    class root(ConfigItem):
        pass

    @mc_config(ef1_prod, load_now=True)
    def config(_):
        with root() as cr:
            Rr('aa')
            Rr('bb')
            AlternateKeyRr()
            AlternateKeyRr(base_name='yyy')
            FixedKeyRr()
            FixedKey2()

    cr = config(prod1).root
    print(cr.ritem)
    assert 'aa' in cr.ritem
    assert 'bb' in cr.ritem
    assert 'xxx' in cr.ritem
    assert cr.ritem['xxx'].base_name == 'xxx'
    assert 'yyy' in cr.ritem
    assert cr.ritem['yyy'].base_name == 'yyy'
    assert 'qqq' in cr.ritem
    assert cr.ritem['qqq'].base_name == 'qqq'


def test_repeatable_key_not_repeatable_error():
    with raises(ConfigDefinitionException) as exinfo:
        @named_as('item')
        @repeatable_key(base_name='xxx')
        class Xx(ConfigItem):
            def __init__(self):
                super().__init__()
                self.aa = 0

    exp_ex = "Decorator '@repeatable_key' is only allowed on instance of RepeatableConfigItem."
    assert exp_ex == str(exinfo.value)


def test_repeatable_key_no_name_value_error():
    with raises(ConfigDefinitionException) as exinfo:
        @named_as('item')
        @repeatable_key()
        class Xx(RepeatableConfigItem):
            def __init__(self):
                super().__init__()
                self.aa = 0

    exp_ex = "Decorator '@repeatable_key' takes exactly one key-value pair."
    assert exp_ex == str(exinfo.value)
