# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

import sys
from collections import OrderedDict
import pytest

from multiconf import mc_config, ConfigItem, RepeatableConfigItem, InvalidUsageException, ConfigException, ConfigBuilder, MC_REQUIRED
from multiconf.decorators import nested_repeatables, named_as
from multiconf.envs import EnvFactory

from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithName, ItemWithAA


ef = EnvFactory()
pp = ef.Env('pp')
prod = ef.Env('prod')

ef2_prod = EnvFactory()
prod2 = ef2_prod.Env('prod')


_json_dump_configbuilder_expected_json_full = """{
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
    "_mc_ConfigBuilder_YBuilder default-builder": {
        "__class__": "YBuilder",
        "__id__": 0000,
        "b": 27,
        "start": 1,
        "y_children": {
            "Hugo": "#ref, id: 0000"
        },
        "_mc_ConfigBuilder_YBuilder default-builder": {
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

_json_dump_configbuilder_expected_json_repeatable_item = """{
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

_json_dump_configbuilder_dont_dump_expected_json_full = """{
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


def test_json_dump_configbuilder():
    class YBuilder(ConfigBuilder):
        def __init__(self, start=1):
            super(YBuilder, self).__init__()
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
            super(Y, self).__init__(mc_key=mc_key)
            self.name = mc_key
            self.server_num = server_num

    @named_as('y_children')
    class YChild(RepeatableConfigItem):
        def __init__(self, mc_key, a):
            super(YChild, self).__init__(mc_key=mc_key)
            self.name = mc_key
            self.a = a

    @mc_config(ef)
    def _(_):
        with ItemWithYs() as cr:
            with YBuilder() as yb1:
                yb1.setattr('b', default=27, mc_set_unknown=True)
                YChild('Hugo', a=10)
                with YBuilder(start=3) as yb2:
                    yb2.setattr('c', default=28, mc_set_unknown=True)
                    YChild('Hanna', a=11)
                    YChild('Herbert', a=12)

    cr = ef.config(prod).ItemWithYs

    assert compare_json(cr, _json_dump_configbuilder_expected_json_full, replace_builders=True, test_decode=True)
    assert compare_json(cr.ys['server2'], _json_dump_configbuilder_expected_json_repeatable_item, replace_builders=True, test_decode=True)

    assert compare_json(cr, _json_dump_configbuilder_dont_dump_expected_json_full, replace_builders=False, dump_builders=False, test_decode=True)
    assert compare_json(cr.ys['server2'], _json_dump_configbuilder_expected_json_repeatable_item, replace_builders=False, dump_builders=False, test_decode=True)




def test_json_dump_with_builders_containment_check():
    @named_as('inners')
    class InnerItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super(InnerItem, self).__init__(mc_key=mc_key)
            self.name = mc_key

    class InnerBuilder(ConfigBuilder):
        def __init__(self):
            super(InnerBuilder, self).__init__()

        def mc_build(self):
            InnerItem('innermost')

    @nested_repeatables('inners')
    class MiddleItem(RepeatableConfigItem):
        def __init__(self, mc_key):
            super(MiddleItem, self).__init__(mc_key=mc_key)
            self.name = mc_key

    class MyMiddleBuilder(ConfigBuilder):
        def __init__(self, name):
            super(MyMiddleBuilder, self).__init__()
            self.name = name

        def mc_build(self):
            with MiddleItem(self.name):
                pass

    class MyOuterBuilder(ConfigBuilder):
        def __init__(self):
            super(MyOuterBuilder, self).__init__()

        def mc_build(self):
            with MyMiddleBuilder('base'):
                InnerBuilder()

    @nested_repeatables('MiddleItems')
    class MyOuterItem(ConfigItem):
        pass

    @mc_config(ef2_prod)
    def _(_):
        with ItemWithName() as cr:
            cr.name = 'myp'
            with MyOuterItem():
                MyOuterBuilder()

    cr = ef2_prod.config(prod2).ItemWithName
    cr.json(builders=True)
    # TODO
    assert True
