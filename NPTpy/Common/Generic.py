

def noop(*args, **kwargs):
    pass


def identity(v):
    return v


def find(iterable, f):
    for item in iterable:
        if f(item):
            return item
    return None


def runAndRemove(aSet, f):
    dead = set()
    for item in aSet:
        if f(item):
            dead.add(item)
    aSet -= dead
    return len(dead)

