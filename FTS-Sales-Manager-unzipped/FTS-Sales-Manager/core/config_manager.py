# -*- coding: utf-8 -*-
"""
core/config_manager.py

تدير هذه الفئة قراءة وكتابة إعدادات التطبيق من/إلى ملف YAML.
تدعم أيضاً قراءة المتغيرات الحساسة من ملف .env
ودعم شامل لإعدادات Views والأداء
"""

import os
import yaml
from dotenv import load_dotenv
from core.logger import logger
from typing import Dict  # إذا لم يكن موجوداً
from typing import Dict, Any, Optional, List

class ConfigManager:
    """
    فئة ConfigManager تتولى:
    - تحميل المتغيرات من ملف .env
    - تحميل الإعدادات من ملف YAML
    - دمج الإعدادات مع إعطاء الأولوية لمتغيرات البيئة
    - حفظ التغييرات (غير الحساسة) في ملف YAML
    - إدارة إعدادات Views والأداء
    """

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """
        تهيئة ConfigManager.

        :param config_path: المسار إلى ملف الإعدادات YAML
        """
        self.config_path: str = config_path
        self.config_data: Dict[str, Any] = {}
        self.env_data: Dict[str, str] = {}

        # تحميل متغيرات البيئة أولاً
        self._load_env()

        # ثم تحميل إعدادات YAML
        self._load_config()

        # دمج الإعدادات
        self._merge_settings()

    def _load_env(self) -> None:
        """
        تحميل المتغيرات من ملف .env
        """
        # البحث عن ملف .env في المجلد الحالي أو المجلد الأعلى
        env_paths = ['.env', '../.env', os.path.join(os.path.dirname(__file__), '..', '.env')]

        env_loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path)
                env_loaded = True
                logger.info(f"ConfigManager: تم تحميل متغيرات البيئة من '{env_path}'")
                break

        if not env_loaded:
            logger.warning("ConfigManager: لم يتم العثور على ملف .env - استخدام القيم الافتراضية")

        # حفظ متغيرات البيئة المهمة
        self.env_data = {
            'airtable_api_key': os.getenv('AIRTABLE_API_KEY', ''),
            'airtable_base_id': os.getenv('AIRTABLE_BASE_ID', ''),
            'airtable_users_table': os.getenv('AIRTABLE_USERS_TABLE', 'Users'),
            'airtable_booking_table': os.getenv('AIRTABLE_BOOKING_TABLE', 'List V2'),
            'default_language': os.getenv('DEFAULT_LANGUAGE', 'ar'),
            'default_theme': os.getenv('DEFAULT_THEME', 'light'),
            'db_path': os.getenv('DB_PATH', 'fts_sales_cache.db'),
        }

        # إضافة جداول القوائم المنسدلة
        self.env_data.update({
            'airtable_guides_table': os.getenv('AIRTABLE_GUIDES_TABLE', 'Guides'),
            'airtable_agencies_table': os.getenv('AIRTABLE_AGENCIES_TABLE', 'Agencies'),
            'airtable_options_table': os.getenv('AIRTABLE_OPTIONS_TABLE', 'Trip Options'),
            'airtable_destinations_table': os.getenv('AIRTABLE_DESTINATIONS_TABLE', 'Destinations'),
                })

        # إضافة جداول القوائم المنسدلة الإضافية
        self.env_data.update({
            'airtable_tripnames_table': os.getenv('AIRTABLE_TRIPNAMES_TABLE', 'Trip Names'),
            'airtable_management_options_table': os.getenv('AIRTABLE_MANAGEMENT_OPTIONS_TABLE', 'Management Options'),
            'airtable_addons_table': os.getenv('AIRTABLE_ADDONS_TABLE', 'Add-ons'),
                })

    def _load_config(self) -> None:
        """
        تحميل الإعدادات من ملف YAML
        """
        if not os.path.exists(self.config_path):
            logger.warning(f"ConfigManager: ملف الإعدادات '{self.config_path}' غير موجود. سيتم إنشاء ملف جديد.")
            parent_dir = os.path.dirname(self.config_path)
            if parent_dir and not os.path.isdir(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                    logger.info(f"ConfigManager: تم إنشاء المجلد '{parent_dir}'.")
                except Exception as exc:
                    logger.error(f"ConfigManager: فشل إنشاء المجلد '{parent_dir}': {exc}", exc_info=True)

            # إنشاء ملف إعدادات افتراضي
            self._create_default_config()
        else:
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = yaml.safe_load(f) or {}
                logger.info(f"ConfigManager: تم تحميل الإعدادات من '{self.config_path}'.")
            except Exception as exc:
                logger.error(f"ConfigManager: خطأ أثناء قراءة ملف الإعدادات '{self.config_path}': {exc}", exc_info=True)
                self.config_data = {}

    def _create_default_config(self) -> None:
        """
        إنشاء ملف إعدادات افتراضي مع دعم Views
        """
        self.config_data = {
            'language': self.env_data.get('default_language', 'ar'),
            'appearance_mode': self.env_data.get('default_theme', 'light'),
            'color_theme': 'blue',
            'view_name': 'Sales App',
            'window_size': {
                'width': 1024,
                'height': 768
            },
            # إضافة الإعدادات الافتراضية لـ Views
            'views_settings': {
                'allow_view_switching': True,
                'show_current_view_in_status': True,
                'default_views': {
                    'admin': 'All Records',
                    'manager': 'Manager View',
                    'editor': 'Team View',
                    'viewer': 'My Bookings'
                },
                'role_views': {
                    'admin': ['All Records', 'Today\'s Bookings', 'This Week', 'This Month'],
                    'manager': ['Manager View', 'Team View', 'Today\'s Bookings', 'This Week'],
                    'editor': ['Team View', 'My Bookings', 'Today\'s Bookings'],
                    'viewer': ['My Bookings']
                }
            },
            'cache_settings': {
                'enable_cache': True,
                'default_cache_duration': 15,
                'view_cache_duration': {
                    'All Records': 30,
                    'Today\'s Bookings': 5,
                    'This Week': 15,
                    'This Month': 60
                }
            },
            'performance_settings': {
                'records_per_page': 100,
                'enable_lazy_loading': True,
                'show_loading_indicator': True,
                'background_loading': True
            }
        }
        self._save_config()

    def _merge_settings(self) -> None:
        """
        دمج الإعدادات مع إعطاء الأولوية لمتغيرات البيئة
        """
        # المتغيرات الحساسة من .env تأخذ الأولوية دائماً
        if self.env_data.get('airtable_api_key'):
            self.config_data['airtable_api_key'] = self.env_data['airtable_api_key']
        if self.env_data.get('airtable_base_id'):
            self.config_data['airtable_base_id'] = self.env_data['airtable_base_id']
        if self.env_data.get('airtable_users_table'):
            self.config_data['airtable_users_table'] = self.env_data['airtable_users_table']
        if self.env_data.get('airtable_booking_table'):
            self.config_data['airtable_booking_table'] = self.env_data['airtable_booking_table']

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        إرجاع قيمة الإعداد، مع التحقق من متغيرات البيئة أولاً

        :param key: اسم الإعداد
        :param default: القيمة الافتراضية
        :return: قيمة الإعداد
        """
        # التحقق من متغيرات البيئة أولاً للمفاتيح الحساسة
        if key in ['airtable_api_key', 'airtable_base_id']:
            env_value = self.env_data.get(key)
            if env_value:
                return env_value

        return self.config_data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        تعيين قيمة جديدة في الإعدادات
        ملاحظة: لا يتم حفظ المعلومات الحساسة في YAML

        :param key: اسم الإعداد
        :param value: القيمة الجديدة
        """
        # منع حفظ المعلومات الحساسة في YAML
        sensitive_keys = ['airtable_api_key', 'airtable_base_id', 'password', 'secret']

        if key not in sensitive_keys:
            self.config_data[key] = value
            logger.debug(f"ConfigManager: تم تعيين key='{key}' إلى القيمة: {value!r}.")
            self._save_config()
        else:
            logger.warning(f"ConfigManager: محاولة حفظ معلومات حساسة '{key}' - تم التجاهل")

    def _save_config(self) -> None:
        """
        حفظ الإعدادات غير الحساسة إلى ملف YAML
        """
        # إنشاء نسخة من البيانات بدون المعلومات الحساسة
        safe_data = {}
        sensitive_keys = ['airtable_api_key', 'airtable_base_id', 'password', 'secret']

        for key, value in self.config_data.items():
            if key not in sensitive_keys:
                safe_data[key] = value

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(safe_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            logger.info(f"ConfigManager: تم حفظ الإعدادات في '{self.config_path}'.")
        except Exception as exc:
            logger.error(f"ConfigManager: فشل حفظ الإعدادات إلى '{self.config_path}': {exc}", exc_info=True)

    def reload(self) -> None:
        """
        إعادة تحميل جميع الإعدادات
        """
        logger.debug("ConfigManager: إعادة تحميل الإعدادات.")
        self._load_env()
        self._load_config()
        self._merge_settings()

    # ============ دوال جديدة لدعم Views ============

    def get_all_settings(self) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات"""
        return self.config_data.copy()

    def get_setting(self, key: str, default: Any = None) -> Any:
        """الحصول على إعداد محدد (مرادف لـ get)"""
        return self.get(key, default)

    def get_nested_setting(self, keys: List[str], default: Any = None) -> Any:
        """
        الحصول على إعداد متداخل

        :param keys: قائمة المفاتيح للوصول للقيمة المتداخلة
        :param default: القيمة الافتراضية
        :return: القيمة المطلوبة أو القيمة الافتراضية
        """
        value = self.config_data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
        return value if value is not None else default

    # دوال خاصة بـ Views
    def get_views_settings(self) -> Dict[str, Any]:
        """الحصول على جميع إعدادات Views"""
        return self.get_setting('views_settings', {
            'allow_view_switching': True,
            'default_views': {'viewer': 'My Bookings'}
        })

    def get_role_views(self, role: str) -> List[str]:
        """
        الحصول على Views المسموحة لدور معين

        :param role: دور المستخدم (admin, manager, editor, viewer)
        :return: قائمة أسماء Views المسموحة
        """
        return self.get_nested_setting(
            ['views_settings', 'role_views', role],
            ['My Bookings']  # القيمة الافتراضية
        )

    def get_default_view(self, role: str) -> str:
        """
        الحصول على View الافتراضي لدور معين

        :param role: دور المستخدم
        :return: اسم View الافتراضي
        """
        return self.get_nested_setting(
            ['views_settings', 'default_views', role],
            'My Bookings'
        )

    def is_view_switching_allowed(self) -> bool:
        """التحقق من السماح بتبديل Views"""
        return self.get_nested_setting(
            ['views_settings', 'allow_view_switching'],
            True
        )

    def get_view_cache_duration(self, view_name: str) -> int:
        """
        الحصول على مدة الكاش لـ View معين بالدقائق

        :param view_name: اسم View
        :return: مدة الكاش بالدقائق
        """
        duration = self.get_nested_setting(
            ['cache_settings', 'view_cache_duration', view_name]
        )
        if duration is None:
            duration = self.get_nested_setting(
                ['cache_settings', 'default_cache_duration'],
                15
            )
        return duration

    def get_view_specific_settings(self, view_name: str) -> Dict[str, Any]:
        """
        الحصول على الإعدادات الخاصة بـ View معين

        :param view_name: اسم View
        :return: قاموس بالإعدادات الخاصة
        """
        return self.get_nested_setting(
            ['views_settings', 'view_specific_settings', view_name],
            {}
        )

    def get_performance_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الأداء"""
        return self.get_setting('performance_settings', {
            'records_per_page': 100,
            'enable_lazy_loading': True,
            'show_loading_indicator': True,
            'background_loading': True
        })

    def get_export_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات التصدير"""
        return self.get_setting('export_settings', {
            'allowed_formats': ['excel', 'pdf', 'csv'],
            'max_export_records': 5000,
            'include_timestamp': True
        })

    def get_cache_settings(self) -> Dict[str, Any]:
        """الحصول على جميع إعدادات الكاش"""
        return self.get_setting('cache_settings', {
            'enable_cache': True,
            'default_cache_duration': 15,
            'max_cache_size': 1000,
            'clear_on_logout': True
        })

    def is_cache_enabled(self) -> bool:
        """التحقق من تفعيل الكاش"""
        return self.get_nested_setting(['cache_settings', 'enable_cache'], True)

    def get_security_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات الأمان"""
        return self.get_setting('security_settings', {
            'session_timeout': 60,
            'log_failed_attempts': True,
            'max_failed_attempts': 5,
            'lockout_duration': 15
        })

    def get_logging_settings(self) -> Dict[str, Any]:
        """الحصول على إعدادات السجلات"""
        return self.get_setting('logging_settings', {
            'level': 'INFO',
            'log_to_file': True,
            'log_file_path': 'logs/app.log',
            'max_log_size': 10,
            'backup_count': 5
        })

    def update_setting(self, key: str, value: Any) -> bool:
        """
        تحديث إعداد معين (مرادف لـ set مع إرجاع نتيجة)

        :param key: اسم الإعداد
        :param value: القيمة الجديدة
        :return: True إذا نجح التحديث
        """
        try:
            self.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False

    def save_settings(self) -> bool:
        """
        حفظ الإعدادات إلى الملف (مرادف لـ _save_config)

        :return: True إذا نجح الحفظ
        """
        try:
            self._save_config()
            return True
        except Exception:
            return False

    # ============ دوال إعدادات المستخدم ============
    USER_SETTINGS_FILE = "user_settings.yaml"

    def _load_user_settings(self):
        """تحميل إعدادات المستخدم الشخصية"""
        try:
            with open(self.USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
                self.user_settings = yaml.safe_load(f) or {}
        except FileNotFoundError:
            self.user_settings = {
                "language": "ar",
                "theme": "light",
                "window_size": {"width": 1024, "height": 768},
                "last_filter": "",
                "last_view": "",  # إضافة آخر View مستخدم
                "favorites_views": []  # Views المفضلة
            }
            with open(self.USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
                yaml.dump(self.user_settings, f, allow_unicode=True)

    def save_user_setting(self, key: str, value: Any):
        """حفظ إعداد مستخدم معين"""
        if not hasattr(self, 'user_settings'):
            self._load_user_settings()

        self.user_settings[key] = value
        with open(self.USER_SETTINGS_FILE, "w", encoding="utf-8") as f:
            yaml.dump(self.user_settings, f, allow_unicode=True)

    def get_user_setting(self, key: str, default: Any = None) -> Any:
        """الحصول على إعداد مستخدم معين"""
        if not hasattr(self, 'user_settings'):
            self._load_user_settings()

        return self.user_settings.get(key, default)

    def get_last_used_view(self) -> Optional[str]:
        """الحصول على آخر View استخدمه المستخدم"""
        return self.get_user_setting('last_view')

    def save_last_used_view(self, view_name: str):
        """حفظ آخر View استخدمه المستخدم"""
        self.save_user_setting('last_view', view_name)

    def get_favorite_views(self) -> List[str]:
        """الحصول على Views المفضلة للمستخدم"""
        return self.get_user_setting('favorites_views', [])

    def add_favorite_view(self, view_name: str):
        """إضافة View للمفضلة"""
        favorites = self.get_favorite_views()
        if view_name not in favorites:
            favorites.append(view_name)
            self.save_user_setting('favorites_views', favorites)

    def remove_favorite_view(self, view_name: str):
        """إزالة View من المفضلة"""
        favorites = self.get_favorite_views()
        if view_name in favorites:
            favorites.remove(view_name)
            self.save_user_setting('favorites_views', favorites)

    def get_airtable_config(self) -> Dict[str, str]:
        """
        الحصول على إعدادات Airtable من متغيرات البيئة

        :return: قاموس يحتوي على api_key و base_id
        """
        return {
            'api_key': self.env_data.get('airtable_api_key', ''),
            'base_id': self.env_data.get('airtable_base_id', ''),
            'users_table': self.env_data.get('airtable_users_table', 'users'),
            'booking_table': self.env_data.get('airtable_booking_table', 'List V2')
        }

    def get_dropdown_tables_config(self) -> Dict[str, str]:
        """
        الحصول على أسماء جداول القوائم المنسدلة

        :return: قاموس بأسماء الجداول
        """
        return {
            'guides': self.env_data.get('airtable_guides_table', 'Guides'),
            'agencies': self.env_data.get('airtable_agencies_table', 'Agencies'),
            'options': self.env_data.get('airtable_options_table', 'Trip Options'),
            'destinations': self.env_data.get('airtable_destinations_table', 'Destinations'),
            'tripnames': self.env_data.get('airtable_tripnames_table', 'Trip Names'),
            'management_options': self.env_data.get('airtable_management_options_table', 'Management Options'),
            'addons': self.env_data.get('airtable_addons_table', 'Add-ons')
        }