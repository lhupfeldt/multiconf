def get_bases(cls):
    yield cls
    for cls1 in cls.__bases__:
        for cls2 in get_bases(cls1):
            yield cls2
