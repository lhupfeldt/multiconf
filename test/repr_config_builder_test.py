# Copyright (c) 2018 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.compare_repr import compare_repr
from .utils.utils import local_func


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


_repr_configbuilder2_expected_repr_repeatable_item = """{
    "__class__": "Y #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "server2",
    "server_num": 2,
    "y_children": {
        "Hugo": {
            "__class__": "YChild #as: 'xxxx', id: 0000",
            "name": "Hugo",
            "a": 10
        }
    },
    "ys": {
        "server3": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "name": "server3",
            "server_num": 3,
            "y_children": {
                "Hanna": {
                    "__class__": "YChild #as: 'xxxx', id: 0000",
                    "name": "Hanna",
                    "a": 11
                },
                "Herbert": {
                    "__class__": "YChild #as: 'xxxx', id: 0000",
                    "name": "Herbert",
                    "a": 12
                }
            },
            "ys": {}
        },
        "server4": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "name": "server4",
            "server_num": 4,
            "y_children": {
                "Hanna": "#ref, id: 0000",
                "Herbert": "#ref, id: 0000"
            },
            "ys": {}
        }
    }
}"""

_repr_configbuilder2_dont_dump_expected_repr_full = """{
    "__class__": "ItemWithYs #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ys": {
        "server1": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "name": "server1",
            "server_num": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild #as: 'xxxx', id: 0000",
                    "name": "Hugo",
                    "a": 10
                }
            },
            "ys": {
                "server3": {
                    "__class__": "Y #as: 'xxxx', id: 0000",
                    "name": "server3",
                    "server_num": 3,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild #as: 'xxxx', id: 0000",
                            "name": "Hanna",
                            "a": 11
                        },
                        "Herbert": {
                            "__class__": "YChild #as: 'xxxx', id: 0000",
                            "name": "Herbert",
                            "a": 12
                        }
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y #as: 'xxxx', id: 0000",
                    "name": "server4",
                    "server_num": 4,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                }
            }
        },
        "server2": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "name": "server2",
            "server_num": 2,
            "y_children": {
                "Hugo": "#ref, id: 0000"
            },
            "ys": {
                "server3": "#ref, id: 0000",
                "server4": "#ref, id: 0000"
            }
        }
    },
    "aaa": "2 #static"
}"""


def test_repr_configbuilder2():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start

        def mc_build(self):
            for num in range(self.start, self.start + self.contained_in.aaa):
                Y('server%d' % num, server_num=num)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    @nested_repeatables('y_children', 'ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key, server_num):
            super().__init__(mc_key=mc_key)
            self.name = mc_key
            self.server_num = server_num

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key, a):
            super().__init__(mc_key=mc_key)
            self.name = mc_key
            self.a = a

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithYs() as cr:
            with YBuilder() as yb1:
                yb1.setattr('b', default=27, mc_set_unknown=True)
                YChild('Hugo', a=10)
                with YBuilder() as yb2:
                    yb2.setattr('start', default=3, pp=117)
                    yb2.setattr('c', default=28, mc_set_unknown=True)
                    YChild('Hanna', a=11)
                    YChild('Herbert', a=12)

    cr = config(prod).ItemWithYs

    assert compare_repr(cr.ys['server2'], _repr_configbuilder2_expected_repr_repeatable_item)
    assert compare_repr(cr, _repr_configbuilder2_dont_dump_expected_repr_full)
    assert compare_repr(cr.ys['server2'], _repr_configbuilder2_expected_repr_repeatable_item)


_repr_attr_ref_configbuilder_expected_repr = """{
    "__class__": "ItemWithYs #as: 'xxxx', id: 0000",
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "yb_ref": "#ref later builder <class 'test.repr_config_builder_test.%(local_func)sYBuilder'>",
    "ys": {
        "server1": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "aa": 777
        },
        "server2": {
            "__class__": "Y #as: 'xxxx', id: 0000",
            "aa": 777
        }
    },
    "aaa": "2 #static"
}"""

def test_repr_attr_ref_configbuilder():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start

        def mc_build(self):
            for num in range(self.start, self.start + self.contained_in.aaa):
                Y('server%d' % num)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 2

    @named_as('ys')
    class Y(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.aa = 777

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithYs() as cr:
            with YBuilder() as yb1:
                yb1.setattr('b', default=27, mc_set_unknown=True)
            cr.setattr('yb_ref', default=yb1, mc_set_unknown=True)

    cr = config(prod).ItemWithYs

    assert compare_repr(cr, _repr_attr_ref_configbuilder_expected_repr % dict(local_func=local_func()))
