from multiconf import mc_config, ConfigItem, ConfigBuilder
from multiconf.decorators import named_as
from multiconf.envs import EnvFactory

from .utils.check_containment import check_containment


ef = EnvFactory()
tst = ef.Env('tst')
prod = ef.Env('prod')


@named_as('outer')
class Outer(ConfigItem):
    def __init__(self, name):
        super().__init__()
        self.name = name


@named_as('outer_child')
class OuterChild(ConfigItem):
    @property
    def outer_name(self):
        outer = self.contained_in
        print('OuterChild.outer_name')
        print('  contained_in:', type(outer))
        _outer = self._mc_contained_in
        print('  _mc_contained_in', type(_outer))
        print("  name:", outer.name)
        return outer.name


@named_as('middle_child')
class MiddleChild(ConfigItem):
    def mc_init(self):
        super().mc_init()
        assert isinstance(self.contained_in, OuterChild)

    @property
    def outer_name(self):
        outer = self.contained_in.contained_in
        print('MiddleChild.outer_name')
        print('  contained_in:', type(self.contained_in))
        print('  contained_in.contained_in:', type(outer))
        _outer = self._mc_contained_in._mc_contained_in
        print('  _mc_contained_in:', type(self._mc_contained_in))
        print('  _mc_contained_in._mc_contained_in', type(_outer))
        print("  name:", outer.name)
        return outer.name


@named_as('inner_child')
class InnerChild(ConfigItem):
    def mc_init(self):
        super().mc_init()
        assert isinstance(self.contained_in, MiddleChild)

    @property
    def outer_name(self):
        outer = self.contained_in.contained_in.contained_in
        print('InnerChild.outer_name')
        print('  contained_in:', type(self.contained_in))
        print('  contained_in.contained_in:', type(self.contained_in.contained_in))
        print('  contained_in.contained_in.contained_in:', type(outer))
        _outer = self._mc_contained_in._mc_contained_in._mc_contained_in
        print('  _mc_contained_in:', type(self._mc_contained_in))
        print('  _mc_contained_in._mc_contained_in:', type(self._mc_contained_in._mc_contained_in))
        print('  _mc_contained_in._mc_contained_in._mc_contained_in:', type(_outer))
        print("  name:", outer.name)
        return outer.name


class OuterMaker(ConfigBuilder):
    def mc_build(self):
        with Outer('the-outer-one'):
            with OuterChild():
                MiddleChild()


def test_nested_builders():
    @mc_config(ef)
    def conf(_):
        with OuterMaker():
            with OuterChild():
                with MiddleChild():
                    InnerChild()

    cfg = conf.load(validate_properties=False, lazy_load=True)(tst).root_conf
    print(cfg)
    print('outer:', id(cfg.outer), 'contained_in:', id(cfg.outer.contained_in))

    outer_child = cfg.outer.outer_child
    print('\nouter_child:', id(outer_child), type(outer_child))
    assert isinstance(outer_child, OuterChild)
    print('    contained_in:', id(outer_child.contained_in), type(outer_child.contained_in))
    assert isinstance(outer_child.contained_in, Outer)
    assert outer_child.outer_name == 'the-outer-one'

    middle_child = outer_child.middle_child
    print('\nmiddle_child:', id(middle_child), type(middle_child))
    assert isinstance(middle_child, MiddleChild)
    print('    contained_in:', id(middle_child.contained_in), type(middle_child.contained_in))
    assert isinstance(middle_child.contained_in, OuterChild)
    print('    contained_in.contained_in:', id(middle_child.contained_in.contained_in), type(middle_child.contained_in.contained_in))
    assert isinstance(middle_child.contained_in.contained_in, Outer)
    assert middle_child.outer_name == 'the-outer-one'

    inner_child = middle_child.inner_child
    print('\ninner_child:', id(inner_child), type(inner_child))
    assert isinstance(inner_child, InnerChild)
    print('    contained_in:', id(inner_child.contained_in), type(inner_child.contained_in))
    assert isinstance(inner_child.contained_in, MiddleChild)
    print('    contained_in.contained_in:', id(inner_child.contained_in.contained_in), type(inner_child.contained_in.contained_in))
    assert isinstance(inner_child.contained_in.contained_in, OuterChild)
    print('    contained_in.contained_in.contained_in:',
          id(inner_child.contained_in.contained_in.contained_in), type(inner_child.contained_in.contained_in.contained_in))
    assert isinstance(inner_child.contained_in.contained_in.contained_in, Outer)
    assert inner_child.outer_name == 'the-outer-one'

    check_containment(cfg)
