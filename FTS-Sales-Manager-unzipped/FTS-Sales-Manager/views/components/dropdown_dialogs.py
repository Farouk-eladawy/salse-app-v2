# -*- coding: utf-8 -*-
"""
views/components/dropdown_dialogs.py

نوافذ حوار القائمة المنسدلة المحدثة والمتكاملة مع بنية التطبيق
"""

import customtkinter as ctk
from typing import Dict, Any, Callable, Optional, List
import webbrowser
from datetime import datetime
import json
import os
from tkinter import messagebox, filedialog

from core.language_manager import LanguageManager
from core.theme_manager import ThemeManager
from core.config_manager import ConfigManager
from core.logger import logger


class ProfileWindow(ctk.CTkToplevel):
    """نافذة عرض وتعديل الملف الشخصي - محدثة لجلب البيانات من Airtable"""

    def __init__(self, parent, controller, lang_manager):
        super().__init__(parent)

        self.controller = controller
        self.lang_manager = lang_manager

        # إعدادات النافذة
        self.title(lang_manager.get("profile_title", "User Profile"))
        self.geometry("450x600")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        # تحميل بيانات المستخدم
        self._load_user_data()

        # بناء الواجهة
        self._build_ui()

        # توسيط النافذة
        self._center_window()

    def _center_window(self):
        """توسيط النافذة على الشاشة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _load_user_data(self):
        """تحميل بيانات المستخدم من Airtable"""
        try:
            # الحصول على معلومات المستخدم الحالي
            current_username = self.controller.current_username

            if current_username and self.controller.airtable_users:
                # جلب جميع المستخدمين
                users = self.controller.airtable_users.fetch_records()

                # البحث عن المستخدم الحالي
                for user in users:
                    fields = user.get('fields', {})
                    if fields.get('Username', '').lower() == current_username.lower():
                        self.user_data = fields
                        self.user_record_id = user.get('id')
                        logger.info(f"تم جلب بيانات المستخدم: {current_username}")
                        return

            # إذا لم يتم العثور على البيانات، استخدم البيانات المحلية
            self.user_data = self.controller.current_user_info or {}
            self.user_record_id = self.user_data.get('record_id')

        except Exception as e:
            logger.error(f"خطأ في جلب بيانات المستخدم: {e}")
            self.user_data = {}
            self.user_record_id = None

    def _build_ui(self):
        """بناء واجهة الملف الشخصي"""
        # الحاوية الرئيسية مع التمرير
        main_frame = ctk.CTkScrollableFrame(self, width=400, height=500)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # العنوان
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))

        # أيقونة المستخدم
        user_icon = ctk.CTkLabel(
            title_frame,
            text="👤",
            font=ctk.CTkFont(size=48)
        )
        user_icon.pack()

        # اسم المستخدم
        username = self.user_data.get('Username', 'Unknown')
        username_label = ctk.CTkLabel(
            title_frame,
            text=username,
            font=ctk.CTkFont(size=24, weight="bold")
        )
        username_label.pack(pady=(10, 5))

        # الدور
        role = self.user_data.get('Role', 'User')
        role_text = self._translate_role(role)
        role_label = ctk.CTkLabel(
            title_frame,
            text=role_text,
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        role_label.pack()

        # خط فاصل
        separator = ctk.CTkFrame(main_frame, height=2, fg_color=("gray70", "gray30"))
        separator.pack(fill="x", pady=20)

        # معلومات المستخدم
        self._create_info_section(main_frame)

        # إحصائيات الاستخدام
        self._create_stats_section(main_frame)

        # أزرار الإجراءات
        self._create_action_buttons(main_frame)

        # زر الإغلاق
        close_btn = ctk.CTkButton(
            self,
            text=self.lang_manager.get("close", "Close"),
            command=self.destroy,
            width=120
        )
        close_btn.pack(pady=(0, 20))

    def _create_info_section(self, parent):
        """إنشاء قسم المعلومات الأساسية"""
        info_frame = ctk.CTkFrame(parent)
        info_frame.pack(fill="x", pady=(0, 20))

        # عنوان القسم
        section_title = ctk.CTkLabel(
            info_frame,
            text=self.lang_manager.get("basic_info", "Basic Information"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # المعلومات
        info_items = [
            ("email", "Email", self.user_data.get('Email', 'Not provided')),
            ("phone", "Phone", self.user_data.get('Phone', 'Not provided')),
            ("department", "Department", self.user_data.get('Department', 'Not specified')),
            ("airtable_view", "Assigned View", self.user_data.get('Airtable View', 'Default')),
            ("status", "Status", "Active" if self.user_data.get('Active', True) else "Inactive")
        ]

        for key, label, value in info_items:
            self._create_info_row(info_frame, self.lang_manager.get(key, label), value)

    def _create_stats_section(self, parent):
        """إنشاء قسم الإحصائيات"""
        stats_frame = ctk.CTkFrame(parent)
        stats_frame.pack(fill="x", pady=(0, 20))

        # عنوان القسم
        section_title = ctk.CTkLabel(
            stats_frame,
            text=self.lang_manager.get("usage_stats", "Usage Statistics"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # الإحصائيات
        last_login = self.user_data.get('Last Login', '')
        if last_login:
            try:
                dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                last_login = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass

        login_count = self.user_data.get('Login Count', 0)
        created_date = self.user_data.get('Created Date', '')
        if created_date:
            try:
                dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                created_date = dt.strftime("%Y-%m-%d")
            except:
                pass

        stats_items = [
            ("last_login", "Last Login", last_login or 'Never'),
            ("login_count", "Login Count", str(login_count)),
            ("created_date", "Member Since", created_date or 'Unknown')
        ]

        for key, label, value in stats_items:
            self._create_info_row(stats_frame, self.lang_manager.get(key, label), value)

    def _create_info_row(self, parent, label, value):
        """إنشاء صف معلومات"""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=3)

        # التسمية
        label_widget = ctk.CTkLabel(
            row_frame,
            text=f"{label}:",
            font=ctk.CTkFont(size=13),
            anchor="w",
            width=120
        )
        label_widget.pack(side="left")

        # القيمة
        value_widget = ctk.CTkLabel(
            row_frame,
            text=str(value),
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w"
        )
        value_widget.pack(side="left", padx=(10, 0))

    def _create_action_buttons(self, parent):
        """إنشاء أزرار الإجراءات"""
        actions_frame = ctk.CTkFrame(parent)
        actions_frame.pack(fill="x", pady=(0, 20))

        # عنوان القسم
        section_title = ctk.CTkLabel(
            actions_frame,
            text=self.lang_manager.get("actions", "Actions"),
            font=ctk.CTkFont(size=16, weight="bold")
        )
        section_title.pack(anchor="w", padx=15, pady=(15, 10))

        # أزرار الإجراءات
        buttons_frame = ctk.CTkFrame(actions_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=10)

        # زر تغيير كلمة المرور
        change_pwd_btn = ctk.CTkButton(
            buttons_frame,
            text=self.lang_manager.get("change_password", "Change Password"),
            command=self._change_password,
            width=180
        )
        change_pwd_btn.pack(pady=5)

        # زر تحديث البريد الإلكتروني
        update_email_btn = ctk.CTkButton(
            buttons_frame,
            text=self.lang_manager.get("update_email", "Update Email"),
            command=self._update_email,
            width=180,
            fg_color="transparent",
            border_width=2
        )
        update_email_btn.pack(pady=5)

    def _translate_role(self, role):
        """ترجمة الدور"""
        role_translations = {
            'admin': self.lang_manager.get("role_admin", "Administrator"),
            'manager': self.lang_manager.get("role_manager", "Manager"),
            'editor': self.lang_manager.get("role_editor", "Editor"),
            'viewer': self.lang_manager.get("role_viewer", "Viewer")
        }
        return role_translations.get(role.lower(), role)

    def _change_password(self):
        """فتح نافذة تغيير كلمة المرور"""
        dialog = ChangePasswordDialog(self, self.controller, self.lang_manager)

    def _update_email(self):
        """فتح نافذة تحديث البريد الإلكتروني"""
        dialog = UpdateEmailDialog(self, self.controller, self.lang_manager, self.user_data.get('Email', ''))


class ChangePasswordDialog(ctk.CTkToplevel):
    """نافذة حوار تغيير كلمة المرور"""

    def __init__(self, parent, controller, lang_manager):
        super().__init__(parent)

        self.controller = controller
        self.lang_manager = lang_manager

        # إعدادات النافذة
        self.title(lang_manager.get("change_password", "Change Password"))
        self.geometry("400x350")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """توسيط النافذة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """بناء الواجهة"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # العنوان
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("change_password", "Change Password"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # كلمة المرور الحالية
        current_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("current_password", "Current Password"),
            anchor="w"
        )
        current_label.pack(fill="x", pady=(0, 5))

        self.current_entry = ctk.CTkEntry(
            main_frame,
            show="•",
            height=40
        )
        self.current_entry.pack(fill="x", pady=(0, 15))

        # كلمة المرور الجديدة
        new_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("new_password", "New Password"),
            anchor="w"
        )
        new_label.pack(fill="x", pady=(0, 5))

        self.new_entry = ctk.CTkEntry(
            main_frame,
            show="•",
            height=40
        )
        self.new_entry.pack(fill="x", pady=(0, 15))

        # تأكيد كلمة المرور
        confirm_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("confirm_password", "Confirm Password"),
            anchor="w"
        )
        confirm_label.pack(fill="x", pady=(0, 5))

        self.confirm_entry = ctk.CTkEntry(
            main_frame,
            show="•",
            height=40
        )
        self.confirm_entry.pack(fill="x", pady=(0, 20))

        # أزرار الإجراءات
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        save_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("save", "Save"),
            command=self._save_password,
            width=100
        )
        save_btn.pack(side="left", padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left")

    def _save_password(self):
        """حفظ كلمة المرور الجديدة"""
        current = self.current_entry.get()
        new = self.new_entry.get()
        confirm = self.confirm_entry.get()

        # التحقق من الإدخال
        if not all([current, new, confirm]):
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                self.lang_manager.get("fill_all_fields", "Please fill all fields")
            )
            return

        if new != confirm:
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                self.lang_manager.get("passwords_dont_match", "Passwords do not match")
            )
            return

        if len(new) < 8:
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                self.lang_manager.get("password_too_short", "Password must be at least 8 characters")
            )
            return

        # محاولة تغيير كلمة المرور
        try:
            if hasattr(self.controller, 'user_mgr') and self.controller.user_mgr:
                success = self.controller.user_mgr.change_password(
                    self.controller.current_username,
                    current,
                    new
                )

                if success:
                    messagebox.showinfo(
                        self.lang_manager.get("success", "Success"),
                        self.lang_manager.get("password_changed", "Password changed successfully")
                    )
                    self.destroy()
                else:
                    messagebox.showerror(
                        self.lang_manager.get("error", "Error"),
                        self.lang_manager.get("incorrect_password", "Current password is incorrect")
                    )
            else:
                messagebox.showerror(
                    self.lang_manager.get("error", "Error"),
                    self.lang_manager.get("feature_not_available", "This feature is not available")
                )
        except Exception as e:
            logger.error(f"خطأ في تغيير كلمة المرور: {e}")
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                str(e)
            )


class UpdateEmailDialog(ctk.CTkToplevel):
    """نافذة حوار تحديث البريد الإلكتروني"""

    def __init__(self, parent, controller, lang_manager, current_email):
        super().__init__(parent)

        self.controller = controller
        self.lang_manager = lang_manager
        self.current_email = current_email

        # إعدادات النافذة
        self.title(lang_manager.get("update_email", "Update Email"))
        self.geometry("400x250")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """توسيط النافذة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """بناء الواجهة"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # العنوان
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("update_email", "Update Email"),
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 20))

        # البريد الحالي
        current_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        current_frame.pack(fill="x", pady=(0, 15))

        current_label = ctk.CTkLabel(
            current_frame,
            text=self.lang_manager.get("current_email", "Current Email:"),
            anchor="w"
        )
        current_label.pack(side="left")

        current_value = ctk.CTkLabel(
            current_frame,
            text=self.current_email or "Not set",
            font=ctk.CTkFont(weight="bold"),
            anchor="w"
        )
        current_value.pack(side="left", padx=(10, 0))

        # البريد الجديد
        new_label = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get("new_email", "New Email"),
            anchor="w"
        )
        new_label.pack(fill="x", pady=(0, 5))

        self.email_entry = ctk.CTkEntry(
            main_frame,
            height=40,
            placeholder_text="example@email.com"
        )
        self.email_entry.pack(fill="x", pady=(0, 20))

        # أزرار الإجراءات
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        save_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("save", "Save"),
            command=self._save_email,
            width=100
        )
        save_btn.pack(side="left", padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left")

    def _save_email(self):
        """حفظ البريد الإلكتروني الجديد"""
        new_email = self.email_entry.get().strip()

        if not new_email:
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                self.lang_manager.get("enter_email", "Please enter an email address")
            )
            return

        # التحقق من صحة البريد الإلكتروني
        if '@' not in new_email or '.' not in new_email:
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                self.lang_manager.get("invalid_email", "Please enter a valid email address")
            )
            return

        # تحديث البريد في Airtable
        messagebox.showinfo(
            self.lang_manager.get("info", "Information"),
            self.lang_manager.get("email_update_request", "Email update request has been sent to administrator")
        )
        self.destroy()


class SettingsWindow(ctk.CTkToplevel):
    """نافذة الإعدادات المحسنة"""

    def __init__(self, parent, lang_manager, config_manager, theme_manager):
        super().__init__(parent)

        self.lang_manager = lang_manager
        self.config_manager = config_manager
        self.theme_manager = theme_manager

        # إعدادات النافذة
        self.title(lang_manager.get("settings_title", "Settings"))
        self.geometry("600x500")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        # متغيرات الإعدادات
        self.settings_changed = False
        self.temp_settings = {}

        self._build_ui()
        self._center_window()
        self._load_current_settings()

    def _center_window(self):
        """توسيط النافذة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """بناء واجهة الإعدادات"""
        # الحاوية الرئيسية
        main_container = ctk.CTkFrame(self)
        main_container.pack(fill="both", expand=True)

        # العنوان
        title_frame = ctk.CTkFrame(main_container, height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            title_frame,
            text=self.lang_manager.get("settings_title", "Settings"),
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(expand=True)

        # التبويبات
        self.tabview = ctk.CTkTabview(main_container, width=550, height=350)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # إضافة التبويبات
        self.tabview.add(self.lang_manager.get("appearance", "Appearance"))
        self.tabview.add(self.lang_manager.get("performance", "Performance"))
        self.tabview.add(self.lang_manager.get("advanced", "Advanced"))

        # محتوى التبويبات
        self._create_appearance_tab()
        self._create_performance_tab()
        self._create_advanced_tab()

        # أزرار الإجراءات
        self._create_action_buttons(main_container)

    def _create_appearance_tab(self):
        """إنشاء تبويب المظهر"""
        tab = self.tabview.tab(self.lang_manager.get("appearance", "Appearance"))

        # إطار المحتوى
        content_frame = ctk.CTkScrollableFrame(tab, height=300)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. إعداد المظهر
        appearance_section = self._create_section(
            content_frame,
            self.lang_manager.get("theme_mode", "Theme Mode")
        )

        self.appearance_var = ctk.StringVar(value=ctk.get_appearance_mode())
        appearance_menu = ctk.CTkOptionMenu(
            appearance_section,
            values=["Light", "Dark", "System"],
            variable=self.appearance_var,
            command=self._on_appearance_change
        )
        appearance_menu.pack(fill="x", pady=5)

        # 2. اللون الأساسي - عرض فقط
        color_section = self._create_section(
            content_frame,
            self.lang_manager.get("primary_color", "Primary Color")
        )

        # عرض الثيم الحالي فقط
        current_theme = self.config_manager.get("color_theme", "blue")
        # تصحيح dark-blue إذا وجد
        if current_theme == "dark-blue":
            current_theme = "blue"

        theme_info_frame = ctk.CTkFrame(color_section, fg_color="transparent")
        theme_info_frame.pack(fill="x", pady=5)

        theme_label = ctk.CTkLabel(
            theme_info_frame,
            text=f"{self.lang_manager.get('current_theme', 'Current Theme')}: ",
            font=ctk.CTkFont(size=13)
        )
        theme_label.pack(side="left")

        theme_value = ctk.CTkLabel(
            theme_info_frame,
            text=current_theme.title(),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=("#1976d2", "#64b5f6")
        )
        theme_value.pack(side="left")

        # رسالة معلومات
        info_msg = ctk.CTkLabel(
            color_section,
            text=self.lang_manager.get(
                "theme_info",
                "ℹ️ لتغيير الثيم اللوني، استخدم قائمة المستخدم في الشريط العلوي"
            ),
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40"),
            wraplength=400
        )
        info_msg.pack(fill="x", pady=(10, 0))

        # 3. حجم الخط
        font_section = self._create_section(
            content_frame,
            self.lang_manager.get("font_size", "Font Size")
        )

        self.font_size_var = ctk.DoubleVar(value=self.config_manager.get("font_size", 14))

        # إطار حجم الخط
        font_frame = ctk.CTkFrame(font_section, fg_color="transparent")
        font_frame.pack(fill="x", pady=5)

        font_slider = ctk.CTkSlider(
            font_frame,
            from_=10,
            to=20,
            variable=self.font_size_var,
            command=self._on_font_size_change
        )
        font_slider.pack(side="left", fill="x", expand=True)

        self.font_size_label = ctk.CTkLabel(
            font_frame,
            text=f"{int(self.font_size_var.get())}px",
            width=50
        )
        self.font_size_label.pack(side="left", padx=(10, 0))

        # 4. معاينة
        preview_section = self._create_section(
            content_frame,
            self.lang_manager.get("preview", "Preview")
        )

        self.preview_frame = ctk.CTkFrame(preview_section, height=100)
        self.preview_frame.pack(fill="x", pady=5)

        preview_content = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_content.pack(expand=True)

        self.preview_label = ctk.CTkLabel(
            preview_content,
            text=self.lang_manager.get("preview_text", "This is a preview of your settings"),
            font=ctk.CTkFont(size=int(self.font_size_var.get()))
        )
        self.preview_label.pack(pady=10)

        # أمثلة أزرار للمعاينة
        preview_buttons = ctk.CTkFrame(preview_content, fg_color="transparent")
        preview_buttons.pack()

        preview_btn1 = ctk.CTkButton(
            preview_buttons,
            text=self.lang_manager.get("sample_button", "Sample Button"),
            width=120,
            height=32
        )
        preview_btn1.pack(side="left", padx=5)

        preview_btn2 = ctk.CTkButton(
            preview_buttons,
            text=self.lang_manager.get("secondary", "Secondary"),
            width=120,
            height=32,
            fg_color="transparent",
            border_width=2
        )
        preview_btn2.pack(side="left", padx=5)

    def _create_performance_tab(self):
        """إنشاء تبويب الأداء"""
        tab = self.tabview.tab(self.lang_manager.get("performance", "Performance"))

        content_frame = ctk.CTkScrollableFrame(tab, height=300)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. التحميل التلقائي
        auto_refresh_section = self._create_section(
            content_frame,
            self.lang_manager.get("auto_refresh", "Auto Refresh")
        )

        self.auto_refresh_var = ctk.BooleanVar(
            value=self.config_manager.get("auto_refresh", True)
        )
        auto_refresh_switch = ctk.CTkSwitch(
            auto_refresh_section,
            text=self.lang_manager.get("enable_auto_refresh", "Enable automatic data refresh"),
            variable=self.auto_refresh_var,
            command=self._on_setting_change
        )
        auto_refresh_switch.pack(anchor="w", pady=5)

        # 2. فترة التحديث
        refresh_interval_section = self._create_section(
            content_frame,
            self.lang_manager.get("refresh_interval", "Refresh Interval")
        )

        self.refresh_interval_var = ctk.IntVar(
            value=self.config_manager.get("refresh_interval", 300)
        )

        interval_frame = ctk.CTkFrame(refresh_interval_section, fg_color="transparent")
        interval_frame.pack(fill="x", pady=5)

        interval_slider = ctk.CTkSlider(
            interval_frame,
            from_=60,
            to=600,
            variable=self.refresh_interval_var,
            command=self._on_interval_change
        )
        interval_slider.pack(side="left", fill="x", expand=True)

        self.interval_label = ctk.CTkLabel(
            interval_frame,
            text="5 min",
            width=60
        )
        self.interval_label.pack(side="left", padx=(10, 0))

        # 3. عدد السجلات في الصفحة
        page_size_section = self._create_section(
            content_frame,
            self.lang_manager.get("records_per_page", "Records per Page")
        )

        self.page_size_var = ctk.StringVar(
            value=str(self.config_manager.get("records_per_page", 100))
        )
        page_sizes = ["50", "100", "200", "500"]
        page_size_menu = ctk.CTkOptionMenu(
            page_size_section,
            values=page_sizes,
            variable=self.page_size_var,
            command=self._on_setting_change
        )
        page_size_menu.pack(fill="x", pady=5)

        # 4. التحميل الكسول
        lazy_loading_section = self._create_section(
            content_frame,
            self.lang_manager.get("lazy_loading", "Lazy Loading")
        )

        self.lazy_loading_var = ctk.BooleanVar(
            value=self.config_manager.get("enable_lazy_loading", True)
        )
        lazy_loading_switch = ctk.CTkSwitch(
            lazy_loading_section,
            text=self.lang_manager.get("enable_lazy_loading", "Load data on demand"),
            variable=self.lazy_loading_var,
            command=self._on_setting_change
        )
        lazy_loading_switch.pack(anchor="w", pady=5)

    def _create_advanced_tab(self):
        """إنشاء تبويب الإعدادات المتقدمة"""
        tab = self.tabview.tab(self.lang_manager.get("advanced", "Advanced"))

        content_frame = ctk.CTkScrollableFrame(tab, height=300)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 1. وضع المطور
        dev_section = self._create_section(
            content_frame,
            self.lang_manager.get("developer_mode", "Developer Mode")
        )

        self.dev_mode_var = ctk.BooleanVar(
            value=self.config_manager.get("developer_mode", False)
        )
        dev_mode_switch = ctk.CTkSwitch(
            dev_section,
            text=self.lang_manager.get("enable_dev_mode", "Show debug information"),
            variable=self.dev_mode_var,
            command=self._on_setting_change
        )
        dev_mode_switch.pack(anchor="w", pady=5)

        # 2. تصدير الإعدادات
        export_section = self._create_section(
            content_frame,
            self.lang_manager.get("export_settings", "Export Settings")
        )

        export_btn = ctk.CTkButton(
            export_section,
            text=self.lang_manager.get("export_to_file", "Export to File"),
            command=self._export_settings,
            width=150
        )
        export_btn.pack(pady=5)

        # 3. استيراد الإعدادات
        import_section = self._create_section(
            content_frame,
            self.lang_manager.get("import_settings", "Import Settings")
        )

        import_btn = ctk.CTkButton(
            import_section,
            text=self.lang_manager.get("import_from_file", "Import from File"),
            command=self._import_settings,
            width=150,
            fg_color="transparent",
            border_width=2
        )
        import_btn.pack(pady=5)

        # 4. إعادة تعيين الإعدادات
        reset_section = self._create_section(
            content_frame,
            self.lang_manager.get("reset_settings", "Reset Settings")
        )

        reset_btn = ctk.CTkButton(
            reset_section,
            text=self.lang_manager.get("reset_to_default", "Reset to Default"),
            command=self._reset_settings,
            width=150,
            fg_color="red",
            hover_color="darkred"
        )
        reset_btn.pack(pady=5)

    def _create_section(self, parent, title):
        """إنشاء قسم في الإعدادات"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=(0, 15))

        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title_label.pack(fill="x", padx=15, pady=(10, 5))

        content_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=15, pady=(0, 10))

        return content_frame

    def _create_action_buttons(self, parent):
        """إنشاء أزرار الإجراءات"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        button_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 20))

        # زر الحفظ
        save_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("save_settings", "Save Settings"),
            command=self._save_settings,
            width=120
        )
        save_btn.pack(side="left", padx=(0, 10))

        # زر التطبيق
        apply_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("apply", "Apply"),
            command=self._apply_settings,
            width=120,
            fg_color="green"
        )
        apply_btn.pack(side="left", padx=(0, 10))

        # زر الإلغاء
        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self._cancel_settings,
            width=120,
            fg_color="gray"
        )
        cancel_btn.pack(side="left")

    def _load_current_settings(self):
        """تحميل الإعدادات الحالية"""
        # المظهر
        current_mode = self.theme_manager.get_current_appearance_mode()
        self.appearance_var.set(current_mode.capitalize())

        # حجم الخط
        font_size = self.config_manager.get("font_size", 14)
        self.font_size_var.set(font_size)
        self._update_font_preview(font_size)

        # الأداء
        self.auto_refresh_var.set(self.config_manager.get("auto_refresh", True))
        self.refresh_interval_var.set(self.config_manager.get("refresh_interval", 300))
        self._update_interval_label(self.refresh_interval_var.get())
        self.page_size_var.set(str(self.config_manager.get("records_per_page", 100)))
        self.lazy_loading_var.set(self.config_manager.get("enable_lazy_loading", True))

        # متقدم
        self.dev_mode_var.set(self.config_manager.get("developer_mode", False))

    def _on_appearance_change(self, choice):
        """معالج تغيير المظهر"""
        self.settings_changed = True
        # معاينة فورية آمنة للـ appearance mode فقط
        try:
            ctk.set_appearance_mode(choice.lower())
        except Exception as e:
            logger.error(f"خطأ في تطبيق وضع المظهر: {e}")

    def _on_color_change(self, choice):
        """معالج تغيير اللون"""
        self.settings_changed = True

        # لا تطبق الثيم مباشرة
        # فقط أظهر رسالة تحذيرية
        if hasattr(self, 'theme_warning_label'):
            self.theme_warning_label.configure(
                text=self.lang_manager.get(
                    "theme_will_apply_on_restart",
                    "⚠️ سيتم تطبيق الثيم بعد إعادة التشغيل"
                )
            )

    def _on_font_size_change(self, value):
        """معالج تغيير حجم الخط"""
        self.settings_changed = True
        self._update_font_preview(int(value))

    def _on_interval_change(self, value):
        """معالج تغيير فترة التحديث"""
        self.settings_changed = True
        self._update_interval_label(int(value))

    def _on_setting_change(self, *args):
        """معالج عام لتغيير الإعدادات"""
        self.settings_changed = True

    def _update_font_preview(self, size):
        """تحديث معاينة حجم الخط"""
        self.font_size_label.configure(text=f"{int(size)}px")
        self.preview_label.configure(font=ctk.CTkFont(size=int(size)))

    def _update_interval_label(self, seconds):
        """تحديث تسمية فترة التحديث"""
        minutes = seconds // 60
        self.interval_label.configure(text=f"{minutes} min")

    def _save_settings(self):
        """حفظ جميع الإعدادات"""
        try:
            # تذكر الثيم القديم للمقارنة
            old_theme = self.config_manager.get("color_theme", "blue")

            # حفظ المظهر
            self.config_manager.set("appearance_mode", self.appearance_var.get().lower())
            self.config_manager.set("font_size", int(self.font_size_var.get()))

            # لا نغير الثيم من هنا لتجنب التجمد
            # new_theme = self.color_var.get()
            # self.config_manager.set("color_theme", new_theme)

            # حفظ الأداء
            self.config_manager.set("auto_refresh", self.auto_refresh_var.get())
            self.config_manager.set("refresh_interval", self.refresh_interval_var.get())
            self.config_manager.set("records_per_page", int(self.page_size_var.get()))
            self.config_manager.set("enable_lazy_loading", self.lazy_loading_var.get())

            # حفظ المتقدم
            self.config_manager.set("developer_mode", self.dev_mode_var.get())

            # تطبيق الإعدادات الآمنة فقط
            self.theme_manager.apply_appearance_mode(self.appearance_var.get().lower())

            # رسالة النجاح
            messagebox.showinfo(
                self.lang_manager.get("success", "Success"),
                self.lang_manager.get("settings_saved", "Settings saved successfully")
            )

            self.settings_changed = False
            self.destroy()

        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات: {e}")
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                str(e)
            )

    def _apply_settings(self):
        """تطبيق الإعدادات بدون إغلاق النافذة"""
        self._save_settings()
        self.settings_changed = False

    def _cancel_settings(self):
        """إلغاء التغييرات"""
        if self.settings_changed:
            if messagebox.askyesno(
                self.lang_manager.get("confirm", "Confirm"),
                self.lang_manager.get("discard_changes", "Discard unsaved changes?")
            ):
                # إعادة الإعدادات الأصلية للـ appearance mode فقط
                original_mode = self.config_manager.get("appearance_mode", "light")
                try:
                    self.theme_manager.apply_appearance_mode(original_mode)
                except Exception as e:
                    logger.error(f"خطأ في إعادة وضع المظهر: {e}")
                self.destroy()
        else:
            self.destroy()

    def _export_settings(self):
        """تصدير الإعدادات إلى ملف"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                settings = self.config_manager.get_all_settings()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)

                messagebox.showinfo(
                    self.lang_manager.get("success", "Success"),
                    self.lang_manager.get("settings_exported", "Settings exported successfully")
                )
            except Exception as e:
                logger.error(f"خطأ في تصدير الإعدادات: {e}")
                messagebox.showerror(
                    self.lang_manager.get("error", "Error"),
                    str(e)
                )

    def _import_settings(self):
        """استيراد الإعدادات من ملف"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # تطبيق الإعدادات
                for key, value in settings.items():
                    self.config_manager.set(key, value)

                messagebox.showinfo(
                    self.lang_manager.get("success", "Success"),
                    self.lang_manager.get("settings_imported", "Settings imported successfully")
                )

                # إعادة تحميل الإعدادات في النافذة
                self._load_current_settings()

            except Exception as e:
                logger.error(f"خطأ في استيراد الإعدادات: {e}")
                messagebox.showerror(
                    self.lang_manager.get("error", "Error"),
                    str(e)
                )

    def _reset_settings(self):
        """إعادة تعيين الإعدادات إلى القيم الافتراضية"""
        if messagebox.askyesno(
            self.lang_manager.get("confirm", "Confirm"),
            self.lang_manager.get("confirm_reset", "Reset all settings to default values?")
        ):
            try:
                # حذف ملف الإعدادات
                if os.path.exists("config/settings.yaml"):
                    os.remove("config/settings.yaml")

                # إعادة تحميل الإعدادات الافتراضية
                self.config_manager.reload()

                messagebox.showinfo(
                    self.lang_manager.get("success", "Success"),
                    self.lang_manager.get("settings_reset", "Settings reset to default")
                )

                self.destroy()

            except Exception as e:
                logger.error(f"خطأ في إعادة تعيين الإعدادات: {e}")
                messagebox.showerror(
                    self.lang_manager.get("error", "Error"),
                    str(e)
                )


class LanguageWindow(ctk.CTkToplevel):
    """نافذة اختيار اللغة المحسنة"""

    def __init__(self, parent, lang_manager, language_callback):
        super().__init__(parent)

        self.lang_manager = lang_manager
        self.language_callback = language_callback

        # إعدادات النافذة
        self.title(lang_manager.get("language_title", "Select Language"))
        self.geometry("350x500")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """توسيط النافذة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """بناء واجهة اختيار اللغة"""
        # العنوان
        title_frame = ctk.CTkFrame(self, height=80)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)

        title_label = ctk.CTkLabel(
            title_frame,
            text=self.lang_manager.get("language_title", "Select Language"),
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(expand=True)

        # الوصف
        desc_label = ctk.CTkLabel(
            self,
            text=self.lang_manager.get("language_desc", "Choose your preferred language"),
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40")
        )
        desc_label.pack(pady=(0, 20))

        # قائمة اللغات المتاحة من ملفات الترجمة
        languages = self._get_available_languages()

        # إطار اللغات
        lang_frame = ctk.CTkScrollableFrame(self, height=280)
        lang_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.selected_lang = ctk.StringVar(value=self.lang_manager.current_lang)

        for code, name, flag, native_name in languages:
            self._create_language_option(lang_frame, code, name, flag, native_name)

        # أزرار الإجراءات
        button_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        button_frame.pack(fill="x", side="bottom", padx=20, pady=(0, 20))

        apply_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("apply", "Apply"),
            command=self._apply_language,
            width=100
        )
        apply_btn.pack(side="left", padx=(0, 10))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self.destroy,
            width=100,
            fg_color="gray"
        )
        cancel_btn.pack(side="left")

    def _get_available_languages(self):
        """الحصول على اللغات المتاحة من مجلد locales"""
        languages = []

        # اللغات الافتراضية
        default_languages = [
            ("ar", "Arabic", "🇸🇦", "العربية"),
            ("en", "English", "🇬🇧", "English")
        ]

        # البحث في مجلد locales
        locales_dir = "locales"
        if os.path.exists(locales_dir):
            for file in os.listdir(locales_dir):
                if file.endswith('.yaml'):
                    lang_code = file.replace('.yaml', '')

                    # البحث عن معلومات اللغة في القائمة الافتراضية
                    for code, name, flag, native in default_languages:
                        if code == lang_code:
                            languages.append((code, name, flag, native))
                            break

        # إذا لم نجد أي لغات، استخدم الافتراضية
        if not languages:
            languages = default_languages[:2]  # العربية والإنجليزية فقط

        return languages

    def _create_language_option(self, parent, code, name, flag, native_name):
        """إنشاء خيار لغة"""
        option_frame = ctk.CTkFrame(parent, height=60)
        option_frame.pack(fill="x", pady=5)

        # زر الاختيار
        radio_btn = ctk.CTkRadioButton(
            option_frame,
            text="",
            variable=self.selected_lang,
            value=code,
            width=20
        )
        radio_btn.pack(side="left", padx=(15, 10))

        # العلم
        flag_label = ctk.CTkLabel(
            option_frame,
            text=flag,
            font=ctk.CTkFont(size=24)
        )
        flag_label.pack(side="left", padx=(0, 10))

        # معلومات اللغة
        info_frame = ctk.CTkFrame(option_frame, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)

        # اسم اللغة بالإنجليزية
        name_label = ctk.CTkLabel(
            info_frame,
            text=name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        name_label.pack(fill="x", pady=(10, 2))

        # اسم اللغة الأصلي
        native_label = ctk.CTkLabel(
            info_frame,
            text=native_name,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
            anchor="w"
        )
        native_label.pack(fill="x", pady=(0, 10))

        # تحديد اللغة الحالية
        if code == self.lang_manager.current_lang:
            current_label = ctk.CTkLabel(
                option_frame,
                text=self.lang_manager.get("current", "Current"),
                font=ctk.CTkFont(size=11),
                text_color="green"
            )
            current_label.pack(side="right", padx=15)

    def _apply_language(self):
        """تطبيق اللغة المختارة"""
        new_lang = self.selected_lang.get()
        if new_lang != self.lang_manager.current_lang:
            self.language_callback(new_lang)
        self.destroy()


class AboutWindow(ctk.CTkToplevel):
    """نافذة حول التطبيق المحسنة"""

    def __init__(self, parent, lang_manager):
        super().__init__(parent)

        self.lang_manager = lang_manager

        # إعدادات النافذة
        self.title(lang_manager.get("about", "About"))
        self.geometry("450x550")
        self.resizable(False, False)

        # جعل النافذة مشروطة
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._center_window()

    def _center_window(self):
        """توسيط النافذة"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _build_ui(self):
        """بناء واجهة حول التطبيق"""
        # الحاوية الرئيسية
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True)

        # الشعار والعنوان
        logo_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        logo_frame.pack(pady=30)

        # خلفية دائرية للشعار
        logo_bg = ctk.CTkFrame(
            logo_frame,
            width=100,
            height=100,
            corner_radius=50,
            fg_color=("#1f538d", "#4a9eff")
        )
        logo_bg.pack()
        logo_bg.pack_propagate(False)

        logo_text = ctk.CTkLabel(
            logo_bg,
            text="FTS",
            font=ctk.CTkFont(size=36, weight="bold"),
            text_color="white"
        )
        logo_text.place(relx=0.5, rely=0.5, anchor="center")

        # اسم التطبيق
        app_name = ctk.CTkLabel(
            main_frame,
            text="FTS TRAVELS",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=("#1f538d", "#4a9eff")
        )
        app_name.pack()

        app_subtitle = ctk.CTkLabel(
            main_frame,
            text="Sales Manager",
            font=ctk.CTkFont(size=16),
            text_color=("gray60", "gray40")
        )
        app_subtitle.pack(pady=(0, 20))

        # معلومات الإصدار
        version_frame = ctk.CTkFrame(main_frame)
        version_frame.pack(fill="x", padx=40, pady=10)

        info_items = [
            ("version", "Version", "2.0.0"),
            ("build", "Build", "2024.01.15"),
            ("developer", "Developer", "FTS Development Team"),
            ("license", "License", "Proprietary")
        ]

        for key, label, value in info_items:
            row_frame = ctk.CTkFrame(version_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=5)

            label_widget = ctk.CTkLabel(
                row_frame,
                text=f"{self.lang_manager.get(key, label)}:",
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
                width=100
            )
            label_widget.pack(side="left", padx=(20, 10))

            value_widget = ctk.CTkLabel(
                row_frame,
                text=value,
                anchor="w"
            )
            value_widget.pack(side="left")

        # الوصف
        desc_frame = ctk.CTkFrame(main_frame)
        desc_frame.pack(fill="x", padx=40, pady=20)

        description = self.lang_manager.get(
            "app_description",
            "FTS Travels Sales Manager is an integrated system for managing tourism sales and bookings.\n\n"
            "The system provides powerful tools for managing customers, bookings, and financial reports."
        )

        desc_label = ctk.CTkLabel(
            desc_frame,
            text=description,
            justify="center",
            wraplength=350,
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=20)

        # روابط
        links_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        links_frame.pack(pady=10)

        website_btn = ctk.CTkButton(
            links_frame,
            text="🌐 " + self.lang_manager.get("website", "Website"),
            width=120,
            command=lambda: webbrowser.open("https://www.ftstravels.com")
        )
        website_btn.pack(side="left", padx=5)

        support_btn = ctk.CTkButton(
            links_frame,
            text="📧 " + self.lang_manager.get("support", "Support"),
            width=120,
            command=lambda: webbrowser.open("mailto:support@ftstravels.com")
        )
        support_btn.pack(side="left", padx=5)

        # حقوق النشر
        copyright_label = ctk.CTkLabel(
            main_frame,
            text="© 2024 FTS - All Rights Reserved",
            font=ctk.CTkFont(size=10),
            text_color=("gray60", "gray40")
        )
        copyright_label.pack(pady=(20, 0))

        # زر الإغلاق
        close_btn = ctk.CTkButton(
            main_frame,
            text=self.lang_manager.get("close", "Close"),
            command=self.destroy,
            width=120
        )
        close_btn.pack(pady=20)