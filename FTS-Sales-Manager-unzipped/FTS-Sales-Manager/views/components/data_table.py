# -*- coding: utf-8 -*-
"""
views/components/data_table.py

مكون جدول البيانات المحسن لعرض السجلات مع تصميم احترافي
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Dict, Any
from datetime import datetime

from core.language_manager import LanguageManager


class DataTableComponent(ctk.CTkFrame):
    """مكون جدول البيانات المحسن"""

    def __init__(
        self,
        parent,
        lang_manager: LanguageManager,
        on_row_double_click: Callable = None,
        on_selection_change: Callable = None,
        **kwargs
    ):
        # تطبيق إعدادات احترافية للإطار
        kwargs.setdefault('corner_radius', 8)
        kwargs.setdefault('fg_color', ("#ffffff", "#2b2b2b"))
        super().__init__(parent, **kwargs)

        self.lang_manager = lang_manager
        self.on_row_double_click = on_row_double_click
        self.on_selection_change = on_selection_change

        self.selected_records = []
        self.all_records = []

        self._build_ui()
        self._apply_professional_style()

    def _build_ui(self):
        """بناء الواجهة المحسنة"""
        # إطار الجدول مع padding محسن
        table_container = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="transparent"
        )
        table_container.pack(fill="both", expand=True, padx=2, pady=2)

        # إنشاء الجدول
        self._create_treeview(table_container)

        # شريط التمرير المحسن
        self._create_scrollbars(table_container)

    def _create_treeview(self, parent):
        """إنشاء جدول TreeView محسن"""
        # الأعمدة
        columns = self._get_column_names()

        # إنشاء TreeView مع إعدادات محسنة
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="tree headings",
            selectmode="extended",
            height=15  # عدد الصفوف المرئية
        )

        # إعداد الأعمدة مع عرض محسن
        self.tree.column("#0", width=50, stretch=False)

        column_configs = [
            ("booking_nr", 130, "center"),
            ("date_trip", 110, "center"),
            ("customer_name", 180, "w"),
            ("hotel_name", 180, "w"),
            ("pickup_time", 100, "center"),
            ("price", 120, "e"),
            ("status", 120, "center")
        ]

        for i, (col, width, anchor) in enumerate(column_configs):
            if i < len(columns):
                self.tree.column(columns[i], width=width, anchor=anchor, minwidth=80)
                self.tree.heading(
                    columns[i],
                    text=col,
                    command=lambda c=columns[i]: self._sort_by_column(c)
                )

        # تطبيق النمط الاحترافي
        self._apply_treeview_style()

        # ربط الأحداث
        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)
        self.tree.bind("<Button-3>", self._on_right_click)  # قائمة سياق

        # وضع الجدول
        self.tree.grid(row=0, column=0, sticky="nsew")
        parent.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)

        # تحديث عناوين الأعمدة
        self._update_column_headers()

    def _apply_treeview_style(self):
        """تطبيق النمط الاحترافي للجدول"""
        style = ttk.Style()

        # فرض إعادة تحديث النمط
        try:
            style.theme_use("clam")
        except:
            pass

        # ألوان احترافية للوضع الفاتح والداكن
        if ctk.get_appearance_mode() == "Dark":
            # الوضع الداكن
            bg_color = "#2b2b2b"
            fg_color = "#ffffff"
            selected_bg = "#1976d2"
            selected_fg = "#ffffff"
            header_bg = "#1e1e1e"
            header_fg = "#ffffff"
            row_hover = "#3a3a3a"
            alt_row_bg = "#323232"
        else:
            # الوضع الفاتح
            bg_color = "#ffffff"
            fg_color = "#333333"
            selected_bg = "#e3f2fd"
            selected_fg = "#1976d2"
            header_bg = "#f8f9fa"
            header_fg = "#333333"
            row_hover = "#f5f5f5"
            alt_row_bg = "#f9f9f9"

        # تكوين Treeview
        style.configure(
            "Treeview",
            background=bg_color,
            foreground=fg_color,
            rowheight=35,
            fieldbackground=bg_color,
            borderwidth=0,
            relief="flat",
            font=('Segoe UI', 10)
        )

        # تكوين رأس الجدول
        style.configure(
            "Treeview.Heading",
            background=header_bg,
            foreground=header_fg,
            relief="flat",
            borderwidth=0,
            font=('Segoe UI', 11, 'bold')
        )

        # تأثيرات التحديد والتمرير
        style.map(
            "Treeview",
            background=[
                ('selected', selected_bg),
                ('active', row_hover)
            ],
            foreground=[
                ('selected', selected_fg),
                ('active', fg_color)
            ]
        )

        # تأثيرات رأس الجدول عند التمرير
        style.map(
            "Treeview.Heading",
            background=[
                ('active', selected_bg),
                ('pressed', selected_bg)
            ],
            foreground=[
                ('active', selected_fg),
                ('pressed', selected_fg)
            ]
        )

        # تطبيق الصفوف المتناوبة
        self.tree.tag_configure('oddrow', background=bg_color)
        self.tree.tag_configure('evenrow', background=alt_row_bg)

        # فرض تحديث الجدول
        self.tree.update_idletasks()

    def _create_scrollbars(self, parent):
        """إنشاء أشرطة تمرير محسنة"""
        # شريط تمرير عمودي محسن
        vsb_frame = ctk.CTkFrame(parent, width=16, fg_color="transparent")
        vsb_frame.grid(row=0, column=1, sticky="ns", padx=(2, 0))

        vsb = ttk.Scrollbar(
            vsb_frame,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar"
        )
        vsb.pack(fill="y", expand=True)
        self.tree.configure(yscrollcommand=vsb.set)

        # شريط تمرير أفقي محسن
        hsb_frame = ctk.CTkFrame(parent, height=16, fg_color="transparent")
        hsb_frame.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        hsb = ttk.Scrollbar(
            hsb_frame,
            orient="horizontal",
            command=self.tree.xview,
            style="Horizontal.TScrollbar"
        )
        hsb.pack(fill="x", expand=True)
        self.tree.configure(xscrollcommand=hsb.set)

        # تطبيق نمط أشرطة التمرير
        self._style_scrollbars()

    def _style_scrollbars(self):
        """تطبيق نمط احترافي لأشرطة التمرير"""
        style = ttk.Style()

        if ctk.get_appearance_mode() == "Dark":
            bg_color = "#2b2b2b"
            thumb_color = "#555555"
            thumb_hover = "#666666"
            arrow_color = "#999999"
        else:
            bg_color = "#f0f0f0"
            thumb_color = "#cccccc"
            thumb_hover = "#aaaaaa"
            arrow_color = "#666666"

        # نمط شريط التمرير العمودي
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=thumb_color,
            darkcolor=bg_color,
            lightcolor=bg_color,
            troughcolor=bg_color,
            bordercolor=bg_color,
            arrowcolor=arrow_color,
            arrowsize=14
        )

        style.map(
            "Vertical.TScrollbar",
            background=[
                ('active', thumb_hover),
                ('pressed', thumb_hover),
                ('!active', thumb_color)
            ]
        )

        # نمط شريط التمرير الأفقي
        style.configure(
            "Horizontal.TScrollbar",
            gripcount=0,
            background=thumb_color,
            darkcolor=bg_color,
            lightcolor=bg_color,
            troughcolor=bg_color,
            bordercolor=bg_color,
            arrowcolor=arrow_color,
            arrowsize=14
        )

        style.map(
            "Horizontal.TScrollbar",
            background=[
                ('active', thumb_hover),
                ('pressed', thumb_hover),
                ('!active', thumb_color)
            ]
        )

    def display_data(self, records: List[Dict[str, Any]]):
        """عرض البيانات في الجدول مع تحسينات بصرية"""
        # حفظ السجلات
        self.all_records = records

        # مسح الجدول
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            return
        for item in self.tree.get_children():
            self.tree.delete(item)

        # إضافة السجلات مع تحسينات
        for idx, record in enumerate(records):
            fields = record.get('fields', {})

            # تحضير البيانات
            values = (
                fields.get('Booking Nr.', ''),
                self._format_date(fields.get('Date Trip', '')),
                fields.get('Customer Name', ''),
                fields.get('Hotel Name', ''),
                self._format_time(fields.get('pickup time', '')),
                self._format_currency(fields.get('Net Rate', 0)),
                self._translate_status(fields.get('Booking Status', ''))
            )

            # تحديد التاجات
            tags = []

            # تاج الصف (زوجي/فردي)
            if idx % 2 == 0:
                tags.append('evenrow')
            else:
                tags.append('oddrow')

            # تاج الحالة
            status = fields.get('Booking Status', '').lower()
            if status == 'confirmed':
                tags.append('confirmed')
            elif status == 'pending':
                tags.append('pending')
            elif status == 'cancelled':
                tags.append('cancelled')
            elif status == 'completed':
                tags.append('completed')

            # إضافة الصف
            item = self.tree.insert("", "end", values=values, tags=tags)

        # تطبيق ألوان الحالات المحسنة
        self._apply_status_colors()

    def _apply_status_colors(self):
        """تطبيق ألوان احترافية للحالات"""
        if ctk.get_appearance_mode() == "Dark":
            # ألوان الوضع الداكن
            self.tree.tag_configure('confirmed', background='#1b5e20', foreground='#ffffff')
            self.tree.tag_configure('pending', background='#f57c00', foreground='#ffffff')
            self.tree.tag_configure('cancelled', background='#b71c1c', foreground='#ffffff')
            self.tree.tag_configure('completed', background='#0d47a1', foreground='#ffffff')
        else:
            # ألوان الوضع الفاتح
            self.tree.tag_configure('confirmed', background='#d4edda', foreground='#155724')
            self.tree.tag_configure('pending', background='#fff3cd', foreground='#856404')
            self.tree.tag_configure('cancelled', background='#f8d7da', foreground='#721c24')
            self.tree.tag_configure('completed', background='#cce5ff', foreground='#004085')

    def _format_date(self, date_str):
        """تنسيق التاريخ بشكل احترافي"""
        if not date_str:
            return ""
        try:
            date = datetime.fromisoformat(date_str[:10])
            if self.lang_manager and self.lang_manager.current_lang == "ar":
                # تنسيق عربي مع أسماء الأيام
                days_ar = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
                day_name = days_ar[date.weekday()]
                return f"{day_name} {date.strftime('%d/%m/%Y')}"
            else:
                # تنسيق إنجليزي
                return date.strftime("%a %d %b %Y")
        except:
            return date_str

    def _format_time(self, time_str):
        """تنسيق الوقت بشكل احترافي"""
        if not time_str:
            return ""
        try:
            # محاولة تحويل الوقت
            if ":" in time_str:
                time_parts = time_str.split(":")
                hour = int(time_parts[0])
                minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                # تنسيق 12 ساعة
                period = "PM" if hour >= 12 else "AM"
                if self.lang_manager and self.lang_manager.current_lang == "ar":
                    period = "م" if hour >= 12 else "ص"

                hour_12 = hour % 12
                if hour_12 == 0:
                    hour_12 = 12

                return f"{hour_12:02d}:{minute:02d} {period}"
            return time_str
        except:
            return time_str

    def _format_currency(self, amount):
        """تنسيق العملة بشكل احترافي"""
        try:
            formatted = f"{float(amount):,.2f}"
            if self.lang_manager and self.lang_manager.current_lang == "ar":
                # استبدال الفاصلة بالفاصلة العربية
                formatted = formatted.replace(",", "،")
                return f"{formatted} $"
            else:
                return f"${formatted}"
        except:
            return "$0.00"

    def _translate_status(self, status):
        """ترجمة الحالة مع أيقونة"""
        if not self.lang_manager:
            return status

        # قاموس الحالات مع الأيقونات
        status_map = {
            'confirmed': ('✓', 'status_confirmed', 'Confirmed'),
            'pending': ('⏳', 'status_pending', 'Pending'),
            'cancelled': ('✗', 'status_cancelled', 'Cancelled'),
            'completed': ('✔', 'status_completed', 'Completed')
        }

        status_lower = status.lower()
        if status_lower in status_map:
            icon, key, default = status_map[status_lower]
            translated = self.lang_manager.get(key, default)
            return f"{icon} {translated}"

        return status

    def _on_right_click(self, event):
        """معالج النقر بالزر الأيمن (قائمة سياق)"""
        # تحديد الصف المنقور
        item = self.tree.identify('item', event.x, event.y)
        if item:
            self.tree.selection_set(item)

            # إنشاء قائمة سياق
            context_menu = tk.Menu(self, tearoff=0)
            context_menu.configure(
                bg=("#ffffff" if ctk.get_appearance_mode() == "Light" else "#2b2b2b"),
                fg=("#000000" if ctk.get_appearance_mode() == "Light" else "#ffffff"),
                activebackground=("#e3f2fd" if ctk.get_appearance_mode() == "Light" else "#1976d2"),
                activeforeground=("#1976d2" if ctk.get_appearance_mode() == "Light" else "#ffffff"),
                font=('Segoe UI', 10)
            )

            # إضافة عناصر القائمة
            context_menu.add_command(
                label=f"✏️ {self.lang_manager.get('edit', 'Edit')}",
                command=lambda: self._context_edit(item)
            )
            context_menu.add_command(
                label=f"📋 {self.lang_manager.get('copy', 'Copy')}",
                command=lambda: self._context_copy(item)
            )
            context_menu.add_separator()
            context_menu.add_command(
                label=f"🗑️ {self.lang_manager.get('delete', 'Delete')}",
                command=lambda: self._context_delete(item)
            )

            # عرض القائمة
            context_menu.tk_popup(event.x_root, event.y_root)

    def _context_edit(self, item):
        """تعديل من القائمة السياقية"""
        index = self.tree.index(item)
        if 0 <= index < len(self.all_records):
            record = self.all_records[index]
            if self.on_row_double_click:
                self.on_row_double_click(record)

    def _context_copy(self, item):
        """نسخ من القائمة السياقية"""
        values = self.tree.item(item)['values']
        if values:
            # نسخ رقم الحجز
            self.clipboard_clear()
            self.clipboard_append(str(values[0]))

    def _context_delete(self, item):
        """حذف من القائمة السياقية"""
        # يمكن تنفيذ منطق الحذف هنا
        pass

    def _sort_by_column(self, column):
        """ترتيب حسب العمود مع مؤشر بصري"""
        # TODO: تنفيذ الترتيب مع إضافة سهم للإشارة لاتجاه الترتيب
        pass

    def _apply_professional_style(self):
        """تطبيق تحسينات إضافية للمظهر الاحترافي"""
        # يمكن إضافة المزيد من التحسينات البصرية هنا
        pass

    def _get_column_names(self):
        """الحصول على أسماء الأعمدة الداخلية"""
        return ["booking_nr", "date_trip", "customer_name", "hotel_name",
                "pickup_time", "price", "status"]

    def _on_double_click(self, event):
        """معالج النقر المزدوج المحسن"""
        selection = self.tree.selection()
        if selection and self.on_row_double_click:
            item = selection[0]
            index = self.tree.index(item)
            if 0 <= index < len(self.all_records):
                record = self.all_records[index]
                self.on_row_double_click(record)

    def _on_selection_change(self, event):
        """معالج تغيير التحديد المحسن"""
        selection = self.tree.selection()
        self.selected_records = []

        for item in selection:
            index = self.tree.index(item)
            if 0 <= index < len(self.all_records):
                self.selected_records.append(self.all_records[index])

        if self.on_selection_change:
            self.on_selection_change(self.selected_records)

    def get_selected_records(self):
        """الحصول على السجلات المحددة"""
        return self.selected_records

    def clear_selection(self):
        """مسح التحديد"""
        self.tree.selection_remove(self.tree.selection())
        self.selected_records = []

    def update_texts(self, lang_manager: LanguageManager):
        """تحديث جميع النصوص عند تغيير اللغة"""
        self.lang_manager = lang_manager

        # تحديث عناوين الأعمدة
        self._update_column_headers()

        # إعادة عرض البيانات لتحديث الترجمات
        if self.all_records:
            self.display_data(self.all_records)

    def _update_column_headers(self):
        """تحديث عناوين الأعمدة بناءً على اللغة الحالية"""
        if not hasattr(self, 'tree') or not self.tree.winfo_exists():
            return

        # تعريف الأعمدة مع مفاتيح الترجمة
        columns_map = [
            ("booking_number", "Booking Nr.", "رقم الحجز"),
            ("trip_date", "Trip Date", "تاريخ الرحلة"),
            ("customer_name", "Customer Name", "اسم العميل"),
            ("hotel", "Hotel", "الفندق"),
            ("pickup_time", "Pickup Time", "وقت الاستلام"),
            ("price", "Price", "السعر"),
            ("status", "Status", "الحالة")
        ]

        # الحصول على اللغة الحالية
        current_lang = self.lang_manager.current_lang if self.lang_manager else "ar"

        # تحديث عناوين الأعمدة
        columns = self.tree["columns"]
        for i, (trans_key, en_name, ar_name) in enumerate(columns_map):
            if i < len(columns):
                # الحصول على النص المترجم
                if self.lang_manager:
                    translated_text = self.lang_manager.get(trans_key, en_name if current_lang == "en" else ar_name)
                else:
                    translated_text = en_name if current_lang == "en" else ar_name

                # تحديث عنوان العمود
                self.tree.heading(columns[i], text=translated_text)

    def set_loading(self, is_loading: bool):
        """عرض حالة التحميل"""
        if is_loading:
            # يمكن إضافة مؤشر تحميل هنا
            pass
        else:
            # إخفاء مؤشر التحميل
            pass

    def refresh_theme(self):
        """تحديث الثيم عند تغييره"""
        # إعادة تطبيق أنماط TreeView
        self._apply_treeview_style()

        # إعادة تطبيق أنماط أشرطة التمرير
        self._style_scrollbars()

        # إعادة تطبيق ألوان الحالات
        self._apply_status_colors()

        # تحديث إطار الجدول
        self.configure(fg_color=("#ffffff", "#2b2b2b"))

        # إعادة عرض البيانات لتطبيق الألوان الجديدة
        if self.all_records:
            # حفظ التحديد الحالي
            current_selection = self.tree.selection()

            # إعادة عرض البيانات
            self.display_data(self.all_records)

            # استعادة التحديد
            if current_selection:
                try:
                    for item in current_selection:
                        self.tree.selection_add(item)
                except:
                    pass