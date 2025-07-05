# -*- coding: utf-8 -*-
"""
utils/window_manager.py - نسخة محسنة مع دعم ملء الشاشة وارتفاع الشاشة الكامل وارتفاع منطقة العمل

أداة احترافية لإدارة النوافذ مع:
- التوسيط على الشاشة دائماً
- التكيف مع حجم الشاشة
- ضمان ظهور النافذة فوق النوافذ الأخرى
- حل مشكلة ظهور النوافذ في الجانب الأيمن
- إظهار سلس بدون وميض
- دعم ملء الشاشة كوضع افتراضي للنافذة الرئيسية
- دعم ارتفاع الشاشة الكامل لنوافذ تسجيل الدخول
- دعم ارتفاع منطقة العمل (حتى شريط المهام) لنوافذ الإضافة والتعديل

التحديثات الأخيرة:
- إضافة workarea_height_mode لجعل النافذة بارتفاع منطقة العمل (حتى شريط المهام)
- إضافة get_available_screen_area للحصول على المساحة المتاحة بدقة
- تحسين _apply_workarea_height_mode لجميع أنظمة التشغيل
- إضافة setup_add_edit_window للاستخدام السريع مع نوافذ الإضافة والتعديل
- دعم محسن لحساب ارتفاع شريط المهام على Windows
- إضافة دعم لنوافذ الحوار بارتفاع منطقة العمل
"""

import platform
import customtkinter as ctk
import tkinter as tk
from typing import Union, Optional, Callable, Tuple
from weakref import WeakSet
import time
import weakref


class WindowManager:
    """مدير النوافذ المحسن مع معالجة آمنة للنوافذ ودعم جميع أوضاع الارتفاع"""

    # استخدام WeakSet لتجنب مشاكل المراجع الدائرية
    _active_windows = WeakSet()

    @staticmethod
    def get_available_screen_area():
        """الحصول على المساحة المتاحة للنوافذ (بدون شريط المهام)"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # إخفاء النافذة المؤقتة

            # الحصول على أبعاد الشاشة الكاملة
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()

            # محاولة الحصول على المساحة المتاحة (بدون شريط المهام)
            try:
                # على Windows
                if platform.system() == "Windows":
                    import ctypes
                    from ctypes import wintypes

                    # الحصول على معلومات منطقة العمل
                    user32 = ctypes.windll.user32
                    rect = wintypes.RECT()
                    user32.SystemParametersInfoW(48, 0, ctypes.byref(rect), 0)  # SPI_GETWORKAREA

                    available_width = rect.right - rect.left
                    available_height = rect.bottom - rect.top
                    work_area_x = rect.left
                    work_area_y = rect.top

                    root.destroy()
                    return available_width, available_height, work_area_x, work_area_y

            except Exception as e:
                print(f"فشل في الحصول على منطقة العمل: {e}")

            # إذا فشل، استخدم تقدير افتراضي (شريط المهام عادة 40-50 بكسل)
            taskbar_height = 50
            available_width = screen_width
            available_height = screen_height - taskbar_height
            work_area_x = 0
            work_area_y = 0

            root.destroy()
            return available_width, available_height, work_area_x, work_area_y

        except Exception as e:
            print(f"خطأ في حساب المساحة المتاحة: {e}")
            # قيم افتراضية آمنة
            return 1920, 1030, 0, 0

    @staticmethod
    def _apply_workarea_height_mode(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel], size: tuple = None):
        """تطبيق وضع ارتفاع منطقة العمل (من أعلى الشاشة إلى شريط المهام)"""
        try:
            # الحصول على المساحة المتاحة
            available_width, available_height, work_x, work_y = WindowManager.get_available_screen_area()

            # تحديد العرض
            if size and len(size) >= 1:
                window_width = size[0]
            else:
                # عرض افتراضي مناسب لنوافذ الإضافة/التعديل
                window_width = min(600, int(available_width * 0.4))

            # ارتفاع منطقة العمل الكامل
            window_height = available_height

            # حساب الموضع المتوسط أفقياً مع وضع النافذة في أعلى منطقة العمل
            x = (available_width - window_width) // 2
            y = work_y  # بداية منطقة العمل (عادة 0)

            # تطبيق الأبعاد والموضع
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # تحديث النافذة
            window.update_idletasks()
            window.update()

            print(f"تم تطبيق وضع ارتفاع منطقة العمل: {window_width}x{window_height}+{x}+{y}")
            print(f"منطقة العمل: {available_width}x{available_height} من ({work_x},{work_y})")

        except Exception as e:
            print(f"خطأ في تطبيق وضع ارتفاع منطقة العمل: {e}")
            # في حالة الفشل، استخدم إعدادات افتراضية آمنة
            try:
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()
                # تقدير ارتفاع شريط المهام
                safe_height = screen_height - 50
                window_width = size[0] if size else 600
                x = (screen_width - window_width) // 2
                window.geometry(f"{window_width}x{safe_height}+{x}+0")
            except:
                pass

    @staticmethod
    def setup_centered_window(window: Union[ctk.CTk, ctk.CTkToplevel],
                             size: tuple = None,
                             parent: Optional[Union[ctk.CTk, ctk.CTkToplevel]] = None,
                             full_height_mode: bool = False,
                             workarea_height_mode: bool = False,  # جديد: للارتفاع حتى شريط المهام
                             **kwargs) -> None:
        """إعداد نافذة مع ضمان التوسيط الصحيح مع دعم أوضاع الارتفاع المختلفة"""

        # إخفاء النافذة أولاً لتجنب الوميض
        if isinstance(window, (ctk.CTkToplevel, tk.Toplevel)):
            window.withdraw()

        # تعيين الحجم بناءً على الوضع المطلوب
        if workarea_height_mode:
            # استخدام ارتفاع منطقة العمل (حتى شريط المهام)
            WindowManager._apply_workarea_height_mode(window, size)
        elif full_height_mode:
            # استخدام ارتفاع الشاشة الكامل (فوق شريط المهام أيضاً)
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # تحديد العرض (إما المحدد أو القيمة الافتراضية)
            if size:
                window_width = size[0]
            else:
                window_width = min(500, int(screen_width * 0.4))  # عرض متوسط مناسب

            # استخدام ارتفاع الشاشة الكامل بدون هوامش
            window_height = screen_height  # ارتفاع الشاشة الكامل

            window.geometry(f"{window_width}x{window_height}")
        elif size:
            window.geometry(f"{size[0]}x{size[1]}")

        # فرض التحديث الكامل
        window.update_idletasks()
        window.update()

        # حساب الموضع بناءً على الوضع
        if workarea_height_mode:
            # الموضع محدد مسبقاً في _apply_workarea_height_mode
            pass
        elif full_height_mode:
            # الموضع للارتفاع الكامل
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            window_width = window.winfo_width() if window.winfo_width() > 1 else window.winfo_reqwidth()

            # حساب الموضع المتوسط
            x = (screen_width - window_width) // 2
            y = 0  # بدون هامش علوي - ملء الشاشة كاملة
            window_height = screen_height  # ارتفاع الشاشة الكامل

            # التأكد من بقاء النافذة داخل الشاشة
            x = max(10, min(x, screen_width - window_width - 10))

            # تطبيق الموضع والحجم النهائي
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        else:
            # التوسيط العادي
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # الحصول على حجم النافذة الفعلي
            if size:
                window_width, window_height = size
            else:
                window_width = window.winfo_reqwidth() if window.winfo_width() <= 1 else window.winfo_width()
                window_height = window.winfo_reqheight() if window.winfo_height() <= 1 else window.winfo_height()

            # حساب الموضع المتوسط
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            # التأكد من بقاء النافذة داخل الشاشة
            x = max(10, min(x, screen_width - window_width - 10))
            y = max(10, min(y, screen_height - window_height - 50))  # 50 لترك مساحة لشريط المهام

            # تطبيق الموضع والحجم النهائي
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # تطبيق باقي الإعدادات (بدون التوسيط مرة أخرى)
        kwargs['center'] = False  # منع التوسيط المكرر
        kwargs['use_smooth_show'] = False  # النافذة مخفية بالفعل
        kwargs['full_height_mode'] = full_height_mode  # تمرير المعلومة للدالة الأساسية
        kwargs['workarea_height_mode'] = workarea_height_mode  # تمرير المعلومة الجديدة
        WindowManager.setup_window(window, parent=parent, **kwargs)

        # إظهار النافذة بشكل سلس
        if isinstance(window, (ctk.CTkToplevel, tk.Toplevel)):
            window.deiconify()
            window.lift()
            window.focus_force()

    @staticmethod
    def setup_window(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                    parent: Optional[Union[ctk.CTk, ctk.CTkToplevel]] = None,
                    center: bool = True,
                    center_on_screen: bool = True,  # للتوسيط على الشاشة دائماً
                    modal: bool = False,
                    focus: bool = True,
                    topmost_duration: int = 300,
                    min_size: tuple = None,
                    max_size: tuple = None,
                    size: tuple = None,
                    responsive: bool = True,  # للتكيف مع حجم الشاشة
                    max_screen_ratio: float = 0.9,  # نسبة الحد الأقصى من الشاشة
                    use_smooth_show: bool = True,  # للإظهار السلس
                    fullscreen_default: bool = False,  # للنافذة الرئيسية
                    full_height_mode: bool = False,  # لارتفاع الشاشة الكامل
                    workarea_height_mode: bool = False) -> None:  # جديد: لارتفاع منطقة العمل
        """إعداد النافذة لتظهر بشكل احترافي مع دعم جميع أوضاع الارتفاع"""
        try:
            # إخفاء النافذة مؤقتاً لتجنب الوميض (حل مشكلة التموضع)
            if use_smooth_show and isinstance(window, (ctk.CTkToplevel, tk.Toplevel)):
                window.withdraw()

            # إضافة النافذة إلى المجموعة الضعيفة
            WindowManager._active_windows.add(window)

            # التحقق من وضع ملء الشاشة
            if fullscreen_default:
                # تطبيق ملء الشاشة فوراً
                WindowManager._apply_fullscreen(window)
                # تجاهل باقي إعدادات الحجم والموضع
                center = False
                size = None
                full_height_mode = False
                workarea_height_mode = False
            elif workarea_height_mode:
                # تطبيق وضع ارتفاع منطقة العمل
                WindowManager._apply_workarea_height_mode(window, size)
                center = False  # لا نحتاج توسيط لأن الموضع محدد مسبقاً
            elif full_height_mode:
                # تطبيق وضع ارتفاع الشاشة الكامل
                WindowManager._apply_full_height_mode(window, size)
                center = False  # لا نحتاج توسيط لأن الموضع محدد مسبقاً
            else:
                # الحصول على حجم الشاشة
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()

                # تعيين الحجم مع التكيف مع الشاشة
                if size and responsive:
                    # حساب الحجم المناسب مع عدم تجاوز نسبة معينة من الشاشة
                    max_width = int(screen_width * max_screen_ratio)
                    max_height = int(screen_height * max_screen_ratio)

                    # تطبيق الحد الأقصى
                    actual_width = min(size[0], max_width)
                    actual_height = min(size[1], max_height)

                    window.geometry(f"{actual_width}x{actual_height}")
                elif size:
                    window.geometry(f"{size[0]}x{size[1]}")

                # فرض التحديث الكامل
                window.update_idletasks()
                window.update()

                # تعيين الحدود مع مراعاة حجم الشاشة
                if min_size:
                    window.minsize(min_size[0], min_size[1])
                if max_size and responsive:
                    # تعديل الحد الأقصى ليتناسب مع الشاشة
                    adjusted_max_width = min(max_size[0], int(screen_width * max_screen_ratio))
                    adjusted_max_height = min(max_size[1], int(screen_height * max_screen_ratio))
                    window.maxsize(adjusted_max_width, adjusted_max_height)
                elif max_size:
                    window.maxsize(max_size[0], max_size[1])

                # توسيط النافذة
                if center:
                    if center_on_screen:
                        # التوسيط الفوري على الشاشة
                        WindowManager.center_window_on_screen(window)
                    else:
                        # التوسيط على النافذة الأصلية
                        WindowManager.center_window(window, parent)

            # جعل النافذة تابعة (لكن مع البقاء فوقها)
            if parent and hasattr(window, 'transient'):
                try:
                    if parent.winfo_exists():
                        window.transient(parent)
                except:
                    pass

            # إظهار النافذة إذا كانت مخفية
            if use_smooth_show and isinstance(window, (ctk.CTkToplevel, tk.Toplevel)):
                window.deiconify()

            # رفع النافذة لتظهر فوق جميع النوافذ (إلا إذا كانت في ملء الشاشة)
            if not fullscreen_default:
                WindowManager.force_bring_to_front(window, topmost_duration)

            # إعطاء التركيز
            if focus:
                WindowManager.set_focus(window)

            # جعلها مشروطة
            if modal and parent:
                WindowManager.make_modal(window, parent)

            # تطبيق إعدادات النظام
            WindowManager._apply_platform_specific(window, fullscreen_default)

            # ربط حدث الإغلاق بطريقة آمنة
            WindowManager._setup_close_handler(window)

            # التأكد من التموضع الصحيح بعد تأخير بسيط (فقط للنوافذ العادية)
            if center and center_on_screen and not fullscreen_default and not full_height_mode and not workarea_height_mode:
                WindowManager.ensure_correct_position(window, delay=100)

        except Exception as e:
            print(f"خطأ في إعداد النافذة: {e}")

    @staticmethod
    def _apply_full_height_mode(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel], size: tuple = None):
        """تطبيق وضع ارتفاع الشاشة الكامل بدون هوامش"""
        try:
            # الحصول على أبعاد الشاشة
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # تحديد العرض
            if size and len(size) >= 1:
                window_width = size[0]
            else:
                # عرض افتراضي مناسب لنافذة تسجيل الدخول
                window_width = min(500, int(screen_width * 0.4))

            # ارتفاع الشاشة الكامل بدون هوامش
            window_height = screen_height

            # حساب الموضع المتوسط أفقياً مع وضع النافذة في أقصى الأعلى
            x = (screen_width - window_width) // 2
            y = 0  # بدون هامش علوي - ملء الشاشة كاملة

            # تطبيق الأبعاد والموضع
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # تحديث النافذة
            window.update_idletasks()
            window.update()

            print(f"تم تطبيق وضع ارتفاع الشاشة الكامل: {window_width}x{window_height}+{x}+{y}")

        except Exception as e:
            print(f"خطأ في تطبيق وضع ارتفاع الشاشة الكامل: {e}")
            # في حالة الفشل، استخدم إعدادات افتراضية
            try:
                screen_height = window.winfo_screenheight()
                window.geometry(f"500x{screen_height}+400+0")
            except:
                pass

    @staticmethod
    def _apply_fullscreen(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]):
        """تطبيق وضع ملء الشاشة بناءً على نظام التشغيل"""
        try:
            system = platform.system()

            # الحصول على أبعاد الشاشة وتعيين النافذة لتملأ الشاشة أولاً
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            window.geometry(f"{screen_width}x{screen_height}+0+0")

            # تحديث النافذة قبل تطبيق الحالة
            window.update_idletasks()
            window.update()

            if system == "Windows":
                # للـ Windows، استخدم state('zoomed') للاحتفاظ بشريط المهام
                try:
                    window.state('zoomed')
                    print("تم تطبيق وضع ملء الشاشة (Windows zoomed)")
                except Exception as e:
                    print(f"فشل في zoomed، محاولة fullscreen: {e}")
                    # إذا فشل zoomed، جرب fullscreen
                    window.attributes('-fullscreen', True)
                    print("تم تطبيق وضع ملء الشاشة (Windows fullscreen)")

            elif system == "Linux":
                # للـ Linux، جرب zoomed أولاً ثم fullscreen
                try:
                    window.attributes('-zoomed', True)
                    print("تم تطبيق وضع ملء الشاشة (Linux zoomed)")
                except Exception as e:
                    print(f"فشل في zoomed، محاولة fullscreen: {e}")
                    window.attributes('-fullscreen', True)
                    print("تم تطبيق وضع ملء الشاشة (Linux fullscreen)")

            elif system == "Darwin":  # macOS
                window.attributes('-fullscreen', True)
                print("تم تطبيق وضع ملء الشاشة (macOS)")

            # تحديث النافذة مرة أخيرة
            window.update_idletasks()
            window.update()

        except Exception as e:
            print(f"خطأ في تطبيق ملء الشاشة: {e}")
            # في حالة الفشل، استخدم الحد الأقصى
            try:
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()
                window.geometry(f"{screen_width-50}x{screen_height-100}+25+25")
                print("تم استخدام حجم الشاشة الأقصى كبديل")
            except:
                pass

    @staticmethod
    def center_window_on_screen(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> None:
        """توسيط النافذة على الشاشة دائماً مع ضمان الدقة"""
        try:
            # فرض التحديث الكامل أولاً
            window.update_idletasks()
            window.update()

            # الحصول على حجم النافذة بطريقة موثوقة
            window_width, window_height = WindowManager._get_window_size(window)

            # إذا كانت القيم غير صحيحة، انتظر وحاول مرة أخرى
            if window_width <= 1 or window_height <= 1:
                window.update()
                window_width = window.winfo_reqwidth()
                window_height = window.winfo_reqheight()

            # الحصول على حجم الشاشة
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # حساب الموضع المتوسط على الشاشة
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2

            # التأكد من أن النافذة داخل حدود الشاشة مع هامش أمان
            margin = 20
            x = max(margin, min(x, screen_width - window_width - margin))
            y = max(margin, min(y, screen_height - window_height - margin))

            # تعيين الموضع بدقة
            window.geometry(f"{window_width}x{window_height}+{x}+{y}")

            # فرض التحديث النهائي
            window.update()

        except Exception as e:
            print(f"خطأ في توسيط النافذة على الشاشة: {e}")

    @staticmethod
    def force_bring_to_front(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                           duration: int = 300) -> None:
        """رفع النافذة للأعلى بشكل قوي لضمان ظهورها فوق جميع النوافذ"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            # رفع النافذة عدة مرات للتأكيد
            window.lift()
            window.update()

            # جعلها في الأعلى مؤقتاً
            window.attributes('-topmost', True)
            window.update()

            # إعطاء التركيز
            window.focus_force()
            window.focus_set()

            # رفع مرة أخرى للتأكيد
            window.lift()

            # على Windows، استخدم طريقة إضافية
            if platform.system() == "Windows":
                window.wm_attributes('-topmost', True)
                window.update()

            if duration > 0:
                # إزالة topmost بعد فترة
                window_ref = weakref.ref(window)
                window.after(duration, lambda: WindowManager._remove_topmost_safe(window_ref))

        except Exception as e:
            print(f"خطأ في رفع النافذة: {e}")

    @staticmethod
    def adjust_window_size_to_screen(window: Union[ctk.CTk, ctk.CTkToplevel],
                                   preferred_width: int,
                                   preferred_height: int,
                                   max_screen_ratio: float = 0.9) -> Tuple[int, int]:
        """تعديل حجم النافذة ليتناسب مع حجم الشاشة"""
        try:
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()

            # حساب الحد الأقصى المسموح
            max_width = int(screen_width * max_screen_ratio)
            max_height = int(screen_height * max_screen_ratio)

            # تطبيق الحدود
            actual_width = min(preferred_width, max_width)
            actual_height = min(preferred_height, max_height)

            return actual_width, actual_height

        except Exception as e:
            print(f"خطأ في تعديل حجم النافذة: {e}")
            return preferred_width, preferred_height

    @staticmethod
    def _get_window_size(window) -> Tuple[int, int]:
        """الحصول على حجم النافذة الفعلي"""
        try:
            # محاولة الحصول على الحجم من geometry
            geometry = window.geometry()
            if geometry:
                # تحليل السلسلة "widthxheight+x+y"
                size_part = geometry.split('+')[0]
                if 'x' in size_part:
                    width, height = map(int, size_part.split('x'))
                    return width, height
        except:
            pass

        # إذا فشل، استخدم winfo_width/height
        width = window.winfo_width()
        height = window.winfo_height()

        # إذا كانت القيم 1، استخدم reqwidth/reqheight
        if width <= 1 or height <= 1:
            width = window.winfo_reqwidth()
            height = window.winfo_reqheight()

        return width, height

    @staticmethod
    def center_window(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                     parent: Optional[Union[ctk.CTk, ctk.CTkToplevel]] = None) -> None:
        """توسيط النافذة (الطريقة القديمة - للتوافق)"""
        try:
            # تحديث النافذة لضمان الحصول على الأبعاد الصحيحة
            window.update_idletasks()

            # الحصول على حجم النافذة
            window_width, window_height = WindowManager._get_window_size(window)

            if parent and WindowManager._is_window_valid(parent):
                # توسيط على النافذة الأصلية
                parent.update_idletasks()

                parent_x = parent.winfo_x()
                parent_y = parent.winfo_y()
                parent_width = parent.winfo_width()
                parent_height = parent.winfo_height()

                # التأكد من أن قيم النافذة الأصلية صحيحة
                if parent_width <= 1 or parent_height <= 1:
                    parent_width, parent_height = WindowManager._get_window_size(parent)

                x = parent_x + (parent_width - window_width) // 2
                y = parent_y + (parent_height - window_height) // 2
            else:
                # توسيط على الشاشة
                screen_width = window.winfo_screenwidth()
                screen_height = window.winfo_screenheight()

                x = (screen_width - window_width) // 2
                y = (screen_height - window_height) // 2

            # التأكد من أن النافذة داخل حدود الشاشة
            x = max(0, x)
            y = max(0, y)

            # تعيين الموضع فقط (بدون تغيير الحجم)
            window.geometry(f"+{x}+{y}")

            # تحديث النافذة
            window.update()

        except Exception as e:
            print(f"خطأ في توسيط النافذة: {e}")

    @staticmethod
    def center_window_delayed(window: Union[ctk.CTk, ctk.CTkToplevel],
                            parent: Optional[Union[ctk.CTk, ctk.CTkToplevel]] = None,
                            delay: int = 50,
                            on_screen: bool = True) -> None:
        """توسيط النافذة مع تأخير للتأكد من اكتمال الرسم"""
        if on_screen:
            window.after(delay, lambda: WindowManager.center_window_on_screen(window))
        else:
            window.after(delay, lambda: WindowManager.center_window(window, parent))

    @staticmethod
    def set_window_position(window: Union[ctk.CTk, ctk.CTkToplevel],
                          x: int, y: int) -> None:
        """تعيين موضع النافذة بشكل مباشر"""
        try:
            window.geometry(f"+{x}+{y}")
            window.update()
        except Exception as e:
            print(f"خطأ في تعيين موضع النافذة: {e}")

    @staticmethod
    def set_window_size_and_position(window: Union[ctk.CTk, ctk.CTkToplevel],
                                    width: int, height: int,
                                    x: Optional[int] = None,
                                    y: Optional[int] = None,
                                    responsive: bool = True) -> None:
        """تعيين حجم وموضع النافذة مع خيار التكيف مع الشاشة"""
        try:
            if responsive:
                width, height = WindowManager.adjust_window_size_to_screen(window, width, height)

            if x is not None and y is not None:
                window.geometry(f"{width}x{height}+{x}+{y}")
            else:
                window.geometry(f"{width}x{height}")
            window.update()
        except Exception as e:
            print(f"خطأ في تعيين حجم وموضع النافذة: {e}")

    @staticmethod
    def _setup_close_handler(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]):
        """إعداد معالج الإغلاق بطريقة آمنة"""
        try:
            # حفظ المعالج الأصلي
            original_protocol = window.protocol("WM_DELETE_WINDOW")

            def safe_close():
                try:
                    # إزالة من قائمة النوافذ النشطة
                    WindowManager._active_windows.discard(window)

                    # استدعاء المعالج الأصلي إن وجد
                    if callable(original_protocol):
                        original_protocol()
                    elif hasattr(window, 'destroy'):
                        window.destroy()
                except Exception as e:
                    print(f"خطأ في إغلاق النافذة: {e}")

            window.protocol("WM_DELETE_WINDOW", safe_close)

        except Exception as e:
            print(f"خطأ في إعداد معالج الإغلاق: {e}")

    @staticmethod
    def _is_window_valid(window) -> bool:
        """التحقق من صحة النافذة بطريقة آمنة"""
        try:
            return window is not None and window.winfo_exists()
        except:
            return False

    @staticmethod
    def bring_to_front(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                      duration: int = 300) -> None:
        """رفع النافذة للأعلى بطريقة آمنة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            window.lift()
            window.attributes('-topmost', True)

            if duration > 0:
                # استخدام weakref لتجنب مشاكل المراجع
                window_ref = weakref.ref(window)
                window.after(duration, lambda: WindowManager._remove_topmost_safe(window_ref))

            window.update()

        except Exception as e:
            print(f"خطأ في رفع النافذة: {e}")

    @staticmethod
    def _remove_topmost_safe(window_ref: weakref.ref):
        """إزالة خاصية topmost بطريقة آمنة"""
        try:
            window = window_ref()
            if window and WindowManager._is_window_valid(window):
                window.attributes('-topmost', False)
        except:
            pass

    @staticmethod
    def set_focus(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> None:
        """إعطاء التركيز للنافذة بطريقة آمنة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            window.focus_force()
            window.focus_set()

            # التركيز على أول عنصر
            for child in window.winfo_children():
                if isinstance(child, (ctk.CTkEntry, ctk.CTkButton, tk.Entry, tk.Button)):
                    child.focus_set()
                    break

        except Exception as e:
            print(f"خطأ في تعيين التركيز: {e}")

    @staticmethod
    def make_modal(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                   parent: Union[ctk.CTk, ctk.CTkToplevel]) -> None:
        """جعل النافذة مشروطة بطريقة آمنة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            if WindowManager._is_window_valid(parent):
                window.transient(parent)

            window.grab_set()
            window.wait_visibility()

        except Exception as e:
            print(f"خطأ في جعل النافذة مشروطة: {e}")

    @staticmethod
    def ensure_correct_position(window: Union[ctk.CTk, ctk.CTkToplevel],
                               delay: int = 50) -> None:
        """التأكد من التموضع الصحيح للنافذة بعد تأخير"""
        def check_and_fix():
            try:
                if WindowManager._is_window_valid(window):
                    # التحقق من موضع النافذة
                    x = window.winfo_x()
                    y = window.winfo_y()

                    # إذا كانت النافذة في موضع غير متوقع (مثل الجانب الأيمن)
                    screen_width = window.winfo_screenwidth()
                    window_width = window.winfo_width()

                    # إذا كانت النافذة قريبة جداً من الحافة اليمنى
                    if x > screen_width - window_width - 100:
                        # إعادة التوسيط
                        WindowManager.center_window_on_screen(window)
            except:
                pass

        window.after(delay, check_and_fix)

    @staticmethod
    def _apply_platform_specific(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                                fullscreen: bool = False) -> None:
        """تطبيق إعدادات خاصة بنظام التشغيل"""
        system = platform.system()

        try:
            if not WindowManager._is_window_valid(window):
                return

            # تجنب تطبيق بعض الإعدادات في وضع ملء الشاشة
            if not fullscreen:
                if system == "Windows":
                    # إعدادات Windows
                    window.attributes('-alpha', 0.0)
                    window.update()
                    window.attributes('-alpha', 1.0)

                    # تحسين DPI
                    try:
                        from ctypes import windll
                        windll.shcore.SetProcessDpiAwareness(1)
                    except:
                        pass

                elif system == "Darwin":  # macOS
                    window.update()
                    window.lift()
                    window.attributes('-topmost', True)
                    window.after(100, lambda: window.attributes('-topmost', False) if WindowManager._is_window_valid(window) else None)

                elif system == "Linux":
                    window.update()
                    window.lift()
            else:
                # إعدادات خاصة بوضع ملء الشاشة
                if system == "Windows":
                    # تحسين الأداء في ملء الشاشة
                    try:
                        window.focus_force()
                        window.lift()
                    except:
                        pass

        except Exception as e:
            print(f"خطأ في تطبيق إعدادات النظام: {e}")

    @staticmethod
    def flash_window(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                    count: int = 3, interval: int = 500) -> None:
        """وميض النافذة بطريقة آمنة"""
        def flash():
            try:
                for i in range(count * 2):
                    if not WindowManager._is_window_valid(window):
                        break

                    if i % 2 == 0:
                        window.attributes('-alpha', 0.7)
                    else:
                        window.attributes('-alpha', 1.0)
                    window.update()
                    time.sleep(interval / 1000)

                # التأكد من إعادة الشفافية الكاملة
                if WindowManager._is_window_valid(window):
                    window.attributes('-alpha', 1.0)

            except Exception as e:
                print(f"خطأ في وميض النافذة: {e}")

        import threading
        flash_thread = threading.Thread(target=flash, daemon=True)
        flash_thread.start()

    @staticmethod
    def animate_window_open(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel],
                          duration: int = 200) -> None:
        """تحريك فتح النافذة بطريقة آمنة (تجنب مع ملء الشاشة)"""
        steps = 10
        step_duration = duration // steps

        try:
            if not WindowManager._is_window_valid(window):
                return

            # تجنب التحريك إذا كانت النافذة في ملء الشاشة
            try:
                if (hasattr(window, 'attributes') and window.attributes('-fullscreen')) or \
                   (hasattr(window, 'state') and window.state() == 'zoomed'):
                    return
            except:
                pass

            window.attributes('-alpha', 0.0)
            window.update()

            for i in range(1, steps + 1):
                if not WindowManager._is_window_valid(window):
                    break

                alpha = i / steps
                window.attributes('-alpha', alpha)
                window.update()
                window.after(step_duration)

        except Exception:
            # في حالة الفشل، اجعل النافذة مرئية
            if WindowManager._is_window_valid(window):
                window.attributes('-alpha', 1.0)

    @staticmethod
    def get_active_windows() -> list:
        """الحصول على قائمة النوافذ النشطة بطريقة آمنة"""
        active = []

        # WeakSet يتعامل تلقائياً مع النوافذ المحذوفة
        for window in WindowManager._active_windows:
            try:
                if WindowManager._is_window_valid(window):
                    active.append(window)
            except:
                pass

        return active

    @staticmethod
    def close_all_windows(except_window: Optional[Union[ctk.CTk, ctk.CTkToplevel]] = None) -> None:
        """إغلاق جميع النوافذ بطريقة آمنة"""
        windows_to_close = []

        # جمع النوافذ للإغلاق
        for window in WindowManager._active_windows:
            try:
                if window != except_window and WindowManager._is_window_valid(window):
                    windows_to_close.append(window)
            except:
                pass

        # إغلاق النوافذ
        for window in windows_to_close:
            try:
                window.destroy()
            except:
                pass

        # تنظيف القائمة
        WindowManager._active_windows = WeakSet()
        if except_window and WindowManager._is_window_valid(except_window):
            WindowManager._active_windows.add(except_window)

    @staticmethod
    def arrange_cascade() -> None:
        """ترتيب النوافذ بشكل متتالي"""
        offset = 30

        active_windows = WindowManager.get_active_windows()
        for i, window in enumerate(active_windows):
            try:
                # تجنب ترتيب النوافذ في ملء الشاشة
                try:
                    if (hasattr(window, 'attributes') and window.attributes('-fullscreen')) or \
                       (hasattr(window, 'state') and window.state() == 'zoomed'):
                        continue
                except:
                    pass

                window.geometry(f"+{50 + i * offset}+{50 + i * offset}")
            except:
                pass

    @staticmethod
    def setup_window_shortcuts(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> None:
        """إعداد اختصارات لوحة المفاتيح بطريقة آمنة مع دعم ملء الشاشة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            # ESC للخروج من ملء الشاشة أو الإغلاق
            def handle_escape(event=None):
                try:
                    if WindowManager._is_window_valid(window):
                        # التحقق من وضع ملء الشاشة
                        is_fullscreen = False
                        try:
                            if hasattr(window, 'attributes'):
                                is_fullscreen = window.attributes('-fullscreen')
                            elif hasattr(window, 'state'):
                                is_fullscreen = window.state() == 'zoomed'
                        except:
                            pass

                        if is_fullscreen:
                            # الخروج من ملء الشاشة
                            WindowManager._exit_fullscreen(window)
                        else:
                            # إغلاق النافذة
                            window.destroy()
                except:
                    pass

            window.bind('<Escape>', handle_escape)

            # F11 لتبديل ملء الشاشة
            def toggle_fullscreen(event=None):
                try:
                    if WindowManager._is_window_valid(window):
                        WindowManager._toggle_fullscreen(window)
                except:
                    pass

            window.bind('<F11>', toggle_fullscreen)

            # Alt+F4 للإغلاق (Windows)
            if platform.system() == "Windows":
                window.bind('<Alt-F4>', lambda e: window.destroy() if WindowManager._is_window_valid(window) else None)

            # Alt+Enter لتبديل ملء الشاشة (اختصار إضافي)
            window.bind('<Alt-Return>', toggle_fullscreen)

        except Exception as e:
            print(f"خطأ في إعداد الاختصارات: {e}")

    @staticmethod
    def _toggle_fullscreen(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> None:
        """تبديل وضع ملء الشاشة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            system = platform.system()
            current_fullscreen = False

            # التحقق من الحالة الحالية
            try:
                if system == "Windows":
                    current_fullscreen = window.state() == 'zoomed'
                else:
                    current_fullscreen = window.attributes('-fullscreen')
            except:
                pass

            # تبديل الحالة
            if current_fullscreen:
                WindowManager._exit_fullscreen(window)
            else:
                WindowManager._apply_fullscreen(window)

        except Exception as e:
            print(f"خطأ في تبديل ملء الشاشة: {e}")

    @staticmethod
    def _exit_fullscreen(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> None:
        """الخروج من وضع ملء الشاشة"""
        try:
            if not WindowManager._is_window_valid(window):
                return

            system = platform.system()

            if system == "Windows":
                try:
                    window.state('normal')
                    print("تم الخروج من ملء الشاشة (Windows normal)")
                except:
                    window.attributes('-fullscreen', False)
                    print("تم الخروج من ملء الشاشة (Windows fullscreen off)")

            elif system == "Linux":
                try:
                    window.attributes('-zoomed', False)
                    print("تم الخروج من ملء الشاشة (Linux zoomed off)")
                except:
                    window.attributes('-fullscreen', False)
                    print("تم الخروج من ملء الشاشة (Linux fullscreen off)")

            elif system == "Darwin":  # macOS
                window.attributes('-fullscreen', False)
                print("تم الخروج من ملء الشاشة (macOS)")

            # تحديث النافذة
            window.update_idletasks()
            window.update()

        except Exception as e:
            print(f"خطأ في الخروج من ملء الشاشة: {e}")

    @staticmethod
    def is_fullscreen(window: Union[ctk.CTk, ctk.CTkToplevel, tk.Tk, tk.Toplevel]) -> bool:
        """التحقق من وضع ملء الشاشة"""
        try:
            if not WindowManager._is_window_valid(window):
                return False

            system = platform.system()

            if system == "Windows":
                try:
                    return window.state() == 'zoomed'
                except:
                    try:
                        return window.attributes('-fullscreen')
                    except:
                        return False
            else:
                try:
                    return window.attributes('-fullscreen')
                except:
                    if system == "Linux":
                        try:
                            return window.attributes('-zoomed')
                        except:
                            return False
                    return False

        except Exception as e:
            print(f"خطأ في التحقق من ملء الشاشة: {e}")
            return False


# دوال مساعدة سريعة محدثة

def setup_window(window, **kwargs):
    """دالة مساعدة سريعة لإعداد النافذة مع التوسيط على الشاشة افتراضياً"""
    # تعيين الافتراضيات الجديدة
    kwargs.setdefault('center_on_screen', True)
    kwargs.setdefault('responsive', True)
    kwargs.setdefault('use_smooth_show', True)
    WindowManager.setup_window(window, **kwargs)

# دالة مساعدة لنوافذ تسجيل الدخول والحوارات مع دعم ارتفاع الشاشة الكامل
def setup_dialog_window(window, size=(600, 400), full_height=False, **kwargs):
    """إعداد نافذة حوار مع ضمان التوسيط الصحيح ودعم ارتفاع الشاشة الكامل"""
    if full_height:
        # استخدام ارتفاع الشاشة الكامل
        WindowManager.setup_centered_window(window, size=size, full_height_mode=True, modal=True, **kwargs)
    else:
        # الحجم العادي
        WindowManager.setup_centered_window(window, size=size, modal=True, **kwargs)

# دالة مساعدة خاصة لنوافذ تسجيل الدخول بارتفاع الشاشة الكامل
def setup_login_window(window, width=500, **kwargs):
    """إعداد نافذة تسجيل الدخول بارتفاع الشاشة الكامل"""
    WindowManager.setup_centered_window(
        window,
        size=(width, 0),  # سيتم تجاهل الارتفاع واستخدام ارتفاع الشاشة الكامل
        full_height_mode=True,
        modal=True,
        **kwargs
    )

# دوال مساعدة جديدة لنوافذ الإضافة والتعديل

def setup_add_edit_window(window, width=600, **kwargs):
    """إعداد نافذة إضافة/تعديل بارتفاع منطقة العمل (حتى شريط المهام)"""
    WindowManager.setup_centered_window(
        window,
        size=(width, 0),  # سيتم تجاهل الارتفاع واستخدام ارتفاع منطقة العمل
        workarea_height_mode=True,
        modal=True,
        **kwargs
    )

def setup_dialog_window_workarea(window, size=(600, 400), workarea_height=False, **kwargs):
    """إعداد نافذة حوار مع خيار استخدام ارتفاع منطقة العمل"""
    if workarea_height:
        # استخدام ارتفاع منطقة العمل
        WindowManager.setup_centered_window(window, size=size, workarea_height_mode=True, modal=True, **kwargs)
    else:
        # الحجم العادي
        WindowManager.setup_centered_window(window, size=size, modal=True, **kwargs)

# دالة مساعدة للنافذة الرئيسية مع ملء الشاشة
def setup_main_window(window, **kwargs):
    """إعداد النافذة الرئيسية مع ملء الشاشة كافتراضي"""
    kwargs.setdefault('fullscreen_default', True)
    kwargs.setdefault('center', False)
    kwargs.setdefault('use_smooth_show', False)
    WindowManager.setup_window(window, **kwargs)


# أمثلة الاستخدام المحدثة:
"""
# 1. نافذة إضافة/تعديل بارتفاع منطقة العمل (الجديد - المطلوب):
add_window = ctk.CTkToplevel()
setup_add_edit_window(add_window, width=600, parent=main_window)

# 2. نافذة حوار بارتفاع منطقة العمل:
dialog = ctk.CTkToplevel()
setup_dialog_window_workarea(dialog, size=(500, 0), workarea_height=True, parent=main_window)

# 3. باستخدام الطريقة المباشرة:
edit_window = ctk.CTkToplevel()
WindowManager.setup_centered_window(
    edit_window,
    size=(600, 0),
    workarea_height_mode=True,  # من أعلى الشاشة حتى شريط المهام
    parent=main_window
)

# 4. نافذة تسجيل دخول بارتفاع الشاشة الكامل:
login_window = ctk.CTkToplevel()
setup_login_window(login_window, width=450, parent=main_window)

# 5. نافذة حوار عادية:
dialog = ctk.CTkToplevel()
setup_dialog_window(dialog, size=(500, 300), parent=main_window)

# 6. النافذة الرئيسية مع ملء الشاشة:
main_window = ctk.CTk()
setup_main_window(main_window, min_size=(1200, 700))

# 7. مقارنة الأوضاع المختلفة:

# وضع عادي (متوسط الشاشة)
normal_window = ctk.CTkToplevel()
setup_dialog_window(normal_window, size=(600, 400))

# وضع ارتفاع منطقة العمل (من الأعلى حتى شريط المهام) - الجديد
workarea_window = ctk.CTkToplevel()
setup_add_edit_window(workarea_window, width=600)

# وضع ارتفاع الشاشة الكامل (فوق شريط المهام أيضاً)
fullheight_window = ctk.CTkToplevel()
setup_login_window(fullheight_window, width=600)
"""