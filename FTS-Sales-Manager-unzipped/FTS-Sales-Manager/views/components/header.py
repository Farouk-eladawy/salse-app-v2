# -*- coding: utf-8 -*-
"""
views/components/header.py

مكون الهيدر العلوي المحسن بتصميم احترافي
"""

import customtkinter as ctk
import tkinter as tk
from typing import Callable, Dict, Any, Optional
import webbrowser
from datetime import datetime
import weakref

from core.language_manager import LanguageManager
from core.logger import logger

# استيراد نوافذ الحوار المحدثة
from .dropdown_dialogs import (
    ProfileWindow,
    SettingsWindow,
    LanguageWindow,
    AboutWindow
)


class DropdownMenu(ctk.CTkToplevel):
    """قائمة منسدلة احترافية مع تأثيرات بصرية وإدارة محسّنة للذاكرة"""

    def __init__(self, parent, x, y, lang_manager, header_component, **kwargs):
        super().__init__(parent, **kwargs)

        self.lang_manager = lang_manager
        # استخدام weakref لتجنب المراجع الدائرية
        self.header_component_ref = weakref.ref(header_component)
        self._after_ids = []  # لتتبع جميع after callbacks
        self._fade_out_id = None

        # إعدادات النافذة
        self.overrideredirect(True)
        self.attributes("-topmost", True)

        # تأثير الشفافية
        self.attributes("-alpha", 0.0)

        # الموضع
        self.geometry(f"+{x}+{y}")

        # الإطار الرئيسي مع ظل
        self.shadow_frame = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=("#000000", "#000000"),
            bg_color="transparent"
        )
        self.shadow_frame.pack(fill="both", expand=True, padx=2, pady=2)

        # الإطار الرئيسي
        self.main_frame = ctk.CTkFrame(
            self.shadow_frame,
            corner_radius=10,
            fg_color=("#ffffff", "#2b2b2b"),
            border_width=1,
            border_color=("#e0e0e0", "#444444")
        )
        self.main_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # بناء العناصر
        self._build_items()

        # تأثير الظهور التدريجي
        self._fade_in()

        # ربط النقر خارج القائمة لإغلاقها
        self.bind("<FocusOut>", lambda e: self._start_fade_out())

        # ربط حركة الماوس للتأثيرات
        self.bind("<Leave>", lambda e: self._start_fade_out())
        self.bind("<Enter>", lambda e: self._cancel_fade_out())

        # تسجيل callback للتنظيف عند الإغلاق
        self.protocol("WM_DELETE_WINDOW", self._cleanup_and_destroy)

    def _fade_in(self):
        """تأثير الظهور التدريجي"""
        try:
            if not self.winfo_exists():
                return

            alpha = float(self.attributes("-alpha"))
            if alpha < 0.95:
                self.attributes("-alpha", alpha + 0.1)
                after_id = self.after(10, self._fade_in)
                self._after_ids.append(after_id)
        except (tk.TclError, AttributeError):
            # النافذة تم إغلاقها
            pass

    def _fade_out(self):
        """تأثير الاختفاء التدريجي"""
        try:
            if not self.winfo_exists():
                return

            alpha = float(self.attributes("-alpha"))
            if alpha > 0.1:
                self.attributes("-alpha", alpha - 0.1)
                after_id = self.after(10, self._fade_out)
                self._after_ids.append(after_id)
            else:
                self._cleanup_and_destroy()
        except (tk.TclError, AttributeError):
            # النافذة تم إغلاقها
            self._cleanup_and_destroy()

    def _start_fade_out(self):
        """بدء الاختفاء بعد تأخير"""
        try:
            if self._fade_out_id:
                self.after_cancel(self._fade_out_id)

            self._fade_out_id = self.after(200, self._check_mouse_position)
            self._after_ids.append(self._fade_out_id)
        except tk.TclError:
            pass

    def _cancel_fade_out(self):
        """إلغاء الاختفاء"""
        try:
            if self._fade_out_id:
                self.after_cancel(self._fade_out_id)
                self._fade_out_id = None
        except tk.TclError:
            pass

    def _check_mouse_position(self):
        """التحقق من موضع الماوس"""
        try:
            if not self.winfo_exists():
                return

            # الحصول على موضع الماوس
            x = self.winfo_pointerx()
            y = self.winfo_pointery()

            # الحصول على حدود النافذة
            x1 = self.winfo_rootx()
            y1 = self.winfo_rooty()
            x2 = x1 + self.winfo_width()
            y2 = y1 + self.winfo_height()

            # التحقق من الموضع
            if not (x1 <= x <= x2 and y1 <= y <= y2):
                self._fade_out()
            else:
                self._start_fade_out()

        except (tk.TclError, AttributeError):
            # النافذة تم إغلاقها
            self._cleanup_and_destroy()

    def _cleanup_and_destroy(self):
        """تنظيف الموارد وإغلاق النافذة"""
        try:
            # إلغاء جميع after callbacks
            for after_id in self._after_ids:
                try:
                    self.after_cancel(after_id)
                except:
                    pass

            # إلغاء fade_out_id إن وجد
            if self._fade_out_id:
                try:
                    self.after_cancel(self._fade_out_id)
                except:
                    pass

            # تدمير النافذة
            if self.winfo_exists():
                self.destroy()

        except:
            # تجاهل أي أخطاء في التنظيف
            pass

    def _build_items(self):
        """بناء عناصر القائمة بتصميم احترافي"""
        header_component = self.header_component_ref()
        if not header_component:
            return

        # رأس القائمة مع معلومات المستخدم
        header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color=("#f8f9fa", "#1e1e1e"),
            corner_radius=10
        )
        header_frame.pack(fill="x", padx=10, pady=10)

        # صورة المستخدم (placeholder)
        user_avatar = ctk.CTkLabel(
            header_frame,
            text="👤",
            font=ctk.CTkFont(size=40),
            width=60,
            height=60,
            fg_color=("#e0e0e0", "#3a3a3a"),
            corner_radius=30
        )
        user_avatar.pack(pady=10)

        # اسم المستخدم
        username = header_component.user_record.get('fields', {}).get('Username', 'User')
        user_label = ctk.CTkLabel(
            header_frame,
            text=username,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        user_label.pack()

        # الدور
        role = header_component.user_record.get('fields', {}).get('Role', '')
        if role:
            role_label = ctk.CTkLabel(
                header_frame,
                text=header_component._translate_role(role),
                font=ctk.CTkFont(size=12),
                text_color=("#666666", "#999999")
            )
            role_label.pack(pady=(0, 10))

        # خط فاصل أنيق
        separator = ctk.CTkFrame(
            self.main_frame,
            height=1,
            fg_color=("#e0e0e0", "#444444")
        )
        separator.pack(fill="x", padx=15, pady=5)

        # عناصر القائمة
        items = [
            ("👤", "profile", self._on_profile, "primary"),
            ("⚙️", "settings", self._on_settings, "default"),
            ("🌐", "language", self._on_language, "default"),
            ("ℹ️", "about", self._on_about, "default"),
            ("separator", None, None, None),
            ("🚪", "logout", self._on_logout, "danger")
        ]

        # إطار العناصر
        items_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        items_frame.pack(fill="both", expand=True, padx=5, pady=5)

        for icon, key, command, style in items:
            if icon == "separator":
                separator = ctk.CTkFrame(
                    items_frame,
                    height=1,
                    fg_color=("#e0e0e0", "#444444")
                )
                separator.pack(fill="x", padx=10, pady=8)
            else:
                self._create_menu_item(items_frame, icon, key, command, style)

    def _create_menu_item(self, parent, icon, key, command, style):
        """إنشاء عنصر قائمة احترافي"""
        text = self.lang_manager.get(f"menu_{key}", key.title())

        # إطار العنصر
        item_frame = ctk.CTkFrame(
            parent,
            height=40,
            fg_color="transparent",
            corner_radius=8
        )
        item_frame.pack(fill="x", padx=5, pady=2)

        # تحديد الألوان حسب النمط
        if style == "primary":
            hover_color = ("#e3f2fd", "#1976d2")
            text_color = ("#1976d2", "#90caf9")
        elif style == "danger":
            hover_color = ("#ffebee", "#b71c1c")
            text_color = ("#d32f2f", "#ff5252")
        else:
            hover_color = ("#f5f5f5", "#3a3a3a")
            text_color = ("#333333", "#ffffff")

        # الزر
        btn = ctk.CTkButton(
            item_frame,
            text=f"{icon}  {text}",
            anchor="w",
            height=36,
            fg_color="transparent",
            hover_color=hover_color,
            text_color=text_color,
            font=ctk.CTkFont(size=13),
            command=command,
            corner_radius=8
        )
        btn.pack(fill="both", expand=True)

        # تأثير hover إضافي
        def on_enter(e):
            btn.configure(font=ctk.CTkFont(size=13, weight="bold"))

        def on_leave(e):
            btn.configure(font=ctk.CTkFont(size=13))

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _on_profile(self):
        """معالج الملف الشخصي"""
        self._cleanup_and_destroy()
        header_component = self.header_component_ref()
        if not header_component:
            return

        controller = header_component.controller
        if controller:
            profile_window = ProfileWindow(
                header_component.winfo_toplevel(),
                controller,
                self.lang_manager
            )
        else:
            logger.error("لا يمكن فتح نافذة الملف الشخصي - المتحكم غير متاح")

    def _on_settings(self):
        """معالج الإعدادات"""
        self._cleanup_and_destroy()
        header_component = self.header_component_ref()
        if not header_component:
            return

        controller = header_component.controller
        if controller and hasattr(controller, 'config_mgr') and hasattr(controller, 'theme_manager'):
            settings_window = SettingsWindow(
                header_component.winfo_toplevel(),
                self.lang_manager,
                controller.config_mgr,
                controller.theme_manager
            )
        else:
            logger.error("لا يمكن فتح نافذة الإعدادات - المتحكم غير متاح")

    def _on_language(self):
        """معالج تغيير اللغة"""
        self._cleanup_and_destroy()
        header_component = self.header_component_ref()
        if not header_component:
            return

        def change_language(new_lang):
            if hasattr(header_component, 'on_language_change'):
                header_component.on_language_change(new_lang)
            else:
                self.lang_manager.set_language(new_lang)
                header_component.update_texts(self.lang_manager)

        language_window = LanguageWindow(
            header_component.winfo_toplevel(),
            self.lang_manager,
            change_language
        )

    def _on_about(self):
        """معالج حول التطبيق"""
        self._cleanup_and_destroy()
        header_component = self.header_component_ref()
        if not header_component:
            return

        about_window = AboutWindow(
            header_component.winfo_toplevel(),
            self.lang_manager
        )

    def _on_logout(self):
        """معالج تسجيل الخروج"""
        self._cleanup_and_destroy()
        header_component = self.header_component_ref()
        if not header_component:
            return

        from tkinter import messagebox
        if messagebox.askyesno(
            self.lang_manager.get("confirm", "Confirm"),
            self.lang_manager.get("confirm_logout", "Are you sure you want to logout?")
        ):
            logger.info("بدء عملية تسجيل الخروج...")

            controller = header_component.controller
            if controller:
                try:
                    if hasattr(controller, 'save_current_state'):
                        controller.save_current_state()

                    if hasattr(controller, 'cleanup'):
                        controller.cleanup()

                    if hasattr(controller, 'on_logout'):
                        controller.on_logout()

                    main_window = header_component.winfo_toplevel()
                    main_window.destroy()

                    if hasattr(controller, 'run'):
                        controller.run()

                except Exception as e:
                    logger.error(f"خطأ في تسجيل الخروج: {e}")
                    messagebox.showerror(
                        self.lang_manager.get("error", "Error"),
                        self.lang_manager.get("logout_error", "An error occurred during logout")
                    )
            else:
                header_component.winfo_toplevel().destroy()


class HeaderComponent(ctk.CTkFrame):
    """مكون الهيدر المحسن بتصميم احترافي"""

    def __init__(
        self,
        parent,
        lang_manager: LanguageManager,
        user_record: Dict[str, Any],
        on_search: Callable = None,
        on_refresh: Callable = None,
        on_menu_click: Callable = None,
        on_language_change: Callable = None,
        on_theme_change: Callable = None,
        controller: Any = None,
        **kwargs
    ):
        # إعدادات احترافية للإطار
        kwargs.setdefault('height', 80)
        kwargs.setdefault('corner_radius', 0)
        kwargs.setdefault('fg_color', ("#ffffff", "#2b2b2b"))

        super().__init__(parent, **kwargs)
        self.pack_propagate(False)

        self.lang_manager = lang_manager
        self.user_record = user_record
        self.on_search = on_search
        self.on_refresh = on_refresh
        self.on_language_change = on_language_change
        self.on_theme_change = on_theme_change
        self.controller = controller

        # متغير للقائمة المنسدلة
        self.dropdown_menu: Optional[DropdownMenu] = None

        # إطار الجانب الأيمن للأزرار الإضافية
        self.right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.right_frame.pack(side="right", fill="y", padx=20)

        self._build_ui()

    def change_theme_with_restart(self, new_theme):
        """تغيير الثيم مع طلب إعادة التشغيل"""
        try:
            # حفظ الثيم الجديد
            self.controller.config_mgr.set("color_theme", new_theme)

            # عرض رسالة
            result = messagebox.askyesno(
                self.lang_manager.get("restart_required", "Restart Required"),
                self.lang_manager.get(
                    "restart_to_apply_theme",
                    f"تم حفظ الثيم '{new_theme}'.\n\n"
                    "يجب إعادة تشغيل التطبيق لتطبيق التغييرات.\n"
                    "هل تريد إعادة التشغيل الآن؟"
                )
            )

            if result:
                # إعادة تشغيل التطبيق
                import sys
                import os
                python = sys.executable
                os.execl(python, python, *sys.argv)

        except Exception as e:
            logger.error(f"خطأ في تغيير الثيم: {e}")
            messagebox.showerror(
                self.lang_manager.get("error", "Error"),
                str(e)
            )

    def _build_ui(self):
        """بناء الواجهة المحسنة"""
        # الشعار المحسن
        self._create_enhanced_logo()

        # شريط البحث المحسن
        self._create_enhanced_search_bar()

        # منطقة المستخدم المحسنة
        self._create_enhanced_user_area()

    def _create_enhanced_logo(self):
        """إنشاء شعار محسن احترافي"""
        # إطار الشعار
        logo_frame = ctk.CTkFrame(
            self,
            width=200,
            fg_color="transparent"
        )
        logo_frame.pack(side="left", fill="y", padx=(20, 10))
        logo_frame.pack_propagate(False)

        # إطار محتوى الشعار
        logo_content = ctk.CTkFrame(logo_frame, fg_color="transparent")
        logo_content.pack(expand=True)

        # إطار الأيقونة والنص
        logo_inner = ctk.CTkFrame(logo_content, fg_color="transparent")
        logo_inner.pack()

        # أيقونة الشركة
        logo_icon_bg = ctk.CTkFrame(
            logo_inner,
            width=50,
            height=50,
            corner_radius=25,
            fg_color=("#1976d2", "#2196f3")
        )
        logo_icon_bg.pack(side="left", padx=(0, 10))
        logo_icon_bg.pack_propagate(False)

        logo_icon = ctk.CTkLabel(
            logo_icon_bg,
            text="FTS",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="white"
        )
        logo_icon.place(relx=0.5, rely=0.5, anchor="center")

        # نصوص الشعار
        text_frame = ctk.CTkFrame(logo_inner, fg_color="transparent")
        text_frame.pack(side="left")

        # النص الرئيسي
        main_text = ctk.CTkLabel(
            text_frame,
            text="FTS TRAVELS",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("#1976d2", "#2196f3")
        )
        main_text.pack(anchor="w")

        # النص الفرعي
        sub_text = ctk.CTkLabel(
            text_frame,
            text="Sales Manager Pro",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#999999")
        )
        sub_text.pack(anchor="w", pady=(0, 2))

    def _create_enhanced_search_bar(self):
        """إنشاء شريط بحث محسن احترافي"""
        search_container = ctk.CTkFrame(self, fg_color="transparent")
        search_container.pack(side="left", fill="both", expand=True, padx=20)

        # إطار البحث الرئيسي
        search_frame = ctk.CTkFrame(
            search_container,
            height=45,
            fg_color=("#f5f5f5", "#333333"),
            corner_radius=25,
            border_width=2,
            border_color=("#e0e0e0", "#444444")
        )
        search_frame.pack(expand=True, fill="x", pady=15)
        search_frame.pack_propagate(False)

        # أيقونة البحث
        search_icon = ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=18),
            text_color=("#666666", "#999999")
        )
        search_icon.pack(side="left", padx=(15, 5))

        # حقل البحث
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text=self.lang_manager.get("search_placeholder", "Search bookings..."),
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.search_entry.pack(side="left", fill="both", expand=True, padx=(5, 10))

        # أزرار الإجراءات
        actions_frame = ctk.CTkFrame(search_frame, fg_color="transparent")
        actions_frame.pack(side="right", padx=(0, 10))

        # زر البحث
        search_btn = ctk.CTkButton(
            actions_frame,
            text="",
            image=None,  # يمكن إضافة أيقونة هنا
            width=35,
            height=35,
            corner_radius=17,
            fg_color=("#1976d2", "#2196f3"),
            hover_color=("#1565c0", "#1e88e5"),
            command=self._on_search
        )
        search_btn.pack(side="left", padx=2)

        # أيقونة البحث للزر
        search_btn_icon = ctk.CTkLabel(
            search_btn,
            text="→",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        search_btn_icon.place(relx=0.5, rely=0.5, anchor="center")

        # زر المسح
        if self.search_var.get():
            clear_btn = ctk.CTkButton(
                actions_frame,
                text="✕",
                width=30,
                height=30,
                corner_radius=15,
                fg_color="transparent",
                hover_color=("#e0e0e0", "#444444"),
                text_color=("#666666", "#999999"),
                command=self.clear_search
            )
            clear_btn.pack(side="left", padx=2)

        # زر التحديث
        if self.on_refresh:
            refresh_btn = ctk.CTkButton(
                actions_frame,
                text="↻",
                width=35,
                height=35,
                corner_radius=17,
                fg_color="transparent",
                hover_color=("#e0e0e0", "#444444"),
                text_color=("#666666", "#999999"),
                font=ctk.CTkFont(size=18),
                command=self.on_refresh
            )
            refresh_btn.pack(side="left", padx=2)

        # ربط Enter بالبحث
        self.search_entry.bind("<Return>", lambda e: self._on_search())

        # تحديث زر المسح عند الكتابة
        self.search_var.trace("w", self._update_clear_button)

    def _update_clear_button(self, *args):
        """تحديث ظهور زر المسح"""
        # يمكن تنفيذ منطق إظهار/إخفاء زر المسح هنا
        pass

    def _create_enhanced_user_area(self):
        """إنشاء منطقة مستخدم محسنة احترافية"""
        user_container = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        user_container.pack(side="left", fill="y")

        # إطار معلومات المستخدم
        user_info_frame = ctk.CTkFrame(
            user_container,
            fg_color=("#f8f9fa", "#1e1e1e"),
            corner_radius=25,
            border_width=1,
            border_color=("#e0e0e0", "#444444")
        )
        user_info_frame.pack(side="left", padx=10, pady=15)

        # إطار المحتوى
        content_frame = ctk.CTkFrame(user_info_frame, fg_color="transparent")
        content_frame.pack(padx=15, pady=8)

        # صورة المستخدم
        avatar_frame = ctk.CTkFrame(
            content_frame,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=("#e0e0e0", "#3a3a3a")
        )
        avatar_frame.pack(side="left", padx=(0, 10))
        avatar_frame.pack_propagate(False)

        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=ctk.CTkFont(size=20)
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # معلومات المستخدم
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(side="left", padx=(0, 10))

        # اسم المستخدم
        username = self.user_record.get('fields', {}).get('Username', 'User')
        username_label = ctk.CTkLabel(
            info_frame,
            text=username,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=("#333333", "#ffffff")
        )
        username_label.pack(anchor="w")

        # الدور
        role = self.user_record.get('fields', {}).get('Role', '')
        if role:
            role_text = self._translate_role(role)
            self.role_label = ctk.CTkLabel(
                info_frame,
                text=role_text,
                font=ctk.CTkFont(size=11),
                text_color=("#666666", "#999999")
            )
            self.role_label.pack(anchor="w")

        # زر القائمة المحسن
        self.menu_btn = ctk.CTkButton(
            content_frame,
            text="▼",
            width=30,
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color=("#e0e0e0", "#444444"),
            text_color=("#666666", "#999999"),
            font=ctk.CTkFont(size=12),
            command=self._toggle_dropdown_menu
        )
        self.menu_btn.pack(side="left")

        # تأثير hover للإطار الكامل
        def on_enter(e):
            user_info_frame.configure(border_color=("#1976d2", "#2196f3"))

        def on_leave(e):
            user_info_frame.configure(border_color=("#e0e0e0", "#444444"))

        user_info_frame.bind("<Enter>", on_enter)
        user_info_frame.bind("<Leave>", on_leave)

        # جعل الإطار كله قابل للنقر
        for widget in [user_info_frame, content_frame, info_frame, username_label]:
            widget.bind("<Button-1>", lambda e: self._toggle_dropdown_menu())

    def _toggle_dropdown_menu(self):
        """إظهار/إخفاء القائمة المنسدلة"""
        if self.dropdown_menu and hasattr(self.dropdown_menu, 'winfo_exists'):
            try:
                if self.dropdown_menu.winfo_exists():
                    self.dropdown_menu._cleanup_and_destroy()
                    self.dropdown_menu = None
                    return
            except:
                self.dropdown_menu = None

        # حساب موضع القائمة
        x = self.menu_btn.winfo_rootx() - 150
        y = self.menu_btn.winfo_rooty() + self.menu_btn.winfo_height() + 10

        # إنشاء القائمة المنسدلة
        self.dropdown_menu = DropdownMenu(
            self,
            x,
            y,
            self.lang_manager,
            self
        )

    def _translate_role(self, role):
        """ترجمة الدور"""
        return self.lang_manager.get(f"role_{role.lower()}", role)

    def _on_search(self):
        """معالج البحث"""
        if self.on_search:
            search_text = self.search_var.get().strip()
            self.on_search(search_text)

    def clear_search(self):
        """مسح البحث"""
        self.search_var.set("")
        if self.on_search:
            self.on_search("")

    def update_texts(self, lang_manager):
        """تحديث نصوص المكون"""
        self.lang_manager = lang_manager

        # تحديث placeholder البحث
        if hasattr(self, 'search_entry'):
            self.search_entry.configure(
                placeholder_text=lang_manager.get("search_placeholder", "Search bookings...")
            )

        # تحديث دور المستخدم
        if hasattr(self, 'role_label'):
            role = self.user_record.get('fields', {}).get('Role', '')
            if role:
                role_text = self._translate_role(role)
                self.role_label.configure(text=role_text)

    def refresh_theme(self):
        """تحديث الثيم"""
        # تحديث ألوان الإطار الرئيسي
        self.configure(fg_color=("#ffffff", "#2b2b2b"))

        # تحديث شريط البحث
        if hasattr(self, 'search_frame'):
            search_frame = self.search_entry.master
            if search_frame:
                search_frame.configure(
                    fg_color=("#f5f5f5", "#333333"),
                    border_color=("#e0e0e0", "#444444")
                )

        # تحديث منطقة المستخدم
        if hasattr(self, 'user_info_frame'):
            for widget in self.right_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    widget.configure(
                        fg_color=("#f8f9fa", "#1e1e1e"),
                        border_color=("#e0e0e0", "#444444")
                    )

        # إغلاق القائمة المنسدلة إذا كانت مفتوحة
        if self.dropdown_menu and self.dropdown_menu.winfo_exists():
            self.dropdown_menu.destroy()
            self.dropdown_menu = None

    def _cleanup(self):
        """تنظيف الموارد"""
        if self.dropdown_menu:
            try:
                self.dropdown_menu._cleanup_and_destroy()
            except:
                pass
            self.dropdown_menu = None

    def destroy(self):
        """تدمير المكون"""
        self._cleanup()
        super().destroy()