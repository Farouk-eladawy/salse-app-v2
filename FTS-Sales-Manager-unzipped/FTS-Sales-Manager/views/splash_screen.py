# -*- coding: utf-8 -*-
"""
views/splash_screen.py

شاشة ترحيب محسنة مع:
- شعار متحرك
- شريط تقدم
- معلومات الإصدار
- رسائل تحميل ديناميكية
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional, Callable
import threading
import time
from PIL import Image, ImageTk
import os


class SplashScreen(ctk.CTkToplevel):
    """
    شاشة ترحيب محسنة مع تأثيرات بصرية وتحميل ديناميكي
    """

    def __init__(self,
                 duration: int = 3000,
                 app_name: str = "FTS Sales Manager",
                 version: str = "2.0",
                 logo_path: Optional[str] = None,
                 loading_callback: Optional[Callable[['SplashScreen'], None]] = None,
                 master: Optional[tk.Tk] = None) -> None:
        """
        تهيئة شاشة الترحيب المحسنة

        :param duration: مدة العرض بالمللي ثانية
        :param app_name: اسم التطبيق
        :param version: رقم الإصدار
        :param logo_path: مسار الشعار (اختياري)
        :param loading_callback: دالة للتحميل في الخلفية
        :param master: النافذة الأساسية (لتجنب إنشاء نافذة tk إضافية)
        """
        # إنشاء نافذة أساسية مخفية إذا لم تُمرر
        if master is None:
            self._temp_root = tk.Tk()
            self._temp_root.withdraw()
            super().__init__(self._temp_root)
        else:
            self._temp_root = None
            super().__init__(master)

        self.app_name = app_name
        self.version = version
        self.logo_path = logo_path
        self.loading_callback = loading_callback
        self._loading_complete = False
        self._min_display_time = 1500  # عرض لمدة 1.5 ثانية على الأقل

        # إعدادات النافذة
        self.overrideredirect(True)  # إزالة إطار النافذة
        self.attributes("-topmost", True)  # فوق جميع النوافذ

        # جعل النافذة شفافة قليلاً (Windows/Linux)
        try:
            self.attributes("-alpha", 0.95)
        except:
            pass

        # تطبيق الثيم
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # بناء المحتوى
        self._build_ui()

        # توسيط النافذة
        self._center_window()

        # بدء التحريك
        self._start_animations()

        # جدولة الإغلاق
        if loading_callback:
            # بدء التحميل في الخلفية
            self._start_background_loading()
        else:
            # إغلاق بعد المدة المحددة
            self.after(duration, self._close_splash)

    def _build_ui(self) -> None:
        """بناء محتوى شاشة الترحيب"""
        # الإطار الرئيسي مع خلفية متدرجة
        self.main_frame = ctk.CTkFrame(
            self,
            fg_color=("#1a1a1a", "#1a1a1a"),
            corner_radius=20,
            border_width=2,
            border_color=("#3498db", "#2980b9")
        )
        self.main_frame.pack(expand=True, fill="both", padx=2, pady=2)

        # إطار المحتوى
        content_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        content_frame.pack(expand=True, fill="both", padx=40, pady=40)

        # الشعار أو الأيقونة
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                # تحميل الصورة
                logo_image = Image.open(self.logo_path)
                logo_image = logo_image.resize((120, 120), Image.Resampling.LANCZOS)
                self.logo_photo = ctk.CTkImage(
                    light_image=logo_image,
                    dark_image=logo_image,
                    size=(120, 120)
                )
                logo_label = ctk.CTkLabel(
                    content_frame,
                    image=self.logo_photo,
                    text=""
                )
                logo_label.pack(pady=(0, 20))
            except:
                # عرض أيقونة نصية في حالة فشل تحميل الصورة
                self._create_text_logo(content_frame)
        else:
            # أيقونة نصية افتراضية
            self._create_text_logo(content_frame)

        # اسم التطبيق
        self.app_label = ctk.CTkLabel(
            content_frame,
            text=self.app_name,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=("#ffffff", "#ffffff")
        )
        self.app_label.pack(pady=(0, 10))

        # الإصدار
        version_label = ctk.CTkLabel(
            content_frame,
            text=f"Version {self.version}",
            font=ctk.CTkFont(size=14),
            text_color=("#cccccc", "#cccccc")
        )
        version_label.pack()

        # شريط التقدم
        self.progress_frame = ctk.CTkFrame(
            content_frame,
            fg_color="transparent"
        )
        self.progress_frame.pack(fill="x", pady=(30, 10))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            width=300,
            height=6,
            corner_radius=3,
            fg_color=("#333333", "#333333"),
            progress_color=("#3498db", "#2980b9")
        )
        self.progress_bar.pack()
        self.progress_bar.set(0)

        # نص التحميل
        self.loading_label = ctk.CTkLabel(
            content_frame,
            text="Initializing...",
            font=ctk.CTkFont(size=12),
            text_color=("#aaaaaa", "#aaaaaa")
        )
        self.loading_label.pack()

        # حقوق النشر
        copyright_label = ctk.CTkLabel(
            content_frame,
            text="© 2024 FTS - All Rights Reserved",
            font=ctk.CTkFont(size=10),
            text_color=("#666666", "#666666")
        )
        copyright_label.pack(side="bottom", pady=(20, 0))

    def _create_text_logo(self, parent):
        """إنشاء شعار نصي"""
        logo_frame = ctk.CTkFrame(
            parent,
            fg_color=("#3498db", "#2980b9"),
            corner_radius=60,
            width=120,
            height=120
        )
        logo_frame.pack(pady=(0, 20))
        logo_frame.pack_propagate(False)

        logo_text = ctk.CTkLabel(
            logo_frame,
            text="FTS",
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=("#ffffff", "#ffffff")
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        # تحديد الحجم
        window_width = 400
        window_height = 500

        # الحصول على أبعاد الشاشة
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # حساب الموضع
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # تطبيق الحجم والموضع
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

    def _start_animations(self):
        """بدء التحريكات"""
        # تأثير fade in
        self._fade_in()

        # تحريك شريط التقدم
        self._animate_progress()

        # تحديث نص التحميل
        self._update_loading_text()

    def _fade_in(self):
        """تأثير الظهور التدريجي"""
        alpha = 0.0

        def update_alpha():
            nonlocal alpha
            if alpha < 0.95:
                alpha += 0.05
                try:
                    self.attributes("-alpha", alpha)
                except:
                    pass
                self.after(20, update_alpha)

        try:
            self.attributes("-alpha", 0.0)
            self.after(10, update_alpha)
        except:
            # في حالة عدم دعم الشفافية
            pass

    def _animate_progress(self):
        """تحريك شريط التقدم"""
        self.progress_value = 0.0

        def update_progress():
            if self.progress_value < 1.0:
                # زيادة بطيئة في البداية، سريعة في النهاية
                if self.progress_value < 0.8:
                    increment = 0.01
                else:
                    increment = 0.02

                self.progress_value += increment
                self.progress_bar.set(min(self.progress_value, 1.0))

                # تحديث كل 50ms
                self.after(50, update_progress)
            elif self._loading_complete:
                # اكتمل التحميل
                self._close_splash()

        update_progress()

    def _update_loading_text(self):
        """تحديث نص التحميل بشكل دوري"""
        messages = [
            "Initializing...",
            "Loading configuration...",
            "Connecting to database...",
            "Loading user data...",
            "Preparing interface...",
            "Almost ready..."
        ]

        index = 0

        def update_text():
            nonlocal index
            if not self._loading_complete:
                self.loading_label.configure(text=messages[index % len(messages)])
                index += 1

                # تحديث كل 500ms
                self.after(500, update_text)

        update_text()

    def _start_background_loading(self):
        """بدء التحميل في الخلفية"""
        start_time = time.time()

        def loading_thread():
            try:
                # استدعاء دالة التحميل
                if self.loading_callback:
                    self.loading_callback(self)
            except Exception as e:
                print(f"Error during loading: {e}")
            finally:
                # التأكد من عرض الشاشة للحد الأدنى من الوقت
                elapsed = (time.time() - start_time) * 1000
                if elapsed < self._min_display_time:
                    time.sleep((self._min_display_time - elapsed) / 1000)

                self._loading_complete = True

        thread = threading.Thread(target=loading_thread, daemon=True)
        thread.start()

    def _close_splash(self):
        """إغلاق شاشة الترحيب مع تأثير fade out"""
        def fade_out(alpha=0.95):
            if alpha > 0.0:
                alpha -= 0.05
                try:
                    self.attributes("-alpha", alpha)
                except:
                    pass
                self.after(20, lambda: fade_out(alpha))
            else:
                # تنظيف النافذة المؤقتة إذا كانت موجودة
                if self._temp_root:
                    self._temp_root.destroy()
                self.destroy()

        # بدء fade out
        fade_out()

    def update_progress(self, value: float, message: str = ""):
        """
        تحديث التقدم يدوياً

        :param value: قيمة التقدم (0.0 - 1.0)
        :param message: رسالة التحميل
        """
        self.progress_value = value
        self.progress_bar.set(value)

        if message:
            self.loading_label.configure(text=message)

    def set_loading_complete(self):
        """وضع علامة اكتمال التحميل"""
        self._loading_complete = True
        self.update_progress(1.0, "Ready!")

        # إغلاق بعد تأخير قصير
        self.after(500, self._close_splash)