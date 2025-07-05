# -*- coding: utf-8 -*-
"""
views/login_window.py

نافذة تسجيل دخول احترافية محسنة مع ارتفاع منطقة العمل (من أعلى الشاشة حتى شريط المهام)
Enhanced Professional Login Window with Workarea Height Layout
"""

import customtkinter as ctk
from tkinter import messagebox
import json
import os
import re
import time
import hashlib
import secrets
import platform
from typing import Any, Callable, Optional, Dict, Tuple
from datetime import datetime, timedelta
import threading
from functools import wraps
import queue

# Core imports
from core.language_manager import LanguageManager
from core.theme_manager import ThemeManager
from core.logger import logger

# النظام الموحد للثيمات والألوان
from core.theme_color_manager import ThemeColorManager, ThemedWindow

# استيراد لوحات الألوان
try:
    from config.modern_color_palettes import get_color_palette, get_available_palettes
    COLOR_PALETTES_AVAILABLE = True
except ImportError:
    COLOR_PALETTES_AVAILABLE = False
    logger.warning("Color palettes module not found. Using default colors.")

# Security imports
try:
    from core.security.encryption import EncryptionManager
    from core.security.rate_limiter import RateLimiter
    from utils.validators import InputValidator
    from config.login_config import LOGIN_CONFIG
    from core.constants import LoginConstants
    try:
        from core.constants import WindowConstants
        if not hasattr(WindowConstants, 'SCREEN_HEIGHT_RATIO'):
            raise AttributeError("Missing SCREEN_HEIGHT_RATIO")
    except (ImportError, AttributeError):
        WindowConstants = None
except ImportError:
    EncryptionManager = None
    RateLimiter = None
    InputValidator = None
    LOGIN_CONFIG = {}
    WindowConstants = None

    class LoginConstants:
        MIN_PASSWORD_LENGTH = 8
        MAX_LOGIN_ATTEMPTS = 5
        LOGIN_TIMEOUT = 30
        SESSION_TIMEOUT = 1800
        PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        LOCKOUT_DURATION = 300

# Window Constants - Updated for workarea height layout
class LocalWindowConstants:
    MIN_WINDOW_WIDTH = 380
    MIN_WINDOW_HEIGHT = 500
    MAX_WINDOW_WIDTH = 450
    DEFAULT_WINDOW_WIDTH = 400
    SCREEN_HEIGHT_RATIO = 0.85
    ANIMATION_DURATION = 300
    FLASH_INTERVAL = 300
    WORKAREA_HEIGHT_ENABLED = True  # تفعيل ارتفاع منطقة العمل
    FULL_HEIGHT_ENABLED = False     # إلغاء الارتفاع الكامل

if WindowConstants is None:
    WindowConstants = LocalWindowConstants
else:
    for attr in ['SCREEN_HEIGHT_RATIO', 'DEFAULT_WINDOW_WIDTH', 'MAX_WINDOW_WIDTH', 'MIN_WINDOW_HEIGHT', 'WORKAREA_HEIGHT_ENABLED']:
        if not hasattr(WindowConstants, attr):
            setattr(WindowConstants, attr, getattr(LocalWindowConstants, attr))

# Window Manager import with workarea height support
try:
    from utils.window_manager import WindowManager, setup_dialog_window, setup_login_window, setup_add_edit_window, setup_dialog_window_workarea
    WINDOW_MANAGER_AVAILABLE = True
except ImportError:
    WINDOW_MANAGER_AVAILABLE = False
    WindowManager = None
    setup_dialog_window = None
    setup_login_window = None
    setup_add_edit_window = None
    setup_dialog_window_workarea = None


def login_error_handler(func):
    """Decorator لمعالجة أخطاء تسجيل الدخول"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            if hasattr(self, '_show_status'):
                self._show_status(f"Error: {str(e)}", "error")
    return wrapper


class LoginWindow(ctk.CTk):
    """
    نافذة تسجيل دخول احترافية محسنة بارتفاع منطقة العمل
    """

    # قيم ثابتة للنافذة - محدثة لارتفاع منطقة العمل
    WINDOW_MIN_WIDTH = 380
    WINDOW_MIN_HEIGHT = 500
    WINDOW_MAX_WIDTH = 450
    WINDOW_DEFAULT_WIDTH = 400
    WINDOW_SCREEN_RATIO = 0.85
    WINDOW_ANIMATION_DURATION = 300
    WINDOW_FLASH_INTERVAL = 300
    WORKAREA_HEIGHT_MODE = True   # تفعيل وضع ارتفاع منطقة العمل
    COMPACT_MODE = False          # إلغاء التصميم المضغوط

    def __init__(
        self,
        controller: Any = None,
        lang_manager: LanguageManager = None,
        theme_manager: ThemeManager = None,
        airtable_model: Any = None,
        user_mgr: Any = None,
        on_login_success: Callable[[Dict[str, Any]], None] = None,
        validate_credentials: Callable[[str, str], Optional[Dict[str, Any]]] = None,
        parent_window: Any = None,
        enable_2fa: bool = False,
        enable_encryption: bool = True,
        enable_rate_limiting: bool = True,
        workarea_height: bool = True  # جديد: للتحكم في ارتفاع منطقة العمل
    ):
        super().__init__()

        # التحقق من صحة parent_window
        self.parent_window = None
        if parent_window:
            if hasattr(parent_window, 'winfo_exists') and hasattr(parent_window, 'tk'):
                try:
                    parent_window.winfo_exists()
                    self.parent_window = parent_window
                except:
                    logger.debug("Parent window is not a valid Tkinter window")

        # إعداد وضع ارتفاع منطقة العمل
        self.workarea_height = workarea_height and self.WORKAREA_HEIGHT_MODE

        # Security features flags
        self.enable_2fa = enable_2fa
        self.enable_encryption = enable_encryption and EncryptionManager is not None
        self.enable_rate_limiting = enable_rate_limiting and RateLimiter is not None

        # Initialize security managers
        self.encryption_manager = EncryptionManager() if self.enable_encryption else None
        self.rate_limiter = RateLimiter() if self.enable_rate_limiting else None

        # معالجة المعاملات
        self.controller = controller
        self.airtable_model = airtable_model
        self.user_mgr = user_mgr

        # إعداد المتغيرات الأساسية
        if controller:
            self.lang_manager = lang_manager or (controller.lang_manager if hasattr(controller, 'lang_manager') else None)
            self.theme_manager = theme_manager or (controller.theme_manager if hasattr(controller, 'theme_manager') else None)
            self.on_login_success = on_login_success or (lambda user_info: controller.on_login_success(user_info))

            if user_mgr and hasattr(user_mgr, 'authenticate'):
                self.validate_credentials = user_mgr.authenticate
            else:
                self.validate_credentials = validate_credentials
        else:
            self.lang_manager = lang_manager
            self.theme_manager = theme_manager
            self.on_login_success = on_login_success
            self.validate_credentials = validate_credentials

        # التحقق من وجود المتطلبات الأساسية
        if not self.lang_manager:
            raise ValueError("LanguageManager is required")
        if not self.theme_manager:
            raise ValueError("ThemeManager is required")

        # النظام الموحد للثيمات والألوان
        self.themed_window = ThemedWindow(self, self.theme_manager)

        # متغيرات داخلية
        self.remember_me = ctk.BooleanVar(value=False)
        self._closing = False
        self._login_attempts = 0
        self._show_password = False
        self._caps_lock_on = False
        self._session_token = None
        self._csrf_token = self._generate_csrf_token()

        try:
            # إعداد النافذة
            self._setup_window()

            # بناء الواجهة بارتفاع منطقة العمل
            self._build_workarea_ui()

            # تحميل بيانات الدخول المحفوظة
            self._load_saved_credentials()

            # Setup window with workarea height layout
            self._setup_window_with_manager()

            # Bind keyboard events
            self.after(50, self._bind_keyboard_events)

            # التركيز على الحقل المناسب
            def set_initial_focus():
                if self._closing or not self.winfo_exists():
                    return
                try:
                    if hasattr(self, 'entry_username') and self.entry_username.winfo_exists():
                        if self.entry_username.get():
                            if hasattr(self, 'entry_password') and self.entry_password.winfo_exists():
                                self.entry_password.focus_set()
                        else:
                            self.entry_username.focus_set()
                except Exception as e:
                    logger.debug(f"Error setting initial focus: {e}")

            if self.winfo_exists():
                self.after(100, set_initial_focus)

            # Start session timeout timer
            self._start_session_timer()

        except Exception as e:
            logger.error(f"Error during initialization: {e}")
            self._on_close()

    def _get_color(self, color_name: str, fallback: str = None) -> str:
        """دالة موحدة للحصول على الألوان"""
        return self.themed_window.get_color(color_name, fallback)

    def _apply_theme(self):
        """تطبيق الثيم الموحد"""
        self.themed_window.apply_theme()

    def _calculate_optimal_window_size(self):
        """حساب الحجم الأمثل للنافذة بارتفاع محدود"""
        try:
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # تحديد العرض
            if screen_width < 500:
                window_width = int(screen_width * 0.85)
            elif screen_width < 800:
                window_width = min(400, int(screen_width * 0.5))
            else:
                window_width = 400

            # تحديد ارتفاع محدود ومناسب (بدلاً من ارتفاع منطقة العمل الكامل)
            if screen_height <= 768:
                window_height = 600  # ارتفاع صغير للشاشات الصغيرة
            elif screen_height <= 1080:
                window_height = 700  # ارتفاع متوسط للشاشات العادية
            else:
                window_height = 750  # ارتفاع أكبر قليلاً للشاشات الكبيرة

            # التأكد من عدم تجاوز الحد الأدنى والأقصى
            window_height = max(window_height, self.WINDOW_MIN_HEIGHT)
            window_height = min(window_height, int(screen_height * 0.8))  # لا يتجاوز 80% من الشاشة

            logger.debug(f"Limited window size: {window_width}x{window_height} for screen {screen_width}x{screen_height}")

            return window_width, window_height

        except Exception as e:
            logger.error(f"Error calculating window size: {e}")
            return 400, 650  # قيم افتراضية محدودة

    def _get_available_color_palettes(self):
        """الحصول على قائمة اللوحات المتاحة للوضع الفاتح"""
        if COLOR_PALETTES_AVAILABLE:
            all_palettes = get_available_palettes()
            return [p for p in all_palettes if p != 'modern_dark']
        return []

    def _save_color_palette_preference(self, palette_name):
        """حفظ تفضيل لوحة الألوان"""
        if hasattr(self, 'controller') and hasattr(self.controller, 'config_manager'):
            self.controller.config_manager.set('light_color_palette', palette_name)
            self.controller.config_manager.save()
            logger.info(f"Saved color palette preference: {palette_name}")

    def _setup_window_with_manager(self):
        """إعداد النافذة باستخدام WindowManager بارتفاع محدود"""
        window_width, window_height = self._calculate_optimal_window_size()

        if WINDOW_MANAGER_AVAILABLE:
            try:
                # استخدام ارتفاع محدود بدلاً من ارتفاع منطقة العمل الكامل
                if setup_dialog_window:
                    setup_dialog_window(
                        self,
                        size=(window_width, window_height),  # استخدام الارتفاع المحسوب
                        parent=self.parent_window,
                        focus=True,
                        topmost_duration=500
                    )
                    logger.debug("Login window setup with limited height using setup_dialog_window")

                else:
                    # الطريقة المباشرة مع ارتفاع محدود
                    WindowManager.setup_centered_window(
                        self,
                        size=(window_width, window_height),
                        parent=self.parent_window,
                        focus=True,
                        topmost_duration=500,
                        modal=True
                    )
                    logger.debug("Login window setup with limited height using direct method")

                # تحريك النافذة إذا كان متاحاً
                if hasattr(WindowManager, 'animate_window_open'):
                    WindowManager.animate_window_open(self, duration=self.WINDOW_ANIMATION_DURATION)

                # إعداد اختصارات النافذة
                if hasattr(WindowManager, 'setup_window_shortcuts'):
                    WindowManager.setup_window_shortcuts(self)

            except Exception as e:
                logger.error(f"Error setting up window with WindowManager: {e}")
                self._fallback_window_setup()
        else:
            self._fallback_window_setup()

    def _fallback_window_setup(self):
        """إعداد احتياطي للنافذة بارتفاع محدود"""
        try:
            window_width, window_height = self._calculate_optimal_window_size()

            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()

            # التوسيط العادي (وسط الشاشة)
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            # التأكد من أن النافذة داخل حدود الشاشة
            x = max(10, min(x, screen_width - window_width - 10))
            y = max(10, min(y, screen_height - window_height - 50))  # ترك مساحة لشريط المهام

            self.geometry(f"{window_width}x{window_height}+{x}+{y}")

            logger.debug(f"Fallback limited window setup: {window_width}x{window_height} at ({x}, {y})")

            self.lift()
            self.focus_force()

            if self.parent_window:
                try:
                    self.transient(self.parent_window)
                    self.grab_set()
                except:
                    pass

        except Exception as e:
            logger.error(f"Error in fallback window setup: {e}")

    def _generate_csrf_token(self) -> str:
        """Generate CSRF token for security"""
        return secrets.token_urlsafe(32)

    def _bind_keyboard_events(self):
        """Bind keyboard events"""
        if self._closing or not self.winfo_exists():
            return

        try:
            self.bind("<KeyPress>", self._check_caps_lock)
            self.bind("<KeyRelease>", self._check_caps_lock)
            self.bind("<Escape>", lambda e: self._on_close())
            self.bind("<F1>", lambda e: self._show_help())
        except Exception as e:
            logger.error(f"Error binding keyboard events: {e}")

    def _check_caps_lock(self, event=None):
        """Check if Caps Lock is on"""
        try:
            if not self.winfo_exists() or self._closing:
                return

            if hasattr(self, 'entry_password') and self.entry_password.focus_get() == self.entry_password:
                if event and event.keysym == 'Caps_Lock':
                    self._caps_lock_on = not self._caps_lock_on
                else:
                    try:
                        import ctypes
                        if platform.system() == "Windows":
                            hllDll = ctypes.WinDLL("User32.dll")
                            VK_CAPITAL = 0x14
                            self._caps_lock_on = bool(hllDll.GetKeyState(VK_CAPITAL) & 1)
                    except:
                        pass

                if self._caps_lock_on and hasattr(self, 'caps_lock_warning'):
                    self.caps_lock_warning.pack(anchor="w", pady=(1, 0))
                elif hasattr(self, 'caps_lock_warning'):
                    self.caps_lock_warning.pack_forget()
        except Exception as e:
            logger.debug(f"Error checking caps lock: {e}")

    def _start_session_timer(self):
        """Start session timeout timer"""
        self._last_activity = time.time()
        self._check_session_timeout()

    def _check_session_timeout(self):
        """Check for session timeout"""
        if self._closing or not self.winfo_exists():
            return

        if time.time() - self._last_activity > LoginConstants.SESSION_TIMEOUT:
            self._show_status(
                self.lang_manager.get("session_timeout", "Session timed out. Please login again."),
                "warning"
            )
            self._on_close()
        else:
            self.after(60000, self._check_session_timeout)

    def _update_activity(self):
        """Update last activity time"""
        self._last_activity = time.time()

    def safe_after(self, ms, func):
        """جدولة دالة بشكل آمن"""
        try:
            if not self._closing and self.winfo_exists():
                return self.after(ms, func)
        except Exception as e:
            if "main thread is not in main loop" in str(e):
                try:
                    return self.after_idle(func)
                except:
                    pass
            logger.error(f"Error in safe_after: {e}")
        return None

    def _setup_window(self):
        """إعداد النافذة بارتفاع منطقة العمل"""
        self.title(self.lang_manager.get("login_window_title", "Login - FTS Sales Manager"))

        self.minsize(self.WINDOW_MIN_WIDTH, self.WINDOW_MIN_HEIGHT)
        self.resizable(False, False)  # منع تغيير الحجم

        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._apply_theme()

        try:
            if os.path.exists("assets/icon.ico"):
                self.iconbitmap("assets/icon.ico")
            else:
                possible_paths = [
                    "assets/icon.ico",
                    "../assets/icon.ico",
                    "../../assets/icon.ico",
                    os.path.join(os.path.dirname(__file__), "../assets/icon.ico")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        self.iconbitmap(path)
                        break
        except Exception as e:
            logger.debug(f"Could not set window icon: {e}")

    def _build_workarea_ui(self):
        """بناء واجهة المستخدم بتخطيط مضغوط ومحسن"""

        # تعيين لون الخلفية الرئيسي
        self.configure(fg_color=self._get_color('background'))

        # الحاوية الرئيسية مع هوامش معقولة
        main_padding = 10
        main_container = ctk.CTkFrame(self, fg_color=self._get_color('background'))
        main_container.pack(fill="both", expand=True, padx=main_padding, pady=main_padding)

        # البطاقة الرئيسية
        card_frame = ctk.CTkFrame(
            main_container,
            fg_color=self._get_color('surface'),
            corner_radius=16,
            border_width=0
        )
        card_frame.pack(fill="both", expand=True)

        # إطار المحتوى العادي (بدون scrollable frame للتوفير في المساحة)
        content_padding = 15
        self.content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=content_padding, pady=content_padding)

        # بناء الأقسام مع تباعد مضغوط
        self._create_compact_header(self.content_frame)
        self._create_compact_login_form(self.content_frame)
        self._create_compact_buttons(self.content_frame)
        self._create_compact_status_area(self.content_frame)
        self._create_compact_footer(self.content_frame)

    def _ensure_content_visibility(self):
        """ضمان إظهار جميع المحتويات في الإطار القابل للتمرير"""
        try:
            if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
                self.scrollable_frame.update_idletasks()
                self.scrollable_frame._parent_canvas.yview_moveto(0)
                self.update()
        except Exception as e:
            logger.debug(f"Error ensuring content visibility: {e}")

    def _create_compact_header(self, parent):
        """إنشاء رأس مضغوط"""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(5, 15))

        # حاوية الشعار المضغوطة
        logo_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_container.pack()

        # شعار مضغوط
        logo_size = 50
        logo_bg = ctk.CTkFrame(
            logo_container,
            width=logo_size,
            height=logo_size,
            corner_radius=logo_size//2,
            fg_color=self._get_color('primary')
        )
        logo_bg.pack()
        logo_bg.pack_propagate(False)

        # حلقة خارجية مضغوطة
        logo_ring = ctk.CTkFrame(
            logo_container,
            width=logo_size + 8,
            height=logo_size + 8,
            corner_radius=(logo_size + 8)//2,
            fg_color=self._get_color('surface'),
            border_width=2,
            border_color=self._get_color('primary')
        )
        logo_ring.place(relx=0.5, rely=0.5, anchor="center")
        logo_bg.lift()

        # نص الشعار المضغوط
        logo_text = ctk.CTkLabel(
            logo_bg,
            text="FTS",
            font=ctk.CTkFont(family="Helvetica", size=18, weight="bold"),
            text_color="white"
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

        # العنوان الرئيسي المضغوط
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="FTS Sales Manager",
            font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"),
            text_color=self._get_color('text_primary')
        )
        self.title_label.pack(pady=(10, 3))

        # العنوان الفرعي المضغوط
        self.subtitle_label = ctk.CTkLabel(
            header_frame,
            text=self.lang_manager.get("login_subtitle", "Secure access to your sales dashboard"),
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color=self._get_color('text_secondary'),
            wraplength=320
        )
        self.subtitle_label.pack(pady=(0, 8))

        # خط فاصل رفيع
        separator = ctk.CTkFrame(header_frame, height=1, fg_color=self._get_color('input_border'))
        separator.pack(fill="x", pady=(10, 0))

    def _create_compact_login_form(self, parent):
        """إنشاء نموذج تسجيل دخول مضغوط"""
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(fill="x", pady=(12, 10))

        # حقل اسم المستخدم
        self._create_compact_input_field(
            form_frame,
            label_text=self.lang_manager.get("username", "Username"),
            placeholder=self.lang_manager.get("enter_username", "Enter your username"),
            icon="👤",
            field_name="username"
        )

        # حقل كلمة المرور
        self._create_compact_password_field(form_frame)

        # الخيارات
        self._create_compact_options(form_frame)

        # 2FA field if enabled
        if self.enable_2fa:
            self._create_compact_2fa_field(form_frame)

    def _create_compact_input_field(self, parent, label_text, placeholder, icon, field_name):
        """إنشاء حقل إدخال مضغوط"""
        # أحجام مضغوطة
        label_font_size = 13
        field_height = 36
        padding_bottom = 5
        field_padding = 8

        # تسمية الحقل
        label = ctk.CTkLabel(
            parent,
            text=label_text,
            font=ctk.CTkFont(family="Helvetica", size=label_font_size, weight="bold"),
            text_color=self._get_color('text_primary'),
            anchor="w"
        )
        label.pack(fill="x", pady=(0, padding_bottom))

        # إطار الحقل
        field_container = ctk.CTkFrame(
            parent,
            fg_color=self._get_color('input_bg'),
            corner_radius=10,
            border_width=1,
            border_color=self._get_color('input_border')
        )
        field_container.pack(fill="x", pady=(0, field_padding))

        # الإطار الداخلي
        field_frame = ctk.CTkFrame(field_container, fg_color="transparent")
        field_frame.pack(fill="x", padx=10, pady=6)

        # الأيقونة
        icon_label = ctk.CTkLabel(
            field_frame,
            text=icon,
            font=ctk.CTkFont(size=15),
            text_color=self._get_color('text_secondary'),
            width=28
        )
        icon_label.pack(side="left", padx=(0, 6))

        # حقل الإدخال
        if field_name == "username":
            self.entry_username = ctk.CTkEntry(
                field_frame,
                placeholder_text=placeholder,
                height=field_height,
                font=ctk.CTkFont(family="Helvetica", size=13),
                fg_color=self._get_color('surface'),
                border_width=0,
                text_color=self._get_color('text_primary'),
                placeholder_text_color=self._get_color('text_secondary')
            )
            self.entry_username.pack(side="left", fill="x", expand=True)

            # تطبيق الثيم تلقائياً
            self.themed_window.apply_to_widget(self.entry_username, 'entry')

            # ربط الأحداث
            self.entry_username.bind("<Return>", lambda e: self.entry_password.focus_set())
            self.entry_username.bind("<FocusIn>", lambda e: self._on_field_focus(field_container, True))
            self.entry_username.bind("<FocusOut>", lambda e: self._on_field_focus(field_container, False))
            self.entry_username.bind("<KeyRelease>", lambda e: self._validate_username())
            self.entry_username.bind("<Button-1>", lambda e: self._update_activity())

            # تسمية الخطأ
            self.username_error = ctk.CTkLabel(
                parent,
                text="",
                font=ctk.CTkFont(size=10),
                text_color=self._get_color('danger'),
                anchor="w"
            )

    def _create_workarea_password_field(self, parent):
        """إنشاء حقل كلمة مرور محسن للارتفاع الكامل"""
        # أحجام محسنة
        label_font_size = 14
        field_height = 40
        button_size = 36
        padding_bottom = 8
        field_padding = 12

        # تسمية الحقل
        self.password_label = ctk.CTkLabel(
            parent,
            text=self.lang_manager.get("password", "Password"),
            font=ctk.CTkFont(family="Helvetica", size=label_font_size, weight="bold"),
            text_color=self._get_color('text_primary'),
            anchor="w"
        )
        self.password_label.pack(fill="x", pady=(0, padding_bottom))

        # إطار الحقل
        field_container = ctk.CTkFrame(
            parent,
            fg_color=self._get_color('input_bg'),
            corner_radius=12,
            border_width=2,
            border_color=self._get_color('input_border')
        )
        field_container.pack(fill="x", pady=(0, field_padding))

        field_frame = ctk.CTkFrame(field_container, fg_color="transparent")
        field_frame.pack(fill="x", padx=12, pady=8)

        # الأيقونة
        lock_icon = ctk.CTkLabel(
            field_frame,
            text="🔒",
            font=ctk.CTkFont(size=16),
            text_color=self._get_color('text_secondary'),
            width=30
        )
        lock_icon.pack(side="left", padx=(0, 8))

        # حقل كلمة المرور
        self.entry_password = ctk.CTkEntry(
            field_frame,
            placeholder_text=self.lang_manager.get("enter_password", "Enter your password"),
            show="•",
            height=field_height,
            font=ctk.CTkFont(family="Helvetica", size=14),
            fg_color=self._get_color('surface'),
            border_width=0,
            text_color=self._get_color('text_primary'),
            placeholder_text_color=self._get_color('text_secondary')
        )
        self.entry_password.pack(side="left", fill="x", expand=True)

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.entry_password, 'entry')

        # أزرار التحكم
        controls_frame = ctk.CTkFrame(field_frame, fg_color="transparent")
        controls_frame.pack(side="left", padx=(8, 0))

        # زر إظهار/إخفاء
        self.toggle_pass_btn = ctk.CTkButton(
            controls_frame,
            text="👁",
            width=button_size,
            height=button_size,
            fg_color=self._get_color('input_bg'),
            hover_color=self._get_color('border'),
            text_color=self._get_color('text_secondary'),
            command=self._toggle_password_visibility,
            corner_radius=8,
            border_width=1,
            border_color=self._get_color('input_border'),
            font=ctk.CTkFont(size=14)
        )
        self.toggle_pass_btn.pack(side="left", padx=(0, 4))

        # زر توليد كلمة مرور
        self.gen_pass_btn = ctk.CTkButton(
            controls_frame,
            text="🔑",
            width=button_size,
            height=button_size,
            fg_color=self._get_color('input_bg'),
            hover_color=self._get_color('border'),
            text_color=self._get_color('text_secondary'),
            command=self._generate_strong_password,
            corner_radius=8,
            border_width=1,
            border_color=self._get_color('input_border'),
            font=ctk.CTkFont(size=14)
        )
        self.gen_pass_btn.pack(side="left")

        # ربط الأحداث
        self.entry_password.bind("<Return>", lambda e: self._login())
        self.entry_password.bind("<FocusIn>", lambda e: self._on_field_focus(field_container, True))
        self.entry_password.bind("<FocusOut>", lambda e: self._on_field_focus(field_container, False))
        self.entry_password.bind("<KeyRelease>", self._update_password_strength)
        self.entry_password.bind("<Button-1>", lambda e: self._update_activity())

        # تحذير Caps Lock
        self.caps_lock_warning = ctk.CTkLabel(
            parent,
            text="⚠️ " + self.lang_manager.get("caps_lock_on", "Caps Lock is ON"),
            font=ctk.CTkFont(size=11),
            text_color="#F59E0B"
        )

        # مؤشر قوة كلمة المرور
        self._create_workarea_password_strength(parent)

    def _create_workarea_password_strength(self, parent):
        """إنشاء مؤشر قوة كلمة مرور محسن للارتفاع الكامل"""
        container_height = 45
        bar_height = 8
        padding_y = (8, 0)

        self.strength_container = ctk.CTkFrame(parent, fg_color="transparent", height=container_height)
        self.strength_container.pack(fill="x", pady=padding_y)

        # شريط التقدم
        strength_bg = ctk.CTkFrame(
            self.strength_container,
            height=bar_height,
            corner_radius=bar_height//2,
            fg_color=self._get_color('input_border')
        )
        strength_bg.pack(fill="x", pady=(0, 5))

        self.strength_bar = ctk.CTkProgressBar(
            strength_bg,
            height=bar_height,
            corner_radius=bar_height//2,
            progress_color=self._get_color('secondary'),
            fg_color=self._get_color('input_border')
        )
        self.strength_bar.pack(fill="both", expand=True)
        self.strength_bar.set(0)

        # تسمية القوة والمتطلبات
        info_frame = ctk.CTkFrame(self.strength_container, fg_color="transparent")
        info_frame.pack(fill="x")

        self.strength_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(family="Helvetica", size=12, weight="bold")
        )
        self.strength_label.pack(side="left")

        self.requirements_text = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=self._get_color('text_secondary')
        )
        self.requirements_text.pack(side="right")

    def _create_workarea_2fa_field(self, parent):
        """Create 2FA field for workarea layout"""
        self.twofa_frame = ctk.CTkFrame(parent, fg_color="transparent")

        # أحجام محسنة للارتفاع الكامل
        label_font_size = 14
        field_height = 40
        icon_font_size = 16
        entry_font_size = 14
        padding_bottom = 8

        # 2FA label
        self.twofa_label = ctk.CTkLabel(
            self.twofa_frame,
            text=self.lang_manager.get("2fa_code", "2FA Code"),
            font=ctk.CTkFont(family="Helvetica", size=label_font_size, weight="bold"),
            text_color=self._get_color('text_primary'),
            anchor="w"
        )
        self.twofa_label.pack(fill="x", pady=(0, padding_bottom))

        # 2FA entry container
        field_container = ctk.CTkFrame(
            self.twofa_frame,
            fg_color=self._get_color('input_bg'),
            corner_radius=12,
            border_width=2,
            border_color=self._get_color('input_border')
        )
        field_container.pack(fill="x")

        field_frame = ctk.CTkFrame(field_container, fg_color="transparent")
        field_frame.pack(fill="x", padx=12, pady=8)

        # 2FA icon
        icon_label = ctk.CTkLabel(
            field_frame,
            text="🔐",
            font=ctk.CTkFont(size=icon_font_size),
            text_color=self._get_color('text_secondary'),
            width=30
        )
        icon_label.pack(side="left", padx=(0, 8))

        # 2FA entry
        self.entry_2fa = ctk.CTkEntry(
            field_frame,
            placeholder_text=self.lang_manager.get("enter_2fa_code", "Enter 6-digit code"),
            height=field_height,
            font=ctk.CTkFont(family="Helvetica", size=entry_font_size),
            fg_color=self._get_color('surface'),
            border_width=0,
            text_color=self._get_color('text_primary'),
            placeholder_text_color=self._get_color('text_secondary')
        )
        self.entry_2fa.pack(side="left", fill="x", expand=True)

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.entry_2fa, 'entry')

        # Initially hidden
        self.twofa_frame.pack_forget()

    def _create_workarea_options(self, parent):
        """إنشاء خيارات محسنة للارتفاع الكامل"""
        options_frame = ctk.CTkFrame(parent, fg_color="transparent")
        options_frame.pack(fill="x", pady=(10, 0))

        # خيار تذكرني
        self.remember_check = ctk.CTkCheckBox(
            options_frame,
            text=self.lang_manager.get("remember_me", "Remember me"),
            variable=self.remember_me,
            font=ctk.CTkFont(family="Helvetica", size=13),
            text_color=self._get_color('text_primary'),
            fg_color=self._get_color('primary'),
            hover_color=self._get_color('primary_hover'),
            border_color=self._get_color('input_border'),
            border_width=2,
            corner_radius=6,
            command=self._update_activity
        )
        self.remember_check.pack(side="left")

        # رابط نسيت كلمة المرور
        self.forgot_btn = ctk.CTkButton(
            options_frame,
            text=self.lang_manager.get("forgot_password", "Forgot password?"),
            font=ctk.CTkFont(family="Helvetica", size=12, weight="normal"),
            fg_color="transparent",
            hover_color=self._get_color('input_bg'),
            text_color=self._get_color('primary'),
            command=self._show_forgot_password
        )
        self.forgot_btn.pack(side="right")

    def _create_workarea_buttons(self, parent):
        """إنشاء أزرار محسنة للارتفاع الكامل"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 15))

        # أحجام محسنة
        button_height = 45
        button_font_size = 15
        button_spacing = 10

        # زر تسجيل الدخول الأساسي
        self.btn_login = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("login", "Sign In"),
            command=self._login,
            height=button_height,
            font=ctk.CTkFont(family="Helvetica", size=button_font_size, weight="bold"),
            corner_radius=12,
            fg_color=self._get_color('primary'),
            hover_color=self._get_color('primary_hover'),
            text_color="white"
        )
        self.btn_login.pack(fill="x", pady=(0, button_spacing))

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.btn_login, 'button')

        # زر الإلغاء الثانوي
        self.btn_cancel = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self._on_close,
            height=button_height,
            font=ctk.CTkFont(family="Helvetica", size=button_font_size, weight="bold"),
            corner_radius=12,
            fg_color=self._get_color('input_bg'),
            hover_color=("#FFE4E6", "#4B5563"),
            text_color=self._get_color('danger'),
            border_width=2,
            border_color=self._get_color('danger')
        )
        self.btn_cancel.pack(fill="x")

    def _create_compact_password_field(self, parent):
        """إنشاء حقل كلمة مرور مضغوط"""
        # أحجام مضغوطة
        label_font_size = 13
        field_height = 36
        button_size = 32
        padding_bottom = 5
        field_padding = 8

        # تسمية الحقل
        self.password_label = ctk.CTkLabel(
            parent,
            text=self.lang_manager.get("password", "Password"),
            font=ctk.CTkFont(family="Helvetica", size=label_font_size, weight="bold"),
            text_color=self._get_color('text_primary'),
            anchor="w"
        )
        self.password_label.pack(fill="x", pady=(0, padding_bottom))

        # إطار الحقل
        field_container = ctk.CTkFrame(
            parent,
            fg_color=self._get_color('input_bg'),
            corner_radius=10,
            border_width=1,
            border_color=self._get_color('input_border')
        )
        field_container.pack(fill="x", pady=(0, field_padding))

        field_frame = ctk.CTkFrame(field_container, fg_color="transparent")
        field_frame.pack(fill="x", padx=10, pady=6)

        # الأيقونة
        lock_icon = ctk.CTkLabel(
            field_frame,
            text="🔒",
            font=ctk.CTkFont(size=15),
            text_color=self._get_color('text_secondary'),
            width=28
        )
        lock_icon.pack(side="left", padx=(0, 6))

        # حقل كلمة المرور
        self.entry_password = ctk.CTkEntry(
            field_frame,
            placeholder_text=self.lang_manager.get("enter_password", "Enter your password"),
            show="•",
            height=field_height,
            font=ctk.CTkFont(family="Helvetica", size=13),
            fg_color=self._get_color('surface'),
            border_width=0,
            text_color=self._get_color('text_primary'),
            placeholder_text_color=self._get_color('text_secondary')
        )
        self.entry_password.pack(side="left", fill="x", expand=True)

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.entry_password, 'entry')

        # أزرار التحكم المضغوطة
        controls_frame = ctk.CTkFrame(field_frame, fg_color="transparent")
        controls_frame.pack(side="left", padx=(6, 0))

        # زر إظهار/إخفاء مضغوط
        self.toggle_pass_btn = ctk.CTkButton(
            controls_frame,
            text="👁",
            width=button_size,
            height=button_size,
            fg_color=self._get_color('input_bg'),
            hover_color=self._get_color('border'),
            text_color=self._get_color('text_secondary'),
            command=self._toggle_password_visibility,
            corner_radius=8,
            border_width=1,
            border_color=self._get_color('input_border'),
            font=ctk.CTkFont(size=13)
        )
        self.toggle_pass_btn.pack(side="left", padx=(0, 3))

        # زر توليد كلمة مرور مضغوط
        self.gen_pass_btn = ctk.CTkButton(
            controls_frame,
            text="🔑",
            width=button_size,
            height=button_size,
            fg_color=self._get_color('input_bg'),
            hover_color=self._get_color('border'),
            text_color=self._get_color('text_secondary'),
            command=self._generate_strong_password,
            corner_radius=8,
            border_width=1,
            border_color=self._get_color('input_border'),
            font=ctk.CTkFont(size=13)
        )
        self.gen_pass_btn.pack(side="left")

        # ربط الأحداث
        self.entry_password.bind("<Return>", lambda e: self._login())
        self.entry_password.bind("<FocusIn>", lambda e: self._on_field_focus(field_container, True))
        self.entry_password.bind("<FocusOut>", lambda e: self._on_field_focus(field_container, False))
        self.entry_password.bind("<KeyRelease>", self._update_password_strength)
        self.entry_password.bind("<Button-1>", lambda e: self._update_activity())

        # تحذير Caps Lock مضغوط
        self.caps_lock_warning = ctk.CTkLabel(
            parent,
            text="⚠️ " + self.lang_manager.get("caps_lock_on", "Caps Lock is ON"),
            font=ctk.CTkFont(size=10),
            text_color="#F59E0B"
        )

        # مؤشر قوة كلمة المرور المضغوط
        self._create_compact_password_strength(parent)

    def _create_compact_password_strength(self, parent):
        """إنشاء مؤشر قوة كلمة مرور مضغوط"""
        container_height = 40
        bar_height = 6
        padding_y = (5, 0)

        self.strength_container = ctk.CTkFrame(parent, fg_color="transparent", height=container_height)
        self.strength_container.pack(fill="x", pady=padding_y)

        # شريط التقدم المضغوط
        strength_bg = ctk.CTkFrame(
            self.strength_container,
            height=bar_height,
            corner_radius=bar_height//2,
            fg_color=self._get_color('input_border')
        )
        strength_bg.pack(fill="x", pady=(0, 4))

        self.strength_bar = ctk.CTkProgressBar(
            strength_bg,
            height=bar_height,
            corner_radius=bar_height//2,
            progress_color=self._get_color('secondary'),
            fg_color=self._get_color('input_border')
        )
        self.strength_bar.pack(fill="both", expand=True)
        self.strength_bar.set(0)

        # تسمية القوة والمتطلبات المضغوطة
        info_frame = ctk.CTkFrame(self.strength_container, fg_color="transparent")
        info_frame.pack(fill="x")

        self.strength_label = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(family="Helvetica", size=11, weight="bold")
        )
        self.strength_label.pack(side="left")

        self.requirements_text = ctk.CTkLabel(
            info_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=self._get_color('text_secondary')
        )
        self.requirements_text.pack(side="right")

    def _create_compact_2fa_field(self, parent):
        """Create compact 2FA field"""
        self.twofa_frame = ctk.CTkFrame(parent, fg_color="transparent")

        # أحجام مضغوطة
        label_font_size = 13
        field_height = 36
        icon_font_size = 15
        entry_font_size = 13
        padding_bottom = 5

        # 2FA label
        self.twofa_label = ctk.CTkLabel(
            self.twofa_frame,
            text=self.lang_manager.get("2fa_code", "2FA Code"),
            font=ctk.CTkFont(family="Helvetica", size=label_font_size, weight="bold"),
            text_color=self._get_color('text_primary'),
            anchor="w"
        )
        self.twofa_label.pack(fill="x", pady=(0, padding_bottom))

        # 2FA entry container
        field_container = ctk.CTkFrame(
            self.twofa_frame,
            fg_color=self._get_color('input_bg'),
            corner_radius=10,
            border_width=1,
            border_color=self._get_color('input_border')
        )
        field_container.pack(fill="x")

        field_frame = ctk.CTkFrame(field_container, fg_color="transparent")
        field_frame.pack(fill="x", padx=10, pady=6)

        # 2FA icon
        icon_label = ctk.CTkLabel(
            field_frame,
            text="🔐",
            font=ctk.CTkFont(size=icon_font_size),
            text_color=self._get_color('text_secondary'),
            width=28
        )
        icon_label.pack(side="left", padx=(0, 6))

        # 2FA entry
        self.entry_2fa = ctk.CTkEntry(
            field_frame,
            placeholder_text=self.lang_manager.get("enter_2fa_code", "Enter 6-digit code"),
            height=field_height,
            font=ctk.CTkFont(family="Helvetica", size=entry_font_size),
            fg_color=self._get_color('surface'),
            border_width=0,
            text_color=self._get_color('text_primary'),
            placeholder_text_color=self._get_color('text_secondary')
        )
        self.entry_2fa.pack(side="left", fill="x", expand=True)

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.entry_2fa, 'entry')

        # Initially hidden
        self.twofa_frame.pack_forget()

    def _create_compact_options(self, parent):
        """إنشاء خيارات مضغوطة"""
        options_frame = ctk.CTkFrame(parent, fg_color="transparent")
        options_frame.pack(fill="x", pady=(8, 0))

        # خيار تذكرني مضغوط
        self.remember_check = ctk.CTkCheckBox(
            options_frame,
            text=self.lang_manager.get("remember_me", "Remember me"),
            variable=self.remember_me,
            font=ctk.CTkFont(family="Helvetica", size=12),
            text_color=self._get_color('text_primary'),
            fg_color=self._get_color('primary'),
            hover_color=self._get_color('primary_hover'),
            border_color=self._get_color('input_border'),
            border_width=1,
            corner_radius=5,
            command=self._update_activity
        )
        self.remember_check.pack(side="left")

        # رابط نسيت كلمة المرور مضغوط
        self.forgot_btn = ctk.CTkButton(
            options_frame,
            text=self.lang_manager.get("forgot_password", "Forgot password?"),
            font=ctk.CTkFont(family="Helvetica", size=11, weight="normal"),
            fg_color="transparent",
            hover_color=self._get_color('input_bg'),
            text_color=self._get_color('primary'),
            command=self._show_forgot_password
        )
        self.forgot_btn.pack(side="right")

    def _create_compact_buttons(self, parent):
        """إنشاء أزرار مضغوطة"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 12))

        # أحجام مضغوطة
        button_height = 40
        button_font_size = 14
        button_spacing = 8

        # زر تسجيل الدخول الأساسي
        self.btn_login = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("login", "Sign In"),
            command=self._login,
            height=button_height,
            font=ctk.CTkFont(family="Helvetica", size=button_font_size, weight="bold"),
            corner_radius=10,
            fg_color=self._get_color('primary'),
            hover_color=self._get_color('primary_hover'),
            text_color="white"
        )
        self.btn_login.pack(fill="x", pady=(0, button_spacing))

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.btn_login, 'button')

        # زر الإلغاء الثانوي
        self.btn_cancel = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self._on_close,
            height=button_height,
            font=ctk.CTkFont(family="Helvetica", size=button_font_size, weight="bold"),
            corner_radius=10,
            fg_color=self._get_color('input_bg'),
            hover_color=("#FFE4E6", "#4B5563"),
            text_color=self._get_color('danger'),
            border_width=1,
            border_color=self._get_color('danger')
        )
        self.btn_cancel.pack(fill="x")

        # تطبيق الثيم تلقائياً
        self.themed_window.apply_to_widget(self.btn_cancel, 'button')

        # SSO buttons (if configured) - مضغوطة
        if LOGIN_CONFIG.get("sso", {}).get("enabled", False):
            self._create_compact_sso_buttons(button_frame)

    def _create_compact_sso_buttons(self, parent):
        """Create compact SSO login buttons"""
        sso_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sso_frame.pack(fill="x", pady=(10, 0))

        # Divider مضغوط
        divider_frame = ctk.CTkFrame(sso_frame, fg_color="transparent")
        divider_frame.pack(fill="x", pady=(0, 8))

        line_left = ctk.CTkFrame(divider_frame, height=1, fg_color=self._get_color('input_border'))
        line_left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            divider_frame,
            text=self.lang_manager.get("or_login_with", "Or login with"),
            font=ctk.CTkFont(size=11),
            text_color=self._get_color('text_secondary')
        ).pack(side="left", padx=8)

        line_right = ctk.CTkFrame(divider_frame, height=1, fg_color=self._get_color('input_border'))
        line_right.pack(side="left", fill="x", expand=True)

        # SSO buttons مضغوطة
        sso_providers = LOGIN_CONFIG.get("sso", {}).get("providers", [])
        sso_button_height = 35

        for provider in sso_providers:
            btn = ctk.CTkButton(
                sso_frame,
                text=f"{provider.get('icon', '🔗')} {provider.get('name', 'SSO')}",
                command=lambda p=provider: self._sso_login(p),
                height=sso_button_height,
                fg_color=self._get_color('input_bg'),
                hover_color=self._get_color('input_border'),
                text_color=self._get_color('text_primary'),
                border_width=1,
                border_color=self._get_color('input_border'),
                font=ctk.CTkFont(size=12),
                corner_radius=8
            )
            btn.pack(fill="x", pady=3)

    def _create_compact_status_area(self, parent):
        """إنشاء منطقة حالة مضغوطة"""
        container_height = 45
        status_font_size = 12
        security_font_size = 10
        padding_y = (5, 8)

        self.status_container = ctk.CTkFrame(parent, fg_color="transparent", height=container_height)
        self.status_container.pack(fill="x", pady=padding_y)
        self.status_container.pack_propagate(False)

        # تسمية الحالة المضغوطة
        self.status_label = ctk.CTkLabel(
            self.status_container,
            text="",
            font=ctk.CTkFont(family="Helvetica", size=status_font_size),
            wraplength=340
        )
        self.status_label.pack(expand=True)

        # شريط التقدم المضغوط
        progress_height = 3
        self.progress = ctk.CTkProgressBar(
            parent,
            mode="indeterminate",
            height=progress_height,
            corner_radius=progress_height//2,
            progress_color=self._get_color('primary'),
            fg_color=self._get_color('input_border')
        )

        # Security status مضغوط
        if self.enable_encryption or self.enable_rate_limiting:
            security_frame = ctk.CTkFrame(parent, fg_color="transparent")
            security_frame.pack(fill="x", pady=(3, 0))

            security_items = []
            if self.enable_encryption:
                security_items.append("🔐 Encrypted")
            if self.enable_rate_limiting:
                security_items.append("🛡️ Protected")

            ctk.CTkLabel(
                security_frame,
                text=" • ".join(security_items),
                font=ctk.CTkFont(size=security_font_size),
                text_color=self._get_color('text_secondary')
            ).pack()

    def _create_compact_footer(self, parent):
        """إنشاء تذييل مضغوط"""
        # خط فاصل رفيع
        separator = ctk.CTkFrame(parent, height=1, fg_color=self._get_color('input_border'))
        separator.pack(fill="x", pady=(8, 10))

        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x")

        # أزرار التحكم المضغوطة
        controls_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        controls_frame.pack(pady=(0, 8))

        button_configs = [
            ("🌐", "English" if self.lang_manager.current_lang == "ar" else "عربي", self._toggle_language),
            ("🎨", self.lang_manager.get("theme", "Theme"), self._toggle_theme),
            ("💬", self.lang_manager.get("help", "Help"), self._show_help)
        ]

        # إضافة زر لوحة الألوان إذا كانت اللوحات متاحة والوضع فاتح
        if COLOR_PALETTES_AVAILABLE and self.theme_manager.get_current_appearance_mode() == "light":
            button_configs.insert(2, ("🎨", self.lang_manager.get("palette", "Colors"), self._show_palette_menu))

        # أحجام الأزرار المضغوطة
        button_width = 80
        button_height = 28
        button_font_size = 10

        for i, (icon, text, command) in enumerate(button_configs):
            btn = ctk.CTkButton(
                controls_frame,
                text=f"{icon} {text}",
                width=button_width,
                height=button_height,
                command=command,
                font=ctk.CTkFont(family="Helvetica", size=button_font_size),
                corner_radius=6,
                fg_color=self._get_color('input_bg'),
                hover_color=self._get_color('input_border'),
                text_color=self._get_color('text_secondary'),
                border_width=1,
                border_color=self._get_color('input_border')
            )
            btn.pack(side="left", padx=3)

            if i == 0:
                self.btn_language = btn
            elif i == 1:
                self.btn_theme = btn
            elif text == self.lang_manager.get("palette", "Colors"):
                self.btn_palette = btn
            elif text == self.lang_manager.get("help", "Help"):
                self.btn_help = btn

        # معلومات الإصدار المضغوطة
        version_label = ctk.CTkLabel(
            footer_frame,
            text="FTS Sales Manager v2.0 © 2024",
            font=ctk.CTkFont(family="Helvetica", size=9),
            text_color=self._get_color('text_secondary')
        )
        version_label.pack(pady=(4, 0))

    def _create_workarea_sso_buttons(self, parent):
        """Create SSO login buttons for workarea layout"""
        sso_frame = ctk.CTkFrame(parent, fg_color="transparent")
        sso_frame.pack(fill="x", pady=(15, 0))

        # Divider
        divider_frame = ctk.CTkFrame(sso_frame, fg_color="transparent")
        divider_frame.pack(fill="x", pady=(0, 10))

        line_left = ctk.CTkFrame(divider_frame, height=2, fg_color=self._get_color('input_border'))
        line_left.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            divider_frame,
            text=self.lang_manager.get("or_login_with", "Or login with"),
            font=ctk.CTkFont(size=12),
            text_color=self._get_color('text_secondary')
        ).pack(side="left", padx=12)

        line_right = ctk.CTkFrame(divider_frame, height=2, fg_color=self._get_color('input_border'))
        line_right.pack(side="left", fill="x", expand=True)

        # SSO buttons
        sso_providers = LOGIN_CONFIG.get("sso", {}).get("providers", [])
        sso_button_height = 40

        for provider in sso_providers:
            btn = ctk.CTkButton(
                sso_frame,
                text=f"{provider.get('icon', '🔗')} {provider.get('name', 'SSO')}",
                command=lambda p=provider: self._sso_login(p),
                height=sso_button_height,
                fg_color=self._get_color('input_bg'),
                hover_color=self._get_color('input_border'),
                text_color=self._get_color('text_primary'),
                border_width=2,
                border_color=self._get_color('input_border'),
                font=ctk.CTkFont(size=13),
                corner_radius=10
            )
            btn.pack(fill="x", pady=4)

    def _create_workarea_status_area(self, parent):
        """إنشاء منطقة حالة محسنة للارتفاع الكامل"""
        container_height = 50
        status_font_size = 13
        security_font_size = 11
        padding_y = (5, 10)

        self.status_container = ctk.CTkFrame(parent, fg_color="transparent", height=container_height)
        self.status_container.pack(fill="x", pady=padding_y)
        self.status_container.pack_propagate(False)

        # تسمية الحالة
        self.status_label = ctk.CTkLabel(
            self.status_container,
            text="",
            font=ctk.CTkFont(family="Helvetica", size=status_font_size),
            wraplength=350
        )
        self.status_label.pack(expand=True)

        # شريط التقدم
        progress_height = 4
        self.progress = ctk.CTkProgressBar(
            parent,
            mode="indeterminate",
            height=progress_height,
            corner_radius=progress_height//2,
            progress_color=self._get_color('primary'),
            fg_color=self._get_color('input_border')
        )

        # Security status
        if self.enable_encryption or self.enable_rate_limiting:
            security_frame = ctk.CTkFrame(parent, fg_color="transparent")
            security_frame.pack(fill="x", pady=(5, 0))

            security_items = []
            if self.enable_encryption:
                security_items.append("🔐 Encrypted")
            if self.enable_rate_limiting:
                security_items.append("🛡️ Protected")

            ctk.CTkLabel(
                security_frame,
                text=" • ".join(security_items),
                font=ctk.CTkFont(size=security_font_size),
                text_color=self._get_color('text_secondary')
            ).pack()

    def _create_workarea_footer(self, parent):
        """إنشاء تذييل محسن للارتفاع الكامل"""
        # خط فاصل
        separator = ctk.CTkFrame(parent, height=2, fg_color=self._get_color('input_border'))
        separator.pack(fill="x", pady=(15, 12))

        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x")

        # أزرار التحكم
        controls_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        controls_frame.pack(pady=(0, 10))

        button_configs = [
            ("🌐", "English" if self.lang_manager.current_lang == "ar" else "عربي", self._toggle_language),
            ("🎨", self.lang_manager.get("theme", "Theme"), self._toggle_theme),
            ("💬", self.lang_manager.get("help", "Help"), self._show_help)
        ]

        # إضافة زر لوحة الألوان إذا كانت اللوحات متاحة والوضع فاتح
        if COLOR_PALETTES_AVAILABLE and self.theme_manager.get_current_appearance_mode() == "light":
            button_configs.insert(2, ("🎨", self.lang_manager.get("palette", "Colors"), self._show_palette_menu))

        # أحجام الأزرار محسنة
        button_width = 90
        button_height = 32
        button_font_size = 11

        for i, (icon, text, command) in enumerate(button_configs):
            btn = ctk.CTkButton(
                controls_frame,
                text=f"{icon} {text}",
                width=button_width,
                height=button_height,
                command=command,
                font=ctk.CTkFont(family="Helvetica", size=button_font_size),
                corner_radius=8,
                fg_color=self._get_color('input_bg'),
                hover_color=self._get_color('input_border'),
                text_color=self._get_color('text_secondary'),
                border_width=1,
                border_color=self._get_color('input_border')
            )
            btn.pack(side="left", padx=4)

            if i == 0:
                self.btn_language = btn
            elif i == 1:
                self.btn_theme = btn
            elif text == self.lang_manager.get("palette", "Colors"):
                self.btn_palette = btn
            elif text == self.lang_manager.get("help", "Help"):
                self.btn_help = btn

        # معلومات الإصدار
        version_label = ctk.CTkLabel(
            footer_frame,
            text="FTS Sales Manager v2.0 © 2024",
            font=ctk.CTkFont(family="Helvetica", size=10),
            text_color=self._get_color('text_secondary')
        )
        version_label.pack(pady=(5, 0))

    def _show_palette_menu(self):
        """عرض قائمة اختيار لوحة الألوان محسنة"""
        if not COLOR_PALETTES_AVAILABLE:
            return

        # حجم النافذة محسن
        palette_window_size = "350x450"
        options_height = 250
        title_font = 18
        desc_font = 12
        radio_font = 13
        button_width = 110
        button_height = 36

        # إنشاء نافذة فرعية لاختيار اللوحة
        palette_window = ctk.CTkToplevel(self)
        palette_window.title(self.lang_manager.get("choose_palette", "Choose Color Palette"))
        palette_window.geometry(palette_window_size)
        palette_window.resizable(False, False)

        # تكوين النافذة
        palette_window.transient(self)
        palette_window.grab_set()

        # العنوان
        title = ctk.CTkLabel(
            palette_window,
            text=self.lang_manager.get("select_palette", "Select Color Palette"),
            font=ctk.CTkFont(size=title_font, weight="bold")
        )
        title.pack(pady=(20, 10))

        # الوصف
        desc = ctk.CTkLabel(
            palette_window,
            text=self.lang_manager.get("palette_desc", "Choose your preferred color scheme for light theme"),
            font=ctk.CTkFont(size=desc_font),
            text_color=self._get_color('text_secondary')
        )
        desc.pack(pady=(0, 15))

        # إطار للخيارات
        options_frame = ctk.CTkScrollableFrame(
            palette_window,
            width=300,
            height=options_height
        )
        options_frame.pack(pady=10, padx=20)

        # قاموس أسماء اللوحات
        palette_names = {
            'modern_purple': ('🟣', self.lang_manager.get("purple_modern", "Modern Purple")),
            'modern_blue': ('🔵', self.lang_manager.get("blue_modern", "Modern Blue")),
            'modern_emerald': ('🟢', self.lang_manager.get("emerald_modern", "Modern Emerald")),
            'modern_pink': ('🩷', self.lang_manager.get("pink_modern", "Modern Pink")),
            'modern_orange': ('🟠', self.lang_manager.get("orange_warm", "Warm Orange")),
            'modern_indigo': ('🟪', self.lang_manager.get("indigo_elegant", "Elegant Indigo")),
            'classic_blue': ('🔷', self.lang_manager.get("blue_classic", "Classic Blue"))
        }

        # الحصول على اللوحة الحالية
        current_palette = 'modern_purple'
        if hasattr(self, 'controller') and hasattr(self.controller, 'config_manager'):
            current_palette = self.controller.config_manager.get('light_color_palette', 'modern_purple')

        # متغير لتتبع الاختيار
        selected_palette = ctk.StringVar(value=current_palette)

        # إنشاء خيارات الراديو
        for palette_key in self._get_available_color_palettes():
            if palette_key in palette_names:
                icon, name = palette_names[palette_key]

                # إطار للخيار
                option_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
                option_frame.pack(fill="x", pady=4)

                # زر الراديو
                radio = ctk.CTkRadioButton(
                    option_frame,
                    text=f"{icon} {name}",
                    variable=selected_palette,
                    value=palette_key,
                    font=ctk.CTkFont(size=radio_font),
                    fg_color=get_color_palette(palette_key)['primary']
                )
                radio.pack(side="left", padx=10)

                # معاينة صغيرة للألوان
                preview_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
                preview_frame.pack(side="right", padx=10)

                colors = get_color_palette(palette_key)
                for color_key in ['primary', 'success', 'danger']:
                    color_box = ctk.CTkFrame(
                        preview_frame,
                        width=18,
                        height=18,
                        corner_radius=4,
                        fg_color=colors[color_key]
                    )
                    color_box.pack(side="left", padx=1)

        # إطار الأزرار
        button_frame = ctk.CTkFrame(palette_window, fg_color="transparent")
        button_frame.pack(pady=20)

        def apply_palette():
            """تطبيق اللوحة المختارة"""
            new_palette = selected_palette.get()
            self._save_color_palette_preference(new_palette)

            self._show_status(
                self.lang_manager.get("palette_saved", "Color palette saved. Please reopen the window."),
                "success"
            )

            palette_window.destroy()
            self.after(1500, self._on_close)

        # أزرار
        apply_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("apply", "Apply"),
            command=apply_palette,
            width=button_width,
            height=button_height,
            fg_color=self._get_color('primary'),
            hover_color=self._get_color('primary_hover')
        )
        apply_btn.pack(side="left", padx=5)

        # زر الإلغاء
        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=palette_window.destroy,
            width=button_width,
            height=button_height,
            fg_color="transparent",
            hover_color=self._get_color('input_bg'),
            text_color=self._get_color('text_primary'),
            border_width=1,
            border_color=self._get_color('input_border')
        )
        cancel_btn.pack(side="left", padx=5)

        # توسيط النافذة
        palette_window.update_idletasks()
        x = (palette_window.winfo_screenwidth() - palette_window.winfo_width()) // 2
        y = (palette_window.winfo_screenheight() - palette_window.winfo_height()) // 2
        palette_window.geometry(f"+{x}+{y}")

    def _on_field_focus(self, field_container, focused):
        """معالجة تأثيرات التركيز على الحقول"""
        if focused:
            field_container.configure(
                border_color=self._get_color('input_focus'),
                border_width=3,
                fg_color=self._get_color('surface')
            )
        else:
            field_container.configure(
                border_color=self._get_color('input_border'),
                border_width=2,
                fg_color=self._get_color('input_bg')
            )

    def _validate_username(self) -> bool:
        """Validate username input"""
        username = self.entry_username.get().strip()

        if not username:
            return True

        if InputValidator:
            is_valid, error_msg = InputValidator.validate_username(username)
        else:
            is_valid = len(username) >= 3 and re.match(r'^[a-zA-Z0-9_.-]+$', username)
            error_msg = "" if is_valid else self.lang_manager.get("invalid_username", "Invalid username format")

        if not is_valid:
            self.username_error.configure(text=error_msg)
            self.username_error.pack(anchor="w", pady=(2, 0))
            return False
        else:
            self.username_error.pack_forget()
            return True

    def _update_password_strength(self, event=None):
        """تحديث مؤشر قوة كلمة المرور محسن للارتفاع الكامل"""
        password = self.entry_password.get()

        if not password:
            self.strength_bar.set(0)
            self.strength_label.configure(text="")
            self.requirements_text.configure(text="")
            return

        # حساب القوة
        has_length = len(password) >= 8
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

        score = sum([has_length, has_upper, has_lower, has_digit, has_special])
        progress = score / 5
        self.strength_bar.set(progress)

        # تحديد المستوى واللون
        if score <= 2:
            text = self.lang_manager.get("pwd_weak", "Weak")
            color = self._get_color('danger')
            req_text = "Need more variety"
        elif score <= 3:
            text = self.lang_manager.get("pwd_fair", "Fair")
            color = "#F59E0B"
            req_text = "Add more elements"
        elif score <= 4:
            text = self.lang_manager.get("pwd_good", "Good")
            color = "#10B981"
            req_text = "Almost perfect!"
        else:
            text = self.lang_manager.get("pwd_strong", "Strong")
            color = self._get_color('success')
            req_text = "Perfect ✓"

        # تحديث الواجهة
        self.strength_bar.configure(progress_color=color)
        self.strength_label.configure(text=text, text_color=color)
        self.requirements_text.configure(text=req_text)

    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        self._show_password = not self._show_password
        if self._show_password:
            self.entry_password.configure(show="")
            self.toggle_pass_btn.configure(text="👁‍🗨")
        else:
            self.entry_password.configure(show="•")
            self.toggle_pass_btn.configure(text="👁")
        self._update_activity()

    def _generate_strong_password(self):
        """Generate a strong password"""
        import string

        length = 16
        chars = string.ascii_letters + string.digits + string.punctuation

        password = ''.join(secrets.choice(chars) for _ in range(length))

        while not all([
            any(c.isupper() for c in password),
            any(c.islower() for c in password),
            any(c.isdigit() for c in password),
            any(c in string.punctuation for c in password)
        ]):
            password = ''.join(secrets.choice(chars) for _ in range(length))

        self.entry_password.delete(0, "end")
        self.entry_password.insert(0, password)
        self._show_password = True
        self._toggle_password_visibility()
        self._toggle_password_visibility()

        self._update_password_strength()

        self._show_status(
            self.lang_manager.get("password_generated", "Strong password generated"),
            "success"
        )

    def _toggle_language(self):
        """Toggle language"""
        new_lang = "en" if self.lang_manager.current_lang == "ar" else "ar"
        self.lang_manager.set_language(new_lang)

        self._update_ui_texts()

        lang_text = "English" if new_lang == "ar" else "عربي"
        self.btn_language.configure(text=f"🌐 {lang_text}")

        self._update_activity()

    def _toggle_theme(self):
        """تبديل الثيم مع التحديث الموحد"""
        # تبديل الوضع
        self.theme_manager.toggle_appearance_mode()
        self._apply_theme()

        # تحديث النظام الموحد
        self.themed_window.refresh_theme()

        # إظهار رسالة بالتغيير
        current_mode = self.theme_manager.get_current_appearance_mode()
        if current_mode == "dark":
            self._show_status(
                self.lang_manager.get("theme_dark", "Dark theme activated"),
                "info"
            )
        else:
            self._show_status(
                self.lang_manager.get("theme_light", "Light theme activated"),
                "info"
            )

        # إعادة تحديث ألوان العناصر
        self._refresh_ui_colors()

        # إعادة بناء الواجهة لتطبيق الألوان الجديدة
        messagebox.showinfo(
            self.lang_manager.get("theme_change", "Theme Changed"),
            self.lang_manager.get("theme_change_msg", "Please reopen the window to apply the new theme colors.")
        )

        self._update_activity()

    def _refresh_ui_colors(self):
        """تحديث ألوان جميع العناصر"""
        # تحديث الأزرار
        self.themed_window.apply_to_widget(self.btn_login, 'button')
        self.themed_window.apply_to_widget(self.btn_cancel, 'button')

        # تحديث الحقول
        for widget in [self.entry_username, self.entry_password]:
            self.themed_window.apply_to_widget(widget, 'entry')

        # تحديث 2FA إذا كان موجوداً
        if hasattr(self, 'entry_2fa'):
            self.themed_window.apply_to_widget(self.entry_2fa, 'entry')

    def _show_help(self):
        """Show help dialog"""
        help_text = self.lang_manager.get(
            "login_help",
            "Login Help:\n\n"
            "• Enter your username and password\n"
            "• Click 'Sign In' or press Enter\n"
            "• Use 'Remember me' to save your username\n"
            "• Contact admin if you forgot your password\n\n"
            "Security Tips:\n"
            "• Use strong passwords (8+ chars, mixed case, numbers, symbols)\n"
            "• Don't share your credentials\n"
            "• Log out when done"
        )

        messagebox.showinfo(
            self.lang_manager.get("help", "Help"),
            help_text
        )

    def _show_forgot_password(self):
        """Show forgot password dialog"""
        messagebox.showinfo(
            self.lang_manager.get("forgot_password", "Forgot Password"),
            self.lang_manager.get("forgot_password_msg",
                                 "Please contact your administrator to reset your password.\n\n"
                                 "Or contact Automation Team:\n"
                                 "Email: eladawy522@gmail.com\nPhone: +201068177086")
        )

    @login_error_handler
    def _login(self):
        """Enhanced login handler with security features"""
        self._update_activity()

        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username:
            self._show_status(
                self.lang_manager.get("error_username_required", "Please enter your username"),
                "error"
            )
            self._flash_window()
            self.entry_username.focus_set()
            return

        if not password:
            self._show_status(
                self.lang_manager.get("error_password_required", "Please enter your password"),
                "error"
            )
            self._flash_window()
            self.entry_password.focus_set()
            return

        if not self._validate_username():
            self._flash_window()
            return

        if self.enable_rate_limiting:
            identifier = f"{username}:{self._get_client_identifier()}"
            allowed, message = self.rate_limiter.check_rate_limit(identifier)

            if not allowed:
                self._show_status(message, "error")
                self._flash_window(count=3)
                self._set_form_state(False)
                return

        twofa_code = None
        if self.enable_2fa and hasattr(self, 'entry_2fa'):
            twofa_code = self.entry_2fa.get().strip()

        remember_user = self.remember_me.get()

        self._set_form_state(False)
        self._show_progress()

        result_queue = queue.Queue()

        def login_process():
            try:
                if self.enable_rate_limiting:
                    self.rate_limiter.record_attempt(identifier)

                user_info = None

                if self.validate_credentials:
                    if self.enable_2fa:
                        try:
                            user_info = self.validate_credentials(username, password, twofa_code)
                        except TypeError:
                            user_info = self.validate_credentials(username, password)
                    else:
                        user_info = self.validate_credentials(username, password)

                elif self.user_mgr and hasattr(self.user_mgr, 'authenticate'):
                    user_info = self.user_mgr.authenticate(username, password)
                else:
                    logger.error("No authentication method available")
                    result_queue.put(("error", "Authentication service not available"))
                    return

                if user_info:
                    if self.enable_rate_limiting:
                        self.rate_limiter.clear_attempts(identifier)

                    if remember_user:
                        self._save_credentials(username)
                    else:
                        self._clear_saved_credentials()

                    self._session_token = secrets.token_urlsafe(32)

                    user_info['session_token'] = self._session_token
                    user_info['login_time'] = datetime.now().isoformat()

                    result_queue.put(("success", user_info))
                else:
                    self._login_attempts += 1
                    result_queue.put(("failed", None))

            except Exception as e:
                logger.error(f"Login error: {e}", exc_info=True)
                result_queue.put(("error", str(e)))

        thread = threading.Thread(target=login_process, daemon=True)
        thread.start()

        def check_result():
            try:
                result = result_queue.get_nowait()
                status, data = result

                if status == "success":
                    self._on_login_success(data)
                elif status == "failed":
                    self._on_login_failed()
                elif status == "error":
                    self._on_login_error(data)

            except queue.Empty:
                if not self._closing and self.winfo_exists():
                    self.after(100, check_result)
            except Exception as e:
                logger.error(f"Error checking login result: {e}")
                self._on_login_error(str(e))

        self.after(100, check_result)

    def _on_login_success(self, user_info):
        """Handle successful login"""
        if self._closing or not self.winfo_exists():
            return

        self._hide_progress()

        username = user_info.get('username', 'Unknown')
        logger.info(f"Login successful for user: {username}")

        self._show_status(
            self.lang_manager.get("login_success", "Login successful! Welcome back."),
            "success"
        )

        if WINDOW_MANAGER_AVAILABLE:
            WindowManager.flash_window(self, count=1, interval=200)

        if self.on_login_success:
            self.after(500, lambda: self.on_login_success(user_info))

        self.after(800, self._on_close)

    def _on_login_failed(self):
        """Handle failed login"""
        if self._closing or not self.winfo_exists():
            return

        self._hide_progress()
        self._set_form_state(True)

        self._flash_window(count=2)

        remaining = LoginConstants.MAX_LOGIN_ATTEMPTS - self._login_attempts

        if remaining > 0:
            msg = self.lang_manager.get("invalid_credentials", "Invalid username or password")
            msg += f"\n{remaining} {self.lang_manager.get('attempts_remaining', 'attempts remaining')}"
            self._show_status(msg, "error")

            self.entry_password.delete(0, "end")
            self.entry_password.focus_set()

            if self.enable_2fa and self._login_attempts > 2:
                self.twofa_frame.pack(fill="x", pady=(8, 0))
        else:
            self._show_status(
                self.lang_manager.get("account_locked",
                                    "Too many failed attempts.\nPlease contact administrator."),
                "error"
            )
            self._set_form_state(False)
            self._flash_window(count=5)

    def _on_login_error(self, error_msg):
        """Handle login error"""
        if self._closing or not self.winfo_exists():
            return

        self._hide_progress()
        self._set_form_state(True)

        self._show_status(
            f"{self.lang_manager.get('error', 'Error')}: {error_msg}",
            "error"
        )

        self._flash_window()

    def _get_client_identifier(self) -> str:
        """Get client identifier for rate limiting"""
        return platform.node()

    def _flash_window(self, count: int = 2, interval: int = 300):
        """Flash window for attention"""
        if WINDOW_MANAGER_AVAILABLE:
            try:
                WindowManager.flash_window(self, count=count, interval=self.WINDOW_FLASH_INTERVAL)
            except Exception as e:
                logger.debug(f"Error flashing window: {e}")
                self.bell()
        else:
            self.bell()

    def _show_status(self, message: str, status_type: str = "info"):
        """عرض رسالة الحالة بتصميم محسن مع الألوان الموحدة"""
        colors = {
            "info": self._get_color('primary'),
            "success": self._get_color('success'),
            "error": self._get_color('danger'),
            "warning": "#F59E0B"
        }

        color = colors.get(status_type, colors["info"])

        if hasattr(self, 'status_label') and self.status_label.winfo_exists():
            icons = {
                "info": "ℹ️",
                "success": "✅",
                "error": "❌",
                "warning": "⚠️"
            }
            icon = icons.get(status_type, "")

            display_message = f"{icon} {message}" if icon else message
            self.status_label.configure(text=display_message, text_color=color)

    def _show_progress(self):
        """Show progress bar"""
        if hasattr(self, 'progress') and self.progress.winfo_exists():
            self.status_label.configure(text="")
            self.progress.pack(fill="x", pady=(0, 5))
            self.progress.start()

    def _hide_progress(self):
        """Hide progress bar"""
        try:
            if hasattr(self, 'progress') and self.progress and self.progress.winfo_exists():
                self.progress.stop()
                self.progress.pack_forget()
        except:
            pass

    def _set_form_state(self, enabled: bool):
        """Enable/disable form elements"""
        if self._closing or not self.winfo_exists():
            return

        state = "normal" if enabled else "disabled"

        elements = [
            'entry_username', 'entry_password', 'btn_login', 'btn_cancel',
            'remember_check', 'toggle_pass_btn', 'gen_pass_btn',
            'btn_language', 'btn_theme', 'btn_help', 'forgot_btn',
            'entry_2fa'
        ]

        for element_name in elements:
            if hasattr(self, element_name):
                element = getattr(self, element_name)
                try:
                    if element and element.winfo_exists():
                        element.configure(state=state)
                except:
                    pass

    def _save_credentials(self, username: str):
        """Save login credentials securely"""
        try:
            data = {
                "username": username,
                "remember": True,
                "timestamp": datetime.now().isoformat()
            }

            if self.enable_encryption:
                encrypted_data = self.encryption_manager.encrypt_data(json.dumps(data))
                save_data = {"encrypted": True, "data": encrypted_data}
            else:
                save_data = data

            os.makedirs("data", exist_ok=True)

            with open("data/login_cache.json", "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved credentials for user: {username}")

        except Exception as e:
            logger.error(f"Error saving credentials: {e}")

    def _load_saved_credentials(self):
        """Load saved login credentials"""
        try:
            cache_file = "data/login_cache.json"

            if os.path.exists(cache_file):
                with open(cache_file, "r", encoding="utf-8") as f:
                    save_data = json.load(f)

                if save_data.get("encrypted") and self.enable_encryption:
                    decrypted = self.encryption_manager.decrypt_data(save_data["data"])
                    data = json.loads(decrypted)
                else:
                    data = save_data

                if data.get("remember") and data.get("username"):
                    self.entry_username.insert(0, data["username"])
                    self.remember_me.set(True)
                    logger.debug(f"Loaded saved credentials for: {data['username']}")

        except Exception as e:
            logger.error(f"Error loading saved credentials: {e}")

    def _clear_saved_credentials(self):
        """Clear saved login credentials"""
        try:
            cache_file = "data/login_cache.json"

            if os.path.exists(cache_file):
                os.remove(cache_file)
                logger.debug("Cleared saved credentials")

        except Exception as e:
            logger.error(f"Error clearing saved credentials: {e}")

    def _update_ui_texts(self):
        """Update all UI texts"""
        self.title(self.lang_manager.get("login_window_title", "Login - FTS Sales Manager"))

        self.subtitle_label.configure(text=self.lang_manager.get("login_subtitle", "Secure access to your sales dashboard"))

        if hasattr(self, 'username_label'):
            self.username_label.configure(text=self.lang_manager.get("username", "Username"))
        self.password_label.configure(text=self.lang_manager.get("password", "Password"))

        self.entry_username.configure(placeholder_text=self.lang_manager.get("enter_username", "Enter your username"))
        self.entry_password.configure(placeholder_text=self.lang_manager.get("enter_password", "Enter your password"))

        self.remember_check.configure(text=self.lang_manager.get("remember_me", "Remember me"))
        self.forgot_btn.configure(text=self.lang_manager.get("forgot_password", "Forgot password?"))

        self.btn_login.configure(text=self.lang_manager.get("login", "Sign In"))
        self.btn_cancel.configure(text=self.lang_manager.get("cancel", "Cancel"))
        self.btn_theme.configure(text="🎨 " + self.lang_manager.get("theme", "Theme"))
        self.btn_help.configure(text="💬 " + self.lang_manager.get("help", "Help"))

        self.caps_lock_warning.configure(text="⚠️ " + self.lang_manager.get("caps_lock_on", "Caps Lock is ON"))

        if hasattr(self, 'twofa_label'):
            self.twofa_label.configure(text=self.lang_manager.get("2fa_code", "2FA Code"))
            self.entry_2fa.configure(placeholder_text=self.lang_manager.get("enter_2fa_code", "Enter 6-digit code"))

    def _sso_login(self, provider: dict):
        """Handle SSO login"""
        self._show_status(
            f"Logging in with {provider.get('name', 'SSO')}...",
            "info"
        )
        # Implement SSO logic here

    def _on_close(self):
        """Enhanced close handler"""
        if self._closing:
            return

        self._closing = True
        logger.info("Closing login window")

        try:
            for after_id in self.tk.call('after', 'info'):
                try:
                    self.after_cancel(after_id)
                except:
                    pass
        except:
            pass

        try:
            if hasattr(self, 'progress') and self.progress and self.progress.winfo_exists():
                self.progress.stop()
        except:
            pass

        try:
            if hasattr(self, 'entry_password') and self.entry_password.winfo_exists():
                self.entry_password.delete(0, "end")
        except:
            pass

        try:
            self.quit()
            self.destroy()
        except:
            pass