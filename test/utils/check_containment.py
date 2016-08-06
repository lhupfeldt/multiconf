# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.repeatable import Repeatable
from multiconf import ConfigItem, ConfigBuilder


def check_containment(start_item, level=0, prefix="  "):
    for key, item in start_item.items():
        if isinstance(item, Repeatable):
            for _rkey, ritem in item.items():
                check_containment(ritem, level+1, "R ")
        if isinstance(item, ConfigItem) and not isinstance(item, ConfigBuilder):
            assert id(item.contained_in) == id(start_item), \
                "item.contained_in: " + repr(id(item.contained_in)) + ('name=' + item.contained_in.name if hasattr(item.contained_in, 'name') else '') + \
                repr(type(item.contained_in)) + \
                ", start_item: " + repr(id(start_item)) + ('name=' + start_item.name if hasattr(start_item, 'name') else '') + \
                repr(type(start_item))
            check_containment(item, level+1)
