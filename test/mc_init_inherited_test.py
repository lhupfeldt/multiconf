from multiconf.envs import EnvFactory
from multiconf import ConfigRoot, ConfigItem

efac = EnvFactory()
pp = efac.Env('pp')
prod = efac.Env('prod')


def test_mc_init_inherited():
    class XBase(ConfigItem):
        def mc_init(self):
            super(XBase, self).mc_init()
            self.version = 1

    class X1(XBase):
        def mc_init(self):
            super(X1, self).mc_init()
            self.version = 2

    class X2(XBase):
        def mc_init(self):
            super(X2, self).mc_init()
            self.setattr('version', prod=3)

    with ConfigRoot(prod, efac) as project:
        X1()
        X2()

    print "project.X1.version:", project.X1.version
    assert project.X1.version == 2
    assert project.X2.version == 3

    with ConfigRoot(pp, efac) as project:
        X1()
        X2()

    assert project.X1.version == 2
    assert project.X2.version == 1
