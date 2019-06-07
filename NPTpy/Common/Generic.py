
def find(iterable, f):
    for item in iterable:
        if f(item):
            return item
    return None
