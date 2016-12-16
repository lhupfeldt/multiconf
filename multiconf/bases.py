def get_bases(cls):
    yield cls
    for cls1 in cls.__bases__:
        for cls2 in get_bases(cls1):
            yield cls2


def get_real_attr(obj, attr_name):
    for cls in get_bases(object.__getattribute__(obj, '__class__')):
        try:
            return object.__getattribute__(cls, attr_name)
        except AttributeError:
            pass
