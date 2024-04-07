
from __future__ import annotations

import weakref

from typing import Generic, Optional, Tuple, TypeVar

from NextLoop.Loop import NextLoop

from .Generic       import SupportsIn, FileDescriptorLike
from .SlotList      import SlotList
from .Futures       import Futures
from .TimedReminder import TimedReminder

T_fd = TypeVar('T_fd', bound=FileDescriptorLike)

class Selectables(Generic[T_fd]):

    class Agent:

        def __init__(self, agency: Selectables[T_fd], key: int, fd: T_fd, active: bool):
            self._agency = agency
            self._key    = key
            self._get_fd = weakref.ref(fd)
            self._active = active
            self._f_key  : Optional[int] = None

        def __del__(self):
            # pylint: disable=protected-access
            self._agency._remove_agent(self)

        def onSelect(self, timeout: Optional[int] = None):
            # pylint: disable=protected-access
            f, self._f_key = self._agency._register(timeout)
            return f

        def on(self):
            self._active = True

        def off(self):
            self._active = False


    def __init__(self, loop: NextLoop, timeout_reminder: TimedReminder):
        self._agents = SlotList[weakref.ref[Selectables.Agent]]()
        self.futures = Futures(loop, timeout_reminder)

    def _register(self, timeout: Optional[int]):
        return self.futures.new(timeout)

    def selected(self, selectables: SupportsIn[Optional[T_fd]], params: Tuple[object, ...] = ()):
        # pylint: disable=protected-access
        for a_ref in self._agents:
            a = a_ref()
            if a and a._f_key is not None and a._get_fd() in selectables:
                f             = self.futures.pop(a._f_key)
                a._f_key = None
                f.ready(*params)

    def new(self, fd: T_fd, active: bool):
        a      = Selectables.Agent(self, -1, fd, active)
        key    = self._agents.append(weakref.ref(a))
        a._key = key
        return a

    def _remove_agent(self, agent: Agent):
        del self._agents[agent._key]
        if agent._f_key is not None:
            f = agent._agency.futures.pop(agent._f_key)
            f.cancel()
            agent._f_key = None

    def get(self):
        'Returns the valid FDs of all active selectables'
        return [
            fd
            for a_ref in self._agents
            for a     in (a_ref(),)
            if  a and a._active
            for fd    in (a._get_fd(),)
            if  fd    is not None
        ]
