# -*- coding: utf-8 -*-
"""
utils/image_utils.py

أدوات مساعدة لتحميل وإدارة الصور في CustomTkinter
"""

import os
import sys
from PIL import Image
import customtkinter as ctk
from typing import Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class ImageLoader:
    """فئة مساعدة لتحميل الصور بطريقة آمنة"""

    # ذاكرة تخزين مؤقت للصور المحملة
    _image_cache = {}

    @staticmethod
    def load_image(
        path: str,
        size: Optional[Tuple[int, int]] = None,
        maintain_aspect_ratio: bool = True
    ) -> Optional[ctk.CTkImage]:
        """
        تحميل صورة وتحويلها إلى CTkImage

        Args:
            path: مسار الصورة
            size: الحجم المطلوب (width, height)
            maintain_aspect_ratio: الحفاظ على نسبة العرض إلى الارتفاع

        Returns:
            CTkImage أو None في حالة الفشل
        """
        # التحقق من الذاكرة المؤقتة
        cache_key = f"{path}_{size}_{maintain_aspect_ratio}"
        if cache_key in ImageLoader._image_cache:
            return ImageLoader._image_cache[cache_key]

        try:
            # التحقق من وجود الملف
            if not os.path.exists(path):
                logger.warning(f"ملف الصورة غير موجود: {path}")
                return None

            # فتح الصورة
            pil_image = Image.open(path)

            # تحويل إلى RGBA للحصول على أفضل توافق
            if pil_image.mode != 'RGBA':
                # إنشاء صورة RGBA جديدة
                rgba_image = Image.new('RGBA', pil_image.size, (255, 255, 255, 255))

                # لصق الصورة الأصلية
                if pil_image.mode == 'P':  # صورة مفهرسة
                    pil_image = pil_image.convert('RGBA')
                rgba_image.paste(pil_image, (0, 0))
                pil_image = rgba_image

            # تغيير الحجم إذا تم تحديده
            if size:
                if maintain_aspect_ratio:
                    pil_image.thumbnail(size, Image.Resampling.LANCZOS)
                    # حساب الحجم الفعلي بعد thumbnail
                    actual_size = pil_image.size
                else:
                    pil_image = pil_image.resize(size, Image.Resampling.LANCZOS)
                    actual_size = size
            else:
                actual_size = pil_image.size

            # إنشاء CTkImage
            ctk_image = ctk.CTkImage(
                light_image=pil_image,
                dark_image=pil_image,
                size=actual_size
            )

            # حفظ في الذاكرة المؤقتة
            ImageLoader._image_cache[cache_key] = ctk_image

            logger.info(f"تم تحميل الصورة بنجاح: {path}")
            return ctk_image

        except Exception as e:
            logger.error(f"فشل تحميل الصورة {path}: {e}")
            return None

    @staticmethod
    def load_icon(
        icon_name: str,
        size: Tuple[int, int] = (24, 24),
        directories: Optional[list] = None
    ) -> Optional[ctk.CTkImage]:
        """
        تحميل أيقونة من مجلدات متعددة

        Args:
            icon_name: اسم الأيقونة (بدون امتداد)
            size: حجم الأيقونة
            directories: قائمة المجلدات للبحث فيها

        Returns:
            CTkImage أو None
        """
        if directories is None:
            directories = [
                "resources/icons",
                "assets/icons",
                "icons",
                "resources",
                "assets"
            ]

        extensions = ['.png', '.jpg', '.jpeg', '.ico', '.gif']

        for directory in directories:
            for ext in extensions:
                path = os.path.join(directory, f"{icon_name}{ext}")
                if os.path.exists(path):
                    return ImageLoader.load_image(path, size)

        logger.warning(f"لم يتم العثور على الأيقونة: {icon_name}")
        return None

    @staticmethod
    def create_placeholder_image(
        size: Tuple[int, int] = (50, 50),
        color: str = "#cccccc",
        text: str = "?"
    ) -> ctk.CTkImage:
        """
        إنشاء صورة بديلة عند فشل تحميل الصورة الأصلية

        Args:
            size: حجم الصورة
            color: لون الخلفية
            text: النص المعروض

        Returns:
            CTkImage
        """
        # إنشاء صورة جديدة
        image = Image.new('RGBA', size, color)

        # يمكن إضافة نص أو رسومات هنا إذا لزم الأمر
        # (يتطلب ImageDraw)

        return ctk.CTkImage(
            light_image=image,
            dark_image=image,
            size=size
        )

    @staticmethod
    def clear_cache():
        """مسح الذاكرة المؤقتة للصور"""
        ImageLoader._image_cache.clear()
        logger.info("تم مسح ذاكرة التخزين المؤقت للصور")


class IconManager:
    """مدير الأيقونات للتطبيق"""

    # أيقونات التطبيق الافتراضية
    DEFAULT_ICONS = {
        "app": "✈️",
        "add": "➕",
        "edit": "✏️",
        "delete": "🗑️",
        "save": "💾",
        "cancel": "❌",
        "refresh": "🔄",
        "search": "🔍",
        "settings": "⚙️",
        "user": "👤",
        "logout": "🚪",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "❌",
        "success": "✅",
        "calendar": "📅",
        "clock": "🕐",
        "money": "💰",
        "document": "📄",
        "folder": "📁",
        "email": "📧",
        "phone": "📞",
        "location": "📍",
        "star": "⭐",
        "heart": "❤️"
    }

    @staticmethod
    def get_icon(name: str, fallback: str = "❓") -> str:
        """الحصول على أيقونة إيموجي"""
        return IconManager.DEFAULT_ICONS.get(name, fallback)

    @staticmethod
    def create_icon_button(
        parent,
        icon_name: str,
        text: str = "",
        command = None,
        size: Tuple[int, int] = (40, 40),
        **kwargs
    ) -> ctk.CTkButton:
        """
        إنشاء زر مع أيقونة

        Args:
            parent: الحاوية الأب
            icon_name: اسم الأيقونة
            text: نص الزر (اختياري)
            command: دالة الأمر
            size: حجم الزر
            **kwargs: خيارات إضافية للزر

        Returns:
            CTkButton
        """
        # محاولة تحميل صورة الأيقونة
        icon_image = ImageLoader.load_icon(icon_name, size=(24, 24))

        if icon_image:
            # إنشاء زر مع صورة
            button = ctk.CTkButton(
                parent,
                image=icon_image,
                text=text,
                command=command,
                width=size[0],
                height=size[1],
                **kwargs
            )
        else:
            # استخدام إيموجي كبديل
            emoji = IconManager.get_icon(icon_name)
            button_text = f"{emoji} {text}" if text else emoji
            button = ctk.CTkButton(
                parent,
                text=button_text,
                command=command,
                width=size[0],
                height=size[1],
                **kwargs
            )

        return button


def setup_window_icon(window, icon_paths: Optional[list] = None):
    """
    تعيين أيقونة النافذة

    Args:
        window: نافذة CTk أو Tk
        icon_paths: قائمة مسارات الأيقونات للمحاولة
    """
    if icon_paths is None:
        icon_paths = [
            "resources/app_icon.ico",
            "resources/icon.ico",
            "assets/icon.ico",
            "resources/app_icon.png",
            "resources/icon.png",
            "assets/icon.png"
        ]

    for path in icon_paths:
        try:
            if os.path.exists(path):
                if path.endswith('.ico'):
                    # استخدام ملف ICO مباشرة
                    window.iconbitmap(path)
                    logger.info(f"تم تعيين أيقونة النافذة: {path}")
                    return True
                else:
                    # تحويل PNG إلى PhotoImage
                    # ملاحظة: iconphoto يتطلب PhotoImage وليس CTkImage
                    from tkinter import PhotoImage
                    icon = PhotoImage(file=path)
                    window.iconphoto(False, icon)
                    logger.info(f"تم تعيين أيقونة النافذة: {path}")
                    return True
        except Exception as e:
            logger.debug(f"فشل تعيين الأيقونة {path}: {e}")
            continue

    logger.warning("لم يتم العثور على أيقونة مناسبة للنافذة")
    return False