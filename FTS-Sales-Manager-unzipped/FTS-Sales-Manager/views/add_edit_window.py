# -*- coding: utf-8 -*-
"""
views/add_edit_window.py - نسخة محسنة ومبسطة مع إصلاح مشكلة رقم الحجز

نافذة إضافة/تعديل محسنة مع:
- كود مبسط ومنظم
- دعم offline mode
- ربط القوائم المنسدلة بـ Airtable
- النظام الموحد لإدارة الثيم
- القوائم المنسدلة المدعومة بالبحث
- دعم شامل لتعدد اللغات مع ترجمة التبويبات والحقول
- دعم الحقول للقراءة فقط (readonly fields) - محسن
- توليد رقم الحجز تلقائياً عند اختيار الوكالة
- إصلاح مشكلة عرض رقم الحجز في وضع التعديل
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
import threading
import time
import random
import string
from core.language_manager import LanguageManager
from utils.window_manager import WindowManager
from core.theme_color_manager import ThemeColorManager, ThemedWindow

# استيراد القوائم المحسنة من الملف الموحد
try:
    from views.components.combobox import (
        EnhancedSearchableComboBox,
        EnhancedSearchableComboBoxImproved,
        create_airtable_combo_for_field,
        create_enhanced_dropdown_with_improved_click
    )
    HAS_ENHANCED_COMBO = True
    HAS_IMPROVED_CLICK = True
except ImportError:
    HAS_ENHANCED_COMBO = False
    HAS_IMPROVED_CLICK = False
    EnhancedSearchableComboBox = None
    EnhancedSearchableComboBoxImproved = None

# استيراد تقويم التاريخ
try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False
    class DateEntry:
        def __init__(self, parent, **kwargs):
            self.var = kwargs.get('textvariable', tk.StringVar())
            self.entry = ctk.CTkEntry(parent, textvariable=self.var, placeholder_text="YYYY-MM-DD")
            self.entry.pack(fill="x")
        def get(self): return self.var.get()
        def set(self, value): self.var.set(value)

from core.logger import logger


class AddEditWindow(ctk.CTkToplevel):
    """نافذة إضافة/تعديل محسنة ومبسطة مع إصلاح مشكلة رقم الحجز"""

    def __init__(self, parent=None, config_mgr=None, db_mgr=None, airtable_model=None,
                 controller=None, dropdown_manager=None, lang_manager=None,
                 field_groups=None, field_type_map=None, mode="add", record_id=None,
                 initial_fields=None):
        super().__init__(parent)

        # المتغيرات الأساسية
        self.parent = parent
        self.config_mgr = config_mgr
        self.db_mgr = db_mgr
        self.airtable_model = airtable_model
        self.controller = controller
        self.dropdown_manager = dropdown_manager
        self.lang_manager = lang_manager
        self.mode = mode
        self.record_id = record_id
        self.initial_fields = initial_fields or {}

        # النظام الموحد للثيم
        self.themed_window = ThemedWindow(self, controller.theme_manager if controller else None)

        # حالة النافذة
        self._is_closing = False
        self._save_in_progress = False
        self._offline_mode = False

        # إعداد البيانات
        self.field_groups = field_groups or self._get_default_field_groups()
        self.field_type_map = field_type_map or self._get_default_field_types()
        self.dropdown_mapping = self._get_dropdown_mapping()
        self.tab_names = list(self.field_groups.keys())

        # متغيرات الواجهة
        self.current_step = 0
        self.field_vars = {}
        self.field_widgets = {}
        self.combo_boxes = {}
        self.enhanced_combos = {}
        self.dropdown_options = {}

        # ملف المسودة
        self.draft_file = f"draft_{self.mode}_{datetime.now().strftime('%Y%m%d')}.json"

        # إعداد النافذة
        self._setup_window()
        self._load_dropdown_options()
        self._build_ui()
        self._setup_events()

        # ملء البيانات في وضع التعديل - محسن
        if self.mode == "edit" and self.initial_fields:
            # تأخير أطول للتأكد من اكتمال بناء الواجهة
            self.after(100, self._populate_fields)

            # تحديثات إضافية للحقول المحمية
            self.after(150, self._force_readonly_fields_update)
            self.after(150, self._ensure_booking_number_display)
            self.after(150, self._verify_readonly_fields)

            # تحديث نهائي شامل
            self.after(200, self._force_ui_refresh)
        elif self.mode == "add":
            self._try_load_draft()

    def _generate_time_options(self):
        """توليد قائمة بجميع أوقات اليوم كل 5 دقائق"""
        time_options = []

        # البدء من 00:00
        current_time = datetime.strptime("00:00", "%H:%M")
        end_time = datetime.strptime("23:59", "%H:%M")

        # إضافة كل 5 دقائق
        while current_time <= end_time:
            time_str = current_time.strftime("%H:%M")
            time_options.append(time_str)
            current_time += timedelta(minutes=5)

        logger.info(f"تم توليد {len(time_options)} وقت (كل 5 دقائق)")
        return time_options

    def _is_valid_time_format(self, time_str):
        """التحقق من صحة تنسيق الوقت HH:MM"""
        try:
            datetime.strptime(str(time_str), "%H:%M")
            return True
        except (ValueError, TypeError):
            return False

    def _get_default_field_groups(self):
        """مجموعات الحقول الافتراضية"""
        return {
            "Basic Information": ["Customer Name", "Hotel Name", "Agency", "Booking Nr.", "Room number"],
            "Trip Details": ["trip Name", "Date Trip", "Option", "des", "Guide", "Product ID", "pickup time", "Remarks", "Add - Ons"],
            "Passenger Info": ["ADT", "CHD", "STD", "Youth", "Inf", "CHD Age"],
            "Contact Info": ["Customer Phone", "Customer Email", "Customer Country"],
            "Pricing Info": ["Total price USD", "Total price EUR", "Total price GBP", "Net Rate", "Currency", "Cost EGP", "Collecting on date Trip", "Management Option", "Add-on"]
        }

    def _get_default_field_types(self):
        """أنواع الحقول الافتراضية"""
        return {
            "Customer Name": "text", "Hotel Name": "text", "Agency": "dropdown",
            "Booking Nr.": "readonly",  # ← حقل محمي
            "Room number": "text", "trip Name": "dropdown", "Date Trip": "date", "Option": "dropdown",
            "des": "dropdown", "Guide": "dropdown", "Product ID": "text", "pickup time": "text",
            "Remarks": "text", "Add - Ons": "text", "ADT": "number", "CHD": "number", "STD": "number",
            "Youth": "number", "Inf": "number", "CHD Age": "text", "Customer Phone": "phone",
            "Customer Email": "email", "Customer Country": "text", "Total price USD": "currency",
            "Total price EUR": "currency", "Total price GBP": "currency", "Net Rate": "currency",
            "Currency": "text", "Cost EGP": "currency", "Collecting on date Trip": "text",
            "Management Option": "dropdown", "Add-on": "dropdown"
        }

    def _get_dropdown_mapping(self):
        """تخطيط القوائم المنسدلة - نسخة محدثة مع الأوقات"""
        if self.dropdown_manager and hasattr(self.dropdown_manager, 'get_field_mapping'):
            mapping = self.dropdown_manager.get_field_mapping()
        else:
            mapping = {
                "Agency": "agencies",
                "Guide": "guides",
                "Option": "options",
                "des": "destinations",
                "trip Name": "Trip Names",
                "Management Option": "management_options",
                "Add-on": "addons"
            }

        # إضافة pickup time كقائمة محلية (ليست من Airtable)
        mapping["pickup time"] = "local_time_options"

        return mapping

    def _load_from_cache(self):
        """تحميل من الكاش - نسخة محدثة مع الأوقات"""
        try:
            all_dropdowns = self.dropdown_manager.get_all_dropdowns()
            for field_name, airtable_key in self.dropdown_mapping.items():
                if field_name == "pickup time":
                    # للأوقات، استخدم القائمة المولدة محلياً
                    self.dropdown_options[field_name] = self._generate_time_options()
                else:
                    self.dropdown_options[field_name] = all_dropdowns.get(airtable_key, [])

            if 'Trip Names' in all_dropdowns:
                self.dropdown_options['trip Name'] = all_dropdowns['Trip Names']

        except Exception as e:
            logger.error(f"خطأ في تحميل من الكاش: {e}")
            self._setup_offline_dropdowns()

    def _load_dropdowns_async(self):
        """تحميل القوائم في الخلفية - نسخة محدثة مع الأوقات"""
        def load_thread():
            try:
                all_dropdowns = self.dropdown_manager.get_all_dropdowns(timeout=15.0)
                for field_name, airtable_key in self.dropdown_mapping.items():
                    if field_name == "pickup time":
                        # للأوقات، استخدم القائمة المولدة محلياً
                        self.dropdown_options[field_name] = self._generate_time_options()
                    else:
                        self.dropdown_options[field_name] = all_dropdowns.get(airtable_key, [])

                if 'Trip Names' in all_dropdowns:
                    self.dropdown_options['trip Name'] = all_dropdowns['Trip Names']

            except Exception as e:
                logger.error(f"خطأ في التحميل: {e}")
                self._offline_mode = True
                self.after(0, self._setup_offline_dropdowns)

        threading.Thread(target=load_thread, daemon=True).start()

    def _setup_window(self):
        """إعداد النافذة"""
        # إعداد النصوص أولاً للحصول على الترجمات
        self._setup_texts()

        title = f"➕ {self.texts['add']}" if self.mode == "add" else f"✏️ {self.texts['edit']}"
        self.title(title)

        # حساب أبعاد النافذة
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 1000
        window_height = screen_height - 100
        x = (screen_width - window_width) // 2
        y = 20

        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(700, 500)
        self.resizable(True, True)

        if self.parent:
            self.transient(self.parent)
            self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self._confirm_close)

    def _load_dropdown_options(self):
        """تحميل القوائم المنسدلة"""
        if not self.dropdown_manager:
            self._offline_mode = True
            self._setup_offline_dropdowns()
            return

        try:
            status = self.dropdown_manager.get_status()
            if status.get('cached_count', 0) > 0:
                self._load_from_cache()
            else:
                self._load_dropdowns_async()
        except Exception as e:
            logger.error(f"خطأ في تحميل القوائم: {e}")
            self._offline_mode = True
            self._setup_offline_dropdowns()

    def _load_from_cache(self):
        """تحميل من الكاش"""
        try:
            all_dropdowns = self.dropdown_manager.get_all_dropdowns()
            for field_name, airtable_key in self.dropdown_mapping.items():
                self.dropdown_options[field_name] = all_dropdowns.get(airtable_key, [])
            if 'Trip Names' in all_dropdowns:
                self.dropdown_options['trip Name'] = all_dropdowns['Trip Names']
        except Exception as e:
            logger.error(f"خطأ في تحميل من الكاش: {e}")
            self._setup_offline_dropdowns()

    def _load_dropdowns_async(self):
        """تحميل القوائم في الخلفية"""
        def load_thread():
            try:
                all_dropdowns = self.dropdown_manager.get_all_dropdowns(timeout=15.0)
                for field_name, airtable_key in self.dropdown_mapping.items():
                    self.dropdown_options[field_name] = all_dropdowns.get(airtable_key, [])
                if 'Trip Names' in all_dropdowns:
                    self.dropdown_options['trip Name'] = all_dropdowns['Trip Names']
            except Exception as e:
                logger.error(f"خطأ في التحميل: {e}")
                self._offline_mode = True
                self.after(0, self._setup_offline_dropdowns)

        threading.Thread(target=load_thread, daemon=True).start()

    def _setup_offline_dropdowns(self):
        """إعداد قوائم افتراضية - نسخة محدثة مع الأوقات"""
        defaults = {
            "Agency": ["Direct", "Online", "Partner"],
            "Guide": ["English", "Arabic", "German", "French"],
            "Option": ["Standard", "Premium", "VIP"],
            "des": ["Cairo", "Luxor", "Aswan", "Hurghada"],
            "trip Name": ["Pyramids Tour", "Nile Cruise", "Desert Safari"],
            "Management Option": ["Standard", "Express", "Custom"],
            "Add-on": ["Lunch", "Transport", "Guide", "Entrance Fees"],
            "pickup time": self._generate_time_options()  # ← إضافة قائمة الأوقات
        }

        for field_name in self.dropdown_mapping:
            if field_name not in self.dropdown_options:
                self.dropdown_options[field_name] = defaults.get(field_name, [])

        # إضافة الأوقات دائماً (حتى لو لم تكن في dropdown_mapping)
        if "pickup time" not in self.dropdown_options:
            self.dropdown_options["pickup time"] = self._generate_time_options()
            logger.info("تم إضافة قائمة الأوقات لحقل pickup time")

    def _setup_texts(self):
        """إعداد النصوص والترجمات"""
        if not self.lang_manager:
            self.texts = {
                "add": "Add", "edit": "Edit", "save": "Save", "cancel": "Cancel",
                "draft": "Draft", "previous": "Previous", "next": "Next",
                "refresh": "Refresh", "success": "Success", "error": "Error",
                "warning": "Warning", "required_field": "This field is required",
                "save_success": "Saved successfully!", "update_success": "Updated successfully!",
                "draft_saved": "Draft saved successfully", "loading": "Loading...",
                "processing": "Processing...", "updating": "Updating..."
            }
        else:
            self.texts = {
                "add": self.lang_manager.get("add", "Add"),
                "edit": self.lang_manager.get("edit", "Edit"),
                "save": self.lang_manager.get("save", "Save"),
                "cancel": self.lang_manager.get("cancel", "Cancel"),
                "draft": self.lang_manager.get("draft", "Draft"),
                "previous": self.lang_manager.get("previous", "Previous"),
                "next": self.lang_manager.get("next", "Next"),
                "refresh": self.lang_manager.get("refresh", "Refresh"),
                "success": self.lang_manager.get("success", "Success"),
                "error": self.lang_manager.get("error", "Error"),
                "warning": self.lang_manager.get("warning", "Warning"),
                "required_field": self.lang_manager.get("required_field", "This field is required"),
                "save_success": self.lang_manager.get("save_success", "Saved successfully!"),
                "update_success": self.lang_manager.get("update_success", "Updated successfully!"),
                "draft_saved": self.lang_manager.get("draft_saved", "Draft saved successfully"),
                "loading": self.lang_manager.get("loading", "Loading..."),
                "processing": self.lang_manager.get("processing", "Processing..."),
                "updating": self.lang_manager.get("updating", "Updating...")
            }

    def _build_ui(self):
        """بناء واجهة المستخدم"""
        # الإطار الرئيسي
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # شريط التقدم
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 10))
        self._create_progress_buttons()

        # إطار المحتوى
        self.content_frame = ctk.CTkScrollableFrame(main_frame)
        self.content_frame.pack(fill="both", expand=True)

        # إنشاء التبويبات
        self.tab_frames = []
        for tab_name in self.tab_names:
            tab_frame = ctk.CTkFrame(self.content_frame)
            tab_frame.pack_forget()
            self.tab_frames.append(tab_frame)
            self._create_tab_content(tab_frame, tab_name)

        # أزرار التنقل
        self._create_navigation_buttons(main_frame)

        # عرض التبويب الأول
        self._show_tab(0)

        # تطبيق الثيم
        self.themed_window.apply_theme()

    def _create_progress_buttons(self):
        """إنشاء أزرار التقدم"""
        self.progress_buttons = []
        for i, name in enumerate(self.tab_names):
            translated_name = self._translate_tab_name(name)
            btn = ctk.CTkButton(
                self.progress_frame,
                text=f"{i+1}. {translated_name}",
                command=lambda idx=i: self._show_tab(idx),
                width=150, height=30
            )
            btn.pack(side="left", padx=5)
            self.progress_buttons.append(btn)

    def _create_tab_content(self, parent, tab_name):
        """إنشاء محتوى التبويب"""
        # عنوان التبويب
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            title_frame,
            text=self._translate_tab_name(tab_name),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack()

        # إطار الحقول
        fields_frame = ctk.CTkFrame(parent, fg_color="transparent")
        fields_frame.pack(fill="both", expand=True, padx=20)

        # إنشاء الحقول
        fields = self.field_groups.get(tab_name, [])
        for field_name in fields:
            self._create_field(fields_frame, field_name)

    def _create_field(self, parent, field_name):
        """إنشاء حقل واحد"""
        field_frame = ctk.CTkFrame(parent, fg_color="transparent")
        field_frame.pack(fill="x", pady=10)

        # التسمية
        label_text = self._translate_field_name(field_name)
        if field_name in ["Customer Name", "Agency", "Date Trip"]:
            label_text += " *"
        elif self.field_type_map.get(field_name) == "readonly":
            label_text += " 🔒"  # رمز القفل للحقول المحمية

        label = ctk.CTkLabel(
            field_frame, text=label_text, anchor="w",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        label.pack(fill="x", pady=(0, 5))

        # الحقل
        initial_value = self._get_initial_value(field_name)
        field_type = self.field_type_map.get(field_name, "text")

        var, widget = self._create_field_by_type(field_frame, field_name, field_type, initial_value)

        if var and widget:
            self.field_vars[field_name] = var
            self.field_widgets[field_name] = widget

    def _create_field_by_type(self, parent, field_name, field_type, initial_value):
        """إنشاء حقل حسب النوع - دالة موحدة"""
        if field_type == "dropdown":
            return self._create_dropdown_field(parent, field_name, initial_value)
        elif field_type == "number":
            return self._create_number_field(parent, initial_value)
        elif field_type == "date":
            return self._create_date_field(parent, initial_value)
        elif field_type == "readonly":
            return self._create_readonly_field(parent, initial_value)
        else:
            return self._create_text_field(parent, field_type, initial_value)

    def _create_dropdown_field(self, parent, field_name, initial_value):
        """إنشاء قائمة منسدلة - نسخة محدثة مع معالجة خاصة للأوقات"""

        # للحقول الزمنية، التأكد من وجود قائمة الأوقات
        if field_name == "pickup time":
            values = self._generate_time_options()
            # إضافة القيمة الأولية إذا لم تكن موجودة وكانت صالحة
            if initial_value and self._is_valid_time_format(initial_value):
                if initial_value not in values:
                    values = [initial_value] + values
                    logger.info(f"تم إضافة الوقت الأولي {initial_value} للقائمة")
        else:
            values = self.dropdown_options.get(field_name, [])
            if initial_value and initial_value not in values:
                values = list(values) + [initial_value]

        # محاولة استخدام النسخة المحسنة
        if HAS_ENHANCED_COMBO and HAS_IMPROVED_CLICK:
            try:
                var, combo = create_enhanced_dropdown_with_improved_click(
                    parent=parent, field_name=field_name, initial_value=initial_value,
                    values=values, themed_window=self.themed_window
                )
                combo.pack(fill="x", pady=5)
                self.enhanced_combos[field_name] = combo

                # ربط حدث تغيير الوكالة لتوليد رقم الحجز
                if field_name == "Agency":
                    self._bind_agency_change_event(combo, var)

                # إضافة تلميح للأوقات
                if field_name == "pickup time":
                    combo.configure(placeholder_text="اختر وقت الإقلاع")

                return var, combo
            except Exception as e:
                logger.warning(f"فشل في إنشاء القائمة المحسنة: {e}")

        # القائمة العادية
        var = tk.StringVar(value=initial_value)
        combo = ctk.CTkComboBox(
            parent, values=values, variable=var,
            state="readonly" if self._offline_mode else "normal"
        )
        self.themed_window.apply_to_widget(combo, 'combobox')
        combo.pack(fill="x", pady=5)
        self.combo_boxes[field_name] = combo

        # ربط حدث تغيير الوكالة لتوليد رقم الحجز
        if field_name == "Agency":
            self._bind_agency_change_event(combo, var)

        return var, combo

    def _bind_agency_change_event(self, combo, var):
        """ربط حدث تغيير الوكالة لتوليد رقم الحجز تلقائياً"""
        def on_agency_change(*args):
            # التأكد من أننا في وضع الإضافة وليس التعديل
            if self.mode == "add":
                agency_value = var.get()
                if agency_value and agency_value.strip():
                    # توليد رقم الحجز الجديد
                    booking_nr = self._generate_booking_number(agency_value)
                    # تحديث حقل رقم الحجز
                    self._update_booking_number_field(booking_nr)
                    logger.info(f"تم توليد رقم حجز جديد: {booking_nr} للوكالة: {agency_value}")

        # ربط الحدث بمتغير الوكالة
        var.trace('w', on_agency_change)

        # ربط حدث إضافي للقوائم المحسنة
        if hasattr(combo, 'bind'):
            combo.bind('<<ComboboxSelected>>', lambda e: on_agency_change())

    def _generate_booking_number(self, agency_name):
        """توليد رقم حجز جديد بالتنسيق المطلوب"""
        try:
            # الحصول على أول ثلاثة أحرف من الوكالة
            agency_prefix = agency_name[:3].upper().replace(' ', '')
            if len(agency_prefix) < 3:
                agency_prefix = agency_prefix.ljust(3, 'X')  # ملء بـ X إذا كان أقل من 3 أحرف

            # التوقيت الحالي بصيغة hhmmss
            current_time = datetime.now()
            time_part = current_time.strftime("%H%M%S")

            # خمسة أرقام وحروف عشوائية
            random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))

            # تجميع رقم الحجز
            booking_number = f"{agency_prefix}-{time_part}-{random_chars}"

            logger.info(f"تم توليد رقم الحجز: {booking_number}")
            return booking_number

        except Exception as e:
            logger.error(f"خطأ في توليد رقم الحجز: {e}")
            # رقم احتياطي في حالة الخطأ
            fallback_time = datetime.now().strftime("%H%M%S")
            fallback_random = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            return f"BKG-{fallback_time}-{fallback_random}"

    def _update_booking_number_field(self, booking_number):
        """تحديث حقل رقم الحجز بالقيمة الجديدة"""
        try:
            if "Booking Nr." in self.field_vars:
                booking_var = self.field_vars["Booking Nr."]
                booking_var.set(booking_number)

                # إجبار تحديث الـ widget إذا كان موجوداً
                if "Booking Nr." in self.field_widgets:
                    widget = self.field_widgets["Booking Nr."]

                    # محاولة تحديث الـ widget مباشرة للحقول المحمية
                    try:
                        if hasattr(widget, 'configure'):
                            # تفعيل مؤقت للتحديث
                            original_state = widget.cget('state')
                            widget.configure(state='normal')

                            # مسح وإدراج القيمة الجديدة
                            if hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                                widget.delete(0, tk.END)
                                widget.insert(0, booking_number)

                            # إعادة الحالة الأصلية
                            widget.configure(state=original_state)

                    except Exception as widget_error:
                        logger.warning(f"فشل في تحديث widget مباشرة: {widget_error}")

                logger.info(f"تم تحديث حقل رقم الحجز: {booking_number}")

        except Exception as e:
            logger.error(f"خطأ في تحديث حقل رقم الحجز: {e}")

    def _create_readonly_field(self, parent, initial_value):
        """إنشاء حقل للقراءة فقط - إصلاح محسن"""
        var = tk.StringVar()

        # تعيين القيمة الأولية إذا كانت موجودة
        if initial_value:
            processed_value = self._process_complex_value(initial_value)
            var.set(str(processed_value) if processed_value else "")

        # استخدام CTkEntry مع تخصيص للحقول المحمية
        widget = ctk.CTkEntry(
            parent,
            textvariable=var,
            state="readonly",
            fg_color="#f8f9fa",  # لون خلفية أفتح للحقول المحمية
            text_color="#495057",  # لون نص أوضح
            border_width=1,
            border_color="#dee2e6",
            font=ctk.CTkFont(size=12)
        )

        widget.pack(fill="x", pady=5)

        # إضافة وظيفة مساعدة لتحديث القيمة
        def update_readonly_value(new_value):
            """تحديث قيمة الحقل المحمي"""
            try:
                # حفظ الحالة الأصلية
                original_state = widget.cget('state')

                # تفعيل الحقل مؤقتاً
                widget.configure(state='normal')

                # مسح وتحديث المحتوى
                widget.delete(0, tk.END)
                widget.insert(0, str(new_value) if new_value else "")

                # إعادة الحالة المحمية
                widget.configure(state='readonly')

                # تحديث المتغير أيضاً
                var.set(str(new_value) if new_value else "")

            except Exception as e:
                logger.error(f"خطأ في تحديث الحقل المحمي: {e}")

        # ربط الوظيفة بالـ widget
        widget.update_readonly_value = update_readonly_value

        return var, widget

    def _create_text_field(self, parent, field_type, initial_value):
        """إنشاء حقل نص"""
        var = tk.StringVar(value=str(initial_value) if initial_value else "")
        placeholder = {"phone": "01x xxxx xxxx", "email": "example@email.com", "currency": "0.00"}.get(field_type, "")

        widget = ctk.CTkEntry(parent, textvariable=var, placeholder_text=placeholder)
        self.themed_window.apply_to_widget(widget, 'entry')
        widget.pack(fill="x", pady=5)
        return var, widget

    def _create_number_field(self, parent, initial_value):
        """إنشاء حقل رقمي"""
        var = tk.IntVar(value=int(initial_value) if initial_value else 0)
        widget = ctk.CTkEntry(parent, textvariable=var, justify="center")
        self.themed_window.apply_to_widget(widget, 'entry')
        widget.pack(fill="x", pady=5)
        return var, widget

    def _create_date_field(self, parent, initial_value):
        """إنشاء حقل تاريخ"""
        date_value = self._parse_date(str(initial_value)) if initial_value else ""
        var = tk.StringVar(value=date_value)

        if HAS_CALENDAR:
            widget = DateEntry(parent, textvariable=var, date_pattern='yyyy-mm-dd')
            widget.pack(fill="x", pady=5)
        else:
            widget = ctk.CTkEntry(parent, textvariable=var, placeholder_text="YYYY-MM-DD")
            self.themed_window.apply_to_widget(widget, 'entry')
            widget.pack(fill="x", pady=5)

        return var, widget

    def _create_navigation_buttons(self, parent):
        """إنشاء أزرار التنقل"""
        nav_frame = ctk.CTkFrame(parent)
        nav_frame.pack(fill="x", pady=10)

        # الأزرار اليسرى
        left_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)

        self.prev_btn = ctk.CTkButton(left_frame, text=f"◀ {self.texts['previous']}", command=self._prev_tab, width=100)
        self.prev_btn.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(left_frame, text=f"{self.texts['next']} ▶", command=self._next_tab, width=100)
        self.next_btn.pack(side="left", padx=5)

        self.refresh_btn = ctk.CTkButton(left_frame, text=f"🔄 {self.texts['refresh']}", command=self._refresh_dropdowns, width=120)
        self.refresh_btn.pack(side="left", padx=5)

        # الأزرار اليمنى
        right_frame = ctk.CTkFrame(nav_frame, fg_color="transparent")
        right_frame.pack(side="right")

        self.cancel_btn = ctk.CTkButton(right_frame, text=f"❌ {self.texts['cancel']}", command=self._confirm_close, width=100)
        self.cancel_btn.pack(side="right", padx=5)

        self.draft_btn = ctk.CTkButton(right_frame, text=f"📝 {self.texts['draft']}", command=self._save_draft, width=100)
        self.draft_btn.pack(side="right", padx=5)

        self.save_btn = ctk.CTkButton(right_frame, text=f"💾 {self.texts['save']}", command=self._save, width=120, font=ctk.CTkFont(size=14, weight="bold"))
        self.save_btn.pack(side="right", padx=5)

    def _setup_events(self):
        """إعداد الأحداث واختصارات لوحة المفاتيح"""
        self.bind('<Control-s>', lambda e: self._save())
        self.bind('<Control-d>', lambda e: self._save_draft())
        self.bind('<Escape>', lambda e: self._confirm_close())
        self.bind('<Control-Right>', lambda e: self._next_tab())
        self.bind('<Control-Left>', lambda e: self._prev_tab())

    def _show_tab(self, index):
        """عرض تبويب محدد"""
        for frame in self.tab_frames:
            frame.pack_forget()

        if 0 <= index < len(self.tab_frames):
            self.tab_frames[index].pack(fill="both", expand=True)
            self.current_step = index

            self.prev_btn.configure(state="normal" if index > 0 else "disabled")
            self.next_btn.configure(state="normal" if index < len(self.tab_frames) - 1 else "disabled")

            # تحديث ألوان أزرار التقدم
            for i, btn in enumerate(self.progress_buttons):
                if i == index:
                    btn.configure(fg_color=self.themed_window.get_color('primary'))
                elif i < index:
                    btn.configure(fg_color=self.themed_window.get_color('success'))
                else:
                    btn.configure(fg_color=self.themed_window.get_color('surface'))

    def _prev_tab(self):
        """التبويب السابق"""
        if self.current_step > 0:
            self._show_tab(self.current_step - 1)

    def _next_tab(self):
        """التبويب التالي"""
        if self.current_step < len(self.tab_frames) - 1:
            self._show_tab(self.current_step + 1)

    def _save(self):
        """حفظ البيانات"""
        if self._save_in_progress or not self._validate_form():
            return

        self._save_in_progress = True
        data = self._collect_data()

        def save_operation():
            try:
                if self.mode == "add":
                    result = self.controller.create_record(data)
                else:
                    result = self.controller.update_record(self.record_id, data)

                if result:
                    success_msg = self.texts['save_success'] if self.mode == "add" else self.texts['update_success']
                    self.after(0, lambda: [
                        messagebox.showinfo(self.texts['success'], success_msg),
                        self._delete_draft(),
                        self.destroy()
                    ])
                else:
                    raise Exception("فشل الحفظ")
            except Exception as e:
                error_msg = f"خطأ في الحفظ: {str(e)}"
                self.after(0, lambda: messagebox.showerror(self.texts['error'], error_msg))
            finally:
                self._save_in_progress = False

        threading.Thread(target=save_operation, daemon=True).start()

    def _validate_form(self):
        """التحقق من صحة النموذج"""
        required_fields = ["Customer Name", "Agency", "Date Trip"]
        for field_name in required_fields:
            if field_name in self.field_widgets:
                value = self._get_widget_value(self.field_widgets[field_name])
                if not value or not value.strip():
                    messagebox.showerror(self.texts['error'], f"{self.texts['required_field']}: {self._translate_field_name(field_name)}")
                    return False
        return True

    def _collect_data(self):
        """جمع البيانات من جميع الحقول"""
        data = {}
        for field_name, widget in self.field_widgets.items():
            value = self._get_widget_value(widget)
            if value:
                field_type = self.field_type_map.get(field_name, "text")
                if field_type == "number":
                    try:
                        data[field_name] = int(value)
                    except ValueError:
                        data[field_name] = 0
                elif field_type == "currency":
                    try:
                        data[field_name] = float(str(value).replace(',', '').strip())
                    except ValueError:
                        data[field_name] = value
                else:
                    data[field_name] = value
        return data

    def _get_widget_value(self, widget):
        """الحصول على قيمة من widget - إصلاح محسن للحقول المحمية"""
        try:
            # المحاولة الأولى: الطريقة العادية
            if hasattr(widget, 'get'):
                value = widget.get()
                return value.strip() if isinstance(value, str) else value

        except tk.TclError as tcl_error:
            # للحقول المحمية، جرب طرق بديلة
            try:
                # محاولة الوصول للمتغير المرتبط
                if hasattr(widget, 'cget'):
                    textvariable = widget.cget('textvariable')
                    if textvariable and hasattr(textvariable, 'get'):
                        value = textvariable.get()
                        logger.debug(f"✅ تم الحصول على قيمة من textvariable: {value}")
                        return value.strip() if isinstance(value, str) else value

                # محاولة قراءة المحتوى مباشرة (للحقول المحمية)
                if hasattr(widget, 'configure'):
                    # تفعيل مؤقت للقراءة
                    original_state = widget.cget('state')
                    widget.configure(state='normal')

                    try:
                        value = widget.get()
                        widget.configure(state=original_state)
                        logger.debug(f"✅ تم الحصول على قيمة بتفعيل مؤقت: {value}")
                        return value.strip() if isinstance(value, str) else value
                    except:
                        widget.configure(state=original_state)
                        raise

            except Exception as e:
                logger.error(f"❌ فشل في جميع محاولات قراءة القيمة: {e}")

        except Exception as e:
            logger.error(f"❌ خطأ عام في قراءة قيمة widget: {e}")

        return ""

    def _save_draft(self):
        """حفظ المسودة"""
        try:
            data = self._collect_data()
            draft_data = {
                "timestamp": datetime.now().isoformat(),
                "mode": self.mode,
                "data": data
            }

            os.makedirs("drafts", exist_ok=True)
            with open(f"drafts/{self.draft_file}", 'w', encoding='utf-8') as f:
                json.dump(draft_data, f, ensure_ascii=False, indent=2)

            messagebox.showinfo(self.texts['success'], self.texts['draft_saved'])
        except Exception as e:
            messagebox.showerror(self.texts['error'], f"فشل حفظ المسودة: {str(e)}")

    def _try_load_draft(self):
        """محاولة تحميل مسودة"""
        try:
            draft_path = f"drafts/{self.draft_file}"
            if os.path.exists(draft_path):
                if messagebox.askyesno("مسودة موجودة", "هل تريد تحميل المسودة المحفوظة؟"):
                    with open(draft_path, 'r', encoding='utf-8') as f:
                        draft_data = json.load(f)
                    self._load_draft_data(draft_data.get("data", {}))
        except Exception as e:
            logger.error(f"خطأ في تحميل المسودة: {e}")

    def _load_draft_data(self, data):
        """تحميل بيانات المسودة"""
        for field_name, value in data.items():
            if field_name in self.field_vars:
                try:
                    var = self.field_vars[field_name]
                    if isinstance(var, tk.IntVar):
                        var.set(int(value) if value else 0)
                    else:
                        var.set(str(value) if value else "")
                except Exception as e:
                    logger.warning(f"خطأ في تحميل {field_name}: {e}")

    def _delete_draft(self):
        """حذف المسودة"""
        try:
            draft_path = f"drafts/{self.draft_file}"
            if os.path.exists(draft_path):
                os.remove(draft_path)
        except Exception as e:
            logger.warning(f"خطأ في حذف المسودة: {e}")

    def _refresh_dropdowns(self):
        """تحديث القوائم المنسدلة"""
        if not self.dropdown_manager:
            messagebox.showinfo(self.texts['error'], "خدمة القوائم غير متاحة")
            return

        def refresh_thread():
            try:
                self.dropdown_manager.refresh_all()
                self._load_from_cache()
                self._update_combo_boxes()
                self.after(0, lambda: messagebox.showinfo(self.texts['success'], "تم تحديث القوائم بنجاح"))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(self.texts['error'], f"فشل التحديث: {str(e)}"))

        threading.Thread(target=refresh_thread, daemon=True).start()

    def _update_combo_boxes(self):
        """تحديث جميع القوائم المنسدلة"""
        # تحديث القوائم العادية
        for field_name, combo in self.combo_boxes.items():
            if field_name in self.dropdown_options:
                try:
                    current_value = combo.get()
                    new_values = self.dropdown_options[field_name]
                    combo.configure(values=new_values)
                    if current_value in new_values:
                        combo.set(current_value)
                except Exception as e:
                    logger.warning(f"فشل تحديث {field_name}: {e}")

        # تحديث القوائم المحسنة
        for field_name, combo in self.enhanced_combos.items():
            if field_name in self.dropdown_options:
                try:
                    current_value = combo.get()
                    new_values = self.dropdown_options[field_name]
                    combo.set_values(new_values)
                    if current_value in new_values:
                        combo.set(current_value)
                except Exception as e:
                    logger.warning(f"فشل تحديث القائمة المحسنة {field_name}: {e}")

    def _confirm_close(self):
        """تأكيد الإغلاق"""
        if self._has_unsaved_changes():
            result = messagebox.askyesnocancel("تغييرات غير محفوظة", "هل تريد حفظ المسودة قبل الإغلاق؟")
            if result is True:
                self._save_draft()
                self.destroy()
            elif result is False:
                self.destroy()
        else:
            self.destroy()

    def _has_unsaved_changes(self):
        """فحص التغييرات غير المحفوظة"""
        if self.mode == "add":
            for var in self.field_vars.values():
                if isinstance(var, tk.IntVar) and var.get() != 0:
                    return True
                elif isinstance(var, tk.StringVar) and var.get():
                    return True
        return False

    def _populate_fields(self):
        """ملء الحقول بالبيانات الأولية - إصلاح محسن مع تركيز على الحقول المحمية"""
        logger.info(f"🚀 بدء ملء الحقول المحسن - عدد الحقول: {len(self.initial_fields)}")

        populated_count = 0
        failed_count = 0
        skipped_count = 0
        readonly_count = 0

        for field_name, value in self.initial_fields.items():
            try:
                # التحقق من وجود الحقل
                if field_name not in self.field_vars:
                    logger.warning(f"⚠️ الحقل '{field_name}' غير موجود في field_vars")
                    skipped_count += 1
                    continue

                # معالجة القيمة
                if value is None or (isinstance(value, str) and not value.strip()):
                    logger.debug(f"⏭️ تخطي الحقل '{field_name}' - قيمة فارغة")
                    skipped_count += 1
                    continue

                processed_value = self._process_complex_value(value)
                logger.info(f"🔄 معالجة الحقل '{field_name}': {value} → {processed_value}")

                if not processed_value:
                    logger.warning(f"⚠️ فشل في معالجة قيمة الحقل '{field_name}': {value}")
                    failed_count += 1
                    continue

                # فحص نوع الحقل
                field_type = self.field_type_map.get(field_name, "text")

                # تعيين القيمة في المتغير أولاً
                var = self.field_vars[field_name]

                if isinstance(var, tk.IntVar):
                    try:
                        int_value = int(float(str(processed_value))) if processed_value else 0
                        var.set(int_value)
                        logger.debug(f"📊 تم تعيين قيمة رقمية للحقل '{field_name}': {int_value}")
                    except (ValueError, TypeError) as e:
                        logger.error(f"❌ خطأ في تحويل القيمة الرقمية للحقل '{field_name}': {e}")
                        var.set(0)
                        failed_count += 1
                        continue
                else:
                    var.set(str(processed_value))
                    logger.debug(f"📝 تم تعيين قيمة نصية للحقل '{field_name}': {processed_value}")

                # معالجة خاصة للحقول المحمية
                if field_type == "readonly":
                    readonly_count += 1
                    logger.info(f"🔒 معالجة حقل محمي: '{field_name}' = '{processed_value}'")

                    # تحديث فوري للحقل المحمي
                    self._force_widget_update(field_name, processed_value)

                    # تحديث إضافي متأخر للتأكد
                    self.after(50, lambda fn=field_name, pv=processed_value: self._force_widget_update(fn, pv))
                    self.after(100, lambda fn=field_name, pv=processed_value: self._force_widget_update(fn, pv))

                else:
                    # للحقول العادية
                    self._force_widget_update(field_name, processed_value)

                # معالجة خاصة للقوائم المنسدلة
                if field_name in self.combo_boxes or field_name in self.enhanced_combos:
                    self._handle_dropdown_value(field_name, processed_value)

                populated_count += 1

            except Exception as e:
                failed_count += 1
                logger.error(f"❌ خطأ في ملء الحقل '{field_name}': {e}")
                import traceback
                traceback.print_exc()

        logger.info(f"📊 نتائج ملء الحقول:")
        logger.info(f"  ✅ نجح: {populated_count}")
        logger.info(f"  🔒 حقول محمية: {readonly_count}")
        logger.info(f"  ❌ فشل: {failed_count}")
        logger.info(f"  ⏭️ تم تخطي: {skipped_count}")

        # تحديثات إضافية متأخرة للحقول المحمية
        self.after(100, self._force_readonly_fields_update)
        self.after(150, self._force_readonly_fields_update)
        self.after(150, self._verify_readonly_fields)

    def _force_readonly_fields_update(self):
        """إجبار تحديث خاص للحقول المحمية"""
        logger.info("🔒 إجبار تحديث الحقول المحمية...")

        for field_name, value in self.initial_fields.items():
            field_type = self.field_type_map.get(field_name, "text")

            if field_type == "readonly" and value:
                processed_value = self._process_complex_value(value)
                if processed_value:
                    logger.info(f"🔄 إعادة تحديث الحقل المحمي '{field_name}': {processed_value}")
                    self._force_widget_update(field_name, processed_value)

    def _verify_readonly_fields(self):
        """فحص والتحقق من الحقول المحمية"""
        logger.info("🔍 فحص الحقول المحمية...")

        for field_name in self.field_widgets.keys():
            field_type = self.field_type_map.get(field_name, "text")

            if field_type == "readonly":
                try:
                    widget = self.field_widgets[field_name]
                    var = self.field_vars.get(field_name)
                    expected_value = self.initial_fields.get(field_name)

                    if expected_value:
                        processed_expected = self._process_complex_value(expected_value)
                        current_var_value = var.get() if var else ""

                        # محاولة قراءة القيمة من الـ widget
                        try:
                            widget_value = self._get_widget_value(widget)
                        except:
                            widget_value = ""

                        logger.info(f"🔍 فحص '{field_name}':")
                        logger.info(f"  📝 متوقع: '{processed_expected}'")
                        logger.info(f"  🔧 متغير: '{current_var_value}'")
                        logger.info(f"  🖼️ widget: '{widget_value}'")

                        # إذا كانت القيم غير متطابقة، أصلحها
                        if str(current_var_value) != str(processed_expected) or str(widget_value) != str(processed_expected):
                            logger.warning(f"⚠️ عدم تطابق في الحقل المحمي '{field_name}' - إصلاح...")
                            self._force_widget_update(field_name, processed_expected)

                except Exception as e:
                    logger.error(f"❌ خطأ في فحص الحقل المحمي '{field_name}': {e}")

    def _ensure_booking_number_display(self):
        """ضمان عرض رقم الحجز بشكل صحيح"""
        booking_field = "Booking Nr."

        if booking_field in self.initial_fields:
            booking_value = self.initial_fields[booking_field]
            processed_booking = self._process_complex_value(booking_value)

            logger.info(f"🎫 ضمان عرض رقم الحجز: '{processed_booking}'")

            if processed_booking:
                # تحديث المتغير
                if booking_field in self.field_vars:
                    self.field_vars[booking_field].set(processed_booking)

                # تحديث الـ widget مباشرة
                if booking_field in self.field_widgets:
                    widget = self.field_widgets[booking_field]

                    try:
                        # للحقول المحمية
                        original_state = widget.cget('state')
                        widget.configure(state='normal')
                        widget.delete(0, tk.END)
                        widget.insert(0, processed_booking)
                        widget.configure(state=original_state)

                        logger.info(f"✅ تم ضمان عرض رقم الحجز: '{processed_booking}'")

                    except Exception as e:
                        logger.error(f"❌ فشل في ضمان عرض رقم الحجز: {e}")

    def _force_widget_update(self, field_name, value):
        """إجبار تحديث widget محدد - إصلاح محسن للحقول المحمية"""
        try:
            if field_name in self.field_widgets:
                widget = self.field_widgets[field_name]

                # فحص إذا كان الحقل محمياً
                field_type = self.field_type_map.get(field_name, "text")

                if field_type == "readonly":
                    # معالجة خاصة للحقول المحمية
                    if hasattr(widget, 'update_readonly_value'):
                        # استخدام الوظيفة المخصصة
                        widget.update_readonly_value(value)
                        logger.debug(f"✅ تم تحديث الحقل المحمي '{field_name}' بالوظيفة المخصصة: {value}")
                    else:
                        # الطريقة التقليدية
                        try:
                            original_state = widget.cget('state')
                            widget.configure(state='normal')
                            widget.delete(0, tk.END)
                            widget.insert(0, str(value))
                            widget.configure(state=original_state)
                            logger.debug(f"✅ تم تحديث الحقل المحمي '{field_name}' بالطريقة التقليدية: {value}")
                        except Exception as readonly_error:
                            logger.error(f"❌ فشل تحديث الحقل المحمي '{field_name}': {readonly_error}")

                            # محاولة تحديث المتغير على الأقل
                            if field_name in self.field_vars:
                                self.field_vars[field_name].set(str(value))

                # للحقول العادية
                elif hasattr(widget, 'delete') and hasattr(widget, 'insert'):
                    try:
                        widget.delete(0, tk.END)
                        widget.insert(0, str(value))
                        logger.debug(f"✅ تم تحديث الحقل العادي '{field_name}': {value}")
                    except tk.TclError as e:
                        logger.error(f"❌ خطأ Tcl في تحديث '{field_name}': {e}")

                # للقوائم المنسدلة
                elif hasattr(widget, 'set'):
                    widget.set(str(value))
                    logger.debug(f"✅ تم تحديث القائمة المنسدلة '{field_name}': {value}")

                # إجبار التحديث المرئي
                widget.update_idletasks()

        except Exception as e:
            logger.error(f"❌ خطأ عام في إجبار تحديث widget '{field_name}': {e}")

    def _force_ui_refresh(self):
        """إجبار تحديث شامل للواجهة"""
        try:
            logger.info("🔄 إجبار تحديث شامل للواجهة...")

            # تحديث جميع المتغيرات مرة أخرى
            for field_name, value in self.initial_fields.items():
                if field_name in self.field_vars and value:
                    try:
                        processed_value = self._process_complex_value(value)
                        if processed_value:
                            var = self.field_vars[field_name]
                            current_value = var.get()

                            # إذا كانت القيمة مختلفة، أعد تعيينها
                            if str(current_value) != str(processed_value):
                                if isinstance(var, tk.IntVar):
                                    var.set(int(float(str(processed_value))) if processed_value else 0)
                                else:
                                    var.set(str(processed_value))
                                logger.debug(f"🔄 إعادة تعيين '{field_name}': {processed_value}")

                            # إجبار تحديث الـ widget مباشرة
                            self._force_widget_update(field_name, processed_value)

                    except Exception as e:
                        logger.error(f"خطأ في التحديث الشامل للحقل '{field_name}': {e}")

            # تحديث النافذة بالكامل
            self.update_idletasks()
            self.update()

            logger.info("✅ اكتمل التحديث الشامل للواجهة")

        except Exception as e:
            logger.error(f"خطأ في التحديث الشامل: {e}")

    def _handle_dropdown_value(self, field_name, value):
        """معالجة خاصة لقيم القوائم المنسدلة - محسنة"""
        try:
            # التحقق من القوائم العادية
            if field_name in self.combo_boxes:
                combo = self.combo_boxes[field_name]
                current_values = list(combo.cget("values"))

                # إذا كانت القيمة غير موجودة، أضفها
                if value not in current_values:
                    new_values = current_values + [value]
                    combo.configure(values=new_values)
                    logger.info(f"تم إضافة القيمة '{value}' إلى القائمة '{field_name}'")

                # تعيين القيمة مع تأخير للتأكد
                combo.set(value)
                self.after(50, lambda: combo.set(value))  # إعادة تعيين مع تأخير
                logger.debug(f"تم تعيين قيمة القائمة العادية '{field_name}': {value}")

            # التحقق من القوائم المحسنة
            elif field_name in self.enhanced_combos:
                combo = self.enhanced_combos[field_name]

                # الحصول على القيم الحالية
                current_values = []
                if hasattr(combo, 'values'):
                    current_values = list(combo.values)
                elif hasattr(combo, 'filtered_values'):
                    current_values = list(combo.filtered_values)

                # إذا كانت القيمة غير موجودة، أضفها
                if value not in current_values:
                    if hasattr(combo, 'add_value'):
                        combo.add_value(value)
                    elif hasattr(combo, 'set_values'):
                        new_values = current_values + [value]
                        combo.set_values(new_values)
                    logger.info(f"تم إضافة القيمة '{value}' إلى القائمة المحسنة '{field_name}'")

                # تعيين القيمة مع تأخير للتأكد
                if hasattr(combo, 'set'):
                    combo.set(value)
                    self.after(50, lambda: combo.set(value))  # إعادة تعيين مع تأخير
                    logger.debug(f"تم تعيين قيمة القائمة المحسنة '{field_name}': {value}")

        except Exception as e:
            logger.error(f"خطأ في معالجة قيمة القائمة المنسدلة '{field_name}': {e}")

    def _verify_dropdown_values(self):
        """فحص إضافي مع إصلاح فوري"""
        logger.info("🔍 بدء فحص وإصلاح قيم القوائم المنسدلة...")

        fixed_count = 0

        for field_name in self.dropdown_mapping.keys():
            if field_name in self.field_vars:
                try:
                    expected_value = self.field_vars[field_name].get()

                    if not expected_value:
                        continue

                    if field_name in self.combo_boxes:
                        combo = self.combo_boxes[field_name]
                        actual_value = combo.get()

                        if str(expected_value) != str(actual_value):
                            logger.warning(f"⚠️ عدم تطابق في القائمة '{field_name}': متوقع='{expected_value}', فعلي='{actual_value}'")

                            # إضافة القيمة إذا لم تكن موجودة
                            current_values = list(combo.cget("values"))
                            if expected_value not in current_values:
                                new_values = current_values + [expected_value]
                                combo.configure(values=new_values)

                            # إعادة تعيين القيمة بقوة
                            combo.set(expected_value)
                            self.after(10, lambda v=expected_value, c=combo: c.set(v))
                            fixed_count += 1
                            logger.info(f"✅ تم إصلاح قيمة القائمة '{field_name}' إلى '{expected_value}'")

                    elif field_name in self.enhanced_combos:
                        combo = self.enhanced_combos[field_name]
                        actual_value = combo.get() if hasattr(combo, 'get') else ""

                        if str(expected_value) != str(actual_value):
                            logger.warning(f"⚠️ عدم تطابق في القائمة المحسنة '{field_name}': متوقع='{expected_value}', فعلي='{actual_value}'")

                            # إضافة القيمة إذا لم تكن موجودة
                            if hasattr(combo, 'add_value'):
                                combo.add_value(expected_value)

                            # إعادة تعيين القيمة
                            if hasattr(combo, 'set'):
                                combo.set(expected_value)
                                self.after(10, lambda v=expected_value, c=combo: c.set(v))
                            fixed_count += 1
                            logger.info(f"✅ تم إصلاح قيمة القائمة المحسنة '{field_name}' إلى '{expected_value}'")

                except Exception as e:
                    logger.error(f"❌ خطأ في فحص القائمة '{field_name}': {e}")

        if fixed_count > 0:
            logger.info(f"🔧 تم إصلاح {fixed_count} قائمة منسدلة")
            # تحديث نهائي للواجهة
            self.after(100, lambda: self.update_idletasks())

    def _process_complex_value(self, value):
        """معالجة محسنة للقيم المعقدة من Airtable"""
        if value is None:
            return ""

        # إضافة logging للتشخيص
        logger.debug(f"Processing complex value: {type(value)} = {value}")

        # معالجة الـ dictionaries
        if isinstance(value, dict):
            # ترتيب أولوية استخراج القيم
            for key in ['name', 'label', 'value', 'text', 'title', 'display_name', 'url', 'id']:
                if key in value and value[key]:
                    result = str(value[key]).strip()
                    logger.debug(f"Extracted from dict[{key}]: {result}")
                    return result
            # إذا لم نجد شيء، أرجع أول قيمة غير فارغة
            for key, val in value.items():
                if val and str(val).strip():
                    result = str(val).strip()
                    logger.debug(f"Fallback from dict[{key}]: {result}")
                    return result
            return ""

        # معالجة الـ arrays
        elif isinstance(value, list):
            if not value:
                return ""
            # إذا كان عنصر واحد، استخدمه
            if len(value) == 1:
                return self._process_complex_value(value[0])
            # إذا كان أكثر من عنصر، اجمعهم
            processed_values = []
            for item in value:
                processed = self._process_complex_value(item)
                if processed:
                    processed_values.append(processed)
            result = ", ".join(processed_values) if processed_values else ""
            logger.debug(f"Processed array: {result}")
            return result

        # القيم البسيطة
        else:
            result = str(value).strip() if value else ""
            logger.debug(f"Simple value: {result}")
            return result

    def _parse_date(self, date_str):
        """تحليل التاريخ"""
        if not date_str:
            return ""
        try:
            if 'T' in date_str:
                return date_str.split('T')[0]
            if len(date_str) == 10 and date_str.count('-') == 2:
                return date_str
            return date_str
        except:
            return date_str

    def _translate_text(self, text):
        """ترجمة النص العام"""
        if not self.lang_manager:
            return text
        key = text.lower().replace(" ", "_")
        return self.lang_manager.get(key, text)

    def _translate_tab_name(self, tab_name):
        """ترجمة أسماء التبويبات بشكل محدد"""
        if not self.lang_manager:
            return tab_name

        # خريطة ترجمة محددة للتبويبات
        tab_translations = {
            "Basic Information": "basic_info",
            "Trip Details": "trip_details",
            "Passenger Info": "passenger_info",
            "Contact Info": "contact_info",
            "Pricing Info": "pricing_info",
            "معلومات أساسية": "basic_info",
            "تفاصيل الرحلة": "trip_details",
            "معلومات الركاب": "passenger_info",
            "معلومات الاتصال": "contact_info",
            "معلومات الأسعار": "pricing_info"
        }

        key = tab_translations.get(tab_name, tab_name.lower().replace(" ", "_"))
        return self.lang_manager.get(key, tab_name)

    def _translate_field_name(self, field_name):
        """ترجمة اسم الحقل"""
        if not self.lang_manager:
            return field_name

        # خريطة ترجمة محددة للحقول
        field_translations = {
            "Customer Name": "customer_name",
            "Hotel Name": "hotel_name",
            "Agency": "agency",
            "Booking Nr.": "booking_number",
            "Room number": "room_number",
            "trip Name": "trip_name",
            "Date Trip": "trip_date",
            "Option": "option",
            "des": "destination",
            "Guide": "guide",
            "Product ID": "product_id",
            "pickup time": "time_dropdown",
            "Remarks": "remarks",
            "Add - Ons": "add_ons",
            "ADT": "adults",
            "CHD": "children",
            "STD": "students",
            "Youth": "youth",
            "Inf": "infants",
            "CHD Age": "children_ages",
            "Customer Phone": "phone_number",
            "Customer Email": "email",
            "Customer Country": "customer_country",
            "Total price USD": "total_price_usd",
            "Total price EUR": "total_price_eur",
            "Total price GBP": "total_price_gbp",
            "Net Rate": "net_rate",
            "Currency": "currency",
            "Cost EGP": "cost_egp",
            "Collecting on date Trip": "collecting_on_date",
            "Management Option": "management_option",
            "Add-on": "add_on"
        }

        key = field_translations.get(field_name, field_name.lower().replace(" ", "_"))
        return self.lang_manager.get(key, field_name)

    def update_language(self, lang_manager):
        """تحديث لغة النافذة"""
        self.lang_manager = lang_manager
        self._setup_texts()  # إعادة إعداد النصوص

        # تحديث عنوان النافذة
        title = "➕ " + self.texts.get("add", "Add") if self.mode == "add" else "✏️ " + self.texts.get("edit", "Edit")
        self.title(title)

        # تحديث أزرار التبويبات
        if hasattr(self, 'progress_buttons'):
            for i, btn in enumerate(self.progress_buttons):
                if i < len(self.tab_names):
                    translated_name = self._translate_tab_name(self.tab_names[i])
                    btn.configure(text=f"{i+1}. {translated_name}")

        # تحديث أزرار التنقل
        if hasattr(self, 'prev_btn'):
            self.prev_btn.configure(text=f"◀ {self.texts['previous']}")
        if hasattr(self, 'next_btn'):
            self.next_btn.configure(text=f"{self.texts['next']} ▶")
        if hasattr(self, 'save_btn'):
            self.save_btn.configure(text=f"💾 {self.texts['save']}")
        if hasattr(self, 'cancel_btn'):
            self.cancel_btn.configure(text=f"❌ {self.texts['cancel']}")
        if hasattr(self, 'draft_btn'):
            self.draft_btn.configure(text=f"📝 {self.texts['draft']}")
        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.configure(text=f"🔄 {self.texts['refresh']}")

    def _get_initial_value(self, field_name):
        """الحصول على القيمة الأولية"""
        value = self.initial_fields.get(field_name)
        return self._process_complex_value(value) if value else ""

    def destroy(self):
        """تنظيف الموارد قبل الإغلاق"""
        self._is_closing = True
        try:
            # تنظيف القواميس
            for attr in ['field_vars', 'field_widgets', 'combo_boxes', 'enhanced_combos', 'dropdown_options']:
                if hasattr(self, attr):
                    getattr(self, attr).clear()
        except Exception as e:
            logger.error(f"خطأ في التنظيف: {e}")
        finally:
            super().destroy()