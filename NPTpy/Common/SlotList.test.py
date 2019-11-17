
import random

from SlotList import *

sl = SlotList()

# Start empty
assert len(sl) == 0

# Append
assert sl.append('Hello 0') == 0 and len(sl) == 1
assert sl.append('Hello 1') == 1 and len(sl) == 2
assert sl.append('Hello 2') == 2 and len(sl) == 3
assert sl.append('Hello 3') == 3 and len(sl) == 4

# Accessible (only) by given IDs
assert sl[0] == 'Hello 0'
assert sl[1] == 'Hello 1'
assert sl[2] == 'Hello 2'
assert sl[3] == 'Hello 3'
assert sl[4] == None

# Deletion
del sl[1]
assert len(sl) == 3
assert sl[1] == None
assert sl[3] == 'Hello 3'
assert sl[4] == None

# Iteration
assert list(sl) == ['Hello 0', 'Hello 2', 'Hello 3']

# IDs should increment and old ones be invalid
newID = sl.append('Hello new')
assert newID > 3
assert sl[1] == None
assert sl[3] == 'Hello 3'
assert sl[newID] == 'Hello new'

# 'del' on old IDs should have no effect
del sl[1]
assert sl[1] == None
assert sl[3] == 'Hello 3'
assert sl[newID] == 'Hello new'

del sl

# Grow after deletion
sl = SlotList()
sl.append('0')
sl.append('1')
sl.append('2')
sl.append('3')
del sl[2]
newID  = sl.append('new')
newID2 = sl.append('new2')
assert sl[0] == '0'
assert sl[1] == '1'
assert sl[2] == None
assert sl[3] == '3'
assert sl[newID]  == 'new'
assert sl[newID2] == 'new2'

del sl

# Assign order should be the same as delete order (oldest first / LRU)
sl = SlotList()
sl.append('0')
sl.append('1')
sl.append('2')
sl.append('3')
del sl[3]
del sl[0]
assert sl[3] == None
assert sl[0] == None
a = sl.append('Hello a')
b = sl.append('Hello b')
# without LRU, we would expect 'b > a' (since 'b' is added later)
# with LRU, 'a' should go where '3' previously was, and 'b' where '0' was:
assert a > b

# deleteAll()
sl.deleteAll()
assert len(sl) == 0
assert sl.append('Test') > a

del sl

# Stress test
sl = SlotList()
d  = {}
for i in range(251):
    v     = f'Hello {i}'
    ID    = sl.append(v)
    d[ID] = v
for i in range(241):
    ID = random.randrange(0, 251)
    del sl[ID]
    if ID in d:
        del d[ID]
for i in range(2111):
    v     = f'Hello {251 + i}'
    ID    = sl.append(v)
    d[ID] = v
# check length and values
assert len(sl) == len(d)
for i in range(251 + 241 + 2111):
    assert sl[i] == d.get(i)
# also check iteration
sd = set(d.values())
for item in sl:
    assert item in sd
del sl
del d
del sd

# OK
print('OK')
