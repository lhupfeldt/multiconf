from multiconf.envs import EnvFactory
from multiconf import ConfigRoot, ConfigItem

efac = EnvFactory()
pp = efac.Env('pp')
prod = efac.Env('prod')


def test_init_inherited():
    class XBase(ConfigItem):
        def __init__(self, version=None):
            super(XBase, self).__init__()
            self.version = version

    class X1(XBase):
        # Deliberatly leave out version from super __init__
        def __init__(self, version):
            super(X1, self).__init__()
            self.version = version

    class X2(XBase):
        # Deliberatly leave out version from super __init__
        def __init__(self, version):
            super(X2, self).__init__()
            self.setattr('version', prod=version)

    with ConfigRoot(prod, efac) as project:
        X1(version=1)
        X2(version=1)

    assert project.X1.version == 1
    assert project.X2.version == 1

    with ConfigRoot(pp, efac) as project:
        X1(version=1)
        X2(version=1)

    assert project.X1.version == 1
    assert project.X2.version is None
