from multiconf.bases import get_bases


def test_bases():
    assert list(get_bases(object)) == [object]

    class Xx(object):
        pass

    assert list(get_bases(Xx)) == [Xx, object]
