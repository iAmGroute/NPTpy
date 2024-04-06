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

    # In C, <nextFree> and <value> could be in a union
    def __init__(self, myID: int, nextFree: int, value: Optional[T]):
        self.myID     = myID
        self.nextFree = nextFree
        self.val      = value

    # Note: python containers call repr() on the items they contain,
    #       even when str() or format() is called on them
    def __repr__(self):
        return '({0}|{1}|{2})'.format(self.myID, self.nextFree, repr(self.val))

    def __bool__(self):
        return self.val is not None


class SlotList(Generic[T]):

    def __init__(self, values: Iterable[T] = [], initial_capacity = 0):
        assert initial_capacity >= 2, initial_capacity # TODO: can we allow == 1?
        self._count     = 0
        self._slots     : List[_Slot[T]] \
                        = [_Slot(i, i+1, None) for i in range(initial_capacity)]
        self._slots[-1].nextFree = -1
        self._firstFree = 0
        self._lastFree  = initial_capacity - 1
        self.extend(values)

    def __len__(self):
        return self._count

    def capacity(self):
        return len(self._slots)

    def isFull(self):
        return len(self) == self.capacity()

    def __bool__(self):
        return bool(len(self))

    def __iter__(self):
        yield from (
            slot.val
            for slot in self._slots
            if slot.val is not None
        )

    def iterKV(self):
        yield from (
            (slot.myID, slot.val)
            for slot in self._slots
            if slot.val is not None
        )

    def listIDs(self):
        return [s.myID for s in self._slots if s]

    def prettyPrint(self, f: Callable[[T], str]):
        result = [f(val) for val in self]
        return '[' + ', '.join(result) + ']'

    def __str__(self):
        return self.prettyPrint(repr)

    def __repr__(self):
        return 'SlotList' + repr(self._slots)

    def __format__(self, fmt: str):
        return self.prettyPrint(lambda x: format(x, fmt))

    def fixFreeIndexes(self):
        indexes = [i for i in range(self.capacity()) if not self._slots[i]]
        self.firstFree = indexes[0]
        for i in range(len(indexes) - 1):
            self._slots[indexes[i]].nextFree = indexes[i + 1]
        self.lastFree  = indexes[-1]

    def grow(self):
        assert self.isFull()
        cap     = self.capacity()
        new_cap = 2 * cap
        mask    = new_cap - 1
        for i in range(cap):
            slot              = self._slots[i]
            self._slots.append(slot)
            newSlot           = _Slot(slot.myID + cap, -1, None)
            index             = newSlot.myID & mask
            self._slots[index] = newSlot
        assert self.capacity() == new_cap, (self, new_cap)
        self.fixFreeIndexes()

    def append(self, value: T):
        if self.firstFree < 0:
            self.grow()
        index          = self.firstFree
        slot           = self._slots[index]
        slot.val       = value
        self.firstFree = slot.nextFree
        self._count    += 1
        return slot.myID

    def extend(self, values: Iterable[T]):
        for v in values:
            self.append(v)

    def _getIndex(self, ID: int):
        index = ID & (self.capacity() - 1)
        slot  = self._slots[index]
        return index if slot.myID == ID else -1

    def _deleteByIndex(self, index: int):
        slot            = self._slots[index]
        if slot:
            self._count -= 1
        slot.myID      += self.capacity()
        slot.nextFree   = -1
        slot.val        = None
        if self.firstFree >= 0:
            self._slots[self.lastFree].nextFree = index
        else:
            self.firstFree = index
        self.lastFree = index

    def deleteAll(self):
        maxID = max(self._slots, key=lambda s: s.myID).myID
        maxID = (maxID | 1) + 1
        self.__init__()
        self._slots[0].myID = maxID
        self._slots[1].myID = maxID + 1

    def __getitem__(self, ID: int):
        index = self._getIndex(ID)
        return self._slots[index].val if index >= 0 else None

    def __setitem__(self, ID: int, value: Optional[T]):
        if value is None:
            del self[ID]
            return
        index = self._getIndex(ID)
        if index < 0:
            raise IndexError(f'ID {ID} does not exist or has been superseded')
        self._slots[index].val = value

    def __delitem__(self, ID: int):
        index = self._getIndex(ID)
        if index < 0:
            return
        self._deleteByIndex(index)

    def pop(self, ID: int):
        index = self._getIndex(ID)
        if index < 0:
            return None
        res = self._slots[index].val
        self._deleteByIndex(index)
        return res

