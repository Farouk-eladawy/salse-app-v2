# -*- coding: utf-8 -*-
"""
controllers/app_controller.py - نسخة محسنة ومبسطة

وحدة التحكم المحسّنة مع:
- كود مبسط ومنظم
- دعم اختياري لربط القوائم المنسدلة بـ Airtable
- إدارة الصلاحيات والمستخدمين
- عمليات CRUD محسنة
- نظام ثيمات موحد
- دعم توليد رقم الحجز التلقائي
- حل مشكلة double JSON encoding في حقل Assigned To
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from tkinter import messagebox
import threading
import json
import time
import tkinter as tk
import customtkinter as ctk

from core.config_manager import ConfigManager
from core.db_manager import DatabaseManager
from core.language_manager import LanguageManager
from core.theme_manager import ThemeManager
from core.user_manager import UserManager
from core.airtable_manager import AirtableModel
from core.logger import logger
from utils.threading_utils import initialize_threading, shutdown_threading
from views.login_window import LoginWindow
from views.main_window import MainWindow

# إخفاء نافذة tk الافتراضية
if tk._default_root:
    tk._default_root.withdraw()

# استيراد مكونات القوائم المنسدلة
try:
    from core.airtable_dropdown_manager import AirtableDropdownManager
    from views.add_edit_window import AddEditWindow
    HAS_AIRTABLE_DROPDOWNS = True
    logger.info("تم تحميل مكونات القوائم المنسدلة")
except ImportError as e:
    logger.warning(f"مكونات القوائم المنسدلة غير متوفرة: {e}")
    HAS_AIRTABLE_DROPDOWNS = False
    AirtableDropdownManager = None
    AddEditWindow = None


class AppController:
    """وحدة التحكم المحسنة والمبسطة"""

    def __init__(self, config_mgr: ConfigManager, db_mgr: DatabaseManager,
                 airtable_users: AirtableModel, airtable_booking: AirtableModel,
                 user_mgr: UserManager) -> None:

        # إخفاء نوافذ tk إضافية
        self._hide_default_tk_windows()

        # المتغيرات الأساسية
        self.config_mgr = config_mgr
        self.db_mgr = db_mgr
        self.airtable_users = airtable_users
        self.airtable_booking = airtable_booking
        self.user_mgr = user_mgr

        # إدارة اللغة والثيم
        self.lang_manager = LanguageManager(self.config_mgr)
        self.theme_manager = ThemeManager(self.config_mgr)

        # نوافذ التطبيق
        self.login_window = None
        self.main_window = None
        self.open_edit_windows = []

        # معلومات المستخدم الحالي
        self.current_username: Optional[str] = None
        self.current_user_info: Optional[Dict[str, Any]] = None
        self.current_user_collaborator: Optional[Any] = None
        self.selected_record: Optional[Dict[str, Any]] = None

        # حالة التطبيق
        self.is_loading = False
        self.loading_operations = set()

        # كاش أرقام الحجز المستخدمة (للتحقق من عدم التكرار)
        self.used_booking_numbers = set()

        # تهيئة مدير القوائم المنسدلة
        self.dropdown_manager = self._initialize_dropdown_manager()

    def _hide_default_tk_windows(self):
        """إخفاء نوافذ tk الافتراضية"""
        try:
            if tk._default_root:
                tk._default_root.withdraw()
            for widget in tk._default_root.winfo_children() if tk._default_root else []:
                if widget.winfo_class() == 'Tk':
                    widget.withdraw()
        except:
            pass

    def _initialize_dropdown_manager(self):
        """تهيئة مدير القوائم المنسدلة"""
        if not HAS_AIRTABLE_DROPDOWNS:
            return None

        try:
            dropdown_manager = AirtableDropdownManager(
                config_manager=self.config_mgr,
                db_manager=self.db_mgr
            )

            if dropdown_manager.has_errors():
                self._handle_dropdown_errors(dropdown_manager.get_all_errors())

            logger.info("تم تهيئة مدير القوائم المنسدلة بنجاح")
            return dropdown_manager

        except Exception as e:
            logger.error(f"خطأ في تهيئة مدير القوائم المنسدلة: {e}")
            return None

    def _handle_dropdown_errors(self, errors):
        """معالجة أخطاء القوائم المنسدلة"""
        error_msg = "تعذر تحميل بعض القوائم المنسدلة:\n\n"
        for key, msg in errors.items():
            error_msg += f"• {msg}\n"

        if hasattr(self, 'main_window') and self.main_window:
            self.main_window.after(1000, lambda: messagebox.showerror(
                "خطأ في القوائم المنسدلة",
                error_msg + "\n\nلن تتمكن من إضافة أو تعديل السجلات."
            ))

    def run(self) -> None:
        """تشغيل التطبيق"""
        logger.info("بدء تشغيل التطبيق")

        self.login_window = LoginWindow(
            controller=self,
            lang_manager=self.lang_manager,
            theme_manager=self.theme_manager,
            airtable_model=self.airtable_users,
            user_mgr=self.user_mgr,
            enable_encryption=True,
            enable_rate_limiting=True,
            enable_2fa=False,
            parent_window=self
        )

        initialize_threading(self.login_window)
        self.login_window.mainloop()

    def on_login_success(self, user_info: Dict[str, str]) -> None:
        """معالج نجاح تسجيل الدخول مع معالجة مبسطة"""
        self.current_username = user_info.get('username', 'Unknown')
        self.current_user_info = user_info

        # معالجة مبسطة لـ Airtable Collaborator - بدون تنظيف معقد
        collaborator_raw = user_info.get('airtable_collaborator')
        if collaborator_raw:
            self.current_user_collaborator = collaborator_raw  # ← استخدام القيمة كما هي
            logger.info(f"تسجيل دخول ناجح: {self.current_username}")
            logger.debug(f"Collaborator: {type(self.current_user_collaborator)} = {self.current_user_collaborator}")
        else:
            logger.warning(f"لا يوجد Airtable Collaborator للمستخدم: {self.current_username}")
            self.current_user_collaborator = None

        # تعيين View للمستخدم
        user_view = user_info.get('view')
        if user_view:
            self.airtable_booking.set_view(user_view)
            logger.info(f"تم تعيين View: {user_view}")

        # إغلاق نافذة تسجيل الدخول
        try:
            if self.login_window:
                self.login_window.destroy()
        except Exception as e:
            logger.warning(f"فشل في إغلاق نافذة تسجيل الدخول: {e}")

        # فتح النافذة الرئيسية
        self._open_main_window(user_info)

    def _open_main_window(self, user_info: Dict[str, str]) -> None:
        """فتح النافذة الرئيسية"""
        try:
            user_record = {
                'id': user_info.get('record_id', ''),
                'fields': {
                    'Username': user_info.get('username', ''),
                    'Airtable View': user_info.get('view'),
                    'Role': user_info.get('role', 'viewer'),
                    'Airtable Collaborator': user_info.get('airtable_collaborator')
                }
            }

            self.main_window = MainWindow(
                lang_manager=self.lang_manager,
                theme_manager=self.theme_manager,
                airtable_model=self.airtable_booking,
                controller=self,
                user_record=user_record
            )

            # تحديث GUI updater
            from utils.threading_utils import get_gui_updater
            get_gui_updater().set_root_widget(self.main_window)

            # تحميل أرقام الحجز المستخدمة للتحقق من عدم التكرار
            self._load_existing_booking_numbers()

            # فحص القوائم المنسدلة بعد الفتح
            if not self.dropdown_manager:
                self.main_window.after(2000, self._show_dropdown_unavailable_message)

            self.main_window.mainloop()

        except Exception as e:
            logger.error(f"خطأ في إنشاء النافذة الرئيسية: {e}")

    def _load_existing_booking_numbers(self):
        """تحميل أرقام الحجز الموجودة للتحقق من عدم التكرار"""
        try:
            records = self.airtable_booking.fetch_records(use_cache=True)
            for record in records:
                booking_nr = record.get('fields', {}).get('Booking Nr.')
                if booking_nr:
                    self.used_booking_numbers.add(booking_nr)

            logger.info(f"تم تحميل {len(self.used_booking_numbers)} رقم حجز موجود")
        except Exception as e:
            logger.warning(f"فشل في تحميل أرقام الحجز: {e}")

    def _show_dropdown_unavailable_message(self):
        """عرض رسالة عدم توفر القوائم المنسدلة"""
        messagebox.showerror(
            "خطأ حرج",
            "لا يمكن تحميل القوائم المنسدلة من Airtable.\n"
            "لن تتمكن من إضافة أو تعديل السجلات.\n\n"
            "تأكد من:\n"
            "- وجود الجداول المطلوبة في Airtable\n"
            "- صحة إعدادات الاتصال في ملف .env"
        )

    # =============== إدارة البيانات ===============

    def fetch_all_records(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """جلب جميع السجلات من Airtable"""
        try:
            records = self.airtable_booking.fetch_records(use_cache=False)
            logger.info(f"تم جلب {len(records)} سجل")

            # تحديث كاش أرقام الحجز
            self.used_booking_numbers.clear()
            for record in records:
                booking_nr = record.get('fields', {}).get('Booking Nr.')
                if booking_nr:
                    self.used_booking_numbers.add(booking_nr)

            # طباعة أسماء الحقول (للتطوير)
            if records:
                field_names = list(records[0].get('fields', {}).keys())
                logger.debug(f"الحقول المتاحة: {len(field_names)} حقل")

            return records
        except Exception as e:
            logger.error(f"خطأ في جلب السجلات: {e}")
            return []

    def refresh_data(self) -> List[Dict[str, Any]]:
        """تحديث البيانات"""
        logger.info("تحديث البيانات من Airtable")
        return self.fetch_all_records()

    def set_selected_record(self, record: Dict[str, Any]) -> None:
        """تعيين السجل المحدد"""
        self.selected_record = record
        logger.debug(f"تم تحديد السجل: {record.get('id')}")

    # =============== إدارة الصلاحيات ===============

    def _check_record_permission(self, record: Dict[str, Any], action: str = "تعديل") -> bool:
        """التحقق من صلاحية العمل على السجل"""
        if not record:
            return False

        # الحصول على معلومات السجل والمستخدم
        record_fields = record.get("fields", {})
        record_assigned_to = record_fields.get("Assigned To")
        current_user_id = self._get_current_user_id()
        is_admin = self.current_user_info.get('role', '').lower() == 'admin'

        # السماح للمشرفين
        if is_admin:
            return True

        # منع العمل على السجلات القديمة
        if not record_assigned_to:
            logger.warning(f"السجل قديم (بدون Assigned To) - منع {action}")
            return False

        # التحقق من تطابق المستخدم
        if current_user_id:
            assigned_to_id = record_assigned_to.get('id') if isinstance(record_assigned_to, dict) else record_assigned_to
            return assigned_to_id == current_user_id

        return False

    def _get_current_user_id(self):
        """الحصول على معرف المستخدم الحالي بتنظيف أساسي فقط"""
        if self.current_user_collaborator:
            if isinstance(self.current_user_collaborator, dict):
                user_id = self.current_user_collaborator.get('id')
            else:
                user_id = self.current_user_collaborator

            # تنظيف أساسي فقط - إزالة مسافات زائدة
            if user_id:
                cleaned_id = str(user_id).strip()
                logger.debug(f"معرف المستخدم: {cleaned_id}")
                return cleaned_id

        return None

    def _get_permission_error_message(self, record: Dict[str, Any], action: str) -> Tuple[str, str]:
        """الحصول على رسالة الخطأ المناسبة"""
        record_assigned_to = record.get("fields", {}).get("Assigned To")

        if not record_assigned_to:
            return ("سجل قديم", f"عذراً، لا يمكن {action} هذا السجل.\n\nهذا السجل قديم وغير مرتبط بأي مستخدم.")
        else:
            return ("عدم وجود صلاحية", f"عذراً، لا يمكنك {action} هذا السجل.\n\nيمكنك فقط {action} السجلات التي قمت بإنشائها.")

    # =============== إدارة النماذج ===============

    def open_add_form(self):
        """فتح نافذة إضافة حجز جديد"""
        if not self._can_open_form():
            return

        self._open_form_with_checks("add")

    def open_edit_form(self) -> None:
        """فتح نافذة تعديل السجل المحدد"""
        if not self.selected_record:
            messagebox.showwarning("تنبيه", "يرجى تحديد سجل للتعديل")
            return

        if not self._can_open_form():
            return

        # التحقق من الصلاحية
        if not self._check_record_permission(self.selected_record, "تعديل"):
            title, message = self._get_permission_error_message(self.selected_record, "تعديل")
            messagebox.showerror(title, message)
            return

        self._open_form_with_checks("edit")

    def _can_open_form(self) -> bool:
        """التحقق من إمكانية فتح النموذج"""
        if self.is_loading:
            messagebox.showinfo(
                "جاري التحميل",
                "يرجى انتظار انتهاء تحميل البيانات قبل فتح النموذج."
            )
            return False

        if not HAS_AIRTABLE_DROPDOWNS or not self.dropdown_manager:
            messagebox.showerror(
                "خطأ",
                "لا يمكن فتح النموذج.\nالقوائم المنسدلة من Airtable غير متوفرة."
            )
            return False

        return True

    def _open_form_with_checks(self, mode: str):
        """فتح النموذج مع التحقق من القوائم المنسدلة"""
        operation_id = f"open_form_{mode}_{datetime.now().timestamp()}"
        self.loading_operations.add(operation_id)

        loading_dialog = self._create_loading_dialog("جاري التحقق من البيانات...")

        def check_and_open():
            try:
                # التحقق من حالة القوائم المنسدلة
                status = self.dropdown_manager.get_status() if self.dropdown_manager else {'errors': {'general': 'غير متاح'}}

                # إغلاق مؤشر التحميل
                self.main_window.after(0, lambda: loading_dialog.destroy())
                self.loading_operations.discard(operation_id)

                if status.get('errors'):
                    self.main_window.after(100, lambda: self._show_dropdown_errors(status['errors']))
                    return

                # فتح النموذج
                self.main_window.after(100, lambda: self._create_form(mode))

            except Exception as e:
                self.main_window.after(0, lambda: loading_dialog.destroy())
                self.loading_operations.discard(operation_id)
                self.main_window.after(100, lambda: messagebox.showerror("خطأ", f"فشل التحقق: {str(e)}"))

        threading.Thread(target=check_and_open, daemon=True).start()

    def _create_form(self, mode: str):
        """إنشاء نموذج إضافة أو تعديل - دالة موحدة"""
        try:
            # التحقق من وجود نافذة مفتوحة لنفس السجل (في وضع التعديل)
            if mode == "edit":
                record_id = self.selected_record.get("id")
                for window in self.open_edit_windows:
                    if (window.winfo_exists() and hasattr(window, 'record_id') and
                        window.record_id == record_id):
                        window.focus_force()
                        return

            # إعداد المعاملات
            form_params = {
                "parent": self.main_window,
                "config_mgr": self.config_mgr,
                "db_mgr": self.db_mgr,
                "airtable_model": self.airtable_booking,
                "controller": self,
                "dropdown_manager": self.dropdown_manager,
                "lang_manager": self.lang_manager,
                "mode": mode
            }

            # إضافة معاملات التعديل
            if mode == "edit":
                form_params.update({
                    "record_id": self.selected_record.get("id"),
                    "initial_fields": self.selected_record.get("fields", {})
                })

            # إنشاء النافذة
            form_window = AddEditWindow(**form_params)

            logger.info(f"تم فتح نافذة {mode} بنجاح")
            self.open_edit_windows.append(form_window)

            # إزالة النافذة عند الإغلاق
            def on_close():
                if form_window in self.open_edit_windows:
                    self.open_edit_windows.remove(form_window)

            form_window.protocol("WM_DELETE_WINDOW", lambda: [on_close(), form_window.destroy()])

        except Exception as e:
            logger.error(f"خطأ في إنشاء نموذج {mode}: {e}")
            messagebox.showerror("خطأ", f"فشل إنشاء النافذة: {str(e)}")

    def _get_form_configuration(self) -> Tuple[Dict, Dict]:
        """الحصول على تكوين مجموعات وأنواع الحقول"""
        field_groups = {
            "معلومات أساسية": [
                "Customer Name", "Hotel Name", "Agency", "Booking Nr."
            ],
            "تفاصيل الرحلة": [
                "trip Name", "Date Trip", "Option", "des", "Guide", "Product ID"
            ],
            "معلومات الركاب": [
                "ADT", "CHD", "STD", "Youth", "CHD Age"
            ],
            "معلومات الاتصال": [
                "Customer Phone", "Customer Email"
            ],
            "معلومات الأسعار": [
                "Total price USD", "Collecting on date Trip"
            ]
        }

        field_type_map = {
            "Customer Name": "text", "Hotel Name": "text", "Agency": "dropdown",
            "Booking Nr.": "readonly", "trip Name": "dropdown", "Date Trip": "date",
            "Option": "dropdown", "des": "dropdown", "Guide": "dropdown",
            "Product ID": "text", "ADT": "number", "CHD": "number", "STD": "number",
            "Youth": "number", "CHD Age": "text", "Customer Phone": "phone",
            "Customer Email": "email", "Total price USD": "currency",
            "Collecting on date Trip": "text"
        }

        return field_groups, field_type_map

    def _show_dropdown_errors(self, errors):
        """عرض أخطاء القوائم المنسدلة"""
        error_msg = "تعذر جلب البيانات من Airtable:\n\n"
        for table, error in errors.items():
            error_msg += f"• {error}\n"
        error_msg += "\n⛔ لن تتمكن من إضافة أو تعديل السجلات."

        messagebox.showerror("خطأ في القوائم المنسدلة", error_msg)

    # =============== عمليات CRUD ===============

    def create_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """إنشاء سجل جديد مع إضافة Assigned To تلقائياً والتحقق من رقم الحجز"""
        try:
            logger.info("جاري إنشاء سجل جديد...")

            # إضافة Assigned To تلقائياً مع التنسيق الصحيح للـ User field
            collaborator_id = self._get_current_user_id()
            if collaborator_id:
                # إرسال القيمة مباشرة بدون معالجة إضافية
                fields['Assigned To'] = {"id": collaborator_id}  # object
                logger.info(f"تم إضافة Assigned To: {collaborator_id}")

            # التحقق من رقم الحجز وضمان عدم التكرار
            booking_nr = fields.get('Booking Nr.')
            if booking_nr:
                # التحقق من عدم وجود رقم الحجز مسبقاً
                if booking_nr in self.used_booking_numbers:
                    logger.warning(f"رقم الحجز {booking_nr} موجود مسبقاً، سيتم إنشاء رقم جديد")
                    # يمكن إضافة منطق لتوليد رقم جديد هنا إذا لزم الأمر
                else:
                    # إضافة رقم الحجز إلى الكاش
                    self.used_booking_numbers.add(booking_nr)
                    logger.info(f"تم إضافة رقم الحجز الجديد: {booking_nr}")

            # تنظيف الحقول - بدون معالجة خاصة لـ Assigned To
            cleaned_fields = self._clean_fields_for_save_simple(fields)

            if not cleaned_fields:
                raise ValueError("لا توجد بيانات لحفظها")

            # إنشاء السجل
            result = self.airtable_booking.create_record(cleaned_fields)

            if result:
                logger.info(f"تم إنشاء السجل بنجاح: {result.get('id')}")
                self._refresh_main_window()
                return result
            else:
                logger.error("فشل إنشاء السجل")
                return None

        except Exception as e:
            logger.error(f"خطأ في إنشاء السجل: {e}")
            raise

    def update_record(self, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """تحديث سجل موجود مع ضمان عدم تعديل رقم الحجز"""
        try:
            logger.info(f"جاري تحديث السجل: {record_id}")

            # تنظيف الحقول (مع منع تعديل Assigned To و Booking Nr.)
            cleaned_fields = self._clean_fields_for_save(fields, exclude_assigned_to=True, exclude_booking_nr=True)

            if not cleaned_fields:
                logger.warning("لا توجد حقول للتحديث")
                return None

            # تحديث السجل
            result = self.airtable_booking.update_record(record_id, cleaned_fields)

            if result:
                logger.info(f"تم تحديث السجل بنجاح: {record_id}")
                self._refresh_main_window()
                return result
            else:
                logger.error(f"فشل تحديث السجل: {record_id}")
                return None

        except Exception as e:
            logger.error(f"خطأ في تحديث السجل: {e}")
            raise

    def delete_record(self) -> bool:
        """حذف السجل المحدد"""
        if not self.selected_record:
            return False

        record_id = self.selected_record.get("id")

        try:
            # التحقق من الصلاحية
            if not self._check_record_permission(self.selected_record, "حذف"):
                title, message = self._get_permission_error_message(self.selected_record, "حذف")
                messagebox.showerror(title, message)
                return False

            # إزالة رقم الحجز من الكاش قبل الحذف
            booking_nr = self.selected_record.get('fields', {}).get('Booking Nr.')
            if booking_nr and booking_nr in self.used_booking_numbers:
                self.used_booking_numbers.remove(booking_nr)
                logger.info(f"تم إزالة رقم الحجز {booking_nr} من الكاش")

            # حذف السجل
            success = self.airtable_booking.delete_record(record_id)

            if success:
                logger.info(f"تم حذف السجل: {record_id}")
                self.selected_record = None
                self._refresh_main_window()

            return success

        except Exception as e:
            logger.error(f"خطأ في حذف السجل: {e}")
            return False

    def batch_delete_records(self, record_ids: List[str]) -> Tuple[int, int]:
        """حذف عدة سجلات"""
        success_count = 0
        unauthorized_count = 0
        old_records_count = 0

        # جلب السجلات للتحقق من الصلاحيات
        all_records = self.fetch_all_records()
        records_dict = {record['id']: record for record in all_records}

        for record_id in record_ids:
            try:
                record = records_dict.get(record_id)
                if not record:
                    continue

                # التحقق من الصلاحية
                if not self._check_record_permission(record, "حذف"):
                    if not record.get("fields", {}).get("Assigned To"):
                        old_records_count += 1
                    else:
                        unauthorized_count += 1
                    continue

                # إزالة رقم الحجز من الكاش
                booking_nr = record.get('fields', {}).get('Booking Nr.')
                if booking_nr and booking_nr in self.used_booking_numbers:
                    self.used_booking_numbers.remove(booking_nr)

                # حذف السجل
                if self.airtable_booking.delete_record(record_id):
                    success_count += 1

            except Exception as e:
                logger.error(f"خطأ في حذف السجل {record_id}: {e}")

        # عرض النتيجة
        self._show_batch_delete_result(success_count, len(record_ids), unauthorized_count, old_records_count)

        if success_count > 0:
            self._refresh_main_window()

        return success_count, len(record_ids)

    def _clean_fields_for_save_simple(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """تنظيف بسيط للحقول بدون معالجة معقدة لحقل Assigned To"""
        # الحقول المحسوبة والمحظورة
        computed_fields = [
            'Created By', 'Last Modified By', 'Created Date', 'Last Modified',
            'Modified By', 'Modified Date'
        ]

        cleaned = {}
        for key, value in fields.items():
            if key in computed_fields:
                continue

            # تنظيف بسيط للقيم النصية العادية
            if value is not None and value != "":
                if isinstance(value, str):
                    cleaned_value = value.strip()
                    if cleaned_value:
                        cleaned[key] = cleaned_value
                else:
                    cleaned[key] = value

        logger.debug(f"تنظيف بسيط: {len(fields)} → {len(cleaned)} حقل")
        return cleaned

    def _clean_fields_for_save(self, fields: Dict[str, Any], exclude_assigned_to: bool = False, exclude_booking_nr: bool = False) -> Dict[str, Any]:
        """تنظيف الحقول قبل الحفظ مع خيارات إضافية ومعالجة خاصة لحقول User"""
        # الحقول المحسوبة والمحظورة
        computed_fields = [
            'Created By', 'Last Modified By', 'Created Date', 'Last Modified',
            'Modified By', 'Modified Date'
        ]

        if exclude_assigned_to:
            computed_fields.append('Assigned To')

        # ← إضافة خيار منع تعديل رقم الحجز في وضع التعديل
        if exclude_booking_nr:
            computed_fields.append('Booking Nr.')
            logger.info("تم استبعاد رقم الحجز من التحديث (محمي من التعديل)")

        # إزالة الحقول المحسوبة والفارغة مع معالجة خاصة لحقول User
        cleaned = {}
        for key, value in fields.items():
            if key in computed_fields:
                continue

            # معالجة خاصة لحقل Assigned To (User field)
            if key == 'Assigned To' and not exclude_assigned_to:
                cleaned_value = self._clean_user_field_value(value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
                    logger.debug(f"تنظيف حقل المستخدم '{key}': {value} → {cleaned_value}")

            # معالجة الحقول العادية
            elif value is not None and value != "":
                # تنظيف القيم النصية من escape characters إضافية
                if isinstance(value, str):
                    cleaned_value = value.strip()
                    if cleaned_value:
                        cleaned[key] = cleaned_value
                else:
                    cleaned[key] = value

        # تسجيل المعلومات للتشخيص
        excluded_count = len(fields) - len(cleaned)
        if excluded_count > 0:
            logger.debug(f"تم استبعاد {excluded_count} حقل من الحفظ")

        return cleaned

    def _clean_user_field_value(self, value) -> Optional[str]:
        """دالة مبسطة لتنظيف حقل المستخدم"""
        if not value:
            return None

        # تنظيف بسيط
        if isinstance(value, dict):
            user_id = value.get('id')
            if user_id:
                return str(user_id).strip()
        elif isinstance(value, str):
            return value.strip()

        return None

    def _show_batch_delete_result(self, success: int, total: int, unauthorized: int, old: int):
        """عرض نتيجة الحذف الدفعي"""
        message = f"تم حذف {success} سجل من أصل {total}\n\n"

        if unauthorized > 0:
            message += f"• {unauthorized} سجل لم يتم حذفه (مملوك لمستخدمين آخرين)\n"

        if old > 0:
            message += f"• {old} سجل قديم (يرجى الاتصال بالدعم الفني)\n"

        if unauthorized > 0:
            message += "\nيمكنك فقط حذف السجلات التي قمت بإنشائها"

        messagebox.showinfo("نتيجة الحذف", message)

    def _refresh_main_window(self):
        """تحديث النافذة الرئيسية"""
        if self.main_window and hasattr(self.main_window, '_refresh_data'):
            self.main_window.after(100, self.main_window._refresh_data)

    # =============== إدارة المستخدمين والجلسة ===============

    def get_current_user_collaborator(self):
        """الحصول على Airtable Collaborator للمستخدم الحالي مع تشخيص محسن"""
        if self.current_user_collaborator:
            logger.debug(f"المستخدم الحالي موجود: {type(self.current_user_collaborator)} = {self.current_user_collaborator}")
            return self.current_user_collaborator

        # محاولة جلبها من قاعدة البيانات
        if self.current_username and self.airtable_users:
            try:
                logger.info(f"محاولة جلب معلومات المستخدم: {self.current_username}")
                users = self.airtable_users.fetch_records()
                for user in users:
                    username = user.get('fields', {}).get('Username', '')
                    if username.lower() == self.current_username.lower():
                        collaborator = user.get('fields', {}).get('Airtable Collaborator')
                        if collaborator:
                            self.current_user_collaborator = collaborator
                            logger.info(f"تم العثور على Collaborator: {type(collaborator)} = {collaborator}")
                            return collaborator
                        else:
                            logger.warning(f"لم يتم العثور على Airtable Collaborator للمستخدم: {username}")

                logger.warning(f"لم يتم العثور على المستخدم: {self.current_username}")
            except Exception as e:
                logger.error(f"خطأ في جلب معلومات المستخدم: {e}")

        return None

    def on_logout(self) -> None:
        """معالج تسجيل الخروج"""
        logger.info("بدء عملية تسجيل الخروج...")

        # إغلاق النوافذ المفتوحة
        for window in self.open_edit_windows:
            try:
                if window.winfo_exists():
                    window.destroy()
            except:
                pass

        self.open_edit_windows.clear()

        # إعادة تعيين المتغيرات
        self.current_username = None
        self.current_user_info = None
        self.current_user_collaborator = None
        self.selected_record = None
        self.is_loading = False
        self.loading_operations.clear()

        # مسح كاش أرقام الحجز
        self.used_booking_numbers.clear()

        # إعادة تعيين الـ View
        self.airtable_booking.set_view(None)

        logger.info("تم تسجيل الخروج بنجاح")

    # =============== الأدوات المساعدة ===============

    def _create_loading_dialog(self, message: str = "جاري التحميل...") -> ctk.CTkToplevel:
        """إنشاء نافذة حوار التحميل"""
        dialog = ctk.CTkToplevel()
        dialog.title("جاري التحميل...")
        dialog.geometry("350x150")

        # توسيط النافذة
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 175
        y = (dialog.winfo_screenheight() // 2) - 75
        dialog.geometry(f"350x150+{x}+{y}")

        dialog.grab_set()
        dialog.transient(self.main_window if self.main_window else None)

        # المحتوى
        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=f"⏳ {message}", font=ctk.CTkFont(size=16)).pack(pady=10)

        progress = ctk.CTkProgressBar(frame)
        progress.pack(fill="x", pady=10)
        progress.configure(mode="indeterminate")
        progress.start()

        ctk.CTkLabel(frame, text="يرجى الانتظار", font=ctk.CTkFont(size=12), text_color="gray").pack()

        return dialog

    def update_all_windows_language(self):
        """تحديث لغة جميع النوافذ المفتوحة"""
        logger.info("تحديث لغة جميع النوافذ...")

        for window in self.open_edit_windows:
            try:
                if window.winfo_exists() and hasattr(window, 'update_language'):
                    window.update_language(self.lang_manager)
            except Exception as e:
                logger.error(f"خطأ في تحديث لغة النافذة: {e}")

    def update_all_windows_theme(self):
        """تحديث الثيم في جميع النوافذ المفتوحة"""
        logger.info("تحديث الثيم في جميع النوافذ...")

        # تحديث النافذة الرئيسية
        if self.main_window and hasattr(self.main_window, 'refresh_theme'):
            try:
                self.main_window.refresh_theme()
            except Exception as e:
                logger.error(f"خطأ في تحديث ثيم النافذة الرئيسية: {e}")

        # تحديث نوافذ التعديل/الإضافة
        for window in self.open_edit_windows:
            try:
                if window.winfo_exists() and hasattr(window, 'refresh_theme'):
                    window.refresh_theme()
            except Exception as e:
                logger.error(f"خطأ في تحديث ثيم النافذة: {e}")

    def cleanup(self):
        """تنظيف الموارد عند إغلاق التطبيق"""
        logger.info("بدء تنظيف موارد التطبيق...")

        # إغلاق النوافذ المفتوحة
        for window in self.open_edit_windows:
            try:
                if window.winfo_exists():
                    window.destroy()
            except:
                pass

        # إيقاف العمليات
        self.is_loading = False
        self.loading_operations.clear()

        # مسح الكاش
        self.used_booking_numbers.clear()

        # إيقاف الخيوط
        shutdown_threading()

        logger.info("تم تنظيف موارد التطبيق")

    # =============== إدارة القوائم المنسدلة ===============

    def refresh_dropdown_manager(self):
        """إعادة تهيئة مدير القوائم المنسدلة"""
        if HAS_AIRTABLE_DROPDOWNS:
            try:
                self.dropdown_manager = AirtableDropdownManager(
                    config_manager=self.config_mgr,
                    db_manager=self.db_mgr
                )
                logger.info("تم إعادة تهيئة مدير القوائم المنسدلة")
                return True
            except Exception as e:
                logger.error(f"فشل في إعادة تهيئة مدير القوائم المنسدلة: {e}")
                self.dropdown_manager = None
                return False
        return False

    def get_dropdown_status(self) -> Dict[str, Any]:
        """الحصول على حالة مدير القوائم المنسدلة"""
        if self.dropdown_manager:
            return self.dropdown_manager.get_status()
        return {
            "available": HAS_AIRTABLE_DROPDOWNS,
            "initialized": False,
            "errors": {"general": "مدير القوائم المنسدلة غير مهيأ"}
        }

    # =============== دوال مساعدة إضافية لأرقام الحجز ===============

    def is_booking_number_unique(self, booking_number: str) -> bool:
        """التحقق من عدم تكرار رقم الحجز"""
        return booking_number not in self.used_booking_numbers

    def add_booking_number_to_cache(self, booking_number: str):
        """إضافة رقم حجز إلى الكاش"""
        if booking_number:
            self.used_booking_numbers.add(booking_number)
            logger.debug(f"تم إضافة رقم الحجز {booking_number} إلى الكاش")

    def remove_booking_number_from_cache(self, booking_number: str):
        """إزالة رقم حجز من الكاش"""
        if booking_number and booking_number in self.used_booking_numbers:
            self.used_booking_numbers.remove(booking_number)
            logger.debug(f"تم إزالة رقم الحجز {booking_number} من الكاش")

    def get_booking_numbers_count(self) -> int:
        """الحصول على عدد أرقام الحجز المحفوظة"""
        return len(self.used_booking_numbers)

    # =============== دوال التشخيص والمساعدة ===============

    def debug_user_info(self):
        """دالة تشخيص مبسطة لفحص معلومات المستخدم الحالي"""
        logger.info("=" * 50)
        logger.info("تشخيص معلومات المستخدم")
        logger.info("=" * 50)

        logger.info(f"اسم المستخدم: {self.current_username}")
        logger.info(f"معلومات المستخدم: {self.current_user_info}")
        logger.info(f"Collaborator (نوع): {type(self.current_user_collaborator)}")
        logger.info(f"Collaborator (قيمة): {self.current_user_collaborator}")
        logger.info(f"Collaborator (repr): {repr(self.current_user_collaborator)}")

        # اختبار الحصول على معرف المستخدم
        user_id = self._get_current_user_id()
        logger.info(f"معرف المستخدم النهائي: '{user_id}'")
        logger.info(f"معرف المستخدم (repr): {repr(user_id)}")

        logger.info("=" * 50)

    def test_user_field_creation(self) -> bool:
        """اختبار مبسط لحقل Assigned To"""
        try:
            user_id = self._get_current_user_id()
            if not user_id:
                logger.error("❌ لا يوجد معرف مستخدم")
                return False

            logger.info(f"✅ اختبار ناجح - معرف المستخدم: '{user_id}'")
            logger.info(f"طول المعرف: {len(user_id)}")
            logger.info(f"يبدأ بـ usr: {user_id.startswith('usr')}")
            return True

        except Exception as e:
            logger.error(f"❌ خطأ في اختبار معرف المستخدم: {e}")
            return False
            # -*- coding: utf-8 -*-
