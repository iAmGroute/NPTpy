
from SlotList import *

sl = SlotList(2)

assert len(sl) == 0

assert sl.append('Hello')   == 0  and len(sl) == 1
assert sl.append('World')   == 1  and len(sl) == 2
assert sl.append('Hello 2') == 2  and len(sl) == 3
assert sl.append('World 2') == 3  and len(sl) == 4
assert sl.append('World 3') == -1 and len(sl) == 4

assert sl[0] == 'Hello'
assert sl[1] == 'World'
assert sl[2] == 'Hello 2'
assert sl[3] == 'World 2'

del sl[1]
assert sl[1] == None
assert sl[5] == None

# Gen should increment
assert sl.append('Hello 3') == 5
assert sl[1] == None
assert sl[5] == 'Hello 3'
assert sl[9] == None

# Del on old gen should have no effect
del sl[1]
assert sl[1] == None
assert sl[5] == 'Hello 3'

# Assign order should be the same as delete order (oldest first)

del sl[3]
del sl[0]
assert sl[3] == None
assert sl[0] == None

assert sl.append('Hello 4') == 7

del sl[5]
del sl[2]

assert sl.append('Hello 5') == 4
assert sl.append('Hello 6') == 9
assert sl.append('Hello 7') == 6

# Check assignments

for i in range(4):
    assert sl[i] == None, '@ i == {0}'.format(i)

assert sl[4] == 'Hello 5'
assert sl[5] == None
assert sl[6] == 'Hello 7'
assert sl[7] == 'Hello 4'

assert sl[8] == None
assert sl[9] == 'Hello 6'
assert sl[10] == None
assert sl[11] == None

for i in range(12, 128):
    assert sl[i] == None, '@ i == {0}'.format(i)

# No more space left
assert sl.append('World 4') == -1


# Delete all slots

del sl[4]

del sl[6]
del sl[7]

del sl[9]

assert sl.append('Hello 8') == 8
for i in range(128):
    assert sl[i] == ('Hello 8' if i == 8 else None), '@ i == {0}'.format(i)

del sl[8]

assert sl.append('Hello 9') == 10
for i in range(128):
    assert sl[i] == ('Hello 9' if i == 10 else None), '@ i == {0}'.format(i)

del sl[10]

for i in range(128):
    assert sl[i] == None, '@ i == {0}'.format(i)


print('OK')
