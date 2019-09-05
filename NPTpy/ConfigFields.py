
from Common.ConfigVerifier import Field


class Bool(Field):

    def verifier(self, val):
        assert val is True or False
        return val


class Int(Field):

    def verify(self, val):
        assert type(val) is int
        return val


class PortalID(Field):

    def decode(self, val):
        return bytes.fromhex(val)

    def verify(self, val):
        assert type(val) is bytes
        assert len(val) == 4
        return val

    def encode(self, val):
        return val.hex().upper()


class Port(Field):

    def verify(self, val):
        assert type(val) is int
        assert 0 <= val < 65536
        return val


class Address(Field):

    def verify(self, val):
        assert type(val) is str
        return val


class Log(Field):

    def verifier(self, val):
        assert val is True or False
        return val

