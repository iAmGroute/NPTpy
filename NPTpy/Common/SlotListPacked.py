# SlotListPacked:
#   A container similar to SlotList,
#   with the advantage of faster sequential iteration,
#   as the items are stored contiguously in memory.
#   This comes at a disadvantage of requiring an additional level of redirection
#   for random accesses, implemented with a SlotList.
#

from typing import Generic, Iterable, List, Optional, TypeVar

from .Generic  import short_str
from .SlotList import SlotList


T = TypeVar('T')


class SlotListPacked(Generic[T]):

    def __init__(self, values: Iterable[T] = (), cap_hint: int = 2):
        self._keys:    List[int]     = []
        self._vals:    List[T]       = []
        self._indexes: SlotList[int] = SlotList(cap_hint=cap_hint)
        self.extend(values)

    def __len__(self):
        return len(self._keys)

    def capacity(self):
        return self._indexes.capacity()

    def __bool__(self):
        return bool(self._keys)

    def items(self):
        return ( (k, v) for k, v in zip(self._keys, self._vals) )

    def keys(self):
        return iter(self._keys)

    def values(self):
        return iter(self._vals)

    __iter__ = values

    def items_mutable(self):
        'Similar to `items` but allows you to delete the last yielded item'
        i      = 0
        k_prev = -1
        while i < len(self._keys):
            k = self._keys[i]
            v = self._vals[i]
            if k == k_prev:
                i += 1
            else:
                k_prev = k
                yield k, v

    def __str__(self):
        return str(self._vals)

    def __repr__(self):
        return 'SlotListPacked(' + repr(self._vals) + ')'

    def __format__(self, fmt: str):
        return format(self._vals, fmt)

    def dbg_str(self, max_len: int = 10):
        'String representation, meant for debugging'
        return (
            'SLP{[' + ' '.join(f'({k}|{short_str(repr(v), max_len)})' for k, v in self.items()) + '], ' +
            self._indexes.dbg_str(max_len) + '}'
        )

    def grow(self):
        self._indexes.grow()

    def append(self, value: T):
        index = len(self._keys)
        key   = self._indexes.append(index)
        self._keys.append(key)
        self._vals.append(value)
        return key

    def extend(self, values: Iterable[T]):
        for v in values:
            self.append(v)

    def clear(self, cap_hint: int = 2):
        self._indexes.clear(cap_hint=cap_hint)
        self._keys.clear()
        self._vals.clear()

    def __getitem__(self, key: int):
        index = self._indexes[key]
        return self._vals[index] if index is not None else None

    def __setitem__(self, key: int, value: Optional[T]):
        if value is None:
            del self[key]
            return
        index = self._indexes[key]
        if index is None:
            raise IndexError(f'key {key} does not exist or has been superseded')
        self._vals[index] = value

    def _delete(self, index: int, key: int):
        repl_key                = self._keys[-1]
        repl_val                = self._vals[-1]
        self._keys[index]       = repl_key
        self._vals[index]       = repl_val
        self._keys.pop(-1)
        self._vals.pop(-1)
        self._indexes[repl_key] = index
        del self._indexes[key]

    def __delitem__(self, key: int):
        index = self._indexes[key]
        if index is None:
            return
        self._delete(index, key)

    def pop(self, key: int):
        index = self._indexes[key]
        if index is None:
            return None
        res = self._vals[index]
        self._delete(index, key)
        return res

