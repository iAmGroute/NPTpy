
def nop(*args, **kwargs):
    # pylint: disable=unused-argument
    return None

def identity(v):
    return v

def identityMany(*args):
    return args

def toTuple(thing):
    if   thing is None:        return ()
    elif type(thing) is tuple: return thing
    else:                      return (thing,)

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

# Like weakref.ref but not weak, intended for consistency
# when mixing refs and weak refs in countainers.
class Ref:
    def __init__(self, obj):
        self.obj = obj
    def __call__(self):
        return self.obj

