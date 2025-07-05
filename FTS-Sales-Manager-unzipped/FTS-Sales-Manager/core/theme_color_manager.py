# -*- coding: utf-8 -*-
"""
core/theme_color_manager.py

نظام ثيم موحد لجميع النوافذ
يجمع بين المرونة والموثوقية والألوان المتقدمة
مع دعم محسن للحقول المحمية (readonly fields)
"""

import customtkinter as ctk
from typing import Dict, Optional, Any
from core.logger import logger

class ThemeColorManager:
    """مدير ألوان الثيم الموحد"""

    def __init__(self, theme_manager=None):
        self.theme_manager = theme_manager
        self._color_cache = {}
        self._load_color_palettes()

    def _load_color_palettes(self):
        """تحميل لوحات الألوان"""
        try:
            from config.modern_color_palettes import get_color_palette, get_available_palettes
            self._has_palettes = True
            self._get_color_palette = get_color_palette
            self._get_available_palettes = get_available_palettes
        except ImportError:
            self._has_palettes = False
            logger.debug("Modern color palettes not available")

    def get_current_colors(self) -> Dict[str, str]:
        """الحصول على لوحة الألوان الحالية"""
        mode = self._get_appearance_mode()
        palette_key = self._get_current_palette_key(mode)

        if self._has_palettes:
            try:
                return self._get_color_palette(palette_key)
            except Exception as e:
                logger.warning(f"Error loading palette {palette_key}: {e}")

        return self._get_default_colors(mode)

    def _get_appearance_mode(self) -> str:
        """الحصول على وضع المظهر الحالي"""
        if self.theme_manager:
            try:
                if hasattr(self.theme_manager, 'get_current_appearance_mode'):
                    return self.theme_manager.get_current_appearance_mode()
                elif hasattr(self.theme_manager, 'current_mode'):
                    return self.theme_manager.current_mode
            except:
                pass

        # الحصول من customtkinter مباشرة
        try:
            return ctk.get_appearance_mode().lower()
        except:
            return "light"

    def _get_current_palette_key(self, mode: str) -> str:
        """الحصول على مفتاح لوحة الألوان الحالية"""
        if mode == "dark":
            return "modern_dark"

        # للوضع الفاتح، محاولة الحصول على التفضيل المحفوظ
        if self.theme_manager and hasattr(self.theme_manager, 'config'):
            try:
                return self.theme_manager.config.get('light_color_palette', 'modern_purple')
            except:
                pass

        return "modern_purple"

    def _get_default_colors(self, mode: str) -> Dict[str, str]:
        """الحصول على الألوان الافتراضية"""
        if mode == "dark":
            return {
                'primary': '#5B5FFF',
                'primary_hover': '#4B4FEF',
                'secondary': '#6B7280',
                'success': '#10B981',
                'danger': '#F43F5E',
                'danger_hover': '#E11D48',
                'warning': '#F59E0B',
                'background': '#1a1a1a',
                'surface': '#2b2b2b',
                'input_bg': '#374151',
                'input_border': '#4B5563',
                'input_focus': '#5B5FFF',
                'border': '#374151',
                'text_primary': '#F9FAFB',
                'text_secondary': '#D1D5DB',
                'shadow': 'rgba(0, 0, 0, 0.25)',
                # ألوان الحقول المحمية
                'readonly_bg': '#1f2937',
                'readonly_border': '#374151',
                'readonly_text': '#9CA3AF'
            }
        else:
            return {
                'primary': '#5B5FFF',
                'primary_hover': '#4B4FEF',
                'secondary': '#6B7280',
                'success': '#10B981',
                'danger': '#F43F5E',
                'danger_hover': '#E11D48',
                'warning': '#F59E0B',
                'background': '#F9FAFB',
                'surface': '#FFFFFF',
                'input_bg': '#F3F4F6',
                'input_border': '#D1D5DB',
                'input_focus': '#5B5FFF',
                'border': '#E5E7EB',
                'text_primary': '#111827',
                'text_secondary': '#6B7280',
                'shadow': 'rgba(0, 0, 0, 0.05)',
                # ألوان الحقول المحمية
                'readonly_bg': '#F3F4F6',
                'readonly_border': '#D1D5DB',
                'readonly_text': '#9CA3AF'
            }

    def get_color(self, color_name: str, fallback: str = None) -> str:
        """الحصول على لون محدد بطريقة آمنة"""
        # التحقق من الكاش أولاً
        cache_key = f"{self._get_appearance_mode()}_{color_name}"
        if cache_key in self._color_cache:
            return self._color_cache[cache_key]

        colors = self.get_current_colors()
        color = colors.get(color_name)

        if not color and fallback:
            color = fallback
        elif not color:
            # ألوان احتياطية أساسية
            backup_colors = {
                'primary': '#1f538d',
                'background': 'gray14' if self._get_appearance_mode() == 'dark' else 'white',
                'surface': 'gray16' if self._get_appearance_mode() == 'dark' else '#f8f9fa',
                'text_primary': 'white' if self._get_appearance_mode() == 'dark' else 'black',
                'text_secondary': 'gray',
                'success': '#4caf50',
                'danger': '#f44336',
                'warning': '#ff9800',
                'readonly_bg': '#f5f5f5' if self._get_appearance_mode() == 'light' else '#2a2a2a',
                'readonly_border': '#cccccc' if self._get_appearance_mode() == 'light' else '#444444',
                'readonly_text': '#666666' if self._get_appearance_mode() == 'light' else '#999999'
            }
            color = backup_colors.get(color_name, '#1f538d')

        # حفظ في الكاش
        self._color_cache[cache_key] = color
        return color

    def apply_to_window(self, window):
        """تطبيق الثيم على النافذة"""
        try:
            bg_color = self.get_color('background')
            window.configure(fg_color=bg_color)
        except Exception as e:
            logger.debug(f"Error applying theme to window: {e}")

    def apply_to_frame(self, frame, frame_type='default'):
        """تطبيق الثيم على إطار"""
        try:
            colors = {
                'default': self.get_color('surface'),
                'transparent': 'transparent',
                'header': self.get_color('surface'),
                'sidebar': self.get_color('input_bg'),
                'content': self.get_color('background')
            }

            fg_color = colors.get(frame_type, self.get_color('surface'))
            frame.configure(fg_color=fg_color)
        except Exception as e:
            logger.debug(f"Error applying theme to frame: {e}")

    def apply_to_button(self, button, button_type='primary'):
        """تطبيق الثيم على زر"""
        try:
            configs = {
                'primary': {
                    'fg_color': self.get_color('primary'),
                    'hover_color': self.get_color('primary_hover'),
                    'text_color': 'white'
                },
                'secondary': {
                    'fg_color': self.get_color('input_bg'),
                    'hover_color': self.get_color('border'),
                    'text_color': self.get_color('text_primary'),
                    'border_width': 1,
                    'border_color': self.get_color('input_border')
                },
                'success': {
                    'fg_color': self.get_color('success'),
                    'hover_color': self.get_color('success'),
                    'text_color': 'white'
                },
                'danger': {
                    'fg_color': self.get_color('danger'),
                    'hover_color': self.get_color('danger_hover'),
                    'text_color': 'white'
                },
                'warning': {
                    'fg_color': self.get_color('warning'),
                    'hover_color': self.get_color('warning'),
                    'text_color': 'white'
                }
            }

            config = configs.get(button_type, configs['primary'])
            button.configure(**config)
        except Exception as e:
            logger.debug(f"Error applying theme to button: {e}")

    def apply_to_entry(self, entry, entry_type='normal'):
        """تطبيق الثيم على حقل إدخال"""
        try:
            if entry_type == 'readonly':
                # ألوان خاصة للحقول المحمية
                entry.configure(
                    fg_color=self.get_color('readonly_bg'),
                    border_color=self.get_color('readonly_border'),
                    text_color=self.get_color('readonly_text')
                )
            else:
                # ألوان عادية للحقول القابلة للتحرير
                entry.configure(
                    fg_color=self.get_color('input_bg'),
                    border_color=self.get_color('input_border'),
                    text_color=self.get_color('text_primary')
                )
        except Exception as e:
            logger.debug(f"Error applying theme to entry: {e}")

    def apply_to_combobox(self, combobox):
        """تطبيق الثيم على قائمة منسدلة"""
        try:
            combobox.configure(
                fg_color=self.get_color('input_bg'),
                button_color=self.get_color('primary'),
                button_hover_color=self.get_color('primary_hover'),
                dropdown_fg_color=self.get_color('surface'),
                dropdown_text_color=self.get_color('text_primary'),
                text_color=self.get_color('text_primary')
            )
        except Exception as e:
            logger.debug(f"Error applying theme to combobox: {e}")

    def apply_to_label(self, label, label_type='primary'):
        """تطبيق الثيم على تسمية"""
        try:
            colors = {
                'primary': self.get_color('text_primary'),
                'secondary': self.get_color('text_secondary'),
                'success': self.get_color('success'),
                'danger': self.get_color('danger'),
                'warning': self.get_color('warning'),
                'readonly': self.get_color('readonly_text')  # ← إضافة لون خاص للتسميات المحمية
            }

            text_color = colors.get(label_type, self.get_color('text_primary'))
            label.configure(text_color=text_color)
        except Exception as e:
            logger.debug(f"Error applying theme to label: {e}")

    def get_readonly_colors(self) -> Dict[str, str]:
        """الحصول على ألوان الحقول المحمية"""
        return {
            'bg_color': self.get_color('readonly_bg'),
            'border_color': self.get_color('readonly_border'),
            'text_color': self.get_color('readonly_text')
        }

    def get_themed_colors_tuple(self, color_name: str) -> tuple:
        """الحصول على tuple للألوان (light, dark)"""
        # للتوافق مع الكود الموجود
        light_colors = self._get_default_colors('light')
        dark_colors = self._get_default_colors('dark')

        light_color = light_colors.get(color_name, '#ffffff')
        dark_color = dark_colors.get(color_name, '#1a1a1a')

        return (light_color, dark_color)

    def invalidate_cache(self):
        """إزالة الكاش عند تغيير الثيم"""
        self._color_cache.clear()

    def get_available_palettes(self) -> list:
        """الحصول على قائمة اللوحات المتاحة"""
        if self._has_palettes:
            try:
                all_palettes = self._get_available_palettes()
                return [p for p in all_palettes if p != 'modern_dark']
            except:
                pass
        return ['modern_purple', 'modern_blue', 'modern_emerald']

    def set_palette(self, palette_name: str):
        """تعيين لوحة ألوان جديدة"""
        if self.theme_manager and hasattr(self.theme_manager, 'config'):
            try:
                self.theme_manager.config.set('light_color_palette', palette_name)
                if hasattr(self.theme_manager.config, 'save'):
                    self.theme_manager.config.save()
                self.invalidate_cache()
                logger.info(f"Color palette changed to: {palette_name}")
            except Exception as e:
                logger.error(f"Error setting palette: {e}")


# كلاس مساعد للنوافذ
class ThemedWindow:
    """كلاس مساعد لتطبيق الثيم على النوافذ"""

    def __init__(self, window, theme_manager=None):
        self.window = window
        self.color_manager = ThemeColorManager(theme_manager)

    def apply_theme(self):
        """تطبيق الثيم الكامل على النافذة"""
        self.color_manager.apply_to_window(self.window)

    def get_color(self, color_name: str, fallback: str = None) -> str:
        """الحصول على لون"""
        return self.color_manager.get_color(color_name, fallback)

    def apply_to_widget(self, widget, widget_type: str, sub_type: str = 'normal'):
        """تطبيق الثيم على widget محدد"""
        if widget_type == 'button':
            self.color_manager.apply_to_button(widget, sub_type)
        elif widget_type == 'entry':
            self.color_manager.apply_to_entry(widget, sub_type)
        elif widget_type == 'combobox':
            self.color_manager.apply_to_combobox(widget)
        elif widget_type == 'label':
            self.color_manager.apply_to_label(widget, sub_type)
        elif widget_type == 'frame':
            self.color_manager.apply_to_frame(widget, sub_type)

    def get_readonly_colors(self) -> Dict[str, str]:
        """الحصول على ألوان الحقول المحمية"""
        return self.color_manager.get_readonly_colors()

    def refresh_theme(self):
        """تحديث الثيم"""
        self.color_manager.invalidate_cache()
        self.apply_theme()