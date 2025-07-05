# -*- coding: utf-8 -*-
"""
views/components/sidebar.py

مكون الشريط الجانبي المحسن بتصميم احترافي
"""

import customtkinter as ctk
from typing import Callable, Dict, Any, Optional

from core.language_manager import LanguageManager


class SidebarComponent(ctk.CTkFrame):
    """مكون الشريط الجانبي المحسن بتصميم احترافي"""

    def __init__(
        self,
        parent,
        lang_manager: LanguageManager,
        theme_manager: Optional[Any] = None,
        on_navigate: Callable = None,
        **kwargs
    ):
        # إعدادات احترافية للإطار
        kwargs.setdefault('width', 280)
        kwargs.setdefault('corner_radius', 0)
        kwargs.setdefault('fg_color', ("#f8f9fa", "#1e1e1e"))

        super().__init__(parent, **kwargs)
        self.pack_propagate(False)

        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.on_navigate = on_navigate
        self.is_collapsed = False
        self.nav_buttons = []
        self.active_button = None

        self._build_ui()

    def _build_ui(self):
        """بناء الواجهة المحسنة"""
        # رأس الشريط الجانبي
        self._create_header()

        # قائمة التنقل
        self._create_navigation_section()

        # قسم الإحصائيات
        self._create_stats_section()

        # قسم الاختصارات السريعة
        self._create_quick_actions()

        # تذييل مع معلومات إضافية
        self._create_footer()

    def _create_header(self):
        """إنشاء رأس الشريط الجانبي"""
        header_frame = ctk.CTkFrame(
            self,
            height=60,
            fg_color=("#e9ecef", "#252525"),
            corner_radius=0
        )
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        # إطار المحتوى
        content_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        content_frame.pack(expand=True)

        # العنوان مع أيقونة
        title_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        title_frame.pack()

        # أيقونة القائمة
        menu_icon = ctk.CTkLabel(
            title_frame,
            text="📊",
            font=ctk.CTkFont(size=20)
        )
        menu_icon.pack(side="left", padx=(0, 8))

        # العنوان
        title_label = ctk.CTkLabel(
            title_frame,
            text=self.lang_manager.get("dashboard", "Dashboard"),
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=("#1976d2", "#2196f3")
        )
        title_label.pack(side="left")

        # زر التبديل
        self.toggle_btn = ctk.CTkButton(
            header_frame,
            text="◀",
            width=30,
            height=30,
            corner_radius=15,
            command=self._toggle_sidebar,
            fg_color="transparent",
            hover_color=("#dee2e6", "#343a40"),
            text_color=("#666666", "#999999"),
            font=ctk.CTkFont(size=14)
        )
        self.toggle_btn.pack(side="right", padx=10)

    def _create_navigation_section(self):
        """إنشاء قسم التنقل المحسن"""
        # إطار القسم
        nav_section = ctk.CTkFrame(self, fg_color="transparent")
        nav_section.pack(fill="x", padx=15, pady=(15, 0))

        # عنوان القسم
        self.nav_title = ctk.CTkLabel(
            nav_section,
            text=self.lang_manager.get("quick_navigation", "Quick Navigation"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#666666", "#999999")
        )
        self.nav_title.pack(anchor="w", pady=(0, 10))

        # إطار الأزرار
        self.nav_frame = ctk.CTkFrame(nav_section, fg_color="transparent")
        self.nav_frame.pack(fill="x")

        # عناصر التنقل
        nav_items = [
            ("🏠", "home", "Home", "primary"),
            ("📅", "today", "Today's Bookings", "info"),
            ("⏳", "pending", "Pending Bookings", "warning"),
            ("✅", "confirmed", "Confirmed Bookings", "success"),
            ("📊", "reports", "Reports", "secondary"),
        ]

        for icon, key, default_text, style in nav_items:
            text = self.lang_manager.get(f"nav_{key}", default_text)
            btn = self._create_nav_button(self.nav_frame, icon, key, text, style)
            self.nav_buttons.append((btn, icon, key, default_text, style))

    def _create_nav_button(self, parent, icon, key, text, style="default"):
        """إنشاء زر تنقل احترافي"""
        # إطار الزر
        button_frame = ctk.CTkFrame(
            parent,
            height=45,
            fg_color="transparent",
            corner_radius=10
        )
        button_frame.pack(fill="x", pady=3)

        # الزر
        btn = ctk.CTkButton(
            button_frame,
            text=f"{icon}  {text}",
            anchor="w",
            height=40,
            fg_color="transparent",
            hover_color=("#e9ecef", "#2d3436"),
            text_color=("#495057", "#e9ecef"),
            font=ctk.CTkFont(size=14),
            command=lambda: self._on_navigate(key, button_frame),
            corner_radius=8
        )
        btn.pack(fill="both", expand=True, padx=2, pady=2)

        # تأثير التحديد
        button_frame.is_active = False
        button_frame.key = key
        button_frame.button = btn
        button_frame.style = style

        # ألوان الأنماط
        style_colors = {
            "primary": ("#1976d2", "#2196f3"),
            "info": ("#0288d1", "#03a9f4"),
            "warning": ("#f57c00", "#ff9800"),
            "success": ("#388e3c", "#4caf50"),
            "secondary": ("#616161", "#757575")
        }
        button_frame.accent_color = style_colors.get(style, style_colors["primary"])

        # تأثيرات hover
        def on_enter(e):
            if not button_frame.is_active:
                color = button_frame.accent_color[1 if ctk.get_appearance_mode() == "Dark" else 0]
                btn.configure(text_color=color)

        def on_leave(e):
            if not button_frame.is_active:
                btn.configure(text_color=("#495057", "#e9ecef"))

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

        return button_frame

    def _on_navigate(self, key, button_frame):
        """معالج التنقل مع تأثيرات بصرية"""
        # إلغاء تفعيل الزر السابق
        if self.active_button:
            self.active_button.is_active = False
            self.active_button.button.configure(
                fg_color="transparent",
                text_color=("#495057", "#e9ecef")
            )

        # تفعيل الزر الحالي
        button_frame.is_active = True
        self.active_button = button_frame

        # تطبيق لون التفعيل
        accent = button_frame.accent_color[1 if ctk.get_appearance_mode() == "Dark" else 0]
        # استخدام لون أفتح بدلاً من الشفافية
        light_accent = self._get_lighter_color(accent, 0.1)
        button_frame.button.configure(
            fg_color=light_accent,
            text_color=accent
        )

        # استدعاء دالة التنقل
        if self.on_navigate:
            self.on_navigate(key)

    def _create_stats_section(self):
        """إنشاء قسم الإحصائيات المحسن"""
        # إطار القسم
        stats_section = ctk.CTkFrame(self, fg_color="transparent")
        stats_section.pack(fill="x", padx=15, pady=(25, 0))

        # عنوان القسم
        self.stats_title = ctk.CTkLabel(
            stats_section,
            text=self.lang_manager.get("quick_stats", "Quick Stats"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#666666", "#999999")
        )
        self.stats_title.pack(anchor="w", pady=(0, 10))

        # إطار البطاقات
        self.stats_frame = ctk.CTkFrame(stats_section, fg_color="transparent")
        self.stats_frame.pack(fill="x")

        # بطاقات الإحصائيات
        self.stats_cards = {}
        self.stats_info = []

        stats_items = [
            ("total", "📊", "Total Bookings", "#1976d2"),
            ("today", "📅", "Today's Bookings", "#388e3c"),
            ("pending", "⏳", "Pending", "#f57c00")
        ]

        for key, icon, default_label, color in stats_items:
            label = self.lang_manager.get(f"stats_{key}", default_label)
            card_frame, value_label = self._create_enhanced_stat_card(
                self.stats_frame, icon, label, color
            )
            self.stats_cards[key] = value_label
            self.stats_info.append((key, icon, default_label, card_frame, color))

    def _create_enhanced_stat_card(self, parent, icon, label, color):
        """إنشاء بطاقة إحصائية محسنة"""
        # إطار البطاقة
        card = ctk.CTkFrame(
            parent,
            height=80,
            corner_radius=12,
            fg_color=("#ffffff", "#2b2b2b"),
            border_width=1,
            border_color=("#e0e0e0", "#444444")
        )
        card.pack(fill="x", pady=5)

        # تأثير hover
        def on_enter(e):
            card.configure(border_color=color)

        def on_leave(e):
            card.configure(border_color=("#e0e0e0", "#444444"))

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        # محتوى البطاقة
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(expand=True, padx=15)

        # الصف العلوي
        top_row = ctk.CTkFrame(content_frame, fg_color="transparent")
        top_row.pack(fill="x")

        # الأيقونة مع خلفية ملونة
        # استخدام ألوان أفتح بدلاً من الشفافية
        light_color = self._get_lighter_color(color, 0.2)
        dark_color = self._get_lighter_color(color, 0.3)

        icon_bg = ctk.CTkFrame(
            top_row,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=(light_color, dark_color)
        )
        icon_bg.pack(side="left")
        icon_bg.pack_propagate(False)

        icon_label = ctk.CTkLabel(
            icon_bg,
            text=icon,
            font=ctk.CTkFont(size=20),
            text_color=color
        )
        icon_label.place(relx=0.5, rely=0.5, anchor="center")

        # القيمة
        value_label = ctk.CTkLabel(
            top_row,
            text="0",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=color
        )
        value_label.pack(side="right")

        # التسمية
        label_widget = ctk.CTkLabel(
            content_frame,
            text=label,
            font=ctk.CTkFont(size=12),
            text_color=("#666666", "#999999")
        )
        label_widget.pack(anchor="w", pady=(5, 0))

        # حفظ مرجع التسمية
        card.label_widget = label_widget
        card.color = color

        return card, value_label

    def _create_quick_actions(self):
        """إنشاء قسم الإجراءات السريعة"""
        # إطار القسم
        actions_section = ctk.CTkFrame(self, fg_color="transparent")
        actions_section.pack(fill="x", padx=15, pady=(25, 0))

        # عنوان القسم
        actions_title = ctk.CTkLabel(
            actions_section,
            text=self.lang_manager.get("quick_actions", "Quick Actions"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=("#666666", "#999999")
        )
        actions_title.pack(anchor="w", pady=(0, 10))

        # أزرار الإجراءات
        actions_frame = ctk.CTkFrame(actions_section, fg_color="transparent")
        actions_frame.pack(fill="x")

        # زر إضافة سريع
        add_btn = ctk.CTkButton(
            actions_frame,
            text=f"➕ {self.lang_manager.get('quick_add', 'Quick Add')}",
            height=35,
            corner_radius=8,
            fg_color=("#4caf50", "#2e7d32"),
            hover_color=("#45a049", "#1b5e20"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.on_navigate and self.on_navigate("add")
        )
        add_btn.pack(fill="x", pady=3)

        # زر البحث السريع
        search_btn = ctk.CTkButton(
            actions_frame,
            text=f"🔍 {self.lang_manager.get('quick_search', 'Quick Search')}",
            height=35,
            corner_radius=8,
            fg_color=("#2196f3", "#1976d2"),
            hover_color=("#1976d2", "#1565c0"),
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self.on_navigate and self.on_navigate("search")
        )
        search_btn.pack(fill="x", pady=3)

    def _create_footer(self):
        """إنشاء تذييل الشريط الجانبي"""
        # مساحة مرنة
        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        # إطار التذييل
        footer_frame = ctk.CTkFrame(
            self,
            height=60,
            fg_color=("#e9ecef", "#252525"),
            corner_radius=0
        )
        footer_frame.pack(fill="x", side="bottom")

        # محتوى التذييل
        footer_content = ctk.CTkFrame(footer_frame, fg_color="transparent")
        footer_content.pack(expand=True)

        # معلومات النظام
        system_info = ctk.CTkLabel(
            footer_content,
            text="FTS System v2.0",
            font=ctk.CTkFont(size=11),
            text_color=("#666666", "#999999")
        )
        system_info.pack()

        # حقوق النشر
        copyright_label = ctk.CTkLabel(
            footer_content,
            text="© 2024 FTS",
            font=ctk.CTkFont(size=10),
            text_color=("#999999", "#666666")
        )
        copyright_label.pack()

    def _toggle_sidebar(self):
        """تبديل الشريط الجانبي مع تأثيرات سلسة"""
        if self.is_collapsed:
            # توسيع الشريط
            self._expand_sidebar()
        else:
            # طي الشريط
            self._collapse_sidebar()

        self.is_collapsed = not self.is_collapsed

    def _collapse_sidebar(self):
        """طي الشريط الجانبي"""
        # تقليل العرض تدريجياً
        target_width = 60
        current_width = self.winfo_width()

        while current_width > target_width:
            current_width = max(current_width - 20, target_width)
            self.configure(width=current_width)
            self.update()
            self.after(10)

        # تغيير أيقونة التبديل
        self.toggle_btn.configure(text="▶")

        # إخفاء النصوص
        for widget in [self.nav_title, self.stats_title]:
            widget.pack_forget()

        # إخفاء البطاقات
        for _, _, _, card, _ in self.stats_info:
            card.pack_forget()

    def _expand_sidebar(self):
        """توسيع الشريط الجانبي"""
        # زيادة العرض تدريجياً
        target_width = 280
        current_width = self.winfo_width()

        while current_width < target_width:
            current_width = min(current_width + 20, target_width)
            self.configure(width=current_width)
            self.update()
            self.after(10)

        # تغيير أيقونة التبديل
        self.toggle_btn.configure(text="◀")

        # إظهار النصوص
        self.nav_title.pack(anchor="w", pady=(0, 10))
        self.stats_title.pack(anchor="w", pady=(0, 10))

        # إظهار البطاقات
        for _, _, _, card, _ in self.stats_info:
            card.pack(fill="x", pady=5)

    def update_stats(self, stats: Dict[str, int]):
        """تحديث الإحصائيات مع تأثيرات"""
        for key, value in stats.items():
            if key in self.stats_cards:
                label = self.stats_cards[key]
                # تحديث القيمة مع تأثير
                self._animate_value_change(label, int(label.cget("text")), value)

    def _animate_value_change(self, label, start, end):
        """تحريك تغيير القيمة"""
        if start == end:
            return

        # حساب الخطوة
        diff = end - start
        steps = 20
        step = diff / steps

        def update_value(current, target, step_count):
            if step_count <= 0:
                label.configure(text=str(int(target)))
                return

            new_value = current + step
            label.configure(text=str(int(new_value)))

            self.after(50, lambda: update_value(new_value, target, step_count - 1))

        update_value(start, end, steps)

    def update_texts(self, lang_manager):
        """تحديث نصوص المكون"""
        self.lang_manager = lang_manager

        # تحديث العناوين
        if hasattr(self, 'nav_title'):
            self.nav_title.configure(
                text=lang_manager.get("quick_navigation", "Quick Navigation")
            )

        if hasattr(self, 'stats_title'):
            self.stats_title.configure(
                text=lang_manager.get("quick_stats", "Quick Stats")
            )

        # تحديث أزرار التنقل
        for btn_frame, icon, key, default_text, style in self.nav_buttons:
            translated_text = lang_manager.get(f"nav_{key}", default_text)
            btn_frame.button.configure(text=f"{icon}  {translated_text}")

        # تحديث بطاقات الإحصائيات
        for key, icon, default_label, card_frame, color in self.stats_info:
            translated_label = lang_manager.get(f"stats_{key}", default_label)
            if hasattr(card_frame, 'label_widget'):
                card_frame.label_widget.configure(text=translated_label)

    def set_active_nav(self, key: str):
        """تعيين العنصر النشط في التنقل"""
        for btn_frame, _, btn_key, _, _ in self.nav_buttons:
            if btn_key == key:
                self._on_navigate(key, btn_frame)
                break

    def add_navigation_button(self, text, icon=None, command=None, style="default"):
        """إضافة زر تنقل مخصص"""
        if not hasattr(self, 'nav_frame'):
            return None

        display_text = f"{icon}  {text}" if icon else text

        # إنشاء الزر
        btn_frame = self._create_nav_button(
            self.nav_frame,
            icon or "•",
            text.lower().replace(" ", "_"),
            display_text,
            style
        )

        # تعيين الأمر المخصص
        if command:
            btn_frame.button.configure(command=command)

        # إضافة للقائمة
        self.nav_buttons.append((btn_frame, icon or "", text, text, style))

        return btn_frame

    def refresh_theme(self):
        """تحديث الثيم عند تغييره"""
        # إعادة بناء الواجهة لتطبيق الألوان الجديدة
        for widget in self.winfo_children():
            widget.destroy()
        self._build_ui()

    def _get_lighter_color(self, hex_color: str, factor: float = 0.2) -> str:
        """الحصول على لون أفتح من اللون المعطى"""
        # إزالة # إذا كانت موجودة
        hex_color = hex_color.lstrip('#')

        # تحويل hex إلى RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        # جعل اللون أفتح
        r = int(r + (255 - r) * factor)
        g = int(g + (255 - g) * factor)
        b = int(b + (255 - b) * factor)

        # التأكد من عدم تجاوز 255
        r = min(255, r)
        g = min(255, g)
        b = min(255, b)

        # تحويل مرة أخرى إلى hex
        return f"#{r:02x}{g:02x}{b:02x}"


# للتوافق مع الأكواد القديمة
Sidebar = SidebarComponent