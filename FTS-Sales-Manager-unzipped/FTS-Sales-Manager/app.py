# -*- coding: utf-8 -*-
"""
app.py

نقطة البداية (entry point) لتشغيل تطبيق FTS Sales Manager.
"""

# تتبع الأخطاء وإدارتها
import sys
import traceback
import warnings
import traceback

# تعطيل تحذير "invalid command name"
warnings.filterwarnings("ignore", message="invalid command name")

# محاولة تفعيل faulthandler فقط إذا كان مدعوماً
try:
    import faulthandler
    # التحقق من أننا لسنا في IDLE
    if hasattr(sys.stderr, 'fileno') and hasattr(sys.stderr.fileno, '__call__'):
        try:
            sys.stderr.fileno()
            faulthandler.enable()
        except:
            # إذا فشل، نتجاهل الخطأ
            pass
except ImportError:
    # إذا لم يكن faulthandler متاحاً
    pass

# معالج أخطاء عام لـ Tkinter
def handle_tk_error(*args):
    import traceback
    import sys

    try:
        # الحالة الأولى: tkinter يرسل (exc_type, exc_value, exc_tb)
        if isinstance(args, tuple) and len(args) == 3 and isinstance(args[1], BaseException):
            exc_type, exc_value, exc_tb = args

        # الحالة الثانية: tkinter يرسل كائن استثناء واحد فقط
        elif isinstance(args, tuple) and len(args) == 1 and isinstance(args[0], BaseException):
            exc_type = type(args[0])
            exc_value = args[0]
            exc_tb = args[0].__traceback__ if hasattr(args[0], "__traceback__") else None

        # الحالة الثالثة: (widget, exc_type, exc_value, exc_tb)
        elif isinstance(args, tuple) and len(args) == 4 and isinstance(args[2], BaseException):
            _, exc_type, exc_value, exc_tb = args

        else:
            print("📦 محتوى args غير المتوقع:", args, file=sys.stderr)
            raise ValueError("تنسيق غير معروف لمعالجة الخطأ")

        traceback.print_exception(exc_type, exc_value, exc_tb)

    except Exception as e:
        print(f"⚠️ فشل أثناء معالجة الاستثناء (داخليًا): {e}", file=sys.stderr)

# معالج أخطاء شامل
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # استيراد logger هنا لتجنب مشاكل الاستيراد المبكر
    from core.logger import logger
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = handle_exception

# باقي الواردات
import os
import tkinter as tk

# إخفاء نافذة tk الافتراضية فوراً بعد استيراد tkinter
if tk._default_root:
    tk._default_root.withdraw()

from core.config_manager import ConfigManager
from core.db_manager import DatabaseManager
from core.airtable_manager import AirtableManager, AirtableModel
from core.user_manager import UserManager
from core.logger import logger
from controllers.app_controller import AppController
from views.splash_screen import SplashScreen

# ربط معالج الأخطاء بـ Tkinter
tk.Tk.report_callback_exception = handle_tk_error


def hide_default_tk_window():
    """إخفاء أي نافذة tk افتراضية"""
    try:
        # إخفاء النافذة الافتراضية إذا كانت موجودة
        if tk._default_root:
            tk._default_root.withdraw()
            tk._default_root.overrideredirect(True)

        # البحث عن أي نوافذ tk مفتوحة وإخفاؤها
        for widget in tk._default_root.winfo_children() if tk._default_root else []:
            if widget.winfo_class() == 'Tk' and widget.title() == 'tk':
                widget.withdraw()
    except:
        pass


def main() -> None:
    """
    الدالة الرئيسية لتشغيل التطبيق.
    """
    # إنشاء نافذة أساسية مخفية لـ CTkToplevel
    root = tk.Tk()
    root.withdraw()  # إخفاء النافذة فوراً
    root.overrideredirect(True)  # إزالة من شريط المهام

    # إخفاء أي نافذة tk افتراضية أخرى
    hide_default_tk_window()

    # 1. عرض شاشة التحميل لمدة قصيرة
    try:
        splash = SplashScreen(duration=2000, master=root)  # تمرير النافذة الأساسية
        splash.update()
    except Exception as e:
        logger.warning(f"Failed to show splash screen: {e}", exc_info=True)

    # إخفاء النافذة مرة أخرى بعد شاشة التحميل
    hide_default_tk_window()

    # 2. تهيئة ConfigManager
    config_mgr = ConfigManager(config_path=os.path.join("config", "settings.yaml"))

    # 3. تهيئة DatabaseManager (SQLite للكاش المحلي)
    db_mgr = DatabaseManager(db_path="fts_sales_cache.db")

    # 4. تهيئة AirtableModel للمستخدمين
    users_table = config_mgr.get("airtable_users_table", "Users")
    airtable_users = AirtableModel(
        config_manager=config_mgr,
        db_manager=db_mgr,
        table_name=users_table
    )

    # 5. تهيئة AirtableModel للحجوزات
    booking_table = config_mgr.get("airtable_booking_table", "List V2")
    airtable_booking = AirtableModel(
        config_manager=config_mgr,
        db_manager=db_mgr,
        table_name=booking_table
    )

    # 6. تهيئة UserManager (يستخدم airtable_users فقط)
    user_mgr = UserManager(airtable_model=airtable_users, db_manager=db_mgr)

    # 7. تشغيل AppController مع كلا النموذجين
    try:
        app_ctrl = AppController(
            config_mgr=config_mgr,
            db_mgr=db_mgr,
            airtable_users=airtable_users,
            airtable_booking=airtable_booking,
            user_mgr=user_mgr
        )
        app_ctrl.run()
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
        raise
    finally:
        # تنظيف النافذة الأساسية
        try:
            if 'root' in locals() and root:
                root.destroy()
        except:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"Fatal error on startup: {e}", exc_info=True)
        # عرض رسالة خطأ للمستخدم
        try:
            import tkinter as tk
            from tkinter import messagebox

            # إنشاء نافذة مؤقتة لرسالة الخطأ
            error_root = tk.Tk()
            error_root.withdraw()  # إخفاء النافذة الرئيسية

            messagebox.showerror(
                "خطأ في بدء التطبيق",
                f"حدث خطأ أثناء تشغيل التطبيق:\n\n{str(e)}\n\nيرجى التحقق من السجلات للمزيد من التفاصيل."
            )

            error_root.destroy()
        except:
            pass
        sys.exit(1)