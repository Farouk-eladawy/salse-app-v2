# -*- coding: utf-8 -*-
"""
core/permissions.py

نظام إدارة الصلاحيات للمستخدمين
يحدد ما يمكن لكل مستخدم القيام به في التطبيق
"""

from typing import List, Set
from functools import wraps
from tkinter import messagebox
from core.logger import logger


class Permission:
    """تعريف الصلاحيات المتاحة في التطبيق"""
    VIEW_ALL = "view_all"
    CREATE_SALES = "create_sales"
    EDIT_SALES = "edit_sales"
    DELETE_SALES = "delete_sales"
    MANAGE_USERS = "manage_users"
    EXPORT_DATA = "export_data"
    VIEW_REPORTS = "view_reports"
    SETTINGS = "settings"


class PermissionManager:
    """
    مدير الصلاحيات - يحدد ويتحقق من صلاحيات المستخدمين
    """

    def __init__(self):
        """تهيئة مدير الصلاحيات"""
        self.current_user_id: str = ""
        self.current_user_permissions: Set[str] = set()

    def set_current_user(self, user_id: str, permissions: List[str]) -> None:
        """
        تعيين المستخدم الحالي وصلاحياته

        :param user_id: معرف المستخدم
        :param permissions: قائمة صلاحيات المستخدم
        """
        self.current_user_id = user_id
        self.current_user_permissions = set(permissions)

        logger.info(f"تم تعيين المستخدم {user_id} بالصلاحيات: {permissions}")

    def has_permission(self, permission: str) -> bool:
        """
        التحقق من وجود صلاحية معينة للمستخدم

        :param permission: الصلاحية المطلوب التحقق منها
        :return: True إذا كان المستخدم يملك الصلاحية
        """
        return permission in self.current_user_permissions

    def check_permission(self, permission: str, show_message: bool = True) -> bool:
        """
        التحقق من الصلاحية مع إظهار رسالة في حالة الرفض

        :param permission: الصلاحية المطلوبة
        :param show_message: إظهار رسالة خطأ في حالة عدم وجود صلاحية
        :return: True إذا كان المستخدم يملك الصلاحية
        """
        if self.has_permission(permission):
            return True

        if show_message:
            permission_names = {
                Permission.VIEW_ALL: "عرض جميع السجلات",
                Permission.CREATE_SALES: "إضافة سجلات جديدة",
                Permission.EDIT_SALES: "تعديل السجلات",
                Permission.DELETE_SALES: "حذف السجلات",
                Permission.MANAGE_USERS: "إدارة المستخدمين",
                Permission.EXPORT_DATA: "تصدير البيانات",
                Permission.VIEW_REPORTS: "عرض التقارير",
                Permission.SETTINGS: "تغيير الإعدادات"
            }

            permission_name = permission_names.get(permission, permission)

            messagebox.showerror(
                "عدم وجود صلاحية",
                f"ليس لديك صلاحية: {permission_name}"
            )

        logger.warning(
            f"محاولة وصول غير مصرح: المستخدم {self.current_user_id} "
            f"حاول {permission}"
        )

        return False

    def get_user_permissions(self) -> Set[str]:
        """
        الحصول على جميع صلاحيات المستخدم الحالي

        :return: مجموعة الصلاحيات
        """
        return self.current_user_permissions.copy()

    def can_user_modify_record(self, record_owner_id: str = None) -> bool:
        """
        التحقق من إمكانية تعديل سجل

        :param record_owner_id: معرف مالك السجل (غير مستخدم حالياً)
        :return: True إذا كان يمكن التعديل
        """
        return self.has_permission(Permission.EDIT_SALES)

    def can_user_delete_record(self) -> bool:
        """
        التحقق من إمكانية حذف سجل

        :return: True إذا كان يمكن الحذف
        """
        return self.has_permission(Permission.DELETE_SALES)


# Singleton instance
permission_manager = PermissionManager()


def require_permission(permission: str):
    """
    Decorator للتحقق من الصلاحيات قبل تنفيذ دالة

    استخدام:
    @require_permission(Permission.DELETE_SALES)
    def delete_record(self):
        # كود الحذف
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if permission_manager.check_permission(permission):
                return func(*args, **kwargs)
            # إذا لم تكن هناك صلاحية، لا تنفذ الدالة
            return None
        return wrapper
    return decorator


# دوال مساعدة للاستخدام السريع
def can_view_all() -> bool:
    """التحقق من صلاحية عرض جميع السجلات"""
    return permission_manager.has_permission(Permission.VIEW_ALL)

def can_create() -> bool:
    """التحقق من صلاحية الإنشاء"""
    return permission_manager.has_permission(Permission.CREATE_SALES)

def can_edit() -> bool:
    """التحقق من صلاحية التعديل"""
    return permission_manager.has_permission(Permission.EDIT_SALES)

def can_delete() -> bool:
    """التحقق من صلاحية الحذف"""
    return permission_manager.has_permission(Permission.DELETE_SALES)

def can_export() -> bool:
    """التحقق من صلاحية التصدير"""
    return permission_manager.has_permission(Permission.EXPORT_DATA)

def can_manage_users() -> bool:
    """التحقق من صلاحية إدارة المستخدمين"""
    return permission_manager.has_permission(Permission.MANAGE_USERS)

def can_view_reports() -> bool:
    """التحقق من صلاحية عرض التقارير"""
    return permission_manager.has_permission(Permission.VIEW_REPORTS)

def can_change_settings() -> bool:
    """التحقق من صلاحية تغيير الإعدادات"""
    return permission_manager.has_permission(Permission.SETTINGS)