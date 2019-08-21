# A simple way to validate and repair configurations after loading.

class Field:

    def __init__(self):
        self.keyName = ''

    def apply(self, val):
        return None


class ConstantField(Field):

    def __init__(self, keyName, val):
        self.keyName = keyName
        self.val     = val

    def apply(self, val):
        return self.val


class ContainerArray:

    def __init__(self, keyName, field):
        self.keyName = keyName
        self.field   = field

    def apply(self, val):
        if type(val) is not list:
            val = []
        me = []
        for i in range(len(val)):
            try:
                me.append(self.field.apply(val[i]))
            except AssertionError:
                pass
        return me


class ContainerObject:

    def __init__(self, keyName, fields):
        self.keyName = keyName
        self.fields  = fields

    def apply(self, val):
        if type(val) is not dict:
            val = {}
        me = {}
        for field in self.fields:
            me[field.keyName] = field.apply(val.get(field.keyName))
        return me


def getContainerArray(keyName, array):
    field = None
    if len(array) == 1:
        val = array[0]
        if   isinstance(val,    Field): field = val
        elif       type(val) is list:   field = getContainerArray('', val)
        elif       type(val) is dict:   field = getContainerObject('', val)
    if field:
        return ContainerArray(keyName, field)
    else:
        return ConstantField(keyName, array)


def getContainerObject(keyName, obj):
    fields = []
    for key in obj:
        val = obj[key]
        if   isinstance(val,    Field): val.keyName = key
        elif       type(val) is list:   val = getContainerArray(key, val)
        elif       type(val) is dict:   val = getContainerObject(key, val)
        else:                           val = ConstantField(key, val)
        fields.append(val)
    return ContainerObject(keyName, fields)


def getVerifier(configTemplate):
    return getContainerObject('', configTemplate)

