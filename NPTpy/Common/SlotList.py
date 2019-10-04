# SlotList:
#   A container based on a fixed length array,
#   useful for fast allocation, random access and random deallocation.
#   An ID is returned on allocation, which is unique
#   until the generation counter overflows (does not happen in Python).
#   Allocated item slots are not stored in consecutive memory locations,
#   as the empty slots can be found anywhere in the array.

class Slot:

    # In C, nextFreeIndex and value could be in a union
    def __init__(self, generation, nextFreeIndex, value):
        self.gen  = generation
        self.next = nextFreeIndex
        self.val  = value

    # Note: python containers call repr() on the items they contain,
    #       even when str() or format() is called on them
    def __repr__(self):
        return '({0}|{1}|{2})'.format(self.gen, self.next, repr(self.val))


class SlotList_Iterator:

    def __init__(self, mySlotList):
        self.subiter = iter(mySlotList.slots)

    def __next__(self):
        while True:
            slot = next(self.subiter)
            if slot.val:
                return slot.val


class SlotList:

    def __init__(self, capacityLog2=1, values=None):
        self.capacityLog2 = capacityLog2
        self.capacity     = 1 << capacityLog2
        self.slots        = [Slot(0, i+1, None) for i in range(self.capacity - 1)] + [Slot(0, -1, None)]
        self.firstFree    = 0
        self.lastFree     = self.capacity - 1
        if values:
            for value in values:
                self.append(value)

    def __len__(self):
        count = 0
        for slot in self.slots:
            if slot.val:
                count += 1
        return count

    def __bool__(self):
        return len(self) > 0

    def __iter__(self):
        return SlotList_Iterator(self)

    def prettyPrint(self, f):
        result = '['
        for val in self:
            result += f(val)
            result += ', '
        if len(result) > 2:
            result = result[:-2]
        result += ']'
        return result

    def __str__(self):
        return self.prettyPrint(repr)

    def __repr__(self):
        return 'SlotList' + repr(self.slots)

    def __format__(self, formatstr):
        return self.prettyPrint(lambda x: format(x, formatstr))


    def append(self, value):
        resultID = -1
        index = self.firstFree
        if index >= 0:
            slot = self.slots[index]
            self.firstFree = slot.next
            slot.next = -1
            slot.val  = value
            resultID  = index + (slot.gen << self.capacityLog2)
        return resultID


    def getIndex(self, ID):

        index = ID & (self.capacity - 1)
        gen   = ID >> self.capacityLog2

        slot = self.slots[index]

        if gen != slot.gen:
            return -1

        return index


    def __getitem__(self, ID):
        index = self.getIndex(ID)
        return self.slots[index].val if index >= 0 else None


    def __setitem__(self, ID, value):

        if value == None:
            del self[ID]
            return

        index = self.getIndex(ID)
        if index < 0:
            raise IndexError('ID does not exist or has been superseded')

        self.slots[index].val = value


    def deleteByIndex(self, index):

        slot = self.slots[index]
        slot.gen += 1
        slot.val  = None

        if self.firstFree >= 0:
            self.slots[self.lastFree].next = index
        else:
            self.firstFree = index

        self.lastFree = index


    def __delitem__(self, ID):
        index = self.getIndex(ID)
        if index < 0:
            return
        self.deleteByIndex(index)


    def deleteAll(self):
        for i in range(self.capacity):
            self.deleteByIndex(i)

