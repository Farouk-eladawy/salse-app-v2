# -*- coding: utf-8 -*-
"""
utils/threading_utils.py

أدوات للتعامل مع الخيوط (Threading) في تطبيق Tkinter
"""

import threading
import queue
from typing import Callable, Any, Optional
import tkinter as tk
from core.logger import logger


class GUIUpdater:
    """فئة لتحديث واجهة المستخدم من خيوط مختلفة بشكل آمن"""

    def __init__(self):
        self.update_queue = queue.Queue()
        self.root_widget = None
        self.is_running = True

    def set_root_widget(self, widget):
        """تعيين النافذة الرئيسية"""
        self.root_widget = widget

    def schedule_update(self, func: Callable, *args, **kwargs):
        """جدولة تحديث في الخيط الرئيسي"""
        if self.root_widget and self.is_running:
            try:
                self.root_widget.after(0, func, *args, **kwargs)
            except Exception as e:
                logger.error(f"خطأ في جدولة التحديث: {e}")

    def stop(self):
        """إيقاف المحدث"""
        self.is_running = False


class ThreadPool:
    """مجموعة خيوط بسيطة لتنفيذ المهام"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.tasks_queue = queue.Queue()
        self.workers = []
        self.is_running = True
        self._start_workers()

    def _start_workers(self):
        """بدء خيوط العمل"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)

    def _worker_loop(self):
        """حلقة العمل للخيط"""
        while self.is_running:
            try:
                task = self.tasks_queue.get(timeout=1)
                if task is None:
                    break

                func, args, kwargs, callback, error_callback = task

                try:
                    result = func(*args, **kwargs)
                    if callback and _gui_updater:
                        _gui_updater.schedule_update(callback, result)
                except Exception as e:
                    logger.error(f"خطأ في تنفيذ المهمة: {e}", exc_info=True)
                    if error_callback and _gui_updater:
                        _gui_updater.schedule_update(error_callback, e)

                self.tasks_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"خطأ في حلقة العمل: {e}", exc_info=True)

    def schedule_task(self, func: Callable, args=None, kwargs=None,
                     callback: Optional[Callable] = None,
                     error_callback: Optional[Callable] = None):
        """جدولة مهمة للتنفيذ"""
        args = args or ()
        kwargs = kwargs or {}
        task = (func, args, kwargs, callback, error_callback)
        self.tasks_queue.put(task)

    def shutdown(self):
        """إيقاف مجموعة الخيوط"""
        self.is_running = False

        # إضافة مهام فارغة لإيقاظ الخيوط
        for _ in self.workers:
            self.tasks_queue.put(None)

        # انتظار انتهاء الخيوط
        for worker in self.workers:
            worker.join(timeout=2)


# المتغيرات العامة
_gui_updater: Optional[GUIUpdater] = None
_thread_pool: Optional[ThreadPool] = None


def initialize_threading(root_widget):
    """تهيئة نظام الخيوط"""
    global _gui_updater, _thread_pool

    _gui_updater = GUIUpdater()
    _gui_updater.set_root_widget(root_widget)

    _thread_pool = ThreadPool(max_workers=3)

    logger.info("تم تهيئة نظام الخيوط")


def shutdown_threading():
    """إيقاف نظام الخيوط"""
    global _gui_updater, _thread_pool

    if _gui_updater:
        _gui_updater.stop()
        _gui_updater = None

    if _thread_pool:
        _thread_pool.shutdown()
        _thread_pool = None

    logger.info("تم إيقاف نظام الخيوط")


def get_gui_updater() -> Optional[GUIUpdater]:
    """الحصول على محدث واجهة المستخدم"""
    return _gui_updater


def get_thread_pool() -> Optional[ThreadPool]:
    """الحصول على مجموعة الخيوط"""
    return _thread_pool


def run_in_thread(func: Callable, args=None, kwargs=None,
                 callback: Optional[Callable] = None,
                 error_callback: Optional[Callable] = None):
    """تشغيل دالة في خيط منفصل"""
    if _thread_pool:
        _thread_pool.schedule_task(func, args, kwargs, callback, error_callback)
    else:
        # تشغيل في خيط جديد مباشرة
        def wrapper():
            try:
                result = func(*(args or ()), **(kwargs or {}))
                if callback and _gui_updater:
                    _gui_updater.schedule_update(callback, result)
            except Exception as e:
                logger.error(f"خطأ في تنفيذ المهمة: {e}", exc_info=True)
                if error_callback and _gui_updater:
                    _gui_updater.schedule_update(error_callback, e)

        thread = threading.Thread(target=wrapper, daemon=True)
        thread.start()


def safe_gui_update(widget, func: Callable, *args, **kwargs):
    """تحديث آمن لواجهة المستخدم"""
    try:
        if widget and widget.winfo_exists():
            widget.after(0, func, *args, **kwargs)
    except tk.TclError:
        # النافذة محذوفة
        pass
    except Exception as e:
        logger.error(f"خطأ في تحديث الواجهة: {e}")