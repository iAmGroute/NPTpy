import sys
import traceback

def serialize(thing):
    r = {}
    for fname, ftype, readable, _ in thing.fields:
        if readable:
            try:
                r[fname] = ftype.serialize(thing, fname)
            except Exception as e:
                print(repr(e), fname, ftype, thing)
                raise
    return r


def update(thing, data):
    for fname, ftype, _, writable in thing.fields:
        if fname in data:
            assert writable, 'Not writable: ' + fname
            ftype.update(thing, fname, data[fname])


class Field:

    def __init__(self, default=None, keyName='', getter=None, setter=None):
        self.default = default
        self.keyName = keyName
        self.getter  = getter if getter else getattr
        self.setter  = setter if setter else setattr

    def decode(self, val):
        return val

    def verify(self, val):
        return val

    def encode(self, val):
        return val

    def get(self, obj, attr):
        return self.getter(obj, attr)

    def set(self, obj, attr, val):
        self.setter(obj, attr, val)

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


def operationDecode(ftype, val):
    return ftype.decode(val)

def operationVerify(ftype, val):
    return ftype.verify(val)

def operationEncode(ftype, val):
    return ftype.encode(val)


class Obj(Field):

    def __init__(self, fields):
        Field.__init__(self)
        self.fields = fields

    def map(self, val, operation):
        r = {}
        for fname, ftype, _, _ in self.fields:
            if fname in val:
                try:
                    r[fname] = operation(ftype, val[fname])
                except Exception as e:
                    print(repr(e), fname, ftype)
                    raise
        return r

    def decode(self, val):
        return self.map(val, operationDecode)

    def verify(self, val):
        return self.map(val, operationVerify)

    def encode(self, val):
        return self.map(val, operationEncode)


class Call(Obj):

    def __init__(self, func, paramFields):
        Obj.__init__(self, paramFields)
        self.func = func

    def get(self, obj, attr):
        raise ValueError('Function call is not readable')

    def set(self, obj, attr, val):
        self.func(obj, **val)


class SlotList(Field):

    def __init__(self, createFunc=None, removeFunc=None):
        Field.__init__(self)
        self.createFunc = createFunc
        self.removeFunc = removeFunc

    def createNew(self, obj, v):
        if self.createFunc:
            self.createFunc(obj, v)
        else:
            raise ValueError('Creation of new items not available')

    def remove(self, obj, k):
        if self.removeFunc:
            self.removeFunc(obj, k)
        else:
            raise ValueError('Removal of items not available')

    def verify(self, val):
        assert type(val) is list
        for kv in val:
            k = kv['k']
            v = kv['v']
            assert k is None or type(k) is int and k >= 0
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
            if k is None:
                if v is None:
                    pass # TODO
                else:
                    self.createNew(obj, v)
            else:
                if v is None:
                    self.remove(obj, k)
                else:
                    update(sl[k], v)


class Constant(Field):

    def __init__(self, keyName, val):
        Field.__init__(self, val, keyName)

    def decode(self, val):
        return self.default

    def verify(self, val):
        return self.default

    def encode(self, val):
        return self.default

    def get(self, obj, attr):
        return self.default

    def set(self, obj, attr, val):
        setattr(obj, attr, self.default)


class Bool(Field):

    def verify(self, val):
        assert val is True or val is False
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
        Field.__init__(self)
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
