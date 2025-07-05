# -*- coding: utf-8 -*-
"""
core/theme_manager.py

تدير هذه الفئة إعداد وتطبيق الثيمات (Themes) في واجهة المستخدم باستخدام مكتبة CustomTkinter.
تعتمد على إعدادات ConfigManager لقراءة ثيم الواجهة (فاتح/داكن) والثيم اللوني (Color Theme).
يمكن تغيير الثيم أثناء تشغيل التطبيق دون الحاجة لإعادة التشغيل.

🔵 التحديث الجديد: دعم الألوان الزرقاء للقوائم المنسدلة
"""

# ------------------------------------------------------------
# استيرادات المكتبات القياسية
# ------------------------------------------------------------
from typing import Optional, Dict, Any, Union
import json
import os

# ------------------------------------------------------------
# استيرادات المكتبات الخارجية
# ------------------------------------------------------------
import customtkinter as ctk
import tkinter as tk

# ------------------------------------------------------------
# استيرادات وحدات المشروع
# ------------------------------------------------------------
from core.config_manager import ConfigManager
from core.logger import logger


class ThemeManager:
    """
    فئة ThemeManager مسؤولة عن:
    - قراءة إعدادات الثيم من ConfigManager.
    - تطبيق ثيم الواجهة (Appearance Mode) وثيم الألوان (Color Theme) على CustomTkinter.
    - تغيير الثيم ديناميكيًا وحفظ الإعدادات.
    - دعم ثيمات مخصصة مثل Windows 7
    - 🔵 دعم الألوان الزرقاء للقوائم المنسدلة
    """

    def __init__(self, config_manager: ConfigManager) -> None:
        """
        تهيئة ThemeManager.
        """
        self.config: ConfigManager = config_manager

        # تعريف الثيمات المخصصة
        self.custom_themes = {
            "windows7_aero": self._get_windows7_aero_colors(),
            "windows7_classic": self._get_windows7_classic_colors(),
            "windows7_basic": self._get_windows7_basic_colors()
        }

        # قائمة الثيمات المدمجة - إزالة dark-blue
        self.builtin_themes = ["blue", "green"]  # ⚠️ أزلنا "dark-blue"

        # قراءة الإعدادات
        self.current_mode: str = self.config.get("appearance_mode", "light")

        # التحقق من الثيم وتصحيحه إذا كان dark-blue
        saved_theme = self.config.get("color_theme", "blue")
        if saved_theme == "dark-blue":
            logger.warning("تم اكتشاف dark-blue theme - سيتم التغيير إلى blue")
            saved_theme = "blue"
            self.config.set("color_theme", "blue")

        self.current_color_theme: str = saved_theme

        # تطبيق appearance mode فقط
        self.apply_appearance_mode(self.current_mode)

        # لا تطبق color theme هنا - سيتم تطبيقه في app_controller

    def apply_blue_theme_to_enhanced_combo(self, combo_widget):
        """🔵 تطبيق الثيم الأزرق على القائمة المحسنة"""
        try:
            if hasattr(combo_widget, 'apply_blue_theme'):
                combo_widget.apply_blue_theme(self)
                logger.info("✅ تم تطبيق الثيم الأزرق على القائمة المحسنة")
            elif hasattr(combo_widget, '_get_blue_colors'):
                # إجبار تحديث الألوان
                combo_widget.theme_manager = self
                if hasattr(combo_widget, '_populate_dropdown_simple'):
                    combo_widget._populate_dropdown_simple()
            else:
                logger.warning("⚠️ القائمة لا تدعم الثيم الأزرق")
        except Exception as e:
            logger.error(f"❌ خطأ في تطبيق الثيم الأزرق: {e}")

    def _get_windows7_aero_colors(self) -> Dict[str, Any]:
        """
        ألوان ثيم Windows 7 Aero مع دعم الألوان الزرقاء للقوائم المنسدلة
        """
        return {
            "window_bg": {"light": "#F0F0F0", "dark": "#1E1E1E"},
            "frame_bg": {"light": "#FFFFFF", "dark": "#2D2D30"},
            "button_bg": {"light": "#E1E1E1", "dark": "#3F3F46"},
            "button_hover": {"light": "#B9D7F1", "dark": "#4B7BB1"},
            "button_pressed": {"light": "#7DA2CE", "dark": "#2C5282"},
            "button_text": {"light": "#000000", "dark": "#FFFFFF"},
            "entry_bg": {"light": "#FFFFFF", "dark": "#383838"},
            "entry_border": {"light": "#7DA2CE", "dark": "#555555"},
            "entry_border_focus": {"light": "#569DE5", "dark": "#0078D7"},
            "text_color": {"light": "#000000", "dark": "#E0E0E0"},
            "label_color": {"light": "#000000", "dark": "#CCCCCC"},
            "disabled_color": {"light": "#8B8B8B", "dark": "#6B6B6B"},
            "selection_bg": {"light": "#0078D7", "dark": "#0078D7"},
            "selection_text": {"light": "#FFFFFF", "dark": "#FFFFFF"},
            "scrollbar_bg": {"light": "#F0F0F0", "dark": "#2D2D30"},
            "scrollbar_thumb": {"light": "#CDCDCD", "dark": "#686868"},
            "scrollbar_thumb_hover": {"light": "#A6A6A6", "dark": "#9E9E9E"},
            "menu_bg": {"light": "#F0F0F0", "dark": "#2D2D30"},
            "menu_hover": {"light": "#E3F2FD", "dark": "#094771"},
            # 🔵 ألوان جديدة للقوائم المنسدلة الزرقاء
            "dropdown_hover": {"light": "#E6F3FF", "dark": "#1E90FF"},
            "dropdown_text_hover": {"light": "#000080", "dark": "#FFFFFF"},
            "dropdown_select": {"light": "#ADD8E6", "dark": "#000080"},
            "dropdown_border": {"light": "#0000FF", "dark": "#ADD8E6"},
            "tooltip_bg": {"light": "#FFFFCC", "dark": "#4B4B4B"},
            "tooltip_text": {"light": "#000000", "dark": "#FFFFFF"},
            "progress_bg": {"light": "#E6E6E6", "dark": "#2D2D30"},
            "progress_fill": {"light": "#06B025", "dark": "#06B025"},
            "tab_active": {"light": "#FFFFFF", "dark": "#3F3F46"},
            "tab_inactive": {"light": "#E8E8E8", "dark": "#2D2D30"},
            "border_color": {"light": "#ADADAD", "dark": "#555555"},
            "shadow_color": {"light": "#B0B0B0", "dark": "#000000"}
        }

    def _get_windows7_classic_colors(self) -> Dict[str, Any]:
        """
        ألوان ثيم Windows 7 Classic (بدون شفافية) مع دعم الألوان الزرقاء
        """
        return {
            "window_bg": {"light": "#D4D0C8", "dark": "#3C3C3C"},
            "frame_bg": {"light": "#ECE9D8", "dark": "#404040"},
            "button_bg": {"light": "#D4D0C8", "dark": "#404040"},
            "button_hover": {"light": "#E0DDD7", "dark": "#4A4A4A"},
            "button_pressed": {"light": "#C4C0B8", "dark": "#353535"},
            "button_text": {"light": "#000000", "dark": "#E0E0E0"},
            "entry_bg": {"light": "#FFFFFF", "dark": "#525252"},
            "entry_border": {"light": "#404040", "dark": "#6B6B6B"},
            "entry_border_focus": {"light": "#0054E3", "dark": "#0078D7"},
            "text_color": {"light": "#000000", "dark": "#E0E0E0"},
            "label_color": {"light": "#000000", "dark": "#D0D0D0"},
            "disabled_color": {"light": "#808080", "dark": "#808080"},
            "selection_bg": {"light": "#316AC5", "dark": "#316AC5"},
            "selection_text": {"light": "#FFFFFF", "dark": "#FFFFFF"},
            "scrollbar_bg": {"light": "#D4D0C8", "dark": "#404040"},
            "scrollbar_thumb": {"light": "#A0A0A0", "dark": "#606060"},
            "scrollbar_thumb_hover": {"light": "#808080", "dark": "#808080"},
            "menu_bg": {"light": "#F0F0F0", "dark": "#404040"},
            "menu_hover": {"light": "#316AC5", "dark": "#316AC5"},
            # 🔵 ألوان زرقاء للقوائم المنسدلة
            "dropdown_hover": {"light": "#CCE7FF", "dark": "#4169E1"},
            "dropdown_text_hover": {"light": "#000080", "dark": "#FFFFFF"},
            "dropdown_select": {"light": "#87CEEB", "dark": "#191970"},
            "dropdown_border": {"light": "#0000CD", "dark": "#87CEEB"},
            "tooltip_bg": {"light": "#FFFFE1", "dark": "#4B4B4B"},
            "tooltip_text": {"light": "#000000", "dark": "#FFFFFF"},
            "progress_bg": {"light": "#E0E0E0", "dark": "#404040"},
            "progress_fill": {"light": "#316AC5", "dark": "#316AC5"},
            "tab_active": {"light": "#ECE9D8", "dark": "#525252"},
            "tab_inactive": {"light": "#D4D0C8", "dark": "#404040"},
            "border_color": {"light": "#808080", "dark": "#6B6B6B"},
            "shadow_color": {"light": "#808080", "dark": "#000000"}
        }

    def _get_windows7_basic_colors(self) -> Dict[str, Any]:
        """
        ألوان ثيم Windows 7 Basic (بدون تأثيرات Aero) مع دعم الألوان الزرقاء
        """
        return {
            "window_bg": {"light": "#E8E8E8", "dark": "#2B2B2B"},
            "frame_bg": {"light": "#F5F5F5", "dark": "#363636"},
            "button_bg": {"light": "#DDDDDD", "dark": "#484848"},
            "button_hover": {"light": "#C8E6F5", "dark": "#5A7FA6"},
            "button_pressed": {"light": "#9ECDE7", "dark": "#405F7E"},
            "button_text": {"light": "#000000", "dark": "#FFFFFF"},
            "entry_bg": {"light": "#FFFFFF", "dark": "#404040"},
            "entry_border": {"light": "#999999", "dark": "#5C5C5C"},
            "entry_border_focus": {"light": "#3399FF", "dark": "#0078D7"},
            "text_color": {"light": "#000000", "dark": "#E0E0E0"},
            "label_color": {"light": "#000000", "dark": "#D4D4D4"},
            "disabled_color": {"light": "#999999", "dark": "#7A7A7A"},
            "selection_bg": {"light": "#3399FF", "dark": "#3399FF"},
            "selection_text": {"light": "#FFFFFF", "dark": "#FFFFFF"},
            "scrollbar_bg": {"light": "#E8E8E8", "dark": "#363636"},
            "scrollbar_thumb": {"light": "#B8B8B8", "dark": "#5C5C5C"},
            "scrollbar_thumb_hover": {"light": "#999999", "dark": "#7A7A7A"},
            "menu_bg": {"light": "#F5F5F5", "dark": "#363636"},
            "menu_hover": {"light": "#D8E9F5", "dark": "#4B6983"},
            # 🔵 ألوان زرقاء للقوائم المنسدلة
            "dropdown_hover": {"light": "#E6F7FF", "dark": "#1E90FF"},
            "dropdown_text_hover": {"light": "#003366", "dark": "#FFFFFF"},
            "dropdown_select": {"light": "#B3D9FF", "dark": "#0066CC"},
            "dropdown_border": {"light": "#0066FF", "dark": "#B3D9FF"},
            "tooltip_bg": {"light": "#FFFFC8", "dark": "#525252"},
            "tooltip_text": {"light": "#000000", "dark": "#FFFFFF"},
            "progress_bg": {"light": "#E0E0E0", "dark": "#363636"},
            "progress_fill": {"light": "#3399FF", "dark": "#3399FF"},
            "tab_active": {"light": "#F5F5F5", "dark": "#484848"},
            "tab_inactive": {"light": "#DDDDDD", "dark": "#363636"},
            "border_color": {"light": "#B5B5B5", "dark": "#5C5C5C"},
            "shadow_color": {"light": "#C0C0C0", "dark": "#000000"}
        }

    def get_theme_colors(self, theme_name: str = None) -> Dict[str, str]:
        """
        الحصول على ألوان الثيم الحالي أو ثيم محدد
        """
        if theme_name is None:
            theme_name = self.current_color_theme

        if theme_name in self.custom_themes:
            colors = self.custom_themes[theme_name]
            mode = self.current_mode if self.current_mode in ["light", "dark"] else "light"
            # إرجاع الألوان للوضع الحالي فقط
            return {key: value[mode] for key, value in colors.items()}

        # للثيمات المدمجة، إرجاع ألوان افتراضية مع الألوان الزرقاء
        return self._get_default_colors()

    def _get_default_colors(self) -> Dict[str, str]:
        """
        الحصول على الألوان الافتراضية للثيمات المدمجة مع دعم الألوان الزرقاء
        """
        if self.current_mode == "dark":
            return {
                "window_bg": "#212121",
                "frame_bg": "#2B2B2B",
                "button_bg": "#3F7CAC",
                "button_hover": "#5294C7",
                "text_color": "#E0E0E0",
                "entry_bg": "#3A3A3A",
                "entry_border": "#565B5E",
                # 🔵 ألوان زرقاء افتراضية للوضع الليلي
                "dropdown_hover": "#1E90FF",
                "dropdown_text_hover": "#FFFFFF",
                "dropdown_select": "#000080",
                "dropdown_border": "#ADD8E6"
            }
        else:
            return {
                "window_bg": "#F0F0F0",
                "frame_bg": "#FFFFFF",
                "button_bg": "#1F538D",
                "button_hover": "#2A5F9E",
                "text_color": "#000000",
                "entry_bg": "#FFFFFF",
                "entry_border": "#CCCCCC",
                # 🔵 ألوان زرقاء افتراضية للوضع النهاري
                "dropdown_hover": "#E6F3FF",
                "dropdown_text_hover": "#000080",
                "dropdown_select": "#ADD8E6",
                "dropdown_border": "#0000FF"
            }

    def get_dropdown_hover_color(self) -> str:
        """الحصول على لون التمرير للقوائم المنسدلة - أزرق فاتح"""
        colors = self.get_theme_colors()
        return colors.get("dropdown_hover", "#E6F3FF" if self.current_mode == "light" else "#1E90FF")

    def get_dropdown_text_hover_color(self) -> str:
        """الحصول على لون النص للقوائم المنسدلة عند التمرير"""
        colors = self.get_theme_colors()
        return colors.get("dropdown_text_hover", "#000080" if self.current_mode == "light" else "#FFFFFF")

    def get_dropdown_select_color(self) -> str:
        """الحصول على لون اختيار القوائم المنسدلة بلوحة المفاتيح"""
        colors = self.get_theme_colors()
        return colors.get("dropdown_select", "#ADD8E6" if self.current_mode == "light" else "#000080")

    def get_dropdown_border_color(self) -> str:
        """الحصول على لون حدود القوائم المنسدلة"""
        colors = self.get_theme_colors()
        return colors.get("dropdown_border", "#0000FF" if self.current_mode == "light" else "#ADD8E6")

    def apply_appearance_mode(self, mode: str) -> None:
        """
        تطبيق ثيم الواجهة (Appearance Mode) على CustomTkinter.
        """
        mode = mode.lower()
        if mode not in ("light", "dark", "system"):
            logger.warning(f"ThemeManager: قيمة غير صالحة للـ appearance_mode: '{mode}'. سيتم استخدام 'light'.")
            mode = "light"

        try:
            ctk.set_appearance_mode(mode)
            self.current_mode = mode
            self.config.set("appearance_mode", mode)
            logger.info(f"ThemeManager: تم تطبيق Appearance Mode='{mode}'.")
        except Exception as exc:
            logger.error(f"ThemeManager: خطأ أثناء تطبيق Appearance Mode='{mode}': {exc}", exc_info=True)

    def apply_color_theme(self, color_theme: str) -> None:
        """
        تطبيق ثيم الألوان على CustomTkinter.
        """
        color_theme = color_theme.lower()

        # إذا كان ثيم مخصص
        if color_theme in self.custom_themes:
            # حفظ الثيم فقط دون تطبيقه على CTk
            self.current_color_theme = color_theme
            self.config.set("color_theme", color_theme)
            logger.info(f"ThemeManager: تم اختيار الثيم المخصص '{color_theme}'.")

        # إذا كان ثيم مدمج
        elif color_theme in self.builtin_themes:
            try:
                # ⚠️ لا تستدعي set_default_color_theme هنا!
                # فقط احفظ الإعداد
                self.current_color_theme = color_theme
                self.config.set("color_theme", color_theme)
                logger.info(f"ThemeManager: تم اختيار Color Theme='{color_theme}'.")

                # إظهار تحذير للمستخدم
                logger.warning("تغيير الثيم يتطلب إعادة تشغيل التطبيق ليتم تطبيقه بالكامل")

            except Exception as exc:
                logger.error(f"ThemeManager: خطأ في حفظ Color Theme='{color_theme}': {exc}")
        else:
            logger.warning(f"ThemeManager: ثيم غير معروف '{color_theme}'.")

    def apply_widget_theme(self, widget: Union[tk.Widget, ctk.CTkBaseClass]) -> None:
        """
        تطبيق ألوان الثيم على عنصر واجهة محدد مع دعم الألوان الزرقاء للقوائم المنسدلة
        """
        if self.current_color_theme not in self.custom_themes:
            return

        colors = self.get_theme_colors()

        try:
            # تطبيق الألوان حسب نوع العنصر
            if isinstance(widget, ctk.CTkButton):
                widget.configure(
                    fg_color=colors.get("button_bg"),
                    hover_color=colors.get("button_hover"),
                    text_color=colors.get("button_text"),
                    corner_radius=4,
                    border_width=1,
                    border_color=colors.get("border_color")
                )

            elif isinstance(widget, ctk.CTkEntry):
                widget.configure(
                    fg_color=colors.get("entry_bg"),
                    border_color=colors.get("entry_border"),
                    text_color=colors.get("text_color"),
                    corner_radius=2,
                    border_width=1
                )

            elif isinstance(widget, ctk.CTkFrame):
                widget.configure(
                    fg_color=colors.get("frame_bg"),
                    corner_radius=6,
                    border_width=1,
                    border_color=colors.get("border_color")
                )

            elif isinstance(widget, ctk.CTkLabel):
                widget.configure(
                    text_color=colors.get("label_color")
                )

            elif isinstance(widget, ctk.CTkTextbox):
                widget.configure(
                    fg_color=colors.get("entry_bg"),
                    border_color=colors.get("entry_border"),
                    text_color=colors.get("text_color"),
                    corner_radius=2,
                    border_width=1,
                    scrollbar_button_color=colors.get("scrollbar_thumb"),
                    scrollbar_button_hover_color=colors.get("scrollbar_thumb_hover")
                )

            elif isinstance(widget, ctk.CTkProgressBar):
                widget.configure(
                    fg_color=colors.get("progress_bg"),
                    progress_color=colors.get("progress_fill"),
                    corner_radius=2,
                    border_width=1,
                    border_color=colors.get("border_color")
                )

            elif isinstance(widget, ctk.CTkCheckBox):
                widget.configure(
                    fg_color=colors.get("selection_bg"),
                    hover_color=colors.get("button_hover"),
                    text_color=colors.get("text_color"),
                    border_color=colors.get("entry_border"),
                    checkmark_color=colors.get("selection_text"),
                    corner_radius=2,
                    border_width=1
                )

            elif isinstance(widget, ctk.CTkSwitch):
                widget.configure(
                    fg_color=colors.get("scrollbar_bg"),
                    progress_color=colors.get("selection_bg"),
                    button_color=colors.get("button_bg"),
                    button_hover_color=colors.get("button_hover"),
                    text_color=colors.get("text_color")
                )

            elif isinstance(widget, ctk.CTkOptionMenu):
                widget.configure(
                    fg_color=colors.get("entry_bg"),
                    button_color=colors.get("button_bg"),
                    button_hover_color=colors.get("button_hover"),
                    text_color=colors.get("text_color"),
                    dropdown_fg_color=colors.get("menu_bg"),
                    dropdown_hover_color=self.get_dropdown_hover_color(),  # 🔵 استخدام اللون الأزرق
                    dropdown_text_color=self.get_dropdown_text_hover_color(),  # 🔵 نص أزرق
                    corner_radius=2
                )

            elif isinstance(widget, ctk.CTkComboBox):
                widget.configure(
                    fg_color=colors.get("entry_bg"),
                    border_color=colors.get("entry_border"),
                    button_color=colors.get("button_bg"),
                    button_hover_color=colors.get("button_hover"),
                    text_color=colors.get("text_color"),
                    dropdown_fg_color=colors.get("menu_bg"),
                    dropdown_hover_color=self.get_dropdown_hover_color(),  # 🔵 استخدام اللون الأزرق
                    dropdown_text_color=self.get_dropdown_text_hover_color(),  # 🔵 نص أزرق
                    corner_radius=2,
                    border_width=1
                )

            elif isinstance(widget, ctk.CTkTabview):
                widget.configure(
                    fg_color=colors.get("frame_bg"),
                    segmented_button_fg_color=colors.get("window_bg"),
                    segmented_button_selected_color=colors.get("tab_active"),
                    segmented_button_selected_hover_color=colors.get("button_hover"),
                    segmented_button_unselected_color=colors.get("tab_inactive"),
                    segmented_button_unselected_hover_color=colors.get("scrollbar_thumb_hover"),
                    text_color=colors.get("text_color"),
                    corner_radius=6
                )

            elif isinstance(widget, ctk.CTkScrollbar):
                widget.configure(
                    fg_color=colors.get("scrollbar_bg"),
                    button_color=colors.get("scrollbar_thumb"),
                    button_hover_color=colors.get("scrollbar_thumb_hover")
                )

            # للعناصر العادية من tkinter
            elif hasattr(widget, 'configure'):
                try:
                    widget.configure(bg=colors.get("window_bg"))
                    if hasattr(widget, 'fg'):
                        widget.configure(fg=colors.get("text_color"))
                except:
                    pass

        except Exception as e:
            logger.debug(f"تعذر تطبيق الثيم على {type(widget).__name__}: {e}")

    def apply_blue_dropdown_theme(self, widget) -> None:
        """
        🔵 تطبيق الثيم الأزرق خصيصاً للقوائم المنسدلة المحسنة
        """
        try:
            if hasattr(widget, '_apply_blue_hover_colors'):
                # للقوائم المحسنة التي تدعم الألوان الزرقاء
                widget._apply_blue_hover_colors(
                    hover_color=self.get_dropdown_hover_color(),
                    text_color=self.get_dropdown_text_hover_color(),
                    select_color=self.get_dropdown_select_color(),
                    border_color=self.get_dropdown_border_color()
                )
                logger.debug(f"تم تطبيق الثيم الأزرق على القائمة المحسنة")
            elif hasattr(widget, 'configure'):
                # للقوائم العادية
                widget.configure(
                    dropdown_hover_color=self.get_dropdown_hover_color(),
                    dropdown_text_color=self.get_dropdown_text_hover_color()
                )
                logger.debug(f"تم تطبيق الثيم الأزرق على القائمة العادية")
        except Exception as e:
            logger.debug(f"فشل في تطبيق الثيم الأزرق: {e}")

    def apply_to_all_widgets(self, parent_widget) -> None:
        """
        تطبيق الثيم على جميع العناصر في النافذة مع دعم خاص للألوان الزرقاء
        """
        def apply_recursively(widget):
            self.apply_widget_theme(widget)

            # تطبيق خاص للقوائم المنسدلة المحسنة
            if hasattr(widget, '_apply_blue_hover_colors'):
                self.apply_blue_dropdown_theme(widget)

            for child in widget.winfo_children():
                apply_recursively(child)

        apply_recursively(parent_widget)

    def get_error_color(self) -> str:
        """الحصول على لون الخطأ حسب الثيم الحالي"""
        if self.current_mode == "dark":
            return "#FF6B6B"
        else:
            return "#DC143C"

    def get_success_color(self) -> str:
        """الحصول على لون النجاح حسب الثيم الحالي"""
        if self.current_mode == "dark":
            return "#51CF66"
        else:
            return "#228B22"

    def get_warning_color(self) -> str:
        """الحصول على لون التحذير حسب الثيم الحالي"""
        if self.current_mode == "dark":
            return "#FFD93D"
        else:
            return "#FFA500"

    def get_info_color(self) -> str:
        """الحصول على لون المعلومات حسب الثيم الحالي"""
        if self.current_mode == "dark":
            return "#339AF0"
        else:
            return "#0066CC"

    def is_windows7_theme(self) -> bool:
        """التحقق من استخدام ثيم Windows 7"""
        return self.current_color_theme.startswith("windows7")

    def get_available_themes(self) -> list:
        """الحصول على قائمة بجميع الثيمات المتاحة"""
        return self.builtin_themes + list(self.custom_themes.keys())

    def toggle_appearance_mode(self) -> None:
        """تبديل ثيم الواجهة بين 'light' و 'dark'"""
        new_mode = "dark" if self.current_mode == "light" else "light"
        logger.debug(f"ThemeManager: تبديل Appearance Mode من '{self.current_mode}' إلى '{new_mode}'.")
        self.apply_appearance_mode(new_mode)

    def get_current_appearance_mode(self) -> str:
        """إرجاع الثيم الحالي للواجهة"""
        return self.current_mode

    def get_current_color_theme(self) -> str:
        """إرجاع ثيم الألوان الحالي"""
        return self.current_color_theme

    def reload(self) -> None:
        """إعادة تحميل وتطبيق الثيمات من ConfigManager"""
        mode = self.config.get("appearance_mode", "light")
        color = self.config.get("color_theme", "blue")
        logger.debug("ThemeManager: إعادة تحميل الثيمات من ConfigManager.")
        self.apply_appearance_mode(mode)
        self.apply_color_theme(color)
