

class CancelledError(Exception):
    pass

def unpack(result):
    if type(result) is tuple:
        # The actual value to return has been packed by a foo(*result) call
        l = len(result)
        if   l == 0: return None
        elif l == 1: return result[0]
        else:        return result
    else:
        # Result is exception
        raise result

