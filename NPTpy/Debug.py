# pylint: skip-file

import objgraph
import inspect
import _frozen_importlib
import _frozen_importlib_external

def _f(): pass

class _c: pass

#builtins =  __builtins__.values()

skipTypes = [
    str, int, float, bytes, bool, type(_f.__code__), type(_c.__weakref__),
    _frozen_importlib.ModuleSpec,
    _frozen_importlib_external.SourceFileLoader
]

def isBuiltinModule(x):
    try:
        return inspect.ismodule(x) and x.__name__[0].islower()
    except:
        return False

def isAllowed(x):
    remove  =  not x                 \
            or type(x) in skipTypes  \
            or inspect.isbuiltin(x)  \
            or x == __builtins__     \
            or inspect.isfunction(x) \
            or inspect.isclass(x)    \
            or isBuiltinModule(x)
#            or x in builtins        \
    return not remove

def getInfo(x):
    res = [repr(type(x))]
    try:    res.append(repr(x.__file__))
    except: pass
    try:    res.append(repr(x.__code__))
    except: pass
    try:    res.append(repr(list(x)))
    except: res.append(repr(x))
    return '\n'.join([r[:300] for r in res])


class Debug:

    def __init__(self, path='.'):
        self.path       = path
        self.graphCount = 0

    def printGraph(self, objects, max_depth=99, ext='dot'):
        objgraph.show_refs(
            objects + [_f], max_depth=max_depth, too_many=999,
            refcounts=True, filter=isAllowed, extra_info=getInfo,
            filename=f'{self.path}/graph/{self.graphCount:03}.{ext}'
        )
        self.graphCount += 1

