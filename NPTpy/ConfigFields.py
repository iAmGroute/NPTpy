import sys
import traceback

def serialize(thing):
    r = {}
    for fname, ftype, _ in thing.fields:
        try:
            r[fname] = ftype.serialize(thing, fname)
        except Exception as e:
            print(repr(e))
    return r


def update(thing, data):
    for fname, ftype, writable in thing.fields:
        if fname in data:
            assert writable, 'Not writable: ' + fname
            ftype.update(thing, fname, data[fname])


class Field:

    def __init__(self, default=None, keyName=''):
        self.default = default
        self.keyName = keyName

    def decode(self, val):
        return val

    def verify(self, val):
        return val

    def encode(self, val):
        return val

    def get(self, obj, attr):
        return getattr(obj, attr)

    def set(self, obj, attr, val):
        setattr(obj, attr, val)

    def read(self, val):
        return self.verify(self.decode(val))

    def write(self, val):
        return self.encode(self.verify(val))

    def apply(self, val):
        return self.encode(self.verify(self.decode(val)))

    def serialize(self, obj, attr):
        return self.write(self.get(obj, attr))

    def update(self, obj, attr, val):
        return self.set(obj, attr, self.read(val))


class SlotList(Field):

    def verify(self, val):
        assert type(val) is list
        for kv in val:
            k = kv['k']
            v = kv['v']
            assert type(k) is int
            assert k >= 0
            assert v is None or type(v) is dict
        return val

    def serialize(self, obj, attr):
        sl = Field.get(self, obj, attr)
        return [ {'k': item.myID, 'v': serialize(item) } for item in sl ]

    def update(self, obj, attr, val):
        val = self.read(val)
        sl = Field.get(self, obj, attr)
        for kv in val:
            k = kv['k']
            v = kv['v']
            try:
                if v is None:
                    del sl[k]
                else:
                    update(sl[k], v)
            except Exception as e:
                print(repr(e))


class Constant(Field):

    def __init__(self, keyName, val):
        Field.__init__(self, val, keyName)

    def decode(self, val):
        return self.default

    def verify(self, val):
        return self.default

    def encode(self, val):
        return self.default

    def get(self, object, attribute):
        return self.default

    def set(self, object, attribute, val):
        setattr(object, attribute, self.default)


class Bool(Field):

    def verifier(self, val):
        assert val is True or False
        return val


class Int(Field):

    def verify(self, val):
        assert type(val) is int
        return val


class Float(Field):

    def verify(self, val):
        assert type(val) is float or val is 0
        return val


class Enum(Field):

    def __init__(self, cls):
        self.cls = cls

    def decode(self, val):
        return self.cls[val]

    def verify(self, val):
        assert type(val) is self.cls
        return val

    def encode(self, val):
        return val.name


class Hex(Field):

    def decode(self, val):
        return bytes.fromhex(val)

    def verify(self, val):
        assert type(val) is bytes
        return val

    def encode(self, val):
        return val.hex().upper()


class PortalID(Hex):

    def verify(self, val):
        val = Hex.verify(self, val)
        assert len(val) == 4
        return val


class Port(Field):

    def verify(self, val):
        assert type(val) is int
        assert 0 <= val < 65536
        return val


class Address(Field):

    def verify(self, val):
        assert type(val) is str
        return val


Log = Bool
