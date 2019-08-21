
from Common.ConfigVerifier import Field

class PortalID(Field):
    def __init__(self, default):
        self.default = default
    def apply(self, val):
        try:
            assert type(val) is str
            portalID = bytes.fromhex(val)
            assert len(portalID) == 4
            return portalID.hex().upper()
        except:
            return self.default

class Port(Field):
    def __init__(self, default):
        self.default = default
    def apply(self, val):
        try:
            assert type(val) is int
            assert 0 <= val < 65536
            return val
        except:
            return self.default

class Address(Field):
    def __init__(self, default):
        self.default = default
    def apply(self, val):
        try:
            assert type(val) is str
            return val
        except:
            return self.default

class Log(Field):
    def __init__(self, default):
        self.default = default
    def apply(self, val):
        if val is True:
            return True
        else:
            return self.default
