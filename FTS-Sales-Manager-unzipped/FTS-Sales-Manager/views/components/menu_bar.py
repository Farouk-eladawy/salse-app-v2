# -*- coding: utf-8 -*-
"""
views/components/menu_bar.py

مكون شريط القوائم
"""

import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional, Dict, Any

from core.language_manager import LanguageManager
from core.logger import logger


class MenuBarComponent:
    """مكون شريط القوائم"""

    def __init__(
        self,
        parent_window,
        lang_manager: LanguageManager,
        user_record: Dict[str, Any],
        callbacks: Dict[str, Callable]
    ):
        """
        تهيئة شريط القوائم

        Args:
            parent_window: النافذة الرئيسية
            lang_manager: مدير اللغة
            user_record: سجل المستخدم
            callbacks: قاموس بالدوال المرجعية
        """
        self.parent = parent_window
        self.lang_manager = lang_manager
        self.user_record = user_record
        self.callbacks = callbacks

        # متغيرات القوائم
        self.dark_mode_var = tk.BooleanVar()
        self.fullscreen_var = tk.BooleanVar(value=False)
        self.performance_mode_var = tk.BooleanVar(value=False)
        self.lang_var = tk.StringVar(value=self.lang_manager.current_lang)

        # إنشاء شريط القوائم
        self._create_menu()

    def _create_menu(self):
        """إنشاء شريط القوائم"""
        try:
            # إنشاء شريط القوائم
            self.menubar = tk.Menu(self.parent)
            self.parent.config(menu=self.menubar)

            # إنشاء القوائم
            self._create_file_menu()
            self._create_edit_menu()
            self._create_view_menu()
            self._create_tools_menu()

            # قائمة المسؤول (للمشرفين فقط)
            if self._is_admin():
                self._create_admin_menu()

            self._create_help_menu()

            logger.info("تم إنشاء شريط القوائم بنجاح")

        except Exception as e:
            logger.error(f"خطأ في إنشاء شريط القوائم: {e}")

    def _create_file_menu(self):
        """إنشاء قائمة ملف"""
        file_menu = tk.Menu(self.menubar, tearoff=0)

        # تسجيل خروج
        file_menu.add_command(
            label=self.lang_manager.get("logout", "Logout"),
            command=self._get_callback('logout'),
            accelerator="Ctrl+Shift+L"
        )

        file_menu.add_separator()

        # تصدير البيانات
        file_menu.add_command(
            label=self.lang_manager.get("export_data", "Export Data"),
            command=self._get_callback('export'),
            accelerator="Ctrl+S"
        )

        file_menu.add_separator()

        # إغلاق
        file_menu.add_command(
            label=self.lang_manager.get("close", "Close"),
            command=self._get_callback('close'),
            accelerator="Alt+F4"
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("file_menu", "File"),
            menu=file_menu
        )

    def _create_edit_menu(self):
        """إنشاء قائمة تحرير"""
        edit_menu = tk.Menu(self.menubar, tearoff=0)

        # إضافة
        edit_menu.add_command(
            label=self.lang_manager.get("add", "Add"),
            command=self._get_callback('add'),
            accelerator="Ctrl+N"
        )

        # تعديل
        edit_menu.add_command(
            label=self.lang_manager.get("edit", "Edit"),
            command=self._get_callback('edit'),
            accelerator="Ctrl+E"
        )

        # حذف
        edit_menu.add_command(
            label=self.lang_manager.get("delete", "Delete"),
            command=self._get_callback('delete'),
            accelerator="Delete"
        )

        edit_menu.add_separator()

        # تحديد الكل
        edit_menu.add_command(
            label=self.lang_manager.get("select_all", "Select All"),
            command=self._get_callback('select_all'),
            accelerator="Ctrl+A"
        )

        # إلغاء التحديد
        edit_menu.add_command(
            label=self.lang_manager.get("clear_selection", "Clear Selection"),
            command=self._get_callback('clear_selection'),
            accelerator="Escape"
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("edit_menu", "Edit"),
            menu=edit_menu
        )

    def _create_view_menu(self):
        """إنشاء قائمة عرض"""
        view_menu = tk.Menu(self.menubar, tearoff=0)

        # الوضع الداكن
        view_menu.add_checkbutton(
            label=self.lang_manager.get("dark_mode", "Dark Mode"),
            variable=self.dark_mode_var,
            command=self._toggle_dark_mode,
            accelerator="Ctrl+T"
        )

        view_menu.add_separator()

        # قائمة لغة فرعية
        self._create_language_submenu(view_menu)

        view_menu.add_separator()

        # تحديث البيانات
        view_menu.add_command(
            label=self.lang_manager.get("refresh", "Refresh"),
            command=self._get_callback('refresh'),
            accelerator="F5"
        )

        # وضع ملء الشاشة
        view_menu.add_checkbutton(
            label=self.lang_manager.get("fullscreen", "Fullscreen"),
            variable=self.fullscreen_var,
            command=self._toggle_fullscreen,
            accelerator="F11"
        )

        # وضع الأداء العالي
        view_menu.add_checkbutton(
            label=self.lang_manager.get("performance_mode", "Performance Mode"),
            variable=self.performance_mode_var,
            command=self._toggle_performance_mode
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("view_menu", "View"),
            menu=view_menu
        )

    def _create_language_submenu(self, parent_menu):
        """إنشاء قائمة اللغة الفرعية"""
        lang_menu = tk.Menu(parent_menu, tearoff=0)

        # العربية
        lang_menu.add_radiobutton(
            label=self.lang_manager.get("arabic", "العربية"),
            command=lambda: self._change_language("ar"),
            value="ar",
            variable=self.lang_var
        )

        # English
        lang_menu.add_radiobutton(
            label=self.lang_manager.get("english", "English"),
            command=lambda: self._change_language("en"),
            value="en",
            variable=self.lang_var
        )

        parent_menu.add_cascade(
            label=self.lang_manager.get("language_menu", "Language"),
            menu=lang_menu
        )

    def _create_tools_menu(self):
        """إنشاء قائمة أدوات"""
        tools_menu = tk.Menu(self.menubar, tearoff=0)

        # البحث
        tools_menu.add_command(
            label=self.lang_manager.get("search", "Search"),
            command=self._get_callback('search'),
            accelerator="Ctrl+F"
        )

        tools_menu.add_separator()

        # الإحصائيات
        tools_menu.add_command(
            label=self.lang_manager.get("statistics", "Statistics"),
            command=self._get_callback('statistics')
        )

        # التقارير
        tools_menu.add_command(
            label=self.lang_manager.get("reports", "Reports"),
            command=self._get_callback('reports')
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("tools_menu", "Tools"),
            menu=tools_menu
        )

    def _create_admin_menu(self):
        """إنشاء قائمة المسؤول"""
        admin_menu = tk.Menu(self.menubar, tearoff=0)

        # إدارة المستخدمين
        admin_menu.add_command(
            label=self.lang_manager.get("user_management", "User Management"),
            command=self._get_callback('user_management')
        )

        # محرر الإعدادات
        admin_menu.add_command(
            label=self.lang_manager.get("config_editor", "Configuration Editor"),
            command=self._get_callback('config_editor')
        )

        admin_menu.add_separator()

        # مسح الذاكرة المؤقتة
        admin_menu.add_command(
            label=self.lang_manager.get("clear_cache", "Clear Cache"),
            command=self._get_callback('clear_cache')
        )

        # عرض السجلات
        admin_menu.add_command(
            label=self.lang_manager.get("view_logs", "View Logs"),
            command=self._get_callback('view_logs')
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("admin_menu", "Admin"),
            menu=admin_menu
        )

    def _create_help_menu(self):
        """إنشاء قائمة المساعدة"""
        help_menu = tk.Menu(self.menubar, tearoff=0)

        # الاختصارات
        help_menu.add_command(
            label=self.lang_manager.get("shortcuts", "Keyboard Shortcuts"),
            command=self._get_callback('shortcuts'),
            accelerator="F1"
        )

        help_menu.add_separator()

        # دليل المستخدم
        help_menu.add_command(
            label=self.lang_manager.get("user_guide", "User Guide"),
            command=self._get_callback('user_guide')
        )

        # حول البرنامج
        help_menu.add_command(
            label=self.lang_manager.get("about", "About"),
            command=self._get_callback('about')
        )

        self.menubar.add_cascade(
            label=self.lang_manager.get("help_menu", "Help"),
            menu=help_menu
        )

    def _is_admin(self) -> bool:
        """التحقق من صلاحيات المسؤول"""
        return self.user_record.get('fields', {}).get('Role', '').lower() == 'admin'

    def _get_callback(self, action: str) -> Callable:
        """الحصول على الدالة المرجعية"""
        return self.callbacks.get(action, lambda: logger.warning(f"No callback for action: {action}"))

    def _toggle_dark_mode(self):
        """تبديل الوضع الداكن"""
        if 'toggle_theme' in self.callbacks:
            self.callbacks['toggle_theme']()

    def _toggle_fullscreen(self):
        """تبديل وضع ملء الشاشة"""
        if self.fullscreen_var.get():
            self.parent.attributes("-fullscreen", True)
        else:
            self.parent.attributes("-fullscreen", False)

        if 'fullscreen_changed' in self.callbacks:
            self.callbacks['fullscreen_changed'](self.fullscreen_var.get())

    def _toggle_performance_mode(self):
        """تبديل وضع الأداء العالي"""
        if 'performance_mode' in self.callbacks:
            self.callbacks['performance_mode'](self.performance_mode_var.get())

    def _change_language(self, lang_code: str):
        """تغيير اللغة"""
        if 'change_language' in self.callbacks:
            self.callbacks['change_language'](lang_code)
            self.lang_var.set(lang_code)

    def update_texts(self):
        """تحديث النصوص عند تغيير اللغة"""
        # إعادة بناء القائمة بالكامل
        self._create_menu()

        # تحديث المتغيرات
        self.lang_var.set(self.lang_manager.current_lang)

    def update_dark_mode(self, is_dark: bool):
        """تحديث حالة الوضع الداكن"""
        self.dark_mode_var.set(is_dark)

    def destroy(self):
        """تدمير المكون"""
        try:
            if hasattr(self, 'menubar'):
                self.menubar.destroy()
        except:
            pass