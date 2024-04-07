
import random

from typing import Type, Union

from .SlotList       import SlotList
from .SlotListPacked import SlotListPacked


def run_container(Container: Union[Type[SlotList], Type[SlotListPacked]]):

    sl = Container()

    # Start empty
    assert len(sl) == 0

    # Append
    assert sl.append('Hello 0') == 0 and len(sl) == 1
    assert sl.append('Hello 1') == 1 and len(sl) == 2
    assert sl.append('Hello 2') == 2 and len(sl) == 3
    assert sl.append('Hello 3') == 3 and len(sl) == 4
    assert sl.append('Hello 4') == 4 and len(sl) == 5

    # Accessible (only) by given IDs
    assert sl[0] == 'Hello 0'
    assert sl[1] == 'Hello 1'
    assert sl[2] == 'Hello 2'
    assert sl[3] == 'Hello 3'
    assert sl[4] == 'Hello 4'
    assert sl[5] == None

    # Deletion
    del    sl[1]
    assert len(sl) == 4
    assert sl[0] == 'Hello 0'
    assert sl[1] == None # deleted
    assert sl[2] == 'Hello 2'
    assert sl[3] == 'Hello 3'
    assert sl[4] == 'Hello 4'
    assert sl[5] == None # never allocated
    assert len(sl) == 4

    # Deletion by setting to None
    sl[4] = None
    assert len(sl) == 3
    assert sl[0] == 'Hello 0'
    assert sl[1] == None
    assert sl[2] == 'Hello 2'
    assert sl[3] == 'Hello 3'
    assert sl[4] == None # just deleted
    assert sl[5] == None
    assert len(sl) == 3

    # Iteration
    assert sorted(sl) == ['Hello 0', 'Hello 2', 'Hello 3']
    # Key iteration
    assert sorted(sl.keys()) == [0, 2, 3]
    # Value iteration
    assert sorted(sl.values()) == ['Hello 0', 'Hello 2', 'Hello 3']
    # Key-Value iteration
    assert sorted(sl.items()) == [(0, 'Hello 0'), (2, 'Hello 2'), (3, 'Hello 3')]
    # Plain iteration same as value iteration
    assert list(sl) == list(sl.values())

    # Keys should increment and old ones be invalid
    new_key = sl.append('Hello new')
    assert new_key > 4
    assert len(sl) == 4
    assert sl[0] == 'Hello 0'
    assert sl[1] == None
    assert sl[2] == 'Hello 2'
    assert sl[3] == 'Hello 3'
    assert sl[4] == None
    assert sl[new_key] == 'Hello new'

    # 'del' on old IDs should have no effect
    del    sl[1]
    del    sl[4]
    sl[1] = None
    sl[4] = None
    assert len(sl) == 4
    assert sl[0] == 'Hello 0'
    assert sl[1] == None
    assert sl[2] == 'Hello 2'
    assert sl[3] == 'Hello 3'
    assert sl[4] == None
    assert sl[new_key] == 'Hello new'

    # pop()
    assert sl.pop(1) == None
    assert len(sl) == 4
    assert sl.pop(3) == 'Hello 3'
    assert len(sl) == 3
    assert sl[0] == 'Hello 0'
    assert sl[1] == None
    assert sl[2] == 'Hello 2'
    assert sl[3] == None
    assert sl[4] == None
    assert sl[new_key] == 'Hello new'

    del sl

    # Initial values as constructor parameter
    ivs = ['World 0', 'World 1', 'World 2', 'World 3']
    sl  = Container(ivs)
    assert sorted(sl) == ivs

    del sl

    # Iteration
    original = list(range(15, 777, 2))
    sl       = Container(original)
    assert list(sl.items()) == [(i, original[i]) for i in range(len(original))]

    # Key-Value iteration allows deletion of the current item
    original = list(range(15, 55, 5))
    sl       = Container(original)
    items    = []
    for k, v in sl.items_mutable():
        if k % 3 == 0:
            del sl[k]
        items.append(v)
    items.sort()
    assert items == original

    expected = [(i, original[i]) for i in range(len(original)) if i % 3 != 0]
    items    = list(sl.items())
    items.sort()
    assert items == expected

    del sl

    # Key-Value iteration doesn't crash if the container is changed between iterations
    original = list(range(5, 25, 2))
    sl       = Container(original)
    i = 0
    for k, v in sl.items():
        del sl[2]
        if   i == 1:
            sl.append(1111)
        elif i >= 3:
            del sl[4]
            del sl[5]
            del sl[6]
        i += 1

    items = list(sl)
    items.append(original[2])
    items.append(original[4])
    items.append(original[5])
    items.append(original[6])
    items.sort()
    assert items == original + [1111]

    del sl
    # Grow after deletion
    sl = Container()
    sl.append('0')
    sl.append('1')
    sl.append('2')
    sl.append('3')
    del sl[2]
    new_key  = sl.append('new')
    newID2 = sl.append('new2')
    assert sl[0] == '0'
    assert sl[1] == '1'
    assert sl[2] == None
    assert sl[3] == '3'
    assert sl[new_key]  == 'new'
    assert sl[newID2] == 'new2'

    del sl

    # Assign order should be the same as delete order (oldest first / FIFO)
    sl = Container()
    sl.append('t0')
    sl.append('t1')
    sl.append('t2')
    sl.append('t3')
    del sl[3]
    del sl[0]
    assert sl[3] == None
    assert sl[0] == None
    a = sl.append('Hello a')
    b = sl.append('Hello b')
    # with LIFO, we would expect `b > a` (since `b` is added later)
    # with FIFO, `a` should go where `t3` previously was, and `b` where `t0` was:
    assert a > b

    # clear()
    sl.clear()
    assert len(sl) == 0
    assert sl.append('Test') > a

    del sl

    # Stress test
    sl = Container()
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


def test_SlotList():
    run_container(SlotList)


def test_SlotListPacked():
    run_container(SlotListPacked)

