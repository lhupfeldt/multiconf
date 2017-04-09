# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from __future__ import print_function

try:
    import demjson
    decode = demjson.JSON(strict=True).decode
except ImportError:
    def decode(_string):
        return True


from .utils import replace_ids, replace_ids_builder, to_compact, to_compact_excluded
from .utils import py3_tc
from .check_containment import check_containment


def _compare_json(
        item, expected_json, replace_builders, dump_builders, sort_attributes,
        test_decode, test_containment, test_excluded, test_compact,
        expect_num_errors, show_all_envs, depth):
    try:
        compact_json = item.json(compact=True, builders=dump_builders, sort_attributes=sort_attributes, show_all_envs=show_all_envs, depth=depth)
        full_json = item.json(builders=dump_builders, sort_attributes=sort_attributes, show_all_envs=show_all_envs, depth=depth)
        if replace_builders:
            if test_compact:
                compact_json_replaced = replace_ids_builder(compact_json)
            full_json_replaced = replace_ids_builder(full_json)
        else:
            if test_compact:
                compact_json_replaced = replace_ids(compact_json)
            full_json_replaced = replace_ids(full_json)

        expected_json %= {'type_or_class': py3_tc}
        compact_expected_json = None

        assert full_json_replaced == expected_json, "Error: full json differs"

        if test_compact:
            if test_excluded:
                compact_expected_json = to_compact_excluded(expected_json)
            else:
                compact_expected_json = to_compact(expected_json)
            assert compact_json_replaced == compact_expected_json, "Error: compact json differs"

        assert item.num_json_errors() == expect_num_errors, \
            "item.num_json_errors(): " + repr(item.num_json_errors()) + ", expect_num_errors: " + repr(expect_num_errors)
    except AssertionError as ex:
        print(str(ex))
        all_envs_msg = "all envs ---" if show_all_envs else ""

        print('--- full ids replaced ---', all_envs_msg)
        print(full_json_replaced)

        print('--- full expected ---', all_envs_msg)
        print(expected_json)

        print('--- full original ---', all_envs_msg)
        print(full_json)

        if test_compact and compact_expected_json:
            print('--- compact ids replaced ---', all_envs_msg)
            print(compact_json_replaced)

            print('--- compact expected ---', all_envs_msg)
            print(compact_expected_json)

            print('--- compact original ---', all_envs_msg)
            print(compact_json)

        return False

    if test_decode:
        try:
            assert decode(compact_json)
            assert decode(full_json)
        except AssertionError:
            all_envs_msg = "all envs ---" if show_all_envs else ""
            print('FAILED DECODE')
            print('--- compact original ---', all_envs_msg)
            print(compact_json)

            print('--- full original ---', all_envs_msg)
            print(full_json)

            return False

    if test_containment:
        check_containment(item)

    return True


def compare_json(item, expected_json, replace_builders=False, dump_builders=True, sort_attributes=True,
                 test_decode=False, test_containment=True, test_excluded=False, test_compact=True,
                 expect_num_errors=0, expected_all_envs_json=None, expect_all_envs_num_errors=None, depth=None):
    res2 = True
    res = _compare_json(
        item, expected_json, replace_builders, dump_builders, sort_attributes,
        test_decode, test_containment, test_excluded, test_compact,
        expect_num_errors, show_all_envs=False, depth=depth)

    if expected_all_envs_json:
        expect_num_errors = expect_all_envs_num_errors or expect_num_errors
        res2 = _compare_json(
            item, expected_all_envs_json, replace_builders, dump_builders, sort_attributes,
            test_decode, test_containment=False, test_excluded=test_excluded, test_compact=False,
            expect_num_errors=expect_num_errors, show_all_envs=True, depth=depth)

    return res and res2
