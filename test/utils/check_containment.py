# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from multiconf.repeatable import Repeatable
from multiconf import ConfigItem, ConfigBuilder


def check_containment(start_item, level=0, prefix="  ", verbose=False):
    if verbose:
        print(prefix, 'level:', level, start_item.json(compact=True, builders=True))
    for key, item in start_item.items():
        if isinstance(item, Repeatable):
            for _rkey, ritem in item.items():
                check_containment(ritem, level+1, "R ", verbose=verbose)
            continue

        if isinstance(item, ConfigItem) and not isinstance(item, ConfigBuilder):
            ci = item.contained_in
            assert id(ci) == id(start_item), \
                "item.contained_in: " + repr(id(ci)) + (', contained in name=' + ci.name if hasattr(ci, 'name') else '') + \
                ", " + repr(type(ci)) + \
                ", start_item: " + repr(id(start_item)) + (', name=' + start_item.name if hasattr(start_item, 'name') else '') + \
                ", " + repr(type(start_item))
            check_containment(item, level+1, verbose=verbose)
