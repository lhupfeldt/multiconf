# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

try:
    import demjson
    decode = demjson.JSON(strict=True).decode
except ImportError:
    def decode(_string):
        return True


from .utils import replace_ids, replace_ids_builder, to_compact
from .check_containment import check_containment


def compare_json(item, expected_json, replace_builders=False, dump_builders=True, test_decode=False, test_containment=True):
    try:
        compact_json = item.json(compact=True, builders=dump_builders)
        full_json = item.json(builders=dump_builders)
        if replace_builders:
            compact_json_replaced = replace_ids_builder(compact_json)
            full_json_replaced = replace_ids_builder(full_json)
        else:            
            compact_json_replaced = replace_ids(compact_json)
            full_json_replaced = replace_ids(full_json)

        assert compact_json_replaced == to_compact(expected_json)
        assert full_json_replaced == expected_json

    except:
        print('--- full ids replaced ---')
        print(full_json_replaced)

        print('--- full expected ---')
        print(expected_json)

        print('--- full original ---')
        print(full_json)

        print('--- compact ids replaced ---')
        print(compact_json_replaced)

        print('--- compact expected ---')
        print(to_compact(expected_json))

        print('--- compact original ---')
        print(compact_json)

        raise

    if test_decode:
        try:
            assert decode(compact_json)
            assert decode(full_json)
        except:
            print('FAILED DECODE')
            print('--- compact original ---')
            print(compact_json)

            print('--- full original ---')
            print(full_json)

    if test_containment:
        check_containment(item)
