def get_bases(cls):
    yield cls
    for cls1 in cls.__bases__:
        yield from get_bases(cls1)
