from multiconf.envs import EnvFactory
from multiconf import mc_config, ConfigItem

efac = EnvFactory()
pp = efac.Env('pp')
prod = efac.Env('prod')


def test_init_inherited():
    class XBase(ConfigItem):
        def __init__(self, version=None):
            super().__init__()
            self.version = version

    class X1(XBase):
        # Deliberatly leave out version from super __init__
        def __init__(self, version):
            super().__init__()
            self.version = version

    class X2(XBase):
        # Deliberatly leave out version from super __init__
        def __init__(self, version):
            super().__init__()
            self.setattr('version', prod=version)

    @mc_config(efac, load_now=True)
    def config(_):
        with ConfigItem():
            X1(version=1)
            X2(version=1)

    project = config(prod).ConfigItem
    assert project.X1.version == 1
    assert project.X2.version == 1

    @mc_config(efac, load_now=True)
    def config(_):
        with ConfigItem():
            X1(version=1)
            X2(version=1)

    project = config(pp).ConfigItem
    assert project.X1.version == 1
    assert project.X2.version is None
