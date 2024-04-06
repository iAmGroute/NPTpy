# SlotList:
#   A container based on a variable length list,
#   useful for fast allocation, random access and random deallocation.
#   An ID is returned on allocation, which is unique
#   until the ID counter overflows (does not happen in Python).
#   Allocated item slots are not stored in consecutive memory locations,
#   as the empty slots can be found anywhere in the array.

from typing import Callable, Generic, Iterable, List, Optional, TypeVar


T = TypeVar('T')


class _Slot(Generic[T]):

    def __init__(self, key: int, next_free: int, val: Optional[T]):
        self.key        = key
        self.next_free  = next_free
        self.val        = val

    # Note: python containers call repr() on the items they contain,
    #       even when str() or format() is called on them
    def __repr__(self):
        return '({0}|{1}|{2})'.format(self.key, self.next_free, repr(self.val))

    def __bool__(self):
        return self.val is not None


class SlotList(Generic[T]):

    def __init__(self, values: Iterable[T] = [], initial_capacity_hint = 2):
        assert initial_capacity_hint >= 0, initial_capacity_hint
        cap = 1 << (initial_capacity_hint-1).bit_length() # hint = 0 -> cap = 2
        self._count      = 0
        self._slots      : List[_Slot[T]] \
                         = [_Slot(i, i+1, None) for i in range(cap)]
        self._slots[-1].next_free = -1
        self._first_free = 0
        self._last_free  = cap - 1
        self.extend(values)

    def __len__(self):
        return self._count

    def capacity(self):
        return len(self._slots)

    def __bool__(self):
        return bool(len(self))

    def items(self):
        return ( (s.key, s.val) for s in self._slots if s )

    def keys(self):
        return (  s.key         for s in self._slots if s )

    def values(self):
        return (         s.val  for s in self._slots if s )

    __iter__ = values

    def pretty_print(self, f: Callable[[T], str]):
        result = [f(val) for val in self]
        return '[' + ', '.join(result) + ']'

    def __str__(self):
        return self.pretty_print(repr)

    def __repr__(self):
        return 'SlotList' + repr(self._slots)

    def __format__(self, fmt: str):
        return self.pretty_print(lambda x: format(x, fmt))

    def _free_list_append(self, index):
        if self._first_free >= 0:
            self._slots[self._last_free].next_free = index
        else:
            self._first_free = index
        self._last_free = index

    def grow(self):
        cap     = self.capacity()
        new_cap = 2 * cap
        mask    = new_cap - 1
        for i in range(cap):
            # link the current slot to its "mirror" index
            slot               = self._slots[i]
            self._slots.append(slot)
            #
            # replace one of the two, based on the key, with an empty slot
            newSlot            = _Slot(slot.key + cap, slot.next_free, None)
            index              = newSlot.key & mask
            self._slots[index] = newSlot
            #
            # case 1: newSlot comes before slot, both are empty
            #  -> newSlot is part of the free list, slot isn't
            #  -> we need to add slot to free list
            #
            # case 2: slot comes before newSlot, both are empty
            #  -> slot is part of the free list, newSlot isn't
            #  -> we need to add newSlot to free list
            #
            # case 1, 2 -> add the latter to the free list
            #
            # case 3: slot isn't empty
            #  -> none are part of the free list
            #  -> we need to add newSlot to the end of the free list
            #
            last_empty_index = index if slot else (index | cap)
            self._slots[last_empty_index].next_free = -1
            self._free_list_append(last_empty_index)
        #
        assert self.capacity() == new_cap, (self, new_cap)

    def append(self, value: T):
        if self._first_free < 0:
            self.grow()
        index             = self._first_free
        slot              = self._slots[index]
        slot.val          = value
        self._first_free  = slot.next_free
        self._count      += 1
        return slot.key

    def extend(self, values: Iterable[T]):
        for v in values:
            self.append(v)

    def _get_index(self, key: int):
        index = key & (self.capacity() - 1)
        slot  = self._slots[index]
        return index if slot.key == key else -1

    def _delete_by_index(self, index: int):
        slot            = self._slots[index]
        assert slot, (self, index, slot)
        slot.key       += self.capacity()
        slot.next_free  = -1
        slot.val        = None
        self._free_list_append(index)

    def clear(self, new_capacity_hint = 2):
        max_key = max(self._slots, key = lambda s: s.key).key
        hint = new_capacity_hint if new_capacity_hint > 0 else self.capacity()
        self._slots.clear()
        self.__init__(initial_capacity_hint=hint)
        key = (max_key | (self.capacity() - 1)) + 1
        for s in self._slots:
            s.key = key
            key  += 1

    def __getitem__(self, key: int):
        index = self._get_index(key)
        return self._slots[index].val if index >= 0 else None

    def __setitem__(self, key: int, value: Optional[T]):
        if value is None:
            del self[key]
            return
        index = self._get_index(key)
        if index < 0:
            raise IndexError(f'key {key} does not exist or has been superseded')
        self._slots[index].val = value

    def __delitem__(self, key: int):
        index = self._get_index(key)
        if index < 0:
            return
        self._delete_by_index(index)

    def pop(self, key: int):
        index = self._get_index(key)
        if index < 0:
            return None
        res = self._slots[index].val
        self._delete_by_index(index)
        return res

