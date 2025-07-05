# -*- coding: utf-8 -*-
"""
core/constants.py

ثوابت التطبيق
Application Constants
"""

from enum import Enum
from typing import Dict, List, Tuple


class LoginConstants:
    """ثوابت تسجيل الدخول"""

    # Password requirements
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    PASSWORD_SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Security settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_TIMEOUT = 30  # seconds
    SESSION_TIMEOUT = 1800  # 30 minutes
    LOCKOUT_DURATION = 300  # 5 minutes

    # Rate limiting
    RATE_LIMIT_WINDOW = 300  # 5 minutes
    RATE_LIMIT_MAX_ATTEMPTS = 5

    # Session management
    SESSION_COOKIE_NAME = "fts_session"
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"

    # Token settings
    TOKEN_LENGTH = 32
    CSRF_TOKEN_LENGTH = 32
    REFRESH_TOKEN_EXPIRY = 604800  # 7 days

    # Validation
    USERNAME_MIN_LENGTH = 3
    USERNAME_MAX_LENGTH = 50
    USERNAME_PATTERN = r'^[a-zA-Z0-9_.-]+$'

    # 2FA settings
    OTP_LENGTH = 6
    OTP_VALIDITY = 300  # 5 minutes
    BACKUP_CODES_COUNT = 10


class WindowConstants:
    """ثوابت النوافذ"""

    # Login window
    LOGIN_WINDOW_SIZE = "450x700"
    MIN_WINDOW_WIDTH = 450
    MIN_WINDOW_HEIGHT = 700
    MAX_WINDOW_WIDTH = 600
    MAX_WINDOW_HEIGHT = 800

    # Animations
    ANIMATION_DURATION = 300
    FLASH_INTERVAL = 300
    FADE_DURATION = 200
    SLIDE_DURATION = 250

    # UI elements
    BUTTON_HEIGHT = 45
    BUTTON_CORNER_RADIUS = 22
    ENTRY_HEIGHT = 45
    ENTRY_CORNER_RADIUS = 10

    # Spacing
    PADDING_X = 25
    PADDING_Y = 25
    ELEMENT_SPACING = 10
    SECTION_SPACING = 20


class ThemeConstants:
    """ثوابت الثيمات"""

    # Color schemes
    THEMES = {
        "blue": {
            "primary": "#3498db",
            "primary_hover": "#2980b9",
            "secondary": "#2c3e50",
            "secondary_hover": "#1a252f",
            "success": "#27ae60",
            "error": "#e74c3c",
            "warning": "#f39c12",
            "info": "#3498db"
        },
        "green": {
            "primary": "#27ae60",
            "primary_hover": "#229954",
            "secondary": "#16a085",
            "secondary_hover": "#138d75",
            "success": "#27ae60",
            "error": "#e74c3c",
            "warning": "#f39c12",
            "info": "#3498db"
        },
        "dark": {
            "primary": "#34495e",
            "primary_hover": "#2c3e50",
            "secondary": "#7f8c8d",
            "secondary_hover": "#707b7c",
            "success": "#27ae60",
            "error": "#e74c3c",
            "warning": "#f39c12",
            "info": "#3498db"
        }
    }

    # Gradients
    GRADIENTS = {
        "primary": ["#3498db", "#2980b9"],
        "success": ["#27ae60", "#229954"],
        "error": ["#e74c3c", "#c0392b"],
        "warning": ["#f39c12", "#d68910"],
        "info": ["#3498db", "#2980b9"]
    }

    # Font settings
    FONT_FAMILY = "Segoe UI"
    FONT_FAMILY_ARABIC = "Arial"
    FONT_SIZE_BASE = 14
    FONT_SIZE_SMALL = 12
    FONT_SIZE_LARGE = 16
    FONT_SIZE_TITLE = 28
    FONT_SIZE_SUBTITLE = 18


class SecurityLevel(Enum):
    """مستويات الأمان"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuthenticationMethod(Enum):
    """طرق المصادقة"""
    PASSWORD = "password"
    TWO_FACTOR = "two_factor"
    BIOMETRIC = "biometric"
    SSO = "sso"
    MAGIC_LINK = "magic_link"
    HARDWARE_KEY = "hardware_key"


class LoginStatus(Enum):
    """حالات تسجيل الدخول"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    LOCKED = "locked"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class PasswordStrength(Enum):
    """قوة كلمة المرور"""
    VERY_WEAK = (0, "very_weak", "#e74c3c")
    WEAK = (1, "weak", "#e74c3c")
    FAIR = (2, "fair", "#f39c12")
    GOOD = (3, "good", "#f1c40f")
    STRONG = (4, "strong", "#27ae60")
    VERY_STRONG = (5, "very_strong", "#27ae60")

    def __init__(self, level: int, name: str, color: str):
        self.level = level
        self.strength_name = name
        self.color = color


class ErrorCode(Enum):
    """رموز الأخطاء"""
    NONE = 0
    INVALID_CREDENTIALS = 1001
    ACCOUNT_LOCKED = 1002
    SESSION_EXPIRED = 1003
    NETWORK_ERROR = 1004
    SERVER_ERROR = 1005
    RATE_LIMIT_EXCEEDED = 1006
    INVALID_2FA = 1007
    PERMISSION_DENIED = 1008
    MAINTENANCE_MODE = 1009
    UNKNOWN_ERROR = 9999


class MessageType(Enum):
    """أنواع الرسائل"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    DEBUG = "debug"


# API Endpoints
API_ENDPOINTS = {
    "auth": {
        "login": "/api/v1/auth/login",
        "logout": "/api/v1/auth/logout",
        "refresh": "/api/v1/auth/refresh",
        "verify": "/api/v1/auth/verify",
        "forgot_password": "/api/v1/auth/forgot-password",
        "reset_password": "/api/v1/auth/reset-password",
        "change_password": "/api/v1/auth/change-password",
        "verify_2fa": "/api/v1/auth/verify-2fa",
        "setup_2fa": "/api/v1/auth/setup-2fa"
    },
    "user": {
        "profile": "/api/v1/user/profile",
        "update_profile": "/api/v1/user/update-profile",
        "sessions": "/api/v1/user/sessions",
        "devices": "/api/v1/user/devices",
        "security_log": "/api/v1/user/security-log"
    }
}


# Regular expressions
REGEX_PATTERNS = {
    "username": r'^[a-zA-Z0-9_.-]+$',
    "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    "phone": r'^\+?[0-9\s\-\(\)]+$',
    "strong_password": r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
    "url": r'^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$',
    "ipv4": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
    "ipv6": r'^(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))$'
}


# Default messages
DEFAULT_MESSAGES = {
    "en": {
        "welcome": "Welcome to FTS Sales Manager",
        "login_prompt": "Please enter your credentials to continue",
        "login_success": "Login successful! Redirecting...",
        "login_failed": "Login failed. Please check your credentials.",
        "account_locked": "Your account has been locked. Please contact support.",
        "session_expired": "Your session has expired. Please login again.",
        "password_changed": "Your password has been changed successfully.",
        "profile_updated": "Your profile has been updated successfully.",
        "logout_success": "You have been logged out successfully.",
        "maintenance_mode": "System is under maintenance. Please try again later."
    },
    "ar": {
        "welcome": "مرحباً بك في مدير مبيعات FTS",
        "login_prompt": "يرجى إدخال بياناتك للمتابعة",
        "login_success": "تم تسجيل الدخول بنجاح! جاري التحويل...",
        "login_failed": "فشل تسجيل الدخول. يرجى التحقق من بياناتك.",
        "account_locked": "تم قفل حسابك. يرجى الاتصال بالدعم.",
        "session_expired": "انتهت صلاحية جلستك. يرجى تسجيل الدخول مرة أخرى.",
        "password_changed": "تم تغيير كلمة المرور بنجاح.",
        "profile_updated": "تم تحديث ملفك الشخصي بنجاح.",
        "logout_success": "تم تسجيل الخروج بنجاح.",
        "maintenance_mode": "النظام تحت الصيانة. يرجى المحاولة لاحقاً."
    }
}


# Icons
ICONS = {
    "user": "👤",
    "lock": "🔒",
    "eye": "👁",
    "eye_closed": "👁‍🗨",
    "key": "🔑",
    "shield": "🛡️",
    "warning": "⚠️",
    "error": "❌",
    "success": "✅",
    "info": "ℹ️",
    "language": "🌐",
    "theme": "🌓",
    "help": "❓",
    "settings": "⚙️",
    "logout": "🚪",
    "fingerprint": "👆",
    "face": "😊",
    "email": "📧",
    "phone": "📱",
    "clock": "🕐",
    "calendar": "📅",
    "location": "📍",
    "device": "💻"
}