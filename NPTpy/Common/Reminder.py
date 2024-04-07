
from __future__ import annotations

import weakref

from typing import Any, Callable, Generic, TypeVar

from .Generic  import nop
from .SlotList import SlotList

T_link = TypeVar('T_link')

class Reminder(Generic[T_link]):

    class Agent:

        def __init__(
                self,
                agency:    Reminder[T_link],
                key:       int,
                link:      T_link,
                on_run:    Callable[[T_link], Any],
                on_skip:   Callable[[T_link], Any],
                enabled:   bool,
                skip_next: bool,
            ):
            self._agency     = agency
            self._key        = key
            self.get_owner   = weakref.ref(link)
            self.get_on_run  = weakref.ref(on_run)
            self.get_on_skip = weakref.ref(on_skip)
            self.enabled     = enabled
            self.skip_next   = skip_next

        def __del__(self):
            self._agency._remove(self._key)

        def run(self):
            # pylint: disable=assignment-from-none
            # pylint: disable=not-callable
            if self.enabled:
                link = self.get_owner()
                if not link:
                    # shouldn't happen
                    self.__del__()
                else:
                    if self.skip_next:
                        self.skip_next = False
                        f = self.get_on_skip()
                        if f is not None: f(link)
                    else:
                        f = self.get_on_run()
                        if f is not None: f(link)


    def __init__(self):
        self._agents = SlotList[weakref.ref[Reminder.Agent]]()

    def _remove(self, key: int):
        del self._agents[key]

    def new(
            self,
            link:      T_link,
            on_run:    Callable[[T_link], Any] = nop,
            on_skip:   Callable[[T_link], Any] = nop,
            enabled:   bool = True,
            skip_next: bool = False
        ):
        a      = Reminder.Agent(self, -1, link, on_run, on_skip, enabled, skip_next)
        key    = self._agents.append(weakref.ref(a))
        a._key = key
        return a

    def run(self):
        for d in self._agents:
            delegate = d()
            if delegate:
                delegate.run()
