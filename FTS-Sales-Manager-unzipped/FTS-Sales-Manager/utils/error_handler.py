# utils/error_handler.py
from functools import wraps
import logging
import traceback
from typing import Callable, Optional
from tkinter import messagebox

def error_handler(error_key: str = "error_general", show_dialog: bool = True):
    """مُزخرف لمعالجة الأخطاء"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                # تسجيل الخطأ
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.error(traceback.format_exc())

                # تحديث شريط الحالة
                if hasattr(self, 'status_bar'):
                    error_msg = self.lang_manager.get(error_key, str(e))
                    self.status_bar.set_status(error_msg, "error")

                # عرض رسالة خطأ
                if show_dialog and hasattr(self, 'lang_manager'):
                    messagebox.showerror(
                        self.lang_manager.get("error", "Error"),
                        error_msg
                    )

                # وميض النافذة
                if hasattr(self, 'winfo_exists') and self.winfo_exists():
                    try:
                        from utils.window_manager import WindowManager
                        WindowManager.flash_window(self, count=2, interval=300)
                    except:
                        pass

                # إطلاق حدث خطأ
                if hasattr(self, 'event_bus') and self.event_bus:
                    self.event_bus.emit("error_occurred", {
                        "function": func.__name__,
                        "error": str(e)
                    })

                return None
        return wrapper
    return decorator