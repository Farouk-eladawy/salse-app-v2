# core/event_system.py
from typing import Callable, Dict, List, Any
import threading
from datetime import datetime
import queue

class EventBus:
    """ناقل الأحداث المركزي"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def emit(self, event_name: str, data: Any = None):
        """إطلاق حدث"""
        subscribers = self._subscribers.get(event_name, [])
        for callback in subscribers:
            try:
                threading.Thread(
                    target=lambda: callback(data),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Error in event callback: {e}")

    def subscribe(self, event_name: str, callback: Callable):
        """الاشتراك في حدث"""
        with self._lock:
            if event_name not in self._subscribers:
                self._subscribers[event_name] = []
            self._subscribers[event_name].append(callback)