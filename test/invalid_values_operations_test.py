# Copyright (c) 2015 Lars Hupfeldt Nielsen, Hupfeldt IT
# All rights reserved. This work is under a BSD license, see LICENSE.TXT.

from multiconf.values import MC_REQUIRED, MC_TODO, McInvalidValue


def test_mc_required_str_plus(capsys):
    assert isinstance("abc" + MC_REQUIRED, McInvalidValue)
    assert isinstance(MC_REQUIRED + "abc", McInvalidValue)


def test_mc_required_int_plus(capsys):
    assert isinstance(1 + MC_REQUIRED, McInvalidValue)
    assert isinstance(MC_REQUIRED + 1, McInvalidValue)


def test_mc_todo_str_plus(capsys):
    assert isinstance("abc" + MC_TODO, McInvalidValue)
    assert isinstance(MC_TODO + "abc", McInvalidValue)


def test_mc_todo_int_plus(capsys):
    assert isinstance(1 + MC_TODO, McInvalidValue)
    assert isinstance(MC_TODO + 1, McInvalidValue)


def test_mc_required_list_append(capsys):
    ll = MC_REQUIRED.append(17)
    assert isinstance(ll, McInvalidValue)
    # TODO, should this be handled?
    # ll = [1].append(MC_REQUIRED)
    # assert isinstance(ll, McInvalidValue)


def test_mc_todo_list_append(capsys):
    ll = MC_TODO.append(18)
    assert isinstance(ll, McInvalidValue)
    # TODO, should this be handled?
    # ll = [3].append(MC_TODO)
    # assert isinstance(ll, McInvalidValue)
