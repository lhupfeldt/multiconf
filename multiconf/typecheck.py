import sys


_min_major_version = 3
_min_minor_version = 6
_min_patch_version = 1

_major_version = sys.version_info[0]
_minor_version = sys.version_info[1]
_patch_version = sys.version_info[2]

unsup_version_msg = "Type checking only supported from Python {}.{}.{}".format(
    _min_major_version, _min_minor_version, _min_patch_version)


def typing_vcheck():
    """Return True if version requirement is satisfied."""
    return _major_version > _min_major_version or (
        _major_version == _min_major_version and _minor_version >= _min_minor_version) or (
            _major_version == _min_major_version and _minor_version == _min_minor_version and _patch_version >= _min_patch_version)


if typing_vcheck():
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
