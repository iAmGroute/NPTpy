
from typing import Any

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

def short_str(x: Any, max_len = 20):
    assert max_len > 2, (x, max_len)
    s = str(x)
    l = len(s)
    return s if l <= max_len else s[:(max_len+1)//2-1] + '..' + s[l-max_len//2+1:]
    # NOTE: (-x//2) rounds down, as `-`` is inversion, while (a-x//2) rounds up, as `-` is subtraction

# Like weakref.ref but not weak, intended for consistency
# when mixing refs and weak refs in containers.
class Ref:
    def __init__(self, obj):
        self.obj = obj
    def __call__(self):
        return self.obj

