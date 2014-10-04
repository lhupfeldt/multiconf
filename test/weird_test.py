from multiconf import ConfigRoot
from multiconf.envs import EnvFactory

efac = EnvFactory()

dev1 = efac.Env('dev1')
devlocal = efac.Env('devlocal')

g_dev = efac.EnvGroup('g_dev', dev1, devlocal)


def test_devlocal():
    # This gives a weird ordering of setattr args?
    with ConfigRoot(devlocal, efac) as rt:
        rt.setattr('xx', default=None, devlocal='good', g_dev='bad')

    assert rt.xx == 'good'
