# -*- coding: utf-8 -*-
"""
views/main_window.py - النسخة المحسنة والمقللة

النافذة الرئيسية مع دمج جميع المميزات المتقدمة في كود مبسط
تفتح في وضع ملء الشاشة كوضع افتراضي مع معالجة شاملة للأخطاء
"""

import customtkinter as ctk
import threading
import os
import tkinter as tk
from tkinter import messagebox
from typing import Any, Dict, List
from datetime import datetime
import platform
import weakref
from functools import wraps

# الاستيرادات الأساسية
from core.language_manager import LanguageManager
from core.theme_manager import ThemeManager
from core.theme_color_manager import ThemeColorManager, ThemedWindow
from core.logger import logger
from core.permissions import permission_manager
from utils.window_manager import WindowManager

# الأنظمة المحسنة الجديدة
from core.state_manager import StateManager, WindowState
from core.event_system import EventBus
from utils.async_operations import AsyncOperationManager

# استيراد المكونات
from views.components.header import HeaderComponent
from views.components.sidebar import SidebarComponent
from views.components.data_table import DataTableComponent
from views.components.toolbar import ToolbarComponent
from views.components.status_bar import StatusBarComponent
from views.components.menu_bar import MenuBarComponent
from utils.image_utils import setup_window_icon


def safe_operation(func):
    """Decorator للعمليات الآمنة"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._is_window_valid():
            return None
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.debug(f"Safe operation error in {func.__name__}: {e}")
            return None
    return wrapper


def error_handler(func):
    """Decorator لمعالجة الأخطاء العامة"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            return None
    return wrapper


class SafeAfterManager:
    """مدير آمن مبسط للعمليات المجدولة"""

    def __init__(self, window):
        self.window_ref = weakref.ref(window)
        self.operations = {}
        self.next_id = 1
        self._shutdown = False

    def schedule(self, delay, operation, *args, **kwargs):
        if self._shutdown:
            return None

        window = self.window_ref()
        if not window or not self._is_window_valid(window):
            return None

        operation_id = f"op_{self.next_id}"
        self.next_id += 1

        def safe_wrapper():
            self.operations.pop(operation_id, None)
            current_window = self.window_ref()
            if not self._shutdown and current_window and self._is_window_valid(current_window):
                try:
                    operation(*args, **kwargs)
                except Exception as e:
                    logger.debug(f"Scheduled operation error: {e}")

        try:
            after_id = window.after(delay, safe_wrapper)
            self.operations[operation_id] = after_id
            return operation_id
        except:
            return None

    def cancel_all(self):
        self._shutdown = True
        window = self.window_ref()
        if window and self._is_window_valid(window):
            for after_id in self.operations.values():
                try:
                    window.after_cancel(after_id)
                except:
                    pass
        self.operations.clear()

    def _is_window_valid(self, window):
        try:
            return window.winfo_exists() and not getattr(window, '_window_destroyed', False)
        except:
            return False


class MainWindow(ctk.CTk):
    """النافذة الرئيسية المحسنة مع كود مبسط"""

    def __init__(self, lang_manager: LanguageManager, theme_manager: ThemeManager,
                 airtable_model: Any, controller: Any, user_record: Dict[str, Any],
                 parent_window: Any = None):
        super().__init__()

        # تهيئة المتغيرات الأساسية
        self.parent_window = parent_window
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.airtable_model = airtable_model
        self.controller = controller
        self.user_record = user_record

        # النظام الموحد والبيانات
        self.themed_window = ThemedWindow(self, theme_manager)
        self.all_records = []
        self.filtered_records = []
        self.selected_records = []
        self.current_page = 1
        self.records_per_page = 50

        # متغيرات الحالة
        self._is_fullscreen = False
        self._closing = False
        self._window_destroyed = False

        # مدير العمليات المجدولة
        self.safe_after = SafeAfterManager(self)

        # تهيئة الأنظمة الجديدة
        self._init_systems()

        # إعداد وبناء الواجهة
        self._setup_window()
        self._apply_theme()
        self._build_ui()

        # إعداد النافذة والاختصارات
        WindowManager.setup_window(self, parent=self.parent_window, center=False,
                                 modal=False, focus=True, topmost_duration=500,
                                 min_size=(1200, 700), fullscreen_default=True)

        self._setup_shortcuts()

        # تطبيق ملء الشاشة وتحميل البيانات
        self.safe_after.schedule(100, self._apply_fullscreen_mode)
        self.safe_after.schedule(500, self._load_data)

        # معالج الإغلاق
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Destroy>", self._on_window_destroy)

    def _init_systems(self):
        """تهيئة الأنظمة الجديدة"""
        try:
            self.state_manager = StateManager()
            self.event_bus = EventBus()
            self.async_manager = AsyncOperationManager()

            self.window_state = WindowState()
            self.state_manager.register_state("main_window", self.window_state)

            if self.event_bus:
                self.event_bus.subscribe("data_loaded", self._on_data_loaded_event)
                self.event_bus.subscribe("search_completed", self._on_search_completed_event)
                self.event_bus.subscribe("error_occurred", self._on_error_event)
        except Exception as e:
            logger.warning(f"Failed to initialize some systems: {e}")
            self.state_manager = None
            self.event_bus = None
            self.async_manager = None

    def _on_window_destroy(self, event=None):
        """معالج تدمير النافذة"""
        if event and event.widget == self:
            self._window_destroyed = True
            self._closing = True
            if hasattr(self, 'safe_after'):
                self.safe_after.cancel_all()

    def _is_window_valid(self):
        """فحص صحة النافذة"""
        try:
            return not self._window_destroyed and not self._closing and self.winfo_exists()
        except:
            self._window_destroyed = True
            return False

    @safe_operation
    def _safe_status_update(self, message, status_type="info"):
        """تحديث آمن لشريط الحالة"""
        if hasattr(self, 'status_bar') and self.status_bar:
            try:
                self.status_bar.set_status(message, status_type)
            except:
                pass

    @safe_operation
    def _safe_toolbar_update(self, **kwargs):
        """تحديث آمن لشريط الأدوات"""
        if hasattr(self, 'toolbar') and self.toolbar:
            for method_name, value in kwargs.items():
                if hasattr(self.toolbar, method_name):
                    try:
                        getattr(self.toolbar, method_name)(value)
                    except:
                        pass

    def _setup_window(self):
        """إعداد النافذة"""
        username = self.user_record.get('fields', {}).get('Username', 'User')
        self.title(f"{self.lang_manager.get('main_window_title', 'FTS Sales Manager')} - {username}")

        self._set_window_icon()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(1200, 700)

    def _set_window_icon(self):
        """تعيين أيقونة النافذة"""
        icon_paths = [
            "resources/app_icon.ico", "resources/fts_icon.ico", "resources/icon.ico",
            "assets/icon.ico", "resources/app_icon.png", "resources/company_logo.png",
            "resources/icon.png", "assets/icon.png"
        ]
        setup_window_icon(self, icon_paths)

    def _apply_theme(self):
        """تطبيق الثيم الموحد"""
        self.themed_window.apply_theme()
        if hasattr(self.theme_manager, 'is_windows7_theme') and self.theme_manager.is_windows7_theme():
            self._apply_windows7_theme()

    def _apply_windows7_theme(self):
        """تطبيق ثيم Windows 7"""
        try:
            if hasattr(self.theme_manager, 'get_theme_colors'):
                colors = self.theme_manager.get_theme_colors()
                self.configure(fg_color=colors.get("window_bg", self.themed_window.get_color('background')))
            if platform.system() == "Windows":
                self.wm_attributes('-alpha', 0.98)
        except Exception as e:
            logger.debug(f"Error applying Windows 7 theme: {e}")

    def _build_ui(self):
        """بناء الواجهة"""
        # الحاوية الرئيسية
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        # إنشاء شريط القوائم
        self._create_menu_bar()

        # إنشاء المكونات
        self._create_header()
        self._create_separator()
        self._create_content_area()
        self._create_status_bar()

    def _create_menu_bar(self):
        """إنشاء شريط القوائم"""
        if hasattr(self.theme_manager, 'is_windows7_theme') and self.theme_manager.is_windows7_theme():
            self._create_windows7_menu_bar()
        else:
            self._create_standard_menu_bar()

    def _create_windows7_menu_bar(self):
        """شريط قوائم Windows 7"""
        colors = getattr(self.theme_manager, 'get_theme_colors', lambda: {
            "menu_bg": "#F0F0F0", "text_color": "#000000",
            "menu_hover": "#E5F1FB", "menu_border": "#D4D4D4"
        })()

        menubar_frame = ctk.CTkFrame(self, height=28, fg_color=colors.get("menu_bg", "#F0F0F0"), corner_radius=0)
        menubar_frame.pack(fill="x")
        menubar_frame.pack_propagate(False)

        # إضافة border وقوائم
        menu_border = ctk.CTkFrame(menubar_frame, height=1, fg_color=colors.get("menu_border", "#D4D4D4"))
        menu_border.pack(side="bottom", fill="x")

        menu_items = [
            (self.lang_manager.get("menu_file", "File"), self._show_menu),
            (self.lang_manager.get("menu_edit", "Edit"), self._show_menu),
            (self.lang_manager.get("menu_view", "View"), self._show_menu),
            (self.lang_manager.get("menu_tools", "Tools"), self._show_menu),
            (self.lang_manager.get("menu_help", "Help"), self._show_menu)
        ]

        for item_text, command in menu_items:
            btn = ctk.CTkButton(menubar_frame, text=item_text, width=70, height=26, corner_radius=0,
                              fg_color="transparent", text_color=colors.get("text_color", "#000000"),
                              hover_color=colors.get("menu_hover", "#E5F1FB"),
                              font=ctk.CTkFont(family="Segoe UI", size=12), command=command)
            btn.pack(side="left", padx=2, pady=1)

        self.windows7_menubar = menubar_frame

    def _create_standard_menu_bar(self):
        """شريط القوائم القياسي"""
        menu_callbacks = {
            'logout': self._logout, 'export': self._export_data, 'close': self._on_close,
            'add': self._add_record, 'edit': self._edit_record, 'delete': self._delete_record,
            'select_all': self._select_all, 'clear_selection': self._clear_selection,
            'toggle_theme': self._toggle_theme, 'change_language': self._change_language_from_menu,
            'refresh': self._refresh_data, 'fullscreen_changed': self._on_fullscreen_changed,
            'performance_mode': self._on_performance_mode_changed, 'search': self._focus_search,
            'statistics': self._show_statistics, 'reports': self._show_reports,
            'user_management': self._show_placeholder, 'config_editor': self._show_placeholder,
            'clear_cache': self._clear_cache, 'view_logs': self._show_placeholder,
            'shortcuts': self._show_help, 'user_guide': self._show_user_guide,
            'about': self._show_about, 'themes_menu': self._show_placeholder,
        }

        self.menu_bar = MenuBarComponent(parent_window=self, lang_manager=self.lang_manager,
                                       user_record=self.user_record, callbacks=menu_callbacks)

    def _create_header(self):
        """إنشاء الهيدر"""
        header_frame = ctk.CTkFrame(self.main_container, height=80, corner_radius=0,
                                  fg_color=self.themed_window.get_color('surface'))
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        self.header = HeaderComponent(header_frame, lang_manager=self.lang_manager,
                                    user_record=self.user_record, controller=self.controller,
                                    on_search=self._on_search, on_refresh=self._refresh_data,
                                    on_language_change=self._handle_language_change,
                                    on_theme_change=self._handle_theme_change)
        self.header.pack(fill="both", expand=True, padx=20, pady=10)

        self._add_language_button()

    def _add_language_button(self):
        """إضافة زر اللغة"""
        current_lang = self.lang_manager.current_lang
        button_text = "🌐 EN" if current_lang == "ar" else "🌐 AR"

        parent = getattr(self.header, 'right_frame', self.header)
        self.language_button = ctk.CTkButton(parent, text=button_text, width=100, height=36,
                                           command=self._toggle_language, font=ctk.CTkFont(size=14, weight="bold"),
                                           corner_radius=8, fg_color=("#007ACC", "#0E639C"),
                                           hover_color=("#005A9E", "#1177BB"))
        self.language_button.pack(side="right", padx=10)

    def _create_separator(self):
        """إنشاء خط فاصل"""
        separator = ctk.CTkFrame(self.main_container, height=2, fg_color=self.themed_window.get_color('border'))
        separator.pack(fill="x")

    def _create_content_area(self):
        """إنشاء منطقة المحتوى"""
        content_frame = ctk.CTkFrame(self.main_container, corner_radius=0, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # الشريط الجانبي
        self._create_sidebar(content_frame)

        # منطقة العمل
        self._create_work_area(content_frame)

    def _create_sidebar(self, parent):
        """إنشاء الشريط الجانبي"""
        self.sidebar_container = ctk.CTkFrame(parent, width=280, corner_radius=0,
                                            fg_color=self.themed_window.get_color('input_bg'))
        self.sidebar_container.pack(side="left", fill="y")
        self.sidebar_container.pack_propagate(False)

        shadow_frame = ctk.CTkFrame(self.sidebar_container, width=2, fg_color=self.themed_window.get_color('border'))
        shadow_frame.pack(side="right", fill="y")

        self.sidebar = SidebarComponent(self.sidebar_container, self.lang_manager, on_navigate=self._on_navigate)
        self.sidebar.pack(fill="both", expand=True, padx=15, pady=15)

    def _create_work_area(self, parent):
        """إنشاء منطقة العمل"""
        work_area_container = ctk.CTkFrame(parent, corner_radius=0, fg_color=self.themed_window.get_color('surface'))
        work_area_container.pack(side="left", fill="both", expand=True)

        work_area = ctk.CTkFrame(work_area_container, corner_radius=10, fg_color=self.themed_window.get_color('background'))
        work_area.pack(fill="both", expand=True, padx=20, pady=15)

        # شريط الأدوات
        self._create_toolbar(work_area)

        # جدول البيانات
        self._create_data_table(work_area)

    def _create_toolbar(self, parent):
        """إنشاء شريط الأدوات"""
        toolbar_container = ctk.CTkFrame(parent, height=60, corner_radius=8, fg_color=self.themed_window.get_color('surface'))
        toolbar_container.pack(fill="x", padx=15, pady=(15, 10))
        toolbar_container.pack_propagate(False)

        self.toolbar = ToolbarComponent(toolbar_container, self.lang_manager, on_add=self._add_record,
                                      on_edit=self._edit_record, on_delete=self._delete_record,
                                      on_refresh=self._refresh_data, on_export=self._export_data)
        self.toolbar.pack(fill="both", expand=True, padx=10, pady=10)

    def _create_data_table(self, parent):
        """إنشاء جدول البيانات"""
        table_container = ctk.CTkFrame(parent, corner_radius=8, fg_color=self.themed_window.get_color('surface'))
        table_container.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # عنوان الجدول
        table_header = ctk.CTkFrame(table_container, height=40, corner_radius=0, fg_color=self.themed_window.get_color('input_bg'))
        table_header.pack(fill="x")
        table_header.pack_propagate(False)

        self.table_title = ctk.CTkLabel(table_header, text=self.lang_manager.get("bookings_list", "Bookings List"),
                                      font=ctk.CTkFont(size=16, weight="bold"),
                                      text_color=self.themed_window.get_color('text_primary'))
        self.table_title.pack(side="left", padx=20, pady=10)

        # الجدول
        self.data_table = DataTableComponent(table_container, self.lang_manager,
                                           on_row_double_click=self._on_row_double_click,
                                           on_selection_change=self._on_selection_change)
        self.data_table.pack(fill="both", expand=True, padx=15, pady=15)

    def _create_status_bar(self):
        """إنشاء شريط الحالة"""
        status_container = ctk.CTkFrame(self.main_container, height=35, corner_radius=0,
                                      fg_color=self.themed_window.get_color('input_bg'))
        status_container.pack(fill="x", side="bottom")
        status_container.pack_propagate(False)

        status_separator = ctk.CTkFrame(status_container, height=1, fg_color=self.themed_window.get_color('border'))
        status_separator.pack(fill="x", side="top")

        self.status_bar = StatusBarComponent(status_container, self.lang_manager)
        self.status_bar.pack(fill="both", expand=True, padx=20, pady=5)

    def _setup_shortcuts(self):
        """إعداد اختصارات لوحة المفاتيح"""
        WindowManager.setup_window_shortcuts(self)

        shortcuts = {
            "<Control-n>": lambda e: self._add_record(), "<Control-e>": lambda e: self._edit_record(),
            "<Delete>": lambda e: self._delete_record(), "<F5>": lambda e: self._refresh_data(),
            "<Control-f>": lambda e: self._focus_search(), "<Control-a>": lambda e: self._select_all(),
            "<Control-s>": lambda e: self._export_data(), "<F1>": lambda e: self._show_help(),
            "<Control-l>": lambda e: self._toggle_language(), "<Control-t>": lambda e: self._toggle_theme(),
            "<Control-Shift-L>": lambda e: self._logout(), "<Control-Shift-F>": lambda e: self._show_placeholder(),
            "<Control-p>": lambda e: self._show_placeholder(), "<F11>": lambda e: self._toggle_fullscreen(),
            "<Escape>": lambda e: self._exit_fullscreen(), "<Alt-Return>": lambda e: self._toggle_fullscreen(),
        }

        for key, command in shortcuts.items():
            self.bind(key, command)

    @error_handler
    def _apply_fullscreen_mode(self):
        """تطبيق وضع ملء الشاشة"""
        try:
            system = platform.system()
            if system == "Windows":
                self.state('zoomed')
            elif system == "Linux":
                try:
                    self.attributes('-zoomed', True)
                except:
                    self.attributes('-fullscreen', True)
            elif system == "Darwin":
                self.attributes('-fullscreen', True)

            self._is_fullscreen = True
            self._safe_status_update(self.lang_manager.get("fullscreen_enabled", "Fullscreen mode enabled"), "success")
            if self._is_window_valid():
                self.update_idletasks()
        except Exception as e:
            logger.error(f"Fullscreen error: {e}")
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            self.geometry(f"{screen_width-100}x{screen_height-100}+50+50")
            self._is_fullscreen = False

    @error_handler
    def _toggle_fullscreen(self):
        """تبديل وضع ملء الشاشة"""
        system = platform.system()

        if system == "Windows":
            current_state = self.state()
            if current_state == 'zoomed':
                self.state('normal')
                self._is_fullscreen = False
            else:
                self.state('zoomed')
                self._is_fullscreen = True
        else:
            try:
                current_state = self.attributes('-fullscreen')
                new_state = not current_state
                self.attributes('-fullscreen', new_state)
                self._is_fullscreen = new_state
            except:
                if system == "Linux":
                    current_state = self.attributes('-zoomed')
                    new_state = not current_state
                    self.attributes('-zoomed', new_state)
                    self._is_fullscreen = new_state

        status = "enabled" if self._is_fullscreen else "disabled"
        self._safe_status_update(self.lang_manager.get(f"fullscreen_{status}", f"Fullscreen {status}"), "info")

        if hasattr(self, 'menu_bar') and self.menu_bar:
            try:
                self.menu_bar.update_fullscreen_state(self._is_fullscreen)
            except:
                pass

    @safe_operation
    def _exit_fullscreen(self):
        """الخروج من وضع ملء الشاشة"""
        if self._is_fullscreen:
            system = platform.system()
            if system == "Windows":
                self.state('normal')
            else:
                try:
                    self.attributes('-fullscreen', False)
                except:
                    if system == "Linux":
                        self.attributes('-zoomed', False)

            self._is_fullscreen = False
            self._safe_status_update(self.lang_manager.get("fullscreen_disabled", "Fullscreen disabled"), "info")

    # ==================== دوال البيانات ====================

    @error_handler
    def _load_data(self):
        """تحميل البيانات"""
        self._safe_status_update(self.lang_manager.get("loading_data", "Loading data..."))
        self._safe_toolbar_update(set_loading=True)

        if self.window_state:
            self.window_state.is_loading = True

        def load_thread():
            try:
                records = self.controller.fetch_all_records()
                if self._is_window_valid():
                    self.safe_after.schedule(0, self._on_data_loaded, records)
            except Exception as e:
                if self._is_window_valid():
                    self.safe_after.schedule(0, self._on_load_error, str(e))

        threading.Thread(target=load_thread, daemon=True).start()

    @safe_operation
    def _on_data_loaded(self, records):
        """معالج تحميل البيانات"""
        self.all_records = records
        self.filtered_records = records

        if self.window_state:
            self.window_state.update_records(records)
            self.window_state.is_loading = False

        if hasattr(self, 'data_table') and self.data_table:
            try:
                self.data_table.display_data(records)
            except Exception as e:
                logger.error(f"Display data error: {e}")

        status_msg = self.lang_manager.get("status_load_complete", "{} records loaded").format(len(records))
        self._safe_status_update(status_msg, "success")
        self._safe_toolbar_update(set_loading=False)
        self._update_stats()

        if self.event_bus:
            self.event_bus.emit("data_loaded", {"count": len(records), "timestamp": datetime.now()})

    @safe_operation
    def _on_load_error(self, error_message):
        """معالج أخطاء التحميل"""
        self._safe_status_update(f"{self.lang_manager.get('error', 'Error')}: {error_message}", "error")
        self._safe_toolbar_update(set_loading=False)

        try:
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showerror(self.lang_manager.get("error", "Error"),
                               f"{self.lang_manager.get('error_load', 'Failed to load data')}:\n{error_message}")
        except:
            pass

    @error_handler
    def _refresh_data(self):
        """تحديث البيانات"""
        self._safe_status_update(self.lang_manager.get("refreshing_data", "Refreshing data..."))
        self._safe_toolbar_update(set_loading=True)

        def refresh_thread():
            try:
                records = self.controller.fetch_all_records(force_refresh=True)
                if self._is_window_valid():
                    self.safe_after.schedule(0, self._on_data_refreshed, records)
            except Exception as e:
                if self._is_window_valid():
                    self.safe_after.schedule(0, self._on_refresh_error, str(e))

        threading.Thread(target=refresh_thread, daemon=True).start()

    @safe_operation
    def _on_data_refreshed(self, records):
        """معالج تحديث البيانات"""
        self.all_records = records
        self.filtered_records = records

        if hasattr(self, 'data_table') and self.data_table:
            try:
                self.data_table.display_data(records)
            except Exception as e:
                logger.error(f"Display refreshed data error: {e}")

        status_msg = self.lang_manager.get("success_update", "Data updated successfully") + f" - {len(records)} " + \
                    self.lang_manager.get("total_records", "records")
        self._safe_status_update(status_msg, "success")
        self._safe_toolbar_update(set_loading=False)
        self._update_stats()

        self.selected_records = []
        self._safe_toolbar_update(update_selection=0)

    @safe_operation
    def _on_refresh_error(self, error_message):
        """معالج أخطاء التحديث"""
        self._safe_status_update(f"{self.lang_manager.get('error_update', 'Update error')}: {error_message}", "error")
        self._safe_toolbar_update(set_loading=False)

        try:
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showerror(self.lang_manager.get("error", "Error"),
                               f"{self.lang_manager.get('error_update', 'Failed to update data')}:\n{error_message}")
        except:
            pass

    @safe_operation
    def _on_search(self, search_text):
        """معالج البحث"""
        if not search_text:
            self.filtered_records = self.all_records
        else:
            search_lower = search_text.lower()
            self.filtered_records = [r for r in self.all_records
                                   if search_lower in str(r.get('fields', {})).lower()]

        if self.window_state:
            self.window_state.filtered_records = self.filtered_records
            self.window_state.search_query = search_text

        if hasattr(self, 'data_table') and self.data_table:
            try:
                self.data_table.display_data(self.filtered_records)
            except Exception as e:
                logger.error(f"Display search results error: {e}")

        status_msg = (f"{self.lang_manager.get('showing', 'Showing')} {len(self.filtered_records)} "
                     f"{self.lang_manager.get('of', 'of')} {len(self.all_records)} "
                     f"{self.lang_manager.get('total_records', 'records')}")
        self._safe_status_update(status_msg)

        if self.event_bus:
            self.event_bus.emit("search_completed", {"query": search_text, "results": len(self.filtered_records)})

    def _update_stats(self):
        """تحديث الإحصائيات"""
        try:
            if hasattr(self, 'sidebar') and self.sidebar and hasattr(self.sidebar, 'update_stats'):
                stats = {
                    'total': len(self.all_records),
                    'today': self._count_records('today'),
                    'pending': self._count_records('pending')
                }
                self.sidebar.update_stats(stats)
        except Exception as e:
            logger.debug(f"Update stats error: {e}")

    def _count_records(self, count_type):
        """عد السجلات حسب النوع"""
        try:
            if count_type == 'today':
                today = str(datetime.now().date())
                return sum(1 for r in self.all_records
                          if r.get('fields', {}).get('Date Trip', '')[:10] == today)
            elif count_type == 'pending':
                return sum(1 for r in self.all_records
                          if r.get('fields', {}).get('Booking Status', '').lower() == 'pending')
            return 0
        except Exception as e:
            logger.debug(f"Count records error: {e}")
            return 0

    # ==================== دوال CRUD ====================

    @error_handler
    def _add_record(self):
        """إضافة حجز جديد"""
        try:
            WindowManager.bring_to_front(self, duration=100)
            self.controller.open_add_form()
            self.safe_after.schedule(1000, self._refresh_data)
        except Exception as e:
            messagebox.showerror(self.lang_manager.get("error", "Error"),
                               self.lang_manager.get("error_add_form", "Failed to open add form"))

    @error_handler
    def _edit_record(self):
        """تعديل الحجز المحدد"""
        if not self.selected_records:
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showwarning(self.lang_manager.get("warning", "Warning"),
                                 self.lang_manager.get("select_booking_edit", "Please select a booking to edit"))
            return

        if len(self.selected_records) > 1:
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showwarning(self.lang_manager.get("warning", "Warning"),
                                 self.lang_manager.get("select_one_booking_only", "You can only edit one booking at a time"))
            return

        try:
            WindowManager.bring_to_front(self, duration=100)
            record = self.selected_records[0]
            self.controller.set_selected_record(record)
            self.controller.open_edit_form()
            self.safe_after.schedule(1000, self._refresh_data)
        except Exception as e:
            messagebox.showerror(self.lang_manager.get("error", "Error"),
                               self.lang_manager.get("error_edit_form", "Failed to open edit form"))

    @error_handler
    def _delete_record(self):
        """حذف الحجز المحدد"""
        if not self.selected_records:
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showwarning(self.lang_manager.get("warning", "Warning"),
                                 self.lang_manager.get("select_booking_delete", "Please select a booking to delete"))
            return

        # تأكيد الحذف
        count = len(self.selected_records)
        if count > 1:
            msg = self.lang_manager.get("confirm_delete_multiple", "Are you sure you want to delete {} bookings?").format(count)
        else:
            msg = self.lang_manager.get("confirm_delete", "Are you sure you want to delete this booking?")

        if not messagebox.askyesno(self.lang_manager.get("confirm", "Confirm"), msg):
            return

        def delete_thread():
            try:
                success_count = 0
                for record in self.selected_records:
                    self.controller.set_selected_record(record)
                    if self.controller.delete_record():
                        success_count += 1

                if self._is_window_valid():
                    self.safe_after.schedule(0, self._on_delete_complete, success_count, len(self.selected_records))
            except Exception as e:
                if self._is_window_valid():
                    self.safe_after.schedule(0, self._show_delete_error, str(e))

        self._safe_status_update(self.lang_manager.get("processing", "Processing..."))
        threading.Thread(target=delete_thread, daemon=True).start()

    @safe_operation
    def _on_delete_complete(self, success_count, total_count):
        """معالج اكتمال الحذف"""
        if success_count == total_count:
            msg = self.lang_manager.get("success_delete", "Deleted successfully") + f" ({success_count})"
            self._safe_status_update(msg, "success")
            messagebox.showinfo(self.lang_manager.get("success", "Success"), msg)
        else:
            msg = f"{success_count} {self.lang_manager.get('of', 'of')} {total_count} {self.lang_manager.get('deleted', 'deleted')}"
            self._safe_status_update(msg, "warning")
            WindowManager.flash_window(self, count=2, interval=300)
            messagebox.showwarning(self.lang_manager.get("warning", "Warning"), msg)

        self._refresh_data()
        if hasattr(self, 'data_table') and self.data_table:
            try:
                self.data_table.clear_selection()
            except:
                pass

        self.selected_records = []
        self._safe_toolbar_update(update_selection=0)

    @safe_operation
    def _show_delete_error(self, error_msg):
        """عرض خطأ الحذف"""
        try:
            messagebox.showerror(self.lang_manager.get("error", "Error"),
                               f"{self.lang_manager.get('error_delete', 'Failed to delete record')}:\n{error_msg}")
        except:
            pass

    # ==================== دوال الواجهة ====================

    @safe_operation
    def _on_row_double_click(self, record):
        """معالج النقر المزدوج"""
        if record:
            self.selected_records = [record]
            self._safe_toolbar_update(update_selection=1)
            self._edit_record()

    @safe_operation
    def _on_selection_change(self, selected_records):
        """معالج تغيير التحديد"""
        self.selected_records = selected_records
        count = len(selected_records)
        self._safe_toolbar_update(update_selection=count)

        if count == 0:
            status_msg = f"{self.lang_manager.get('showing', 'Showing')} {len(self.filtered_records)} {self.lang_manager.get('total_records', 'records')}"
        else:
            status_msg = self.lang_manager.get("selected_count", "Selected: {} booking(s)").format(count)

        self._safe_status_update(status_msg)

    @safe_operation
    def _on_navigate(self, destination):
        """معالج التنقل"""
        self._safe_status_update(f"{self.lang_manager.get('navigating_to', 'Navigating to')}: {destination}")

    # ==================== دوال اللغة والثيم ====================

    @error_handler
    def _toggle_language(self):
        """تبديل اللغة"""
        current_lang = self.lang_manager.current_lang
        new_lang = "en" if current_lang == "ar" else "ar"

        confirm_msg = self.lang_manager.get("confirm_change_language", "Change language?")
        if messagebox.askyesno(self.lang_manager.get("menu_change_language", "Change Language"), confirm_msg):
            self.lang_manager.set_language(new_lang)

            button_text = "🌐 EN" if new_lang == "ar" else "🌐 AR"
            if hasattr(self, 'language_button') and self.language_button:
                try:
                    self.language_button.configure(text=button_text)
                except:
                    pass

            self._update_all_texts()

            if hasattr(self.controller, 'update_all_windows_language'):
                try:
                    self.controller.update_all_windows_language()
                except:
                    pass

            self._safe_status_update(self.lang_manager.get("success_save", "Language changed successfully"), "success")

    @error_handler
    def _toggle_theme(self):
        """تبديل الثيم"""
        current_mode = self.theme_manager.get_current_appearance_mode()
        new_mode = "dark" if current_mode == "light" else "light"

        self.theme_manager.apply_appearance_mode(new_mode)
        ctk.set_appearance_mode(new_mode)

        self.themed_window.refresh_theme()
        self._refresh_all_components_theme()

        theme_name = "Dark" if new_mode == "dark" else "Light"
        self._safe_status_update(f"Theme changed to {theme_name}", "success")

    @safe_operation
    def _handle_language_change(self, new_language):
        """معالج تغيير اللغة من الهيدر"""
        self.lang_manager.set_language(new_language)

        button_text = "🌐 EN" if new_language == "ar" else "🌐 AR"
        if hasattr(self, 'language_button') and self.language_button:
            try:
                self.language_button.configure(text=button_text)
            except:
                pass

        self._update_all_texts()

        if hasattr(self.controller, 'update_all_windows_language'):
            try:
                self.controller.update_all_windows_language()
            except:
                pass

        self._safe_status_update(self.lang_manager.get("success_save", "Language changed successfully"), "success")

    @safe_operation
    def _handle_theme_change(self, new_theme):
        """معالج تغيير الثيم من الهيدر"""
        ctk.set_appearance_mode(new_theme.lower())

        if hasattr(self.theme_manager, 'apply_appearance_mode'):
            self.theme_manager.apply_appearance_mode(new_theme.lower())
        elif hasattr(self.theme_manager, 'current_mode'):
            self.theme_manager.current_mode = new_theme.lower()

        self._apply_theme()
        self.refresh_theme()

        if hasattr(self, 'menu_bar') and self.menu_bar:
            try:
                self.menu_bar.update_dark_mode(new_theme.lower() == "dark")
            except:
                pass

        theme_name = "Dark" if new_theme.lower() == "dark" else "Light"
        self._safe_status_update(f"Theme changed to {theme_name}", "success")

    @safe_operation
    def _update_all_texts(self):
        """تحديث جميع النصوص"""
        username = self.user_record.get('fields', {}).get('Username', 'User')
        self.title(f"{self.lang_manager.get('main_window_title', 'FTS Sales Manager')} - {username}")

        # تحديث المكونات
        components = ['header', 'sidebar', 'toolbar', 'data_table', 'status_bar']
        for component_name in components:
            if hasattr(self, component_name):
                component = getattr(self, component_name)
                if component and hasattr(component, 'update_texts'):
                    try:
                        component.update_texts(self.lang_manager)
                    except Exception as e:
                        logger.debug(f"Update texts error for {component_name}: {e}")

        if hasattr(self, 'menu_bar') and self.menu_bar and hasattr(self.menu_bar, 'update_texts'):
            try:
                self.menu_bar.update_texts()
            except:
                pass

        if hasattr(self, 'table_title') and self.table_title:
            try:
                self.table_title.configure(text=self.lang_manager.get("bookings_list", "Bookings List"))
            except:
                pass

    @safe_operation
    def _refresh_all_components_theme(self):
        """تحديث ثيم جميع المكونات"""
        if hasattr(self, 'main_container') and self.main_container:
            self.themed_window.apply_to_widget(self.main_container, 'frame')

        components = ['header', 'sidebar', 'toolbar', 'data_table', 'status_bar']
        for component_name in components:
            if hasattr(self, component_name):
                component = getattr(self, component_name)
                if component:
                    try:
                        if hasattr(component, 'refresh_theme'):
                            component.refresh_theme()
                        elif hasattr(component, 'apply_theme'):
                            component.apply_theme(self.themed_window)
                    except Exception as e:
                        logger.debug(f"Refresh theme error for {component_name}: {e}")

        if hasattr(self, 'windows7_menubar'):
            self._update_windows7_menubar_theme()

    def _update_windows7_menubar_theme(self):
        """تحديث ثيم شريط قوائم Windows 7"""
        try:
            colors = getattr(self.theme_manager, 'get_theme_colors', lambda: {
                "menu_bg": self.themed_window.get_color('surface'),
                "text_color": self.themed_window.get_color('text_primary'),
                "menu_hover": self.themed_window.get_color('input_bg')
            })()

            if hasattr(self, 'windows7_menubar') and self.windows7_menubar:
                self.windows7_menubar.configure(fg_color=colors.get("menu_bg"))

                for widget in self.windows7_menubar.winfo_children():
                    if isinstance(widget, ctk.CTkButton):
                        widget.configure(text_color=colors.get("text_color"), hover_color=colors.get("menu_hover"))
        except Exception as e:
            logger.debug(f"Windows 7 menubar theme update error: {e}")

    def refresh_theme(self):
        """تحديث الثيم العام"""
        try:
            self._apply_theme()
            if hasattr(self, 'main_container') and self.main_container:
                self.main_container.configure(fg_color="transparent")
            self._refresh_all_components_theme()
        except Exception as e:
            logger.error(f"Refresh theme error: {e}")

    def get_themed_color(self, color_name: str, fallback: str = None) -> str:
        """دالة مساعدة للحصول على الألوان"""
        return self.themed_window.get_color(color_name, fallback)

    # ==================== دوال الاختصارات ====================

    @safe_operation
    def _focus_search(self):
        """التركيز على حقل البحث"""
        if hasattr(self.header, 'search_entry') and self.header.search_entry:
            self.header.search_entry.focus_set()
            WindowManager.bring_to_front(self, duration=100)

    @safe_operation
    def _select_all(self):
        """تحديد جميع السجلات"""
        if hasattr(self.data_table, 'tree') and self.data_table.tree:
            self.data_table.tree.selection_set(self.data_table.tree.get_children())
            self._on_selection_change(self.all_records)

    @safe_operation
    def _clear_selection(self):
        """إلغاء التحديد"""
        if hasattr(self.data_table, 'clear_selection'):
            self.data_table.clear_selection()
        self.selected_records = []
        self._safe_toolbar_update(update_selection=0)

    # ==================== دوال القوائم ====================

    def _show_menu(self):
        """عرض قائمة عامة (Windows 7)"""
        pass

    def _show_placeholder(self):
        """عرض رسالة placeholder للميزات قيد التطوير"""
        self._safe_status_update(self.lang_manager.get("coming_soon", "Coming soon"), "info")

    @error_handler
    def _logout(self):
        """تسجيل الخروج"""
        if messagebox.askyesno(self.lang_manager.get("confirm", "Confirm"),
                             self.lang_manager.get("confirm_logout", "Are you sure you want to logout?")):
            self.destroy()
            if hasattr(self.controller, 'on_logout'):
                try:
                    self.controller.on_logout()
                except:
                    pass
            if hasattr(self.controller, 'run'):
                try:
                    self.controller.run()
                except:
                    pass

    @error_handler
    def _export_data(self):
        """تصدير البيانات"""
        self._safe_status_update(self.lang_manager.get("export", "Export") + " - " +
                                 self.lang_manager.get("coming_soon", "Coming soon"))
        WindowManager.flash_window(self, count=2, interval=300)
        messagebox.showinfo(self.lang_manager.get("info", "Information"),
                          self.lang_manager.get("export_coming_soon", "Export feature coming soon"))

    @safe_operation
    def _change_language_from_menu(self, lang_code: str):
        """تغيير اللغة من القائمة"""
        if self.lang_manager.current_lang != lang_code:
            self.lang_manager.set_language(lang_code)

            button_text = "🌐 EN" if lang_code == "ar" else "🌐 AR"
            if hasattr(self, 'language_button') and self.language_button:
                try:
                    self.language_button.configure(text=button_text)
                except:
                    pass

            self._update_all_texts()

            if hasattr(self.controller, 'update_all_windows_language'):
                try:
                    self.controller.update_all_windows_language()
                except:
                    pass

            self._safe_status_update(self.lang_manager.get("success_save", "Language changed successfully"), "success")

    @safe_operation
    def _on_fullscreen_changed(self, is_fullscreen: bool):
        """معالج تغيير وضع ملء الشاشة"""
        self._is_fullscreen = is_fullscreen
        status = "enabled" if is_fullscreen else "disabled"
        self._safe_status_update(self.lang_manager.get(f"fullscreen_{status}", f"Fullscreen {status}"), "info")

    @safe_operation
    def _on_performance_mode_changed(self, is_enabled: bool):
        """معالج تغيير وضع الأداء العالي"""
        status_key = "performance_mode_enabled" if is_enabled else "performance_mode_disabled"
        self._safe_status_update(self.lang_manager.get(status_key, f"Performance mode {'enabled' if is_enabled else 'disabled'}"), "info")

        if hasattr(self.data_table, 'tree') and self.data_table.tree:
            height = 20 if is_enabled else 15
            self.data_table.tree.configure(height=height)

    @error_handler
    def _show_statistics(self):
        """عرض الإحصائيات"""
        stats_msg = f"""
{self.lang_manager.get("statistics", "Statistics")}:

{self.lang_manager.get("total_records", "Total Records")}: {len(self.all_records)}
{self.lang_manager.get("today_bookings", "Today's Bookings")}: {self._count_records('today')}
{self.lang_manager.get("pending_bookings", "Pending Bookings")}: {self._count_records('pending')}
"""
        messagebox.showinfo(self.lang_manager.get("statistics", "Statistics"), stats_msg)

    @error_handler
    def _show_reports(self):
        """عرض التقارير"""
        self._safe_status_update(self.lang_manager.get("reports_coming_soon", "Reports feature coming soon"), "info")
        messagebox.showinfo(self.lang_manager.get("info", "Information"),
                          self.lang_manager.get("reports_coming_soon", "Reports feature coming soon"))

    @error_handler
    def _clear_cache(self):
        """مسح الذاكرة المؤقتة"""
        if messagebox.askyesno(self.lang_manager.get("confirm", "Confirm"),
                             self.lang_manager.get("confirm_clear_cache", "Clear all cached data?")):
            self._safe_status_update(self.lang_manager.get("cache_cleared", "Cache cleared successfully"), "success")

    @error_handler
    def _show_help(self):
        """عرض المساعدة"""
        help_text = f"""
{self.lang_manager.get("keyboard_shortcuts", "Keyboard Shortcuts")}:

- Ctrl+N - {self.lang_manager.get("add_button", "Add Booking")}
- Ctrl+E - {self.lang_manager.get("edit_button", "Edit Booking")}
- Delete - {self.lang_manager.get("delete_button", "Delete Booking")}
- F5 - {self.lang_manager.get("refresh", "Refresh")}
- Ctrl+F - {self.lang_manager.get("search", "Search")}
- Ctrl+A - {self.lang_manager.get("select_all", "Select All")}
- Escape - {self.lang_manager.get("exit_fullscreen", "Exit Fullscreen")}
- F11 - {self.lang_manager.get("fullscreen", "Toggle Fullscreen")}
- F1 - {self.lang_manager.get("help", "Help")}
"""
        messagebox.showinfo(self.lang_manager.get("keyboard_shortcuts", "Keyboard Shortcuts"), help_text)

    @error_handler
    def _show_user_guide(self):
        """عرض دليل المستخدم"""
        guide_msg = f"""
{self.lang_manager.get("user_guide", "User Guide")}:

1. {self.lang_manager.get("guide_add", "To add a booking: Click Add button or press Ctrl+N")}
2. {self.lang_manager.get("guide_edit", "To edit: Double-click on a booking or press Ctrl+E")}
3. {self.lang_manager.get("guide_delete", "To delete: Select bookings and press Delete")}
4. {self.lang_manager.get("guide_search", "To search: Use the search box or press Ctrl+F")}
5. {self.lang_manager.get("guide_fullscreen", "To toggle fullscreen: Press F11 or Alt+Enter")}
"""
        messagebox.showinfo(self.lang_manager.get("user_guide", "User Guide"), guide_msg)

    @error_handler
    def _show_about(self):
        """عرض معلومات البرنامج"""
        about_msg = f"""
{self.lang_manager.get("app_name", "FTS Sales Manager")}
{self.lang_manager.get("version", "Version")}: 2.0

{self.lang_manager.get("developed_by", "Developed by")}: FTS Development Team
{self.lang_manager.get("copyright", "© 2024 FTS. All rights reserved.")}

{self.lang_manager.get("logged_as", "Logged in as")}: {self.user_record.get('fields', {}).get('Username', 'User')}
{self.lang_manager.get("user_role", "Role")}: {self.user_record.get('fields', {}).get('Role', 'User')}
"""
        messagebox.showinfo(self.lang_manager.get("about", "About"), about_msg)

    # ==================== معالجات الأحداث الجديدة ====================

    def _on_data_loaded_event(self, data):
        """معالج حدث تحميل البيانات"""
        logger.info(f"Data loaded event: {data}")

    def _on_search_completed_event(self, data):
        """معالج حدث اكتمال البحث"""
        logger.info(f"Search completed: {data}")

    def _on_error_event(self, data):
        """معالج حدث الخطأ"""
        logger.error(f"Error event: {data}")

    # ==================== حفظ واستعادة حالة النافذة ====================

    def _save_window_state(self):
        """حفظ حالة النافذة"""
        try:
            window_state = {
                'fullscreen': self._is_fullscreen,
                'geometry': self.geometry() if not self._is_fullscreen else None,
                'state': self.state() if hasattr(self, 'state') else None
            }

            if hasattr(self.controller, 'config_mgr'):
                self.controller.config_mgr.set('main_window_state', window_state)
                logger.debug("Window state saved")
        except Exception as e:
            logger.error(f"Save window state error: {e}")

    def _restore_window_state(self):
        """استعادة حالة النافذة"""
        try:
            if hasattr(self.controller, 'config_mgr'):
                window_state = self.controller.config_mgr.get('main_window_state', {})

                if window_state.get('fullscreen', True):
                    self.safe_after.schedule(200, self._apply_fullscreen_mode)
                elif window_state.get('geometry'):
                    self.geometry(window_state['geometry'])
                else:
                    self.safe_after.schedule(200, self._apply_fullscreen_mode)
        except Exception as e:
            logger.error(f"Restore window state error: {e}")
            self.safe_after.schedule(200, self._apply_fullscreen_mode)

    # ==================== معالج الإغلاق ====================

    def _on_close(self):
        """معالج إغلاق النافذة"""
        if self._closing:
            return

        try:
            if messagebox.askyesno(self.lang_manager.get("confirm", "Confirm"),
                                 self.lang_manager.get("confirm_exit", "Are you sure you want to exit?")):
                self._closing = True
                self._window_destroyed = True

                # حفظ الحالة وتنظيف الموارد
                self._save_window_state()

                if hasattr(self, 'safe_after'):
                    self.safe_after.cancel_all()

                if hasattr(self, 'async_manager') and self.async_manager:
                    try:
                        self.async_manager.shutdown()
                    except:
                        pass

                # إغلاق النوافذ الفرعية
                if hasattr(self.controller, 'open_edit_windows'):
                    for window in list(self.controller.open_edit_windows):
                        try:
                            if hasattr(window, 'winfo_exists') and window.winfo_exists():
                                window.destroy()
                        except:
                            pass
                    try:
                        self.controller.open_edit_windows.clear()
                    except:
                        pass

                # تنظيف المتحكم
                if hasattr(self.controller, 'cleanup'):
                    try:
                        self.controller.cleanup()
                    except:
                        pass

                # إغلاق النافذة
                try:
                    self.quit()
                    self.destroy()
                except:
                    try:
                        self.withdraw()
                    except:
                        pass
        except Exception as e:
            logger.error(f"Close error: {e}")
            self._closing = True
            self._window_destroyed = True
            try:
                self.destroy()
            except:
                pass