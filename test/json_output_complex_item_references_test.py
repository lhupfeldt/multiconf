# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf import mc_config, ConfigItem
from multiconf.envs import EnvFactory

from .utils.utils import local_func
from .utils.compare_json import compare_json
from .utils.tstclasses import ItemWithAA, ItemWithName


ef = EnvFactory()
pprd = ef.Env('pprd')
prod = ef.Env('prod')


_json_dump_pprd_attr_dict_ref_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "pprd"
    },
    "aa": 0,
    "Ref1": {
        "__class__": "Ref1",
        "__id__": 0000,
        "aa": {
            "a": "#ref, id: 0000"
        },
        "bb": {
            "a": "<class 'test.json_output_complex_item_references_test.%(local_func)sRef0'>"
        },
        "a": 3,
        "a #static": true,
        "mm": "#ref self, id: 0000",
        "mm #calculated": true,
        "nn": "<class 'test.json_output_complex_item_references_test.%(local_func)sRef0'>"
    },
    "Ref2": {
        "__class__": "Ref2",
        "__id__": 0000,
        "r1mmnn": 1114,
        "r1mmnn #calculated": true
    }
}"""

_json_dump_prod_attr_dict_ref_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "Ref1": {
        "__class__": "Ref1",
        "__id__": 0000,
        "aa": {
            "a": "#ref, id: 0000"
        },
        "bb": {
            "a": "#ref, id: 0000"
        },
        "a": 3,
        "a #static": true,
        "mm": "#ref self, id: 0000",
        "mm #calculated": true,
        "nn": "#ref self, id: 0000",
        "nn #calculated": true
    },
    "Ref2": {
        "__class__": "Ref2",
        "__id__": 0000,
        "r1mmnn": 6,
        "r1mmnn #calculated": true
    }
}"""

_json_dump_all_envs_attr_dict_ref_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "MC_NO_ENV"
    },
    "aa": 0,
    "Ref1": {
        "__class__": "Ref1",
        "__id__": 0000,
        "aa": {
            "a": "#ref, id: 0000"
        },
        "bb": {
            "pprd": {
                "a": "<class 'test.json_output_complex_item_references_test.%(local_func)sRef0'>"
            },
            "prod": {
                "a": "#ref, id: 0000"
            }
        },
        "bb #multiconf attribute": true,
        "a": 3,
        "a #static": true,
        "mm": "#ref self, id: 0000",
        "mm #calculated": true,
        "nn": {
            "pprd": "<class 'test.json_output_complex_item_references_test.%(local_func)sRef0'>",
            "prod": "#ref self, id: 0000",
            "prod #calculated": true
        },
        "nn #multiconf env specific @property": true
    },
    "Ref2": {
        "__class__": "Ref2",
        "__id__": 0000,
        "r1mmnn": {
            "pprd": 1114,
            "pprd #calculated": true,
            "prod": 6,
            "prod #calculated": true
        },
        "r1mmnn #multiconf env specific @property": true
    }
}"""

def test_json_dump_attr_dict_ref_item():
    class Ref0(ConfigItem):
        a = 1111

    class Ref1(ConfigItem):
        a = 3

        @property
        def mm(self):
            return self.aa['a']

        @property
        def nn(self):
            return self.bb['a']

    class Ref2(ConfigItem):
        """Reference attributes on dicts of ref1 objects"""
        @property
        def r1mmnn(self):
            return self.contained_in.Ref1.mm.a + self.contained_in.Ref1.nn.a

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA(aa=0) as cr:
            with Ref1() as ref1:
                ref1.setattr('aa', mc_set_unknown=True, default={'a': ref1})
                ref1.setattr('bb', mc_set_unknown=True, default={'a': ref1}, pprd={'a': Ref0})
            ref2 = Ref2()
        return ref1, ref2

    cfg = config(pprd)
    ref1, ref2 = cfg.mc_config_result
    assert compare_json(cfg.ItemWithAA, _json_dump_pprd_attr_dict_ref_item_expected_json % dict(local_func=local_func()))
    assert ref1.mm == ref1
    assert ref1.nn == Ref0
    assert ref2.r1mmnn == 1114

    cfg = config(prod)
    ref1, ref2 = cfg.mc_config_result
    assert compare_json(cfg.ItemWithAA, _json_dump_prod_attr_dict_ref_item_expected_json,
                        expected_all_envs_json=_json_dump_all_envs_attr_dict_ref_item_expected_json % dict(local_func=local_func()))
    assert ref1.mm == ref1
    assert ref1.nn == ref1
    assert ref2.r1mmnn == 6


_json_dump_attr_list_ref_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 0,
    "Ref1": {
        "__class__": "Ref1",
        "__id__": 0000,
        "aa": [
            "#ref, id: 0000"
        ],
        "bb": [
            "#ref, id: 0000"
        ],
        "a": 3,
        "a #static": true,
        "mm": "#ref self, id: 0000",
        "mm #calculated": true,
        "nn": "#ref self, id: 0000",
        "nn #calculated": true
    },
    "Ref2": {
        "__class__": "Ref2",
        "__id__": 0000,
        "r1mmnn": 6,
        "r1mmnn #calculated": true
    }
}"""

def test_json_dump_attr_list_ref_item():
    class Ref1(ConfigItem):
        a = 3

        @property
        def mm(self):
            return self.aa[0]

        @property
        def nn(self):
            return self.bb[0]

    class Ref2(ConfigItem):
        """Reference attributes on lists of ref1 objects"""
        @property
        def r1mmnn(self):
            return self.contained_in.Ref1.mm.a + self.contained_in.Ref1.nn.a

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA(aa=0) as cr:
            with Ref1() as ref1:
                ref1.setattr('aa', mc_set_unknown=True, default=[ref1])
                ref1.setattr('bb', mc_set_unknown=True, default=[ref1])
            ref2 = Ref2()
        return ref1, ref2

    cr = config(prod).ItemWithAA
    ref1, ref2 = cr.root_conf.mc_config_result
    assert compare_json(cr, _json_dump_attr_list_ref_item_expected_json)
    assert ref1.mm == ref1
    assert ref1.nn == ref1
    assert ref2.r1mmnn == 6


_json_dump_attr_tuple_ref_item_expected_json = """{
    "__class__": "ItemWithAA",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": 1,
    "Ref1": {
        "__class__": "Ref1",
        "__id__": 0000,
        "aa": [
            "#ref, id: 0000",
            "#ref, id: 0000"
        ],
        "bb": [
            "#ref, id: 0000",
            "#ref, id: 0000"
        ],
        "mm": "#ref self, id: 0000",
        "mm #calculated": true,
        "nn": "#ref, id: 0000",
        "nn #calculated": true,
        "xx": 3,
        "xx #static": true
    },
    "Ref2": {
        "__class__": "Ref2",
        "__id__": 0000,
        "r1mmnn": 4,
        "r1mmnn #calculated": true
    }
}"""

def test_json_dump_attr_tuple_ref_item():
    class Ref1(ConfigItem):
        xx = 3

        @property
        def mm(self):
            return self.aa[0]

        @property
        def nn(self):
            return self.bb[1]

    class Ref2(ConfigItem):
        """Reference attributes on tuples of ref1 objects"""
        @property
        def r1mmnn(self):
            return self.contained_in.Ref1.mm.xx + self.contained_in.Ref1.nn.aa

    @mc_config(ef, load_now=True)
    def config(root):
        with ItemWithAA(aa=1) as cr:
            with Ref1() as ref1:
                ref1.setattr('aa', mc_set_unknown=True, default=(ref1, cr))
                ref1.setattr('bb', mc_set_unknown=True, default=(ref1, cr))
            ref2 = Ref2()
        return ref1, ref2

    cr = config(prod).ItemWithAA
    ref1, ref2 = cr.root_conf.mc_config_result
    assert compare_json(cr, _json_dump_attr_tuple_ref_item_expected_json)
    assert ref1.mm == ref1
    assert ref1.nn == cr
    assert ref2.r1mmnn == 4


_json_dump_ref_outside_exluded_item1_expected_json = """{
    "__class__": "Ref1",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "#outside-ref: Excluded: <class 'test.utils.tstclasses.ItemWithName'>, name: Tootsi"
}"""

def test_json_dump_ref_outside_exluded_item1():
    class Ref1(ItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName('Tootsi') as it:
            it.mc_select_envs(exclude=[prod])
        with Ref1() as ref1:
            ref1.aa = it

    cr = config(prod)
    ref1 = cr.Ref1
    assert compare_json(ref1, _json_dump_ref_outside_exluded_item1_expected_json)


_json_dump_ref_outside_exluded_item_partially_set_name_attribute_mc_required_expected_json = """{
    "__class__": "Ref1",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "#outside-ref: Excluded: <class 'test.utils.tstclasses.ItemWithName'>"
}"""

def test_json_dump_ref_outside_exluded_item_partially_set_name_attribute_mc_required():
    class Ref1(ItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with ItemWithName() as it:
            it.mc_select_envs(exclude=[prod])
            it.setattr('name', pprd='Tootsi')
        with Ref1() as ref1:
            ref1.aa = it

    cr = config(prod)
    ref1 = cr.Ref1
    assert compare_json(ref1, _json_dump_ref_outside_exluded_item_partially_set_name_attribute_mc_required_expected_json)


_json_dump_ref_outside_exluded_item_partially_set_name_attribute_non_existing_expected_json = """{
    "__class__": "Ref1",
    "__id__": 0000,
    "env": {
        "__class__": "Env",
        "name": "prod"
    },
    "aa": "#outside-ref: Excluded: <class 'multiconf.multiconf.ConfigItem'>"
}"""

def test_json_dump_ref_outside_exluded_item_partially_set_name_attribute_non_existing():
    class Ref1(ItemWithAA):
        pass

    @mc_config(ef, load_now=True)
    def config(_):
        with ConfigItem() as it:
            it.mc_select_envs(exclude=[prod])
            it.setattr('name', pprd='Tootsi', mc_set_unknown=True)
        with Ref1() as ref1:
            ref1.aa = it

    cr = config(prod)
    ref1 = cr.Ref1
    assert compare_json(ref1, _json_dump_ref_outside_exluded_item_partially_set_name_attribute_non_existing_expected_json)
