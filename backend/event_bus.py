import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Optional

class EventBus(ABC):
    @abstractmethod
    async def emit(self, event_name: str, payload: Optional[dict] = None):
        pass

    @abstractmethod
    async def subscribe(self, event_name: str):
        pass
        
    @abstractmethod
    async def clear(self, event_name: str):
        pass

class InMemoryEventBus(EventBus):
    def __init__(self):
        self._events: Dict[str, asyncio.Event] = {}
        self._lock = asyncio.Lock()

    def _get_event(self, event_name: str) -> asyncio.Event:
        if event_name not in self._events:
            self._events[event_name] = asyncio.Event()
        return self._events[event_name]

    async def emit(self, event_name: str, payload: Optional[dict] = None):
        async with self._lock:
            event = self._get_event(event_name)
            event.set()

    async def subscribe(self, event_name: str):
        async with self._lock:
            event = self._get_event(event_name)
        
        await event.wait()

    async def clear(self, event_name: str):
        async with self._lock:
            event = self._get_event(event_name)
            event.clear()
