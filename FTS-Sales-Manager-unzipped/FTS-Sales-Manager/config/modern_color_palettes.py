# -*- coding: utf-8 -*-
"""
config/modern_color_palettes.py

لوحات ألوان عصرية إضافية لنافذة تسجيل الدخول
Additional Modern Color Palettes for Login Window
"""

# لوحات الألوان العصرية
MODERN_PALETTES = {
    # اللوحة الحالية - بنفسجية عصرية
    'modern_purple': {
        'primary': '#5B5FFF',
        'primary_hover': '#4B4FEF',
        'secondary': '#6B7280',
        'success': '#10B981',
        'danger': '#F43F5E',
        'danger_hover': '#E11D48',
        'background': '#F9FAFB',
        'surface': '#FFFFFF',
        'input_bg': '#F3F4F6',
        'input_border': '#D1D5DB',
        'input_focus': '#5B5FFF',
        'border': '#E5E7EB',
        'text_primary': '#111827',
        'text_secondary': '#6B7280',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة أزرق كحلي عصري
    'modern_blue': {
        'primary': '#0EA5E9',
        'primary_hover': '#0284C7',
        'secondary': '#64748B',
        'success': '#22C55E',
        'danger': '#EF4444',
        'danger_hover': '#DC2626',
        'background': '#F8FAFC',
        'surface': '#FFFFFF',
        'input_bg': '#F1F5F9',
        'input_border': '#CBD5E1',
        'input_focus': '#0EA5E9',
        'border': '#E2E8F0',
        'text_primary': '#0F172A',
        'text_secondary': '#64748B',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة خضراء زمردية
    'modern_emerald': {
        'primary': '#10B981',
        'primary_hover': '#059669',
        'secondary': '#6B7280',
        'success': '#34D399',
        'danger': '#F87171',
        'danger_hover': '#EF4444',
        'background': '#F9FAFB',
        'surface': '#FFFFFF',
        'input_bg': '#F3F4F6',
        'input_border': '#D1D5DB',
        'input_focus': '#10B981',
        'border': '#E5E7EB',
        'text_primary': '#111827',
        'text_secondary': '#6B7280',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة وردية عصرية
    'modern_pink': {
        'primary': '#EC4899',
        'primary_hover': '#DB2777',
        'secondary': '#6B7280',
        'success': '#10B981',
        'danger': '#F43F5E',
        'danger_hover': '#E11D48',
        'background': '#FEF3F2',
        'surface': '#FFFFFF',
        'input_bg': '#FEE2E2',
        'input_border': '#FCA5A5',
        'input_focus': '#EC4899',
        'border': '#FBBF24',
        'text_primary': '#1F2937',
        'text_secondary': '#6B7280',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة داكنة احترافية
    'modern_dark': {
        'primary': '#6366F1',
        'primary_hover': '#4F46E5',
        'secondary': '#9CA3AF',
        'success': '#34D399',
        'danger': '#F87171',
        'danger_hover': '#EF4444',
        'background': '#111827',
        'surface': '#1F2937',
        'input_bg': '#374151',
        'input_border': '#4B5563',
        'input_focus': '#6366F1',
        'border': '#374151',
        'text_primary': '#F9FAFB',
        'text_secondary': '#D1D5DB',
        'shadow': 'rgba(0, 0, 0, 0.3)'
    },

    # لوحة برتقالية دافئة
    'modern_orange': {
        'primary': '#F97316',
        'primary_hover': '#EA580C',
        'secondary': '#6B7280',
        'success': '#22C55E',
        'danger': '#EF4444',
        'danger_hover': '#DC2626',
        'background': '#FFFBEB',
        'surface': '#FFFFFF',
        'input_bg': '#FEF3C7',
        'input_border': '#FDE68A',
        'input_focus': '#F97316',
        'border': '#FCD34D',
        'text_primary': '#1F2937',
        'text_secondary': '#6B7280',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة أرجوانية أنيقة
    'modern_indigo': {
        'primary': '#7C3AED',
        'primary_hover': '#6D28D9',
        'secondary': '#6B7280',
        'success': '#10B981',
        'danger': '#F43F5E',
        'danger_hover': '#E11D48',
        'background': '#FAF5FF',
        'surface': '#FFFFFF',
        'input_bg': '#F3E8FF',
        'input_border': '#DDD6FE',
        'input_focus': '#7C3AED',
        'border': '#C4B5FD',
        'text_primary': '#1F2937',
        'text_secondary': '#6B7280',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    },

    # لوحة كلاسيكية زرقاء
    'classic_blue': {
        'primary': '#2563EB',
        'primary_hover': '#1D4ED8',
        'secondary': '#64748B',
        'success': '#16A34A',
        'danger': '#DC2626',
        'danger_hover': '#B91C1C',
        'background': '#F0F9FF',
        'surface': '#FFFFFF',
        'input_bg': '#E0F2FE',
        'input_border': '#BAE6FD',
        'input_focus': '#2563EB',
        'border': '#93C5FD',
        'text_primary': '#1E293B',
        'text_secondary': '#64748B',
        'shadow': 'rgba(0, 0, 0, 0.05)'
    }
}

# دالة للحصول على لوحة ألوان
def get_color_palette(palette_name='modern_purple'):
    """
    الحصول على لوحة ألوان محددة

    Args:
        palette_name: اسم اللوحة المطلوبة

    Returns:
        dict: لوحة الألوان المطلوبة
    """
    return MODERN_PALETTES.get(palette_name, MODERN_PALETTES['modern_purple'])

# دالة لعرض جميع اللوحات المتاحة
def get_available_palettes():
    """الحصول على قائمة بأسماء جميع اللوحات المتاحة"""
    return list(MODERN_PALETTES.keys())

# دالة لمعاينة لوحة ألوان
def preview_palette(palette_name):
    """طباعة معاينة للوحة ألوان"""
    palette = get_color_palette(palette_name)
    print(f"\n=== {palette_name.upper()} PALETTE ===")
    for key, value in palette.items():
        print(f"{key}: {value}")
    print("=" * 30)

# مثال لكيفية استخدام لوحة ألوان مختلفة في login_window.py:
"""
# في بداية ملف login_window.py
from config.modern_color_palettes import get_color_palette

# اختيار لوحة الألوان المطلوبة
PROFESSIONAL_COLORS = get_color_palette('modern_blue')  # أو أي لوحة أخرى

# أو يمكن جعلها قابلة للتخصيص من خلال الإعدادات
theme_palette = config_manager.get('color_palette', 'modern_purple')
PROFESSIONAL_COLORS = get_color_palette(theme_palette)
"""