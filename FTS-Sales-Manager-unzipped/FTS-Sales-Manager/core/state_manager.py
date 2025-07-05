# core/state_manager.py
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import threading

@dataclass
class WindowState:
    """حالة النافذة الرئيسية"""
    all_records: List[Dict[str, Any]] = field(default_factory=list)
    filtered_records: List[Dict[str, Any]] = field(default_factory=list)
    selected_records: List[Dict[str, Any]] = field(default_factory=list)
    current_page: int = 1
    records_per_page: int = 50
    is_loading: bool = False
    last_refresh: Optional[datetime] = None
    search_query: str = ""
    sort_column: Optional[str] = None
    sort_order: str = "asc"

    def reset_selection(self):
        """مسح التحديد"""
        self.selected_records.clear()

    def update_records(self, records: List[Dict[str, Any]]):
        """تحديث السجلات"""
        self.all_records = records
        self.filtered_records = records
        self.last_refresh = datetime.now()

    def get_selected_count(self) -> int:
        """عدد السجلات المحددة"""
        return len(self.selected_records)

class StateManager:
    """مدير الحالة المركزي"""

    def __init__(self):
        self._states: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._observers: Dict[str, List[Callable]] = {}

    def register_state(self, name: str, state: Any):
        """تسجيل حالة جديدة"""
        with self._lock:
            self._states[name] = state

    def get_state(self, name: str) -> Any:
        """الحصول على حالة"""
        with self._lock:
            return self._states.get(name)

    def update_state(self, name: str, updates: Dict[str, Any]):
        """تحديث حالة"""
        with self._lock:
            state = self._states.get(name)
            if state:
                for key, value in updates.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                self._notify_observers(name, state)

    def subscribe(self, state_name: str, callback: Callable):
        """الاشتراك في تغييرات الحالة"""
        if state_name not in self._observers:
            self._observers[state_name] = []
        self._observers[state_name].append(callback)

    def _notify_observers(self, state_name: str, state: Any):
        """إشعار المراقبين بالتغييرات"""
        for callback in self._observers.get(state_name, []):
            try:
                callback(state)
            except Exception as e:
                print(f"Error notifying observer: {e}")