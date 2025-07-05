# -*- coding: utf-8 -*-
"""
config/login_styles.py

تكوين الأنماط والألوان الاحترافية لنافذة تسجيل الدخول
Professional Styles Configuration for Login Window
"""

# لوحة الألوان الاحترافية
PROFESSIONAL_THEMES = {
    'light': {
        # الألوان الأساسية
        'primary': '#2563eb',           # أزرق احترافي
        'primary_hover': '#1d4ed8',     # أزرق داكن
        'primary_light': '#dbeafe',     # أزرق فاتح جداً

        # الألوان الثانوية
        'secondary': '#64748b',         # رمادي أنيق
        'secondary_hover': '#475569',   # رمادي داكن
        'secondary_light': '#e2e8f0',   # رمادي فاتح

        # ألوان الحالة
        'success': '#10b981',           # أخضر عصري
        'success_hover': '#059669',     # أخضر داكن
        'success_light': '#d1fae5',     # أخضر فاتح

        'danger': '#ef4444',            # أحمر حديث
        'danger_hover': '#dc2626',      # أحمر داكن
        'danger_light': '#fee2e2',      # أحمر فاتح

        'warning': '#f59e0b',           # برتقالي
        'warning_hover': '#d97706',     # برتقالي داكن
        'warning_light': '#fef3c7',     # برتقالي فاتح

        'info': '#3b82f6',              # أزرق معلوماتي
        'info_hover': '#2563eb',        # أزرق معلوماتي داكن
        'info_light': '#dbeafe',        # أزرق معلوماتي فاتح

        # ألوان الخلفية والسطح
        'background': '#f8fafc',        # خلفية رئيسية
        'surface': '#ffffff',           # سطح البطاقات
        'surface_hover': '#f9fafb',     # سطح عند المرور

        # الحدود والظلال
        'border': '#e2e8f0',            # حدود عادية
        'border_focus': '#2563eb',      # حدود عند التركيز
        'shadow': 'rgba(0, 0, 0, 0.1)', # لون الظل
        'shadow_hover': 'rgba(0, 0, 0, 0.15)', # ظل عند المرور

        # النصوص
        'text_primary': '#1e293b',      # نص أساسي
        'text_secondary': '#64748b',    # نص ثانوي
        'text_tertiary': '#94a3b8',     # نص ثالثي
        'text_disabled': '#cbd5e1',     # نص معطل
        'text_inverse': '#ffffff',      # نص معكوس
    },

    'dark': {
        # الألوان الأساسية
        'primary': '#3b82f6',           # أزرق لامع
        'primary_hover': '#2563eb',     # أزرق أكثر لمعاناً
        'primary_light': '#1e3a8a',     # أزرق داكن

        # الألوان الثانوية
        'secondary': '#6b7280',         # رمادي متوسط
        'secondary_hover': '#9ca3af',   # رمادي فاتح
        'secondary_light': '#374151',   # رمادي داكن

        # ألوان الحالة
        'success': '#10b981',           # أخضر لامع
        'success_hover': '#34d399',     # أخضر فاتح
        'success_light': '#064e3b',     # أخضر داكن

        'danger': '#f87171',            # أحمر لامع
        'danger_hover': '#fca5a5',      # أحمر فاتح
        'danger_light': '#7f1d1d',      # أحمر داكن

        'warning': '#fbbf24',           # أصفر لامع
        'warning_hover': '#fcd34d',     # أصفر فاتح
        'warning_light': '#78350f',     # أصفر داكن

        'info': '#60a5fa',              # أزرق معلوماتي لامع
        'info_hover': '#93bbfc',        # أزرق معلوماتي فاتح
        'info_light': '#1e3a8a',        # أزرق معلوماتي داكن

        # ألوان الخلفية والسطح
        'background': '#0f172a',        # خلفية داكنة
        'surface': '#1e293b',           # سطح البطاقات
        'surface_hover': '#334155',     # سطح عند المرور

        # الحدود والظلال
        'border': '#334155',            # حدود داكنة
        'border_focus': '#3b82f6',      # حدود عند التركيز
        'shadow': 'rgba(0, 0, 0, 0.5)', # لون الظل
        'shadow_hover': 'rgba(0, 0, 0, 0.7)', # ظل عند المرور

        # النصوص
        'text_primary': '#f1f5f9',      # نص أساسي فاتح
        'text_secondary': '#cbd5e1',    # نص ثانوي
        'text_tertiary': '#94a3b8',     # نص ثالثي
        'text_disabled': '#475569',     # نص معطل
        'text_inverse': '#0f172a',      # نص معكوس
    }
}

# تأثيرات الظلال
SHADOW_EFFECTS = {
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
    'none': 'none'
}

# تكوينات الخطوط
FONT_CONFIG = {
    'primary_family': 'Segoe UI',      # الخط الأساسي لـ Windows
    'secondary_family': 'Helvetica',   # خط احتياطي
    'arabic_family': 'Tahoma',         # خط عربي

    'sizes': {
        'xs': 10,
        'sm': 12,
        'base': 14,
        'lg': 16,
        'xl': 18,
        'xxl': 24,
        'xxxl': 30
    },

    'weights': {
        'normal': 'normal',
        'medium': 'normal',
        'bold': 'bold'
    }
}

# تكوينات الانتقالات والحركات
ANIMATION_CONFIG = {
    'durations': {
        'fast': 150,      # ميلي ثانية
        'normal': 300,
        'slow': 500
    },

    'easing': {
        'linear': 'linear',
        'ease_in': 'ease-in',
        'ease_out': 'ease-out',
        'ease_in_out': 'ease-in-out'
    }
}

# تكوينات الأبعاد والمسافات
SPACING_CONFIG = {
    'padding': {
        'xs': 5,
        'sm': 10,
        'md': 15,
        'lg': 20,
        'xl': 30
    },

    'margin': {
        'xs': 5,
        'sm': 10,
        'md': 15,
        'lg': 20,
        'xl': 30
    },

    'border_radius': {
        'none': 0,
        'sm': 5,
        'md': 10,
        'lg': 15,
        'xl': 20,
        'full': 9999  # للدوائر الكاملة
    },

    'border_width': {
        'thin': 1,
        'normal': 2,
        'thick': 3
    }
}

# دالة للحصول على موضوع حسب الوضع
def get_theme_colors(mode='light'):
    """الحصول على ألوان الموضوع حسب الوضع"""
    return PROFESSIONAL_THEMES.get(mode, PROFESSIONAL_THEMES['light'])

# دالة لتطبيق الظل على عنصر
def apply_shadow(widget, shadow_type='md'):
    """تطبيق تأثير الظل على عنصر"""
    # ملاحظة: customtkinter لا يدعم الظلال مباشرة
    # هذه الدالة للتوثيق والاستخدام المستقبلي
    return SHADOW_EFFECTS.get(shadow_type, SHADOW_EFFECTS['md'])

# دالة للحصول على حجم الخط
def get_font_size(size='base', is_small_window=False):
    """الحصول على حجم الخط المناسب"""
    base_size = FONT_CONFIG['sizes'].get(size, 14)
    if is_small_window:
        return max(base_size - 2, 10)  # تقليل الحجم للشاشات الصغيرة
    return base_size

# دالة لإنشاء تكوين خط كامل
def get_font_config(size='base', weight='normal', is_small_window=False):
    """الحصول على تكوين خط كامل"""
    return {
        'family': FONT_CONFIG['primary_family'],
        'size': get_font_size(size, is_small_window),
        'weight': FONT_CONFIG['weights'].get(weight, 'normal')
    }