# -*- coding: utf-8 -*-
"""
views/components/toolbar.py

شريط الأدوات المحسن بتصميم احترافي
"""

import customtkinter as ctk
from typing import Callable, Optional
from core.language_manager import LanguageManager


class ToolbarComponent(ctk.CTkFrame):
    """شريط الأدوات المحسن بتصميم احترافي"""

    def __init__(
        self,
        parent,
        lang_manager: LanguageManager,
        theme_manager=None,
        on_add=None,
        on_edit=None,
        on_delete=None,
        on_refresh=None,
        on_export=None,
        on_import=None,  # إضافة استيراد
        on_print=None,   # إضافة طباعة
        on_language_toggle=None
    ):
        # إعدادات احترافية للإطار
        super().__init__(parent, height=60, corner_radius=0, fg_color="transparent")

        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.on_add = on_add
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_refresh = on_refresh
        self.on_export = on_export
        self.on_import = on_import
        self.on_print = on_print
        self.on_language_toggle = on_language_toggle

        # حالة الأزرار
        self.is_loading = False

        self._build_ui()

    def _build_ui(self):
        """بناء واجهة شريط الأدوات المحسنة"""
        # الحاوية الرئيسية
        main_container = ctk.CTkFrame(
            self,
            corner_radius=10,
            fg_color=("#f8f9fa", "#1e1e1e"),
            border_width=1,
            border_color=("#e0e0e0", "#444444")
        )
        main_container.pack(fill="both", expand=True)

        # إطار الأزرار الرئيسية (يسار)
        left_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=10, pady=8)

        # مجموعة أزرار CRUD
        crud_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        crud_frame.pack(side="left", padx=(0, 20))

        # زر الإضافة
        self.add_button = self._create_action_button(
            crud_frame,
            icon="➕",
            text=self.lang_manager.get('add_button', 'Add'),
            command=self.on_add,
            style="primary",
            tooltip=self.lang_manager.get('add_tooltip', 'Add new booking (Ctrl+N)')
        )
        self.add_button.pack(side="left", padx=3)

        # زر التعديل
        self.edit_button = self._create_action_button(
            crud_frame,
            icon="✏️",
            text=self.lang_manager.get('edit_button', 'Edit'),
            command=self.on_edit,
            style="info",
            state="disabled",
            tooltip=self.lang_manager.get('edit_tooltip', 'Edit selected booking (Ctrl+E)')
        )
        self.edit_button.pack(side="left", padx=3)

        # زر الحذف
        self.delete_button = self._create_action_button(
            crud_frame,
            icon="🗑️",
            text=self.lang_manager.get('delete_button', 'Delete'),
            command=self.on_delete,
            style="danger",
            state="disabled",
            tooltip=self.lang_manager.get('delete_tooltip', 'Delete selected bookings (Delete)')
        )
        self.delete_button.pack(side="left", padx=3)

        # خط فاصل
        separator1 = ctk.CTkFrame(
            left_frame,
            width=1,
            fg_color=("#e0e0e0", "#444444")
        )
        separator1.pack(side="left", fill="y", padx=10)

        # مجموعة أزرار العمليات
        operations_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        operations_frame.pack(side="left")

        # زر التحديث
        self.refresh_button = self._create_action_button(
            operations_frame,
            icon="🔄",
            text=self.lang_manager.get('refresh', 'Refresh'),
            command=self.on_refresh,
            style="secondary",
            tooltip=self.lang_manager.get('refresh_tooltip', 'Refresh data (F5)')
        )
        self.refresh_button.pack(side="left", padx=3)

        # زر التصدير
        self.export_button = self._create_action_button(
            operations_frame,
            icon="📤",
            text=self.lang_manager.get('export', 'Export'),
            command=self.on_export,
            style="secondary",
            tooltip=self.lang_manager.get('export_tooltip', 'Export to Excel (Ctrl+S)')
        )
        self.export_button.pack(side="left", padx=3)

        # زر الاستيراد
        if self.on_import:
            self.import_button = self._create_action_button(
                operations_frame,
                icon="📥",
                text=self.lang_manager.get('import', 'Import'),
                command=self.on_import,
                style="secondary",
                tooltip=self.lang_manager.get('import_tooltip', 'Import from Excel')
            )
            self.import_button.pack(side="left", padx=3)

        # زر الطباعة
        if self.on_print:
            self.print_button = self._create_action_button(
                operations_frame,
                icon="🖨️",
                text=self.lang_manager.get('print', 'Print'),
                command=self.on_print,
                style="secondary",
                tooltip=self.lang_manager.get('print_tooltip', 'Print selected (Ctrl+P)')
            )
            self.print_button.pack(side="left", padx=3)

        # إطار الجانب الأيمن
        right_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=10, pady=8)

        # مؤشر التحميل
        self.loading_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.loading_frame.pack(side="right", padx=10)

        self.loading_spinner = ctk.CTkLabel(
            self.loading_frame,
            text="",
            font=ctk.CTkFont(size=16)
        )
        self.loading_spinner.pack(side="left", padx=(0, 5))

        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("#666666", "#999999")
        )
        self.loading_label.pack(side="left")

        # عداد التحديد
        self.selection_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.selection_frame.pack(side="right", padx=10)

        self.selection_icon = ctk.CTkLabel(
            self.selection_frame,
            text="☑️",
            font=ctk.CTkFont(size=14)
        )

        self.selection_label = ctk.CTkLabel(
            self.selection_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("#666666", "#999999")
        )

        # زر تبديل اللغة (إذا كان مطلوباً)
        if self.on_language_toggle:
            separator2 = ctk.CTkFrame(
                right_frame,
                width=1,
                fg_color=("#e0e0e0", "#444444")
            )
            separator2.pack(side="right", fill="y", padx=10)

            current_lang = self.lang_manager.current_lang
            button_text = "🌐 EN" if current_lang == "ar" else "🌐 AR"

            self.language_button = self._create_action_button(
                right_frame,
                icon="",
                text=button_text,
                command=self.on_language_toggle,
                style="accent",
                tooltip=self.lang_manager.get('change_language', 'Change Language (Ctrl+L)')
            )
            self.language_button.pack(side="right", padx=3)

    def _create_action_button(self, parent, icon, text, command, style="default", state="normal", tooltip=None):
        """إنشاء زر إجراء احترافي مع تأثيرات"""
        # تحديد الألوان حسب النمط
        colors = self._get_button_colors(style)

        # إطار الزر
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")

        # الزر
        btn = ctk.CTkButton(
            button_frame,
            text=f"{icon} {text}" if icon else text,
            width=120,
            height=40,
            corner_radius=8,
            fg_color=colors["bg"],
            hover_color=colors["hover"],
            text_color=colors["text"],
            font=ctk.CTkFont(size=14, weight="bold"),
            command=command,
            state=state,
            border_width=2,
            border_color=colors["border"]
        )
        btn.pack()

        # تأثيرات hover متقدمة
        def on_enter(e):
            if btn.cget("state") != "disabled":
                btn.configure(border_color=colors["border_hover"])
                # عرض tooltip
                if tooltip and hasattr(self, '_show_tooltip'):
                    self._show_tooltip(btn, tooltip)

        def on_leave(e):
            if btn.cget("state") != "disabled":
                btn.configure(border_color=colors["border"])
                # إخفاء tooltip
                if hasattr(self, '_hide_tooltip'):
                    self._hide_tooltip()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        # حفظ مرجع للزر
        button_frame.button = btn

        return button_frame

    def _get_button_colors(self, style):
        """الحصول على ألوان الزر حسب النمط"""
        is_dark = ctk.get_appearance_mode() == "Dark"

        color_schemes = {
            "primary": {
                "bg": ("#4caf50", "#2e7d32"),
                "hover": ("#45a049", "#1b5e20"),
                "text": ("white", "white"),
                "border": ("#4caf50", "#2e7d32"),
                "border_hover": ("#388e3c", "#1b5e20")
            },
            "info": {
                "bg": ("#2196f3", "#1976d2"),
                "hover": ("#1976d2", "#1565c0"),
                "text": ("white", "white"),
                "border": ("#2196f3", "#1976d2"),
                "border_hover": ("#1565c0", "#0d47a1")
            },
            "danger": {
                "bg": ("#f44336", "#d32f2f"),
                "hover": ("#d32f2f", "#c62828"),
                "text": ("white", "white"),
                "border": ("#f44336", "#d32f2f"),
                "border_hover": ("#c62828", "#b71c1c")
            },
            "secondary": {
                "bg": ("#9e9e9e", "#616161"),
                "hover": ("#757575", "#424242"),
                "text": ("white", "white"),
                "border": ("#9e9e9e", "#616161"),
                "border_hover": ("#616161", "#424242")
            },
            "accent": {
                "bg": ("#9c27b0", "#7b1fa2"),
                "hover": ("#7b1fa2", "#6a1b9a"),
                "text": ("white", "white"),
                "border": ("#9c27b0", "#7b1fa2"),
                "border_hover": ("#6a1b9a", "#4a148c")
            },
            "default": {
                "bg": ("#e0e0e0", "#424242"),
                "hover": ("#d5d5d5", "#616161"),
                "text": ("#333333", "#ffffff"),
                "border": ("#e0e0e0", "#424242"),
                "border_hover": ("#bdbdbd", "#616161")
            }
        }

        scheme = color_schemes.get(style, color_schemes["default"])

        return {
            "bg": scheme["bg"][1 if is_dark else 0],
            "hover": scheme["hover"][1 if is_dark else 0],
            "text": scheme["text"][1 if is_dark else 0],
            "border": scheme["border"][1 if is_dark else 0],
            "border_hover": scheme["border_hover"][1 if is_dark else 0]
        }

    def update_selection(self, count: int):
        """تحديث حالة الأزرار وعرض عدد المحدد"""
        # تحديث حالة الأزرار
        if count == 0:
            self.edit_button.button.configure(state="disabled")
            self.delete_button.button.configure(state="disabled")
            # إخفاء عداد التحديد
            self.selection_icon.pack_forget()
            self.selection_label.pack_forget()
        else:
            # عرض عداد التحديد
            self.selection_icon.pack(side="left", padx=(0, 5))
            self.selection_label.pack(side="left")

            if count == 1:
                self.edit_button.button.configure(state="normal")
                self.delete_button.button.configure(state="normal")
                self.selection_label.configure(
                    text=self.lang_manager.get("selected_one", "1 selected")
                )
            else:
                self.edit_button.button.configure(state="disabled")
                self.delete_button.button.configure(state="normal")
                self.selection_label.configure(
                    text=self.lang_manager.get("selected_multiple", f"{count} selected")
                )

    def set_loading(self, is_loading: bool, message: str = None):
        """تعيين حالة التحميل مع رسالة اختيارية"""
        self.is_loading = is_loading

        if is_loading:
            # عرض مؤشر التحميل
            self.loading_spinner.configure(text="⟳")
            self.loading_label.configure(
                text=message or self.lang_manager.get("loading", "Loading...")
            )

            # تدوير المؤشر
            self._animate_spinner()

            # تعطيل زر التحديث
            self.refresh_button.button.configure(state="disabled")
        else:
            # إخفاء مؤشر التحميل
            self.loading_spinner.configure(text="")
            self.loading_label.configure(text="")

            # تفعيل زر التحديث
            self.refresh_button.button.configure(state="normal")

    def _animate_spinner(self):
        """تحريك مؤشر التحميل"""
        if self.is_loading:
            current = self.loading_spinner.cget("text")
            # دوران المؤشر
            spinners = ["⟳", "⟲", "⟱", "⟰"]
            try:
                idx = spinners.index(current)
                next_idx = (idx + 1) % len(spinners)
                self.loading_spinner.configure(text=spinners[next_idx])
            except:
                self.loading_spinner.configure(text=spinners[0])

            # جدولة الإطار التالي
            self.after(200, self._animate_spinner)

    def update_texts(self, lang_manager):
        """تحديث نصوص المكون"""
        self.lang_manager = lang_manager

        # تحديث نصوص الأزرار
        button_updates = [
            (self.add_button, 'add_button', 'Add', '➕'),
            (self.edit_button, 'edit_button', 'Edit', '✏️'),
            (self.delete_button, 'delete_button', 'Delete', '🗑️'),
            (self.refresh_button, 'refresh', 'Refresh', '🔄'),
            (self.export_button, 'export', 'Export', '📤')
        ]

        for button_frame, key, default, icon in button_updates:
            if hasattr(button_frame, 'button'):
                text = lang_manager.get(key, default)
                button_frame.button.configure(text=f"{icon} {text}")

        # تحديث الأزرار الاختيارية
        if hasattr(self, 'import_button'):
            self.import_button.button.configure(
                text=f"📥 {lang_manager.get('import', 'Import')}"
            )

        if hasattr(self, 'print_button'):
            self.print_button.button.configure(
                text=f"🖨️ {lang_manager.get('print', 'Print')}"
            )

        # تحديث زر اللغة
        if hasattr(self, 'language_button'):
            current_lang = lang_manager.current_lang
            button_text = "🌐 EN" if current_lang == "ar" else "🌐 AR"
            self.language_button.button.configure(text=button_text)

        # تحديث نص التحميل إذا كان ظاهراً
        if self.is_loading:
            self.loading_label.configure(
                text=lang_manager.get("loading", "Loading...")
            )

        # تحديث عداد التحديد إذا كان ظاهراً
        if hasattr(self, 'selection_label'):
            current_text = self.selection_label.cget("text")
            if current_text:
                # استخراج العدد من النص الحالي
                try:
                    count = int(''.join(filter(str.isdigit, current_text)))
                    if count == 1:
                        self.selection_label.configure(
                            text=lang_manager.get("selected_one", "1 selected")
                        )
                    else:
                        self.selection_label.configure(
                            text=lang_manager.get("selected_multiple", f"{count} selected")
                        )
                except:
                    pass

    def refresh_theme(self):
        """تحديث الثيم عند تغييره"""
        # تحديث ألوان الإطار الرئيسي
        main_container = self.winfo_children()[0] if self.winfo_children() else None
        if main_container and isinstance(main_container, ctk.CTkFrame):
            main_container.configure(
                fg_color=("#f8f9fa", "#1e1e1e"),
                border_color=("#e0e0e0", "#444444")
            )

        # تحديث ألوان الأزرار
        self._update_button_colors()

        # إعادة تحديد حالة التحميل إذا كانت نشطة
        if self.is_loading:
            current_text = self.loading_label.cget("text")
            self.set_loading(True, current_text)

    def _update_button_colors(self):
        """تحديث ألوان الأزرار حسب الثيم الجديد"""
        # قائمة الأزرار مع أنماطها
        button_configs = [
            (self.add_button, "primary"),
            (self.edit_button, "info"),
            (self.delete_button, "danger"),
            (self.refresh_button, "secondary"),
            (self.export_button, "secondary")
        ]

        # إضافة الأزرار الاختيارية إذا كانت موجودة
        if hasattr(self, 'import_button'):
            button_configs.append((self.import_button, "secondary"))
        if hasattr(self, 'print_button'):
            button_configs.append((self.print_button, "secondary"))
        if hasattr(self, 'language_button'):
            button_configs.append((self.language_button, "accent"))

        # تحديث كل زر
        for button_frame, style in button_configs:
            if hasattr(button_frame, 'button'):
                colors = self._get_button_colors(style)
                button_frame.button.configure(
                    fg_color=colors["bg"],
                    hover_color=colors["hover"],
                    text_color=colors["text"],
                    border_color=colors["border"]
                )

    def show_success_feedback(self, message: str):
        """عرض رسالة نجاح مؤقتة"""
        # يمكن إضافة منطق لعرض رسالة نجاح مؤقتة
        pass

    def show_error_feedback(self, message: str):
        """عرض رسالة خطأ مؤقتة"""
        # يمكن إضافة منطق لعرض رسالة خطأ مؤقتة
        pass


# للتوافق مع الكود القديم
class Toolbar(ToolbarComponent):
    """صنف بديل للتوافق مع الأكواد القديمة"""
    pass