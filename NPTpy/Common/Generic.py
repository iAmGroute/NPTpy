
from typing import Any, Callable, Container, Generic, Iterable, Protocol, Set, Tuple, TypeVar, Union

T = TypeVar('T')

Predicate = Callable[[T], bool]

SupportsIn = Union[Container[T], Iterable[T]]

class SupportsFileno(Protocol):
    def fileno(self) -> int: ...

FileDescriptorLike = Union[int, SupportsFileno]

def nop(*args: object, **kwargs: object):
    # pylint: disable=unused-argument
    return None

def identity(v): # type: ignore
    return v     # type: ignore

def identityMany(*args): # type: ignore
    return args          # type: ignore

def toTuple(thing: Union[Any, Tuple[object, ...]]) -> Tuple[object, ...]:
    if   thing is None:            return ()
    elif isinstance(thing, tuple): return thing
    else:                          return (thing,)

def find(iterable: Iterable[T], f: Predicate[T]):
    for item in iterable:
        if f(item):
            return item
    return None

def runAndRemove(set_: Set[T], f: Predicate[T]):
    dead = {
        x
        for x in set_
        if f(x)
    }
    set_ -= dead
    return len(dead)

def short_str(x: object, max_len: int = 20):
    assert max_len > 2, (x, max_len)
    s = str(x)
    l = len(s)
    return s if l <= max_len else s[:(max_len+1)//2-1] + '..' + s[l-max_len//2+1:]
    # NOTE: (-x//2) rounds down, as `-`` is inversion, while (a-x//2) rounds up, as `-` is subtraction

# Like weakref.ref but not weak, intended for consistency
# when mixing refs and weak refs in containers.
class Ref(Generic[T]):
    def __init__(self, obj: T):
        self.obj = obj
    def __call__(self):
        return self.obj
