from multiconf.bases import get_bases, get_real_attr


def test_bases():
    assert list(get_bases(object)) == [object]

    class Xx(object):
        pass

    assert list(get_bases(Xx)) == [Xx, object]


def test_get_real_attr():
    class Xx1(object):
        a = 0

    class Xx2(Xx1):
        pass

    get_real_attr(Xx2(), 'a')
