# -*- coding: utf-8 -*-
"""
core/language_manager.py

تدير هذه الفئة تحميل الترجمات (locale) بناءً على اختيار المستخدم للغة (عربي أو إنجليزي).
تعتمد على ملفات YAML داخل مجلد locales/ للحصول على النصوص المترجمة حسب المفاتيح.
يمكن تغيير اللغة أثناء تشغيل التطبيق دون إعادة تشغيله.
"""

# ------------------------------------------------------------
# استيرادات المكتبات القياسية
# ------------------------------------------------------------
import os
from typing import Any, Dict

# ------------------------------------------------------------
# استيرادات المكتبات الخارجية
# ------------------------------------------------------------
import yaml

# ------------------------------------------------------------
# استيرادات وحدات المشروع
# ------------------------------------------------------------
from core.config_manager import ConfigManager
from core.logger import logger


class LanguageManager:
    """
    فئة LanguageManager مسؤولة عن:
    - قراءة إعدادات اللغة الحالية من ConfigManager.
    - تحميل ملف الترجمة المناسب (ar.yaml أو en.yaml) إلى قاموس داخلي.
    - توفير واجهة للحصول على النص المترجم حسب المفتاح (text key).
    - تغيير اللغة وتحديث ConfigManager وإعادة تحميل الترجمات.
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        """
        تهيئة LanguageManager.
        :param config_manager: كائن ConfigManager لقراءة/تعديل إعداد اللغة في ملف الإعدادات.
        """
        self.config_manager = config_manager

        # افتراض أن ConfigManager لديه دالة get() أو get_config()
        try:
            # محاولة الحصول على اللغة من ConfigManager
            self.current_lang: str = self.config_manager.get("language", "en")
        except AttributeError:
            try:
                # محاولة بديلة
                config_data = self.config_manager.get_config()
                self.current_lang: str = config_data.get("language", "en")
            except:
                # القيمة الافتراضية
                self.current_lang: str = "en"

        self.translations: Dict[str, Any] = {}
        self._load_translations()

    def _load_translations(self) -> None:
        """
        تحميل ملف الترجمة بناءً على self.current_lang إلى القاموس self.translations.
        يتوقع وجود ملف ضمن مجلد "locales" بالتنسيق "<lang>.yaml"، مثل "ar.yaml" أو "en.yaml".
        """
        lang_code = self.current_lang.lower()
        locales_dir = os.path.join("locales")
        file_name = f"{lang_code}.yaml"
        file_path = os.path.join(locales_dir, file_name)

        if not os.path.isdir(locales_dir):
            logger.warning(f"LanguageManager: مجلد 'locales/' غير موجود. لا يمكن تحميل الترجمات.")
            self.translations = {}
            return

        if not os.path.isfile(file_path):
            logger.error(f"LanguageManager: ملف الترجمة '{file_path}' غير موجود. استخدم المفاتيح الافتراضية (اللغة الإنجليزية).")
            self.translations = {}
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.translations = yaml.safe_load(f) or {}
            logger.info(f"LanguageManager: تم تحميل الترجمات من '{file_path}'.")
        except Exception as exc:
            logger.error(f"LanguageManager: خطأ أثناء قراءة ملف الترجمة '{file_path}': {exc}", exc_info=True)
            self.translations = {}

    def get(self, key: str, default: str = "") -> str:
        """
        إرجاع النص المترجم للمفتاح المحدد.
        إذا لم يكن المفتاح موجودًا في القاموس، يُعاد default.

        :param key: المفتاح النصي كما هو موجود في ملفات الترجمة YAML.
        :param default: القيمة الافتراضية إذا لم يُعثر على المفتاح.
        :return: النص المترجم (أو default).
        """
        # في حالة وجود تعشيش في ملفات YAML تكون القيم قد تكون dict؛ ولكن هنا نتوقع قيمة نصية لكل مفتاح.
        value = self.translations.get(key)
        if isinstance(value, str):
            return value
        elif value is None:
            return default
        else:
            # في حال كان المفتاح يشير إلى هيكل معقد (غير نص مباشرة)، نحوله إلى نص
            try:
                return str(value)
            except Exception:
                return default

    def set_language(self, lang_code: str) -> None:
        """
        تغيير اللغة الحالية إلى lang_code (مثل "ar" أو "en").
        يتم تحديث ConfigManager وحفظه، ثم إعادة تحميل الترجمات الجديدة.

        :param lang_code: رمز اللغة الجديد.
        """
        try:
            lang_code = lang_code.lower()
            previous = self.current_lang
            if lang_code == previous:
                logger.debug(f"LanguageManager: اللغة '{lang_code}' هي نفسها اللغة الحالية؛ لا تغيير.")
                return

            # تحديث الإعدادات وحفظها
            self.current_lang = lang_code

            # إصلاح الخطأ: استخدام self.config_manager بدلاً من self.config
            if hasattr(self.config_manager, 'set'):
                self.config_manager.set("language", lang_code)
            elif hasattr(self.config_manager, 'update_config'):
                self.config_manager.update_config({"language": lang_code})
            else:
                logger.warning(f"LanguageManager: لا يمكن حفظ إعداد اللغة. ConfigManager لا يحتوي على دالة set() أو update_config().")

            logger.info(f"LanguageManager: تم تغيير اللغة من '{previous}' إلى '{lang_code}'. إعادة تحميل الترجمات.")
            self._load_translations()

        except Exception as exc:
            logger.error(f"LanguageManager: خطأ أثناء تغيير اللغة إلى '{lang_code}': {exc}", exc_info=True)
            # في حالة الخطأ، نحاول على الأقل إعادة تحميل الترجمات للغة الحالية
            self._load_translations()

    def reload(self) -> None:
        """
        إعادة تحميل الترجمات بناءً على self.current_lang الحالية.
        يمكن استدعاؤه إذا تم تعديل ملفات الترجمة يدويًا أثناء تشغيل التطبيق.
        """
        try:
            logger.debug("LanguageManager: إعادة تحميل الترجمات.")
            self._load_translations()
        except Exception as exc:
            logger.error(f"LanguageManager: خطأ أثناء إعادة تحميل الترجمات: {exc}", exc_info=True)

    def get_current_language(self) -> str:
        """
        إرجاع رمز اللغة الحالية.
        :return: رمز اللغة الحالية (مثل "ar" أو "en").
        """
        return self.current_lang

    def is_rtl(self) -> bool:
        """
        تحديد ما إذا كانت اللغة الحالية تُكتب من اليمين إلى اليسار.
        :return: True إذا كانت اللغة العربية، False للغات الأخرى.
        """
        return self.current_lang.lower() in ["ar", "arabic", "العربية"]