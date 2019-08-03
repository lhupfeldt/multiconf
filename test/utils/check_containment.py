# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from collections import OrderedDict

from multiconf import AbstractConfigItem
from multiconf.multiconf import _RootEnvProxy, _ItemParentProxy


def _id_name_type(item):
    return repr(id(item)) + (', name=' + item.name if hasattr(item, 'name') else '') + ", " + repr(type(item))


_ex_msg_simple = """Containment error:
   item: {item}
   item.contained_in: {ci}
   start_item: {start_item}
"""

_ex_msg_complex = """Containment error:
   item: {item}
   item.contained_in (compared): {ci}
   start_item (compared): {start_item}

   item.contained_in (actual): {real_ci}
   start_item (actual): {real_start_item}
"""

def _mk_ex_msg(item, compared_ci, real_ci, compared_start_item, real_start_item):
    if real_ci or real_start_item:
        return _ex_msg_complex.format(
            item=_id_name_type(item), ci=_id_name_type(compared_ci), start_item=_id_name_type(compared_start_item),
            real_ci=_id_name_type(real_ci), real_start_item=_id_name_type(real_start_item))
    return _ex_msg_simple.format(item=_id_name_type(item), ci=_id_name_type(compared_ci), start_item=_id_name_type(compared_start_item))


def check_containment(start_item, level=0, prefix="  ", verbose=False):
    if isinstance(start_item, _RootEnvProxy):
        start_item = start_item.root_conf

    if verbose:
        print(prefix, 'level:', level, start_item.json(compact=True, builders=True))

    for key, item in start_item.items():
        if isinstance(item, OrderedDict):
            for _rkey, ritem in item.items():
                check_containment(ritem, level+1, "R ", verbose=verbose)
            continue

        if isinstance(item, AbstractConfigItem):
            ci = item.contained_in

            assert ci == start_item, _mk_ex_msg(item, ci, None, start_item, None)

            if type(ci) == type(start_item):
                # Either both proxy or both not proxy
                assert id(ci) == id(start_item), _mk_ex_msg(item, ci, None, start_item, None)
            elif isinstance(start_item, _ItemParentProxy):
                assert id(ci) == id(start_item._mc_proxied_item), _mk_ex_msg(item, ci, None, start_item._mc_proxied_item, start_item)
            elif isinstance(ci, _ItemParentProxy):
                assert id(ci._mc_proxied_item) == id(start_item), _mk_ex_msg(item, ci._mc_proxied_item, ci, start_item, None)
            else:
                raise Exception('Oops, should not get here')

            check_containment(item, level+1, verbose=verbose)
