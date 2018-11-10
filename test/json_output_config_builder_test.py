# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, ConfigBuilder
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.compare_json import compare_json
from .utils.utils import local_func
from .utils.tstclasses import ItemWithName


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


_json_dump_configbuilder1_all_envs_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server1",
            "server_num": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {}
        }
    },
    "mc_ConfigBuilder_YBuilder default-builder": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1,
        "y_children": {
            "Hugo": "#ref, id: 0000"
        }
    },
    "aaa": 1,
    "aaa #static": true
}"""

def test_json_dump_configbuilder1():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super().__init__()
            self.start = start

        def mc_build(self):
            for num in range(self.start, self.start + self.contained_in.aaa):
                Y('server%d' % num, server_num=num)

    @nested_repeatables('ys')
    class ItemWithYs(ConfigItem):
        aaa = 1

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
                # with YBuilder() as yb2:
                #     yb2.setattr('start', default=3, pp=117)
                #     yb2.setattr('c', default=28, mc_set_unknown=True)

    cr = config(prod).ItemWithYs

    assert compare_json(cr, None, replace_builders=True, test_decode=True,
                        expected_all_envs_json=_json_dump_configbuilder1_all_envs_expected_json_full)


_json_dump_configbuilder2_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server1",
            "server_num": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {
                "server3": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "name": "server3",
                    "server_num": 3,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 11,
                            "name": "Hanna"
                        },
                        "Herbert": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 12,
                            "name": "Herbert"
                        }
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y",
                    "__id__": 0000,
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
            "__class__": "Y",
            "__id__": 0000,
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
    "mc_ConfigBuilder_YBuilder default-builder": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1,
        "y_children": {
            "Hugo": "#ref, id: 0000"
        },
        "mc_ConfigBuilder_YBuilder default-builder": {
            "__class__": "YBuilder",
            "__id__": 0000,
            "c": 28,
            "start": 3,
            "y_children": {
                "Hanna": "#ref, id: 0000",
                "Herbert": "#ref, id: 0000"
            }
        },
        "ys": {
            "server3": "#ref, id: 0000",
            "server4": "#ref, id: 0000"
        }
    },
    "aaa": 2,
    "aaa #static": true
}"""

_json_dump_configbuilder2_all_envs_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server1",
            "server_num": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {
                "server117": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "#item does not exist in": "Env('prod')",
                    "name": {
                        "pp": "server117",
                        "prod #no value for Env('prod')": true
                    },
                    "name #multiconf attribute": true,
                    "server_num": {
                        "pp": 117,
                        "prod #no value for Env('prod')": true
                    },
                    "server_num #multiconf attribute": true,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 11,
                            "name": "Hanna"
                        },
                        "Herbert": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 12,
                            "name": "Herbert"
                        }
                    },
                    "ys": {}
                },
                "server118": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "#item does not exist in": "Env('prod')",
                    "name": {
                        "pp": "server118",
                        "prod #no value for Env('prod')": true
                    },
                    "name #multiconf attribute": true,
                    "server_num": {
                        "pp": 118,
                        "prod #no value for Env('prod')": true
                    },
                    "server_num #multiconf attribute": true,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                },
                "server3": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "#item does not exist in": "Env('pp')",
                    "name": {
                        "pp #no value for Env('pp')": true,
                        "prod": "server3"
                    },
                    "name #multiconf attribute": true,
                    "server_num": {
                        "pp #no value for Env('pp')": true,
                        "prod": 3
                    },
                    "server_num #multiconf attribute": true,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "#item does not exist in": "Env('pp')",
                    "name": {
                        "pp #no value for Env('pp')": true,
                        "prod": "server4"
                    },
                    "name #multiconf attribute": true,
                    "server_num": {
                        "pp #no value for Env('pp')": true,
                        "prod": 4
                    },
                    "server_num #multiconf attribute": true,
                    "y_children": {
                        "Hanna": "#ref, id: 0000",
                        "Herbert": "#ref, id: 0000"
                    },
                    "ys": {}
                }
            }
        },
        "server2": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server2",
            "server_num": 2,
            "y_children": {
                "Hugo": "#ref, id: 0000"
            },
            "ys": {
                "server117": "#ref, id: 0000",
                "server118": "#ref, id: 0000",
                "server3": "#ref, id: 0000",
                "server4": "#ref, id: 0000"
            }
        }
    },
    "mc_ConfigBuilder_YBuilder default-builder": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1,
        "y_children": {
            "Hugo": "#ref, id: 0000"
        },
        "mc_ConfigBuilder_YBuilder default-builder": {
            "__class__": "YBuilder",
            "__id__": 0000,
            "c": 28,
            "start": {
                "pp": 117,
                "prod": 3
            },
            "start #multiconf attribute": true,
            "y_children": {
                "Hanna": "#ref, id: 0000",
                "Herbert": "#ref, id: 0000"
            }
        },
        "ys": {
            "server117": "#ref, id: 0000",
            "server118": "#ref, id: 0000",
            "server3": "#ref, id: 0000",
            "server4": "#ref, id: 0000"
        }
    },
    "aaa": 2,
    "aaa #static": true
}"""

_json_dump_configbuilder2_expected_json_repeatable_item = """{
    "__class__": "Y",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "name": "server2",
    "server_num": 2,
    "y_children": {
        "Hugo": {
            "__class__": "YChild",
            "__id__": 0000,
            "a": 10,
            "name": "Hugo"
        }
    },
    "ys": {
        "server3": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server3",
            "server_num": 3,
            "y_children": {
                "Hanna": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 11,
                    "name": "Hanna"
                },
                "Herbert": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 12,
                    "name": "Herbert"
                }
            },
            "ys": {}
        },
        "server4": {
            "__class__": "Y",
            "__id__": 0000,
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

_json_dump_configbuilder2_dont_dump_expected_json_full = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "name": "server1",
            "server_num": 1,
            "y_children": {
                "Hugo": {
                    "__class__": "YChild",
                    "__id__": 0000,
                    "a": 10,
                    "name": "Hugo"
                }
            },
            "ys": {
                "server3": {
                    "__class__": "Y",
                    "__id__": 0000,
                    "name": "server3",
                    "server_num": 3,
                    "y_children": {
                        "Hanna": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 11,
                            "name": "Hanna"
                        },
                        "Herbert": {
                            "__class__": "YChild",
                            "__id__": 0000,
                            "a": 12,
                            "name": "Herbert"
                        }
                    },
                    "ys": {}
                },
                "server4": {
                    "__class__": "Y",
                    "__id__": 0000,
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
            "__class__": "Y",
            "__id__": 0000,
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
    "aaa": 2,
    "aaa #static": true
}"""


def test_json_dump_configbuilder2():
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

    assert compare_json(cr, _json_dump_configbuilder2_expected_json_full, replace_builders=True, test_decode=True,
                        expected_all_envs_json=_json_dump_configbuilder2_all_envs_expected_json_full)
    assert compare_json(cr.ys['server2'], _json_dump_configbuilder2_expected_json_repeatable_item, replace_builders=True, test_decode=True)

    assert compare_json(cr, _json_dump_configbuilder2_dont_dump_expected_json_full, replace_builders=False, dump_builders=False, test_decode=True)
    assert compare_json(cr.ys['server2'], _json_dump_configbuilder2_expected_json_repeatable_item, replace_builders=False, dump_builders=False, test_decode=True)


def test_json_dump_with_builders_containment_check():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.name = mc_key

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super().__init__(mc_key=mc_key)
            self.name = mc_key

    class MyMiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super().__init__()
            self.name = name

        def mc_build(self):
            with MiddleItem(self.name):
                pass

    class MyOuterBuilder(ConfigBuilder):
        def __init__(self):
            super().__init__()

        def mc_build(self):
            with MyMiddleBuilder('base'):
                InnerBuilder()

    @nested_repeatables('MiddleItems')
    class MyOuterItem(ConfigItem):
        pass

    @mc_config(ef2_prod, load_now=True)
    def config(_):
        with ItemWithName() as cr:
            cr.name = 'myp'
            with MyOuterItem():
                MyOuterBuilder()

    cr = config(prod2).ItemWithName
    cr.json(builders=True)
    # TODO
    assert True


_json_dump_attr_ref_configbuilder_expected_json = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "yb_ref": "#ref later builder <class 'test.json_output_config_builder_test.%(local_func)sYBuilder'>",
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "aa": 777
        },
        "server2": {
            "__class__": "Y",
            "__id__": 0000,
            "aa": 777
        }
    },
    "aaa": 2,
    "aaa #static": true
}"""

_json_dump_attr_ref_configbuilder_expected_json_with_builders = """{
    "__class__": "ItemWithYs",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "yb_ref": "#ref later builder, id: 0000",
    "ys": {
        "server1": {
            "__class__": "Y",
            "__id__": 0000,
            "aa": 777
        },
        "server2": {
            "__class__": "Y",
            "__id__": 0000,
            "aa": 777
        }
    },
    "mc_ConfigBuilder_YBuilder default-builder": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1
    },
    "aaa": 2,
    "aaa #static": true
}"""

def test_json_dump_attr_ref_configbuilder():
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

    assert compare_json(cr, _json_dump_attr_ref_configbuilder_expected_json % dict(local_func=local_func()),
                        replace_builders=False, dump_builders=False, test_decode=True)
    assert compare_json(cr, _json_dump_attr_ref_configbuilder_expected_json_with_builders, replace_builders=True)
