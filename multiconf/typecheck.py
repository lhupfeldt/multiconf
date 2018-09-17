import typing

import typing_inspect


def type_check(item, attr_name, value):
    th_cls = typing.get_type_hints(item) if hasattr(item, '__annotations__') else {}
    try:
        tt = th_cls[attr_name]
    except KeyError:
        th_init = typing.get_type_hints(item.__init__)
        try:
            tt = th_init[attr_name]
        except KeyError:
            return

    allowed = typing_inspect.get_args(tt) or tt
    if not isinstance(value, allowed):
        one_of = "with one of following types" if isinstance(allowed, tuple) else "of type"
        return "Expected value {one_of}: {exp}, got {got} for {cls}.{member}".format(
            one_of=one_of, exp=allowed, got=type(value), cls=item.__class__.__name__, member=attr_name)

    return None
