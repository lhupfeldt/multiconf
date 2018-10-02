# Copyright (c) 2018 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from .utils import replace_ids as _replace_ids, replace_ids_builder, to_compact


def compare_repr(item, expected_repr, replace_builders=False, replace_ids=True, replace_address=True):
    got_repr = repr(item)

    try:
        if replace_ids:
            if replace_builders:
                got_repr_replaced = replace_ids_builder(got_repr, address=replace_address)
            else:
                got_repr_replaced = _replace_ids(got_repr, address=replace_address)
        else:
            got_repr_replaced = got_repr

        assert got_repr_replaced == expected_repr, "Error: repr differs"

    except AssertionError as ex:
        print(str(ex))

        def show(msg, replaced_ids, got_repr):
            msg += " - ids replaced" if replaced_ids else ""
            print('---', msg, '---')
            print(got_repr)

        show('got repr', replace_ids, got_repr_replaced)
        show('expected repr', False, expected_repr)
        if replace_ids:
            show('got repr original', False, got_repr)

        return False

    return True
