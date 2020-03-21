# SlotMap:
#   A container based on a variable length list,
#   useful for fast allocation, random access, random deallocation and fast unordered iteration.
#   An ID is returned on allocation, which is unique
#   until the ID counter overflows (does not happen in Python).
#   Allocated item slots are always stored in consecutive memory locations,
#   and an index SlotList remaps the given IDs to actual indexes.

from .SlotList import SlotList

class Slot:

    def __init__(self, myID, value):
        self.myID = myID
        self.val  = value

    # Note: python containers call repr() on the items they contain,
    #       even when str() or format() is called on them
    def __repr__(self):
        return '({0}|{1})'.format(self.myID, repr(self.val))


class Iterator:

    def __init__(self, mySlotMap):
        self.subiter = iter(mySlotMap.slots)

    def __iter__(self):
        return self

    def __next__(self):
        slot = next(self.subiter)
        return slot.val


class IteratorKV:

    def __init__(self, mySlotMap):
        self.slots  = mySlotMap.slots
        self.i      = 0
        self.lastID = -1

    def __iter__(self):
        return self

    def __next__(self):
        i = self.i
        if i >= len(self.slots): raise StopIteration
        if self.slots[i].myID == self.lastID:
            i += 1
            if i >= len(self.slots): raise StopIteration
            self.i = i
        slot = self.slots[i]
        self.lastID = slot.myID
        return slot.myID, slot.val


class SlotMap:

    def __init__(self, values=None):
        self.slots   = []
        self.indexes = SlotList()
        if values:
            for value in values:
                self.append(value)

    def __len__(self):
        return len(self.slots)

    def __bool__(self):
        return bool(self.slots)

    def __iter__(self):
        return Iterator(self)

    def iterKV(self):
        return IteratorKV(self)

    def listIDs(self):
        return self.indexes.listIDs()

    def prettyPrint(self, f):
        result = [f(val) for val in self]
        return '[' + ', '.join(result) + ']'

    def __str__(self):
        return self.prettyPrint(repr)

    def __repr__(self):
        return 'SlotMap' + repr(self.slots)

    def __format__(self, formatstr):
        return self.prettyPrint(lambda x: format(x, formatstr))

    def append(self, value):
        slot      = Slot(0, value)
        index     = len(self.slots)
        self.slots.append(slot)
        slot.myID = self.indexes.append(index)
        return slot.myID

    def _delete(self, index, ID):
        replacement       = self.slots[-1]
        self.slots[index] = replacement
        self.slots.pop()
        self.indexes[replacement.myID] = index
        del self.indexes[ID]

    def deleteAll(self):
        self.slots = []
        self.indexes.deleteAll()

    def __getitem__(self, ID):
        index = self.indexes[ID]
        return self.slots[index].val if index is not None else None

    def __setitem__(self, ID, value):
        if value is None:
            del self[ID]
            return
        index = self.indexes[ID]
        if index is None:
            raise IndexError(f'ID {ID} does not exist or has been superseded')
        self.slots[index].val = value

    def __delitem__(self, ID):
        index = self.indexes[ID]
        if index is None:
            return
        self._delete(index, ID)

    def pop(self, ID):
        index = self.indexes[ID]
        if index is None:
            return None
        res = self.slots[index].val
        self._delete(index, ID)
        return res

