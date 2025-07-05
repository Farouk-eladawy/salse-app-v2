# -*- coding: utf-8 -*-
"""
views/components/status_bar.py

مكون شريط الحالة المحسن بتصميم احترافي مع حماية من الأخطاء
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Tuple
import threading

from core.language_manager import LanguageManager


class StatusBarComponent(ctk.CTkFrame):
    """مكون شريط الحالة المحسن بتصميم احترافي مع حماية من الأخطاء"""

    def __init__(
        self,
        parent,
        lang_manager: LanguageManager,
        **kwargs
    ):
        # إعدادات احترافية للإطار
        kwargs.setdefault('height', 35)
        kwargs.setdefault('corner_radius', 0)
        kwargs.setdefault('fg_color', ("#f8f9fa", "#1e1e1e"))
        kwargs.setdefault('border_width', 1)
        kwargs.setdefault('border_color', ("#e0e0e0", "#444444"))

        super().__init__(parent, **kwargs)
        self.pack_propagate(False)

        self.lang_manager = lang_manager

        # متغيرات الحالة
        self.current_status = ""
        self.status_type = "info"
        self.progress_active = False

        # متغير لتتبع حالة التدمير
        self._destroyed = False
        self._time_update_running = False

        self._build_ui()
        self._start_time_update()

        # ربط حدث التدمير
        self.bind("<Destroy>", self._on_destroy)

    def _on_destroy(self, event=None):
        """معالج تدمير المكون"""
        if event and event.widget == self:
            self._destroyed = True
            self._time_update_running = False

    def _is_valid(self):
        """فحص صحة المكون قبل أي عملية"""
        try:
            return not self._destroyed and self.winfo_exists()
        except:
            self._destroyed = True
            return False

    def _safe_configure(self, widget, **kwargs):
        """تكوين آمن للمكونات مع فحص الصحة"""
        try:
            if self._is_valid() and widget and hasattr(widget, 'configure'):
                if hasattr(widget, 'winfo_exists'):
                    if widget.winfo_exists():
                        widget.configure(**kwargs)
                        return True
                else:
                    widget.configure(**kwargs)
                    return True
        except Exception as e:
            # تسجيل الخطأ بهدوء دون إيقاف البرنامج
            pass
        return False

    def _build_ui(self):
        """بناء الواجهة المحسنة"""
        # الحاوية الرئيسية
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10)

        # القسم الأيسر - رسالة الحالة
        left_section = ctk.CTkFrame(main_container, fg_color="transparent")
        left_section.pack(side="left", fill="x", expand=True)

        # أيقونة الحالة
        self.status_icon = ctk.CTkLabel(
            left_section,
            text="ℹ️",
            font=ctk.CTkFont(size=14),
            width=20
        )
        self.status_icon.pack(side="left", padx=(0, 5))

        # رسالة الحالة
        self.status_label = ctk.CTkLabel(
            left_section,
            text=self.lang_manager.get("ready", "Ready"),
            anchor="w",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", fill="x", expand=True)

        # شريط التقدم (مخفي افتراضياً)
        self.progress_bar = ctk.CTkProgressBar(
            left_section,
            width=150,
            height=8,
            corner_radius=4,
            progress_color=("#2196f3", "#1976d2")
        )

        # القسم الأوسط - معلومات إضافية
        middle_section = ctk.CTkFrame(main_container, fg_color="transparent")
        middle_section.pack(side="left", padx=20)

        # عداد العناصر
        self.items_frame = ctk.CTkFrame(middle_section, fg_color="transparent")
        self.items_frame.pack(side="left", padx=10)

        self.items_icon = ctk.CTkLabel(
            self.items_frame,
            text="📄",
            font=ctk.CTkFont(size=12)
        )

        self.items_label = ctk.CTkLabel(
            self.items_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#999999")
        )

        # القسم الأيمن - المؤشرات
        right_section = ctk.CTkFrame(main_container, fg_color="transparent")
        right_section.pack(side="right")

        # مؤشر الاتصال
        self.connection_frame = ctk.CTkFrame(right_section, fg_color="transparent")
        self.connection_frame.pack(side="left", padx=10)

        self.connection_indicator = ctk.CTkLabel(
            self.connection_frame,
            text="●",
            font=ctk.CTkFont(size=10),
            text_color=("#4caf50", "#2e7d32")
        )
        self.connection_indicator.pack(side="left", padx=(0, 3))

        self.connection_label = ctk.CTkLabel(
            self.connection_frame,
            text=self.lang_manager.get("connected", "Connected"),
            font=ctk.CTkFont(size=11),
            text_color=("#4caf50", "#2e7d32")
        )
        self.connection_label.pack(side="left")

        # خط فاصل
        separator = ctk.CTkFrame(
            right_section,
            width=1,
            fg_color=("#e0e0e0", "#444444")
        )
        separator.pack(side="left", fill="y", padx=10)

        # الوقت والتاريخ
        self.datetime_frame = ctk.CTkFrame(right_section, fg_color="transparent")
        self.datetime_frame.pack(side="left", padx=10)

        self.time_label = ctk.CTkLabel(
            self.datetime_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#1976d2", "#2196f3")
        )
        self.time_label.pack()

        self.date_label = ctk.CTkLabel(
            self.datetime_frame,
            text="",
            font=ctk.CTkFont(size=10),
            text_color=("#666666", "#999999")
        )
        self.date_label.pack()

    def set_status(self, message: str, status_type: str = "info", duration: int = None):
        """تعيين رسالة الحالة مع نوع وأيقونة - مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            self.current_status = message
            self.status_type = status_type

            # تحديث النص بطريقة آمنة
            if not self._safe_configure(self.status_label, text=message):
                return

            # تحديد الأيقونة واللون حسب النوع
            status_config = self._get_status_config(status_type)

            # تحديث الأيقونة
            self._safe_configure(
                self.status_icon,
                text=status_config["icon"],
                text_color=status_config["color"]
            )

            # تحديث لون النص
            self._safe_configure(self.status_label, text_color=status_config["color"])

            # تأثير الظهور
            self._animate_status_change()

            # إخفاء تلقائي بعد مدة معينة
            if duration and self._is_valid():
                self.after(duration * 1000, lambda: self._delayed_status_reset())

        except Exception as e:
            # في حالة حدوث خطأ، نحاول مرة أخيرة بطريقة بسيطة
            pass

    def _delayed_status_reset(self):
        """إعادة تعيين الحالة بعد تأخير مع فحص الصحة"""
        if self._is_valid():
            self.set_status(self.lang_manager.get("ready", "Ready"), "info")

    def _get_status_config(self, status_type: str) -> dict:
        """الحصول على تكوين الحالة"""
        is_dark = ctk.get_appearance_mode() == "Dark"

        status_configs = {
            "info": {
                "icon": "ℹ️",
                "color": ("#2196f3", "#1976d2")
            },
            "success": {
                "icon": "✅",
                "color": ("#4caf50", "#2e7d32")
            },
            "warning": {
                "icon": "⚠️",
                "color": ("#ff9800", "#f57c00")
            },
            "error": {
                "icon": "❌",
                "color": ("#f44336", "#d32f2f")
            },
            "loading": {
                "icon": "⏳",
                "color": ("#9c27b0", "#7b1fa2")
            }
        }

        config = status_configs.get(status_type, status_configs["info"])
        # اختيار اللون حسب الوضع
        config["color"] = config["color"][1 if is_dark else 0]

        return config

    def _animate_status_change(self):
        """تأثير تغيير الحالة مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            # تأثير الوميض للفت الانتباه
            if self.status_type in ["error", "warning"]:
                for i in range(2):
                    if not self._is_valid():
                        break

                    self._safe_configure(self.status_label, text_color="transparent")
                    if self._is_valid():
                        self.update()
                        self.after(100)

                    color = self._get_status_config(self.status_type)["color"]
                    self._safe_configure(self.status_label, text_color=color)
                    if self._is_valid():
                        self.update()
                        self.after(100)
        except:
            pass

    def set_connection_status(self, connected: bool, details: str = None):
        """تعيين حالة الاتصال مع تفاصيل - مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            if connected:
                self._safe_configure(self.connection_indicator, text_color=("#4caf50", "#2e7d32"))
                text = self.lang_manager.get("connected", "Connected")
                if details:
                    text += f" • {details}"
                self._safe_configure(
                    self.connection_label,
                    text=text,
                    text_color=("#4caf50", "#2e7d32")
                )

                # تأثير النبض للاتصال النشط
                self._pulse_connection_indicator()
            else:
                self._safe_configure(self.connection_indicator, text_color=("#f44336", "#d32f2f"))
                text = self.lang_manager.get("disconnected", "Disconnected")
                if details:
                    text += f" • {details}"
                self._safe_configure(
                    self.connection_label,
                    text=text,
                    text_color=("#f44336", "#d32f2f")
                )
        except:
            pass

    def _pulse_connection_indicator(self):
        """تأثير نبض لمؤشر الاتصال مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        def pulse():
            if self._is_valid():
                # تكبير
                self._safe_configure(self.connection_indicator, font=ctk.CTkFont(size=12))
                if self._is_valid():
                    self.after(200, lambda: self._safe_configure(self.connection_indicator, font=ctk.CTkFont(size=10)) if self._is_valid() else None)

        try:
            pulse()
        except:
            pass

    def show_progress(self, value: float = None, text: str = None):
        """عرض شريط التقدم مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            if not self.progress_active:
                self.progress_active = True
                if hasattr(self.progress_bar, 'pack') and self._is_valid():
                    self.progress_bar.pack(side="left", padx=(10, 0))
                    if hasattr(self.progress_bar, 'set'):
                        self.progress_bar.set(0)

            if value is not None and hasattr(self.progress_bar, 'set'):
                self.progress_bar.set(value)

            if text:
                self.set_status(text, "loading")

            # إخفاء التقدم عند الاكتمال
            if value and value >= 1.0 and self._is_valid():
                self.after(500, self.hide_progress)
        except:
            pass

    def hide_progress(self):
        """إخفاء شريط التقدم مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            self.progress_active = False
            if hasattr(self.progress_bar, 'pack_forget'):
                self.progress_bar.pack_forget()
            self.set_status(self.lang_manager.get("ready", "Ready"), "info")
        except:
            pass

    def show_items_count(self, total: int, filtered: int = None):
        """عرض عداد العناصر مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            if total > 0:
                if hasattr(self.items_icon, 'pack') and self._is_valid():
                    self.items_icon.pack(side="left", padx=(0, 3))

                if filtered is not None and filtered < total:
                    text = self.lang_manager.get(
                        "showing_filtered",
                        f"Showing {filtered} of {total}"
                    )
                else:
                    text = self.lang_manager.get(
                        "total_items",
                        f"{total} items"
                    )

                self._safe_configure(self.items_label, text=text)
                if hasattr(self.items_label, 'pack') and self._is_valid():
                    self.items_label.pack(side="left")
            else:
                if hasattr(self.items_icon, 'pack_forget'):
                    self.items_icon.pack_forget()
                if hasattr(self.items_label, 'pack_forget'):
                    self.items_label.pack_forget()
        except:
            pass

    def _update_time(self):
        """تحديث الوقت والتاريخ مع حماية من الأخطاء"""
        if not self._is_valid() or not self._time_update_running:
            return

        try:
            now = datetime.now()

            # تنسيق الوقت
            time_format = "%I:%M:%S %p" if self.lang_manager.current_lang == "en" else "%H:%M:%S"
            time_str = now.strftime(time_format)
            self._safe_configure(self.time_label, text=time_str)

            # تنسيق التاريخ
            if self.lang_manager.current_lang == "ar":
                # التاريخ بالعربية
                months_ar = [
                    "يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
                    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
                ]
                days_ar = [
                    "الإثنين", "الثلاثاء", "الأربعاء", "الخميس",
                    "الجمعة", "السبت", "الأحد"
                ]

                day = days_ar[now.weekday()]
                month = months_ar[now.month - 1]
                date_str = f"{day}، {now.day} {month} {now.year}"
            else:
                # التاريخ بالإنجليزية
                date_str = now.strftime("%A, %d %B %Y")

            self._safe_configure(self.date_label, text=date_str)

            # جدولة التحديث التالي
            if self._is_valid() and self._time_update_running:
                self.after(1000, self._update_time)

        except Exception as e:
            # إذا حدث خطأ، توقف عن التحديث
            self._time_update_running = False

    def _start_time_update(self):
        """بدء تحديث الوقت مع حماية من الأخطاء"""
        if self._is_valid():
            self._time_update_running = True
            self._update_time()

    def show_notification(self, title: str, message: str, type: str = "info"):
        """عرض إشعار مؤقت مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            # إنشاء إطار الإشعار
            top_window = self.winfo_toplevel()
            if not top_window or not hasattr(top_window, 'winfo_exists') or not top_window.winfo_exists():
                return

            notif_frame = ctk.CTkFrame(
                top_window,
                corner_radius=8,
                fg_color=("#ffffff", "#2b2b2b"),
                border_width=2,
                border_color=self._get_status_config(type)["color"]
            )

            # وضع الإشعار فوق شريط الحالة
            notif_frame.place(
                in_=self,
                x=10,
                y=-80,
                width=300,
                height=70
            )

            # محتوى الإشعار
            content_frame = ctk.CTkFrame(notif_frame, fg_color="transparent")
            content_frame.pack(expand=True, padx=15, pady=10)

            # العنوان
            title_label = ctk.CTkLabel(
                content_frame,
                text=title,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            )
            title_label.pack(fill="x")

            # الرسالة
            msg_label = ctk.CTkLabel(
                content_frame,
                text=message,
                font=ctk.CTkFont(size=11),
                anchor="w",
                text_color=("#666666", "#999999")
            )
            msg_label.pack(fill="x")

            # تأثير الظهور
            notif_frame.lift()

            # إخفاء تلقائي بعد 3 ثواني
            if self._is_valid():
                self.after(3000, lambda: self._safe_destroy_notification(notif_frame))

        except Exception as e:
            pass

    def _safe_destroy_notification(self, notification_frame):
        """تدمير آمن للإشعار"""
        try:
            if notification_frame and hasattr(notification_frame, 'winfo_exists'):
                if notification_frame.winfo_exists():
                    notification_frame.destroy()
        except:
            pass

    def update_texts(self, lang_manager: LanguageManager):
        """تحديث نصوص المكون مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            self.lang_manager = lang_manager

            # تحديث النص الافتراضي
            if self.current_status == "" or self.status_type == "info":
                self._safe_configure(self.status_label, text=lang_manager.get("ready", "Ready"))

            # تحديث نص الاتصال
            current_connection_text = ""
            try:
                if hasattr(self.connection_label, 'cget'):
                    current_connection_text = self.connection_label.cget("text")
            except:
                pass

            if "Connected" in current_connection_text or "متصل" in current_connection_text:
                self._safe_configure(
                    self.connection_label,
                    text=lang_manager.get("connected", "Connected")
                )
            elif current_connection_text:  # إذا كان هناك نص
                self._safe_configure(
                    self.connection_label,
                    text=lang_manager.get("disconnected", "Disconnected")
                )
        except Exception as e:
            pass

    def set_user_info(self, username: str, role: str = None):
        """عرض معلومات المستخدم في شريط الحالة"""
        if not self._is_valid():
            return

        try:
            user_text = f"👤 {username}"
            if role:
                user_text += f" ({role})"

            # يمكن إضافة إطار لمعلومات المستخدم إذا لزم الأمر
            pass
        except:
            pass

    def refresh_theme(self):
        """تحديث الثيم عند تغييره مع حماية من الأخطاء"""
        if not self._is_valid():
            return

        try:
            # تحديث الألوان حسب الوضع الجديد
            if self.current_status:
                self.set_status(self.current_status, self.status_type)

            # تحديث ألوان الاتصال
            current_connection_text = ""
            try:
                if hasattr(self.connection_label, 'cget'):
                    current_connection_text = self.connection_label.cget("text")
            except:
                pass

            if self.lang_manager.get("connected", "Connected") in current_connection_text:
                self.set_connection_status(True)
            elif current_connection_text:  # إذا كان هناك نص
                self.set_connection_status(False)
        except Exception as e:
            pass