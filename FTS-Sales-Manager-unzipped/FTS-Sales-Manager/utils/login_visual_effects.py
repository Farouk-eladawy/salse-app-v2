# -*- coding: utf-8 -*-
"""
utils/login_visual_effects.py

تأثيرات بصرية وحركات متقدمة لنافذة تسجيل الدخول
Advanced Visual Effects and Animations for Login Window
"""

import customtkinter as ctk
from typing import Optional, Tuple, Callable
import threading
import time
import math

class LoginVisualEffects:
    """كلاس للتأثيرات البصرية المتقدمة"""

    @staticmethod
    def create_gradient_frame(parent, colors: Tuple[str, str], orientation='vertical', **kwargs):
        """إنشاء إطار بتدرج لوني"""
        # customtkinter لا يدعم التدرجات مباشرة، لذا نستخدم لون واحد
        # يمكن استخدام Canvas للتدرجات المعقدة
        frame = ctk.CTkFrame(parent, fg_color=colors[0], **kwargs)
        return frame

    @staticmethod
    def add_hover_effect(widget, normal_color: str, hover_color: str,
                        scale_factor: float = 1.05, duration: int = 200):
        """إضافة تأثير hover متقدم"""
        original_width = None
        original_height = None

        def on_enter(event):
            nonlocal original_width, original_height
            try:
                # حفظ الأبعاد الأصلية
                if hasattr(widget, 'cget'):
                    original_width = widget.cget('width')
                    original_height = widget.cget('height')

                # تغيير اللون
                if hasattr(widget, 'configure'):
                    if 'fg_color' in widget.configure():
                        widget.configure(fg_color=hover_color)

                # تأثير التكبير (محاكاة)
                if original_width and original_height and scale_factor > 1:
                    new_width = int(original_width * scale_factor)
                    new_height = int(original_height * scale_factor)
                    # لا يمكن تطبيق التكبير الفعلي في customtkinter

            except Exception as e:
                pass

        def on_leave(event):
            try:
                # إعادة اللون الأصلي
                if hasattr(widget, 'configure'):
                    if 'fg_color' in widget.configure():
                        widget.configure(fg_color=normal_color)

            except Exception as e:
                pass

        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    @staticmethod
    def create_shadow_effect(widget, parent, shadow_color='#00000020',
                           offset_x=0, offset_y=4, blur_radius=10):
        """محاكاة تأثير الظل"""
        # إنشاء إطار خلفي للظل
        shadow_frame = ctk.CTkFrame(
            parent,
            fg_color=shadow_color,
            corner_radius=widget.cget('corner_radius') if hasattr(widget, 'cget') else 0
        )

        # وضع الظل خلف العنصر
        shadow_frame.place(
            in_=widget,
            x=offset_x,
            y=offset_y,
            relwidth=1,
            relheight=1
        )

        # رفع العنصر الأصلي فوق الظل
        widget.lift()

        return shadow_frame

    @staticmethod
    def animate_fade_in(widget, duration: int = 500, steps: int = 20):
        """تأثير الظهور التدريجي"""
        # customtkinter لا يدعم transparency مباشرة
        # لذا نحاكي التأثير بإظهار العنصر تدريجياً

        def fade_animation():
            widget.pack_forget()
            time.sleep(0.1)
            widget.pack()

        thread = threading.Thread(target=fade_animation, daemon=True)
        thread.start()

    @staticmethod
    def create_loading_animation(parent, size: int = 40, color: str = '#2563eb'):
        """إنشاء رسوم متحركة للتحميل"""
        loading_frame = ctk.CTkFrame(parent, fg_color="transparent")

        # دائرة التحميل
        spinner = ctk.CTkProgressBar(
            loading_frame,
            mode="indeterminate",
            width=size * 3,
            height=size // 4,
            progress_color=color
        )
        spinner.pack()
        spinner.start()

        # نص التحميل
        loading_text = ctk.CTkLabel(
            loading_frame,
            text="Loading...",
            font=ctk.CTkFont(size=12),
            text_color=color
        )
        loading_text.pack(pady=(5, 0))

        return loading_frame, spinner

    @staticmethod
    def pulse_effect(widget, color1: str, color2: str, duration: int = 1000):
        """تأثير النبض للعناصر المهمة"""
        def pulse():
            toggle = True
            while True:
                try:
                    if hasattr(widget, 'winfo_exists') and widget.winfo_exists():
                        color = color1 if toggle else color2
                        widget.configure(fg_color=color)
                        toggle = not toggle
                        time.sleep(duration / 2000)  # تحويل إلى ثواني
                    else:
                        break
                except:
                    break

        thread = threading.Thread(target=pulse, daemon=True)
        thread.start()

    @staticmethod
    def create_ripple_effect(button, ripple_color: str = '#ffffff40'):
        """تأثير التموج عند النقر"""
        def on_click(event):
            # محاكاة بسيطة للتأثير
            original_color = button.cget('fg_color')
            button.configure(fg_color=ripple_color)
            button.after(200, lambda: button.configure(fg_color=original_color))

        button.bind("<Button-1>", on_click)

    @staticmethod
    def shake_effect(widget, amplitude: int = 10, duration: int = 500):
        """تأثير الاهتزاز للأخطاء"""
        original_x = widget.winfo_x()

        def shake():
            steps = 10
            for i in range(steps):
                if not widget.winfo_exists():
                    break

                # حساب الإزاحة
                progress = i / steps
                offset = int(amplitude * math.sin(progress * math.pi * 4) * (1 - progress))

                # تطبيق الإزاحة
                widget.place(x=original_x + offset)
                time.sleep(duration / steps / 1000)

            # إعادة للموضع الأصلي
            if widget.winfo_exists():
                widget.place(x=original_x)

        thread = threading.Thread(target=shake, daemon=True)
        thread.start()

    @staticmethod
    def create_tooltip(widget, text: str, delay: int = 1000):
        """إنشاء تلميح أداة احترافي"""
        tooltip = None

        def show_tooltip(event):
            nonlocal tooltip

            # إنشاء نافذة التلميح
            tooltip = ctk.CTkToplevel(widget)
            tooltip.withdraw()
            tooltip.overrideredirect(True)

            # تصميم التلميح
            tooltip_label = ctk.CTkLabel(
                tooltip,
                text=text,
                font=ctk.CTkFont(size=11),
                fg_color='#1e293b',
                text_color='white',
                corner_radius=6,
                padx=10,
                pady=5
            )
            tooltip_label.pack()

            # حساب الموضع
            x = widget.winfo_rootx() + widget.winfo_width() // 2
            y = widget.winfo_rooty() - 30

            tooltip.geometry(f"+{x}+{y}")
            tooltip.deiconify()

        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None

        widget.bind("<Enter>", lambda e: widget.after(delay, lambda: show_tooltip(e)))
        widget.bind("<Leave>", hide_tooltip)

    @staticmethod
    def apply_glass_effect(frame):
        """تطبيق تأثير الزجاج (glassmorphism)"""
        # customtkinter لا يدعم الشفافية الحقيقية
        # لكن يمكن محاكاة التأثير بالألوان
        frame.configure(
            fg_color='#ffffff10',  # شبه شفاف
            border_width=1,
            border_color='#ffffff30'
        )

    @staticmethod
    def create_gradient_button(parent, text: str, colors: Tuple[str, str], **kwargs):
        """إنشاء زر بتدرج لوني"""
        # استخدام اللون الأول كلون أساسي واللون الثاني للـ hover
        button = ctk.CTkButton(
            parent,
            text=text,
            fg_color=colors[0],
            hover_color=colors[1],
            **kwargs
        )

        # إضافة تأثيرات إضافية
        LoginVisualEffects.create_ripple_effect(button)

        return button

    @staticmethod
    def create_animated_entry(parent, placeholder: str, **kwargs):
        """إنشاء حقل إدخال مع رسوم متحركة"""
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, **kwargs)

        # تأثير التركيز
        def on_focus_in(event):
            if hasattr(entry, 'configure'):
                entry.configure(border_width=2)

        def on_focus_out(event):
            if hasattr(entry, 'configure'):
                entry.configure(border_width=1)

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

        return entry

    @staticmethod
    def create_success_animation(parent, message: str = "Success!", duration: int = 2000):
        """رسوم متحركة للنجاح"""
        success_frame = ctk.CTkFrame(
            parent,
            fg_color='#10b981',
            corner_radius=10
        )

        # أيقونة النجاح
        icon_label = ctk.CTkLabel(
            success_frame,
            text="✓",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="white"
        )
        icon_label.pack(pady=(10, 5))

        # رسالة النجاح
        message_label = ctk.CTkLabel(
            success_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color="white"
        )
        message_label.pack(pady=(0, 10), padx=20)

        # إظهار مؤقت
        success_frame.pack(pady=20)
        success_frame.after(duration, success_frame.destroy)

        return success_frame

# دوال مساعدة لتطبيق التأثيرات على نافذة تسجيل الدخول
def enhance_login_window(login_window):
    """تطبيق جميع التحسينات البصرية على نافذة تسجيل الدخول"""
    effects = LoginVisualEffects()

    # تطبيق تأثيرات على الأزرار
    if hasattr(login_window, 'btn_login'):
        effects.add_hover_effect(
            login_window.btn_login,
            '#2563eb',
            '#1d4ed8',
            scale_factor=1.02
        )
        effects.create_ripple_effect(login_window.btn_login)
        effects.create_tooltip(
            login_window.btn_login,
            "Press Enter to login quickly"
        )

    if hasattr(login_window, 'btn_cancel'):
        effects.add_hover_effect(
            login_window.btn_cancel,
            'transparent',
            '#fee2e2'
        )

    # تطبيق تأثيرات على حقول الإدخال
    if hasattr(login_window, 'entry_username'):
        effects.create_tooltip(
            login_window.entry_username,
            "Enter your registered username"
        )

    if hasattr(login_window, 'entry_password'):
        effects.create_tooltip(
            login_window.entry_password,
            "Enter your secure password"
        )

    # تطبيق تأثير الظهور التدريجي
    if hasattr(login_window, 'scrollable_frame'):
        effects.animate_fade_in(login_window.scrollable_frame)

    return login_window