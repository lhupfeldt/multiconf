# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

from collections import OrderedDict

from multiconf import ConfigItem  #, ConfigBuilder
from multiconf.multiconf import _RootEnvProxy, _ItemParentProxy


def _id_name_type(item):
    return repr(id(item)) + (', name=' + item.name if hasattr(item, 'name') else '') + ", " + repr(type(item))


def check_containment(start_item, level=0, prefix="  ", verbose=False):
    if isinstance(start_item, _RootEnvProxy):
        start_item = start_item.root_conf
    if isinstance(start_item, _ItemParentProxy):
        start_item = start_item._mc_item
    if verbose:
        print(prefix, 'level:', level, start_item.json(compact=True, builders=True))
    for key, item in start_item.items():
        if isinstance(item, OrderedDict):
            for _rkey, ritem in item.items():
                check_containment(ritem, level+1, "R ", verbose=verbose)
            continue

        if isinstance(item, (ConfigItem, _ItemParentProxy)):  #  and not isinstance(item, ConfigBuilder):
            ci = None
            try:
                ci = item.contained_in
                assert id(ci) == id(start_item)
            except Exception as ex:
                raise AssertionError(
                    "Containment error:\n" + repr(ex) + \
                    "  item: " + _id_name_type(item) + '\n' + \
                    "  item.contained_in: " + _id_name_type(ci) + '\n' + \
                    "  start_item: " + _id_name_type(start_item))
            check_containment(item, level+1, verbose=verbose)
