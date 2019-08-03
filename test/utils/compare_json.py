# Copyright (c) 2012 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

try:
    import demjson
    decode = demjson.JSON(strict=True).decode
except ImportError:
    def decode(_string):
        return True


from .utils import replace_ids as _replace_ids, replace_ids_builder, to_compact, to_compact_excluded
from .check_containment import check_containment


def _compare_json(
        item, expected_json, replace_builders, dump_builders, sort_attributes,
        test_decode, test_containment, test_excluded, test_compact, property_methods,
        expect_num_errors, warn_nesting, show_all_envs, depth, replace_ids, replace_address):
    try:
        compact_json = item.json(
            compact=True, property_methods=property_methods, builders=dump_builders, sort_attributes=sort_attributes, warn_nesting=warn_nesting,
            show_all_envs=show_all_envs, depth=depth, persistent_ids=not replace_ids)
        full_json = item.json(property_methods=property_methods, builders=dump_builders, sort_attributes=sort_attributes, warn_nesting=warn_nesting,
                              show_all_envs=show_all_envs, depth=depth, persistent_ids=not replace_ids)

        if replace_ids or replace_address:
            assert replace_ids, "You must use 'replace_ids' if using 'replace_address'"
            if replace_builders:
                if test_compact:
                    compact_json_replaced = replace_ids_builder(compact_json, address=replace_address)
                full_json_replaced = replace_ids_builder(full_json, address=replace_address)
            else:
                if test_compact:
                    compact_json_replaced = _replace_ids(compact_json, address=replace_address)
                full_json_replaced = _replace_ids(full_json, address=replace_address)
        else:
            compact_json_replaced = compact_json
            full_json_replaced = full_json

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

        def show(msg, replaced_ids, json):
            msg += " - ids replaced" if replaced_ids else ""
            msg += " - all envs" if show_all_envs else ""
            print('---', msg, '---')
            print(json)

        show('full', replace_ids, full_json_replaced)
        show('full expected', False, expected_json)
        if replace_ids:
            show('full original', False, full_json)

        if test_compact and compact_expected_json:
            show('compact', replace_ids, compact_json_replaced)
            show('compact expected', False, compact_expected_json)
            if replace_ids:
                show('compact original', False, compact_json)

        import platform
        if platform.python_implementation() != 'PyPy':
            return False
        # TODO PyPy is at Python 3.6 level and does not implement dict as ordered, continue with other checks

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
                 test_decode=False, test_containment=True, test_excluded=False, test_compact=True, property_methods=True,
                 expect_num_errors=0, warn_nesting=False, expected_all_envs_json=None, expect_all_envs_num_errors=None, depth=None,
                 replace_ids=True, replace_address=False):
    res = True
    if expected_json:
        res = _compare_json(
            item, expected_json, replace_builders, dump_builders, sort_attributes,
            test_decode, test_containment, test_excluded, test_compact, property_methods,
            expect_num_errors, warn_nesting, show_all_envs=False, depth=depth,
            replace_ids=replace_ids, replace_address=replace_address)

    res2 = True
    if expected_all_envs_json:
        expect_num_errors = expect_all_envs_num_errors or expect_num_errors
        res2 = _compare_json(
            item, expected_all_envs_json, replace_builders, dump_builders, sort_attributes,
            test_decode, test_containment=False, test_excluded=test_excluded, test_compact=False, property_methods=property_methods,
            expect_num_errors=expect_num_errors, warn_nesting=warn_nesting, show_all_envs=True, depth=depth,
            replace_ids=replace_ids, replace_address=replace_address)

    return res and res2
