

def noop(*args, **kwargs):
    pass

def identity(v):
    return v

def identityMany(*args):
    return args

def toTuple(thing):
    return thing if isinstance(thing, tuple) else (thing,)

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

class Counter:
    def __init__(self, initialValue=0):
        self.value = initialValue
    def __call__(self, increment=1):
        result = self.value
        self.value += increment
        return result

