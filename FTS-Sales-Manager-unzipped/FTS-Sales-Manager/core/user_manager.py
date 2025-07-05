# -*- coding: utf-8 -*-
"""
core/user_manager.py - نسخة محسنة

مدير المستخدمين المحسن مع إصلاح مشكلة get_field_value
"""

from typing import Dict, Optional, Any
import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta

from core.airtable_manager import AirtableModel
from core.db_manager import DatabaseManager
from core.logger import logger


class UserManager:
    """مدير المستخدمين المحسن"""

    def __init__(self, airtable_model: AirtableModel, db_manager: DatabaseManager) -> None:
        self.airtable_model: AirtableModel = airtable_model
        self.db: DatabaseManager = db_manager

        # تخزين المستخدمين في الذاكرة
        self._users_cache: Dict[str, Dict[str, Any]] = {}

        # حماية ضد هجمات القوة الغاشمة
        self._failed_attempts: Dict[str, list] = {}
        self._max_attempts = 5
        self._lockout_duration = timedelta(minutes=15)

        # مفتاح التشفير
        self._salt = b"FTS_SALES_MANAGER_2024"

        # تحميل المستخدمين
        self._load_users()

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        """تشفير كلمة المرور باستخدام PBKDF2-HMAC-SHA256"""
        if salt is None:
            salt = secrets.token_bytes(32)

        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100_000
        )

        storage = salt + key
        return base64.b64encode(storage).decode('ascii')

    def _verify_password(self, stored_password: str, provided_password: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            decoded = base64.b64decode(stored_password)
            if len(decoded) >= 32:
                salt = decoded[:32]
                stored_key = decoded[32:]

                new_key = hashlib.pbkdf2_hmac(
                    'sha256',
                    provided_password.encode('utf-8'),
                    salt,
                    100_000
                )

                return hmac.compare_digest(stored_key, new_key)
        except Exception:
            pass

        # التوافق مع كلمات المرور القديمة
        return stored_password == provided_password

    def _is_account_locked(self, username: str) -> bool:
        """التحقق من قفل الحساب"""
        if username not in self._failed_attempts:
            return False

        cutoff_time = datetime.now() - self._lockout_duration
        self._failed_attempts[username] = [
            attempt for attempt in self._failed_attempts[username]
            if attempt > cutoff_time
        ]

        return len(self._failed_attempts[username]) >= self._max_attempts

    def _record_failed_attempt(self, username: str) -> None:
        """تسجيل محاولة فاشلة"""
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []

        self._failed_attempts[username].append(datetime.now())

        cutoff_time = datetime.now() - self._lockout_duration
        self._failed_attempts[username] = [
            attempt for attempt in self._failed_attempts[username]
            if attempt > cutoff_time
        ]

    def _clear_failed_attempts(self, username: str) -> None:
        """مسح المحاولات الفاشلة"""
        if username in self._failed_attempts:
            del self._failed_attempts[username]

    def _load_users(self) -> None:
        """جلب جميع سجلات المستخدمين من Airtable"""
        logger.info("UserManager: بدء جلب المستخدمين من Airtable")

        try:
            records = self.airtable_model.fetch_records(use_cache=False)
            self._users_cache.clear()

            active_users = 0
            inactive_users = 0

            for rec in records:
                fields = rec.get("fields", {}) or {}

                username = fields.get("Username")
                if not username:
                    continue

                # كلمة المرور - محاولة العثور عليها في حقول مختلفة
                stored_password = fields.get("PasswordHash") or fields.get("Password") or fields.get("password")
                if not stored_password:
                    logger.warning(f"UserManager: المستخدم '{username}' بدون كلمة مرور")
                    continue

                is_active = fields.get("Active", True)
                if not is_active:
                    inactive_users += 1
                    logger.debug(f"UserManager: المستخدم '{username}' غير نشط")
                    continue

                active_users += 1

                # البيانات الإضافية
                airtable_view = fields.get("Airtable View")
                role = fields.get("Role", "viewer")
                airtable_collaborator = fields.get("Airtable Collaborator")

                last_login = fields.get("Last Login")
                login_count = fields.get("Login Count", 0)

                lookup_key = username.lower()
                self._users_cache[lookup_key] = {
                    'username': username,
                    'password': stored_password,
                    'view': airtable_view,
                    'role': role,
                    'airtable_collaborator': airtable_collaborator,
                    'record_id': rec.get("id"),
                    'is_active': is_active,
                    'last_login': last_login,
                    'login_count': login_count
                }

                logger.debug(f"تم تحميل المستخدم: {username} (Role: {role})")

            logger.info(f"UserManager: تم تحميل {active_users} مستخدم نشط ({inactive_users} غير نشط)")

        except Exception as exc:
            logger.error(f"UserManager: خطأ أثناء جلب المستخدمين: {exc}", exc_info=True)
            if not self._users_cache:
                raise Exception("فشل في تحميل بيانات المستخدمين من Airtable")

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """التحقق من بيانات تسجيل الدخول"""
        if self._is_account_locked(username):
            logger.warning(f"UserManager: محاولة دخول لحساب مقفل '{username}'")
            return None

        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)

        if not user_info:
            logger.warning(f"UserManager: محاولة دخول باسم مستخدم غير موجود '{username}'")
            self._record_failed_attempt(username)
            return None

        if self._verify_password(user_info['password'], password):
            logger.info(f"UserManager: تسجيل دخول ناجح للمستخدم '{username}'")

            self._clear_failed_attempts(username)

            # تحديث آخر تسجيل دخول
            self._update_last_login(user_info['record_id'])

            # تحديث كلمة المرور إذا كانت نص عادي
            if user_info['password'] == password:
                logger.info(f"UserManager: تحديث كلمة مرور المستخدم '{username}' لتكون مشفرة")
                self._update_password_hash(user_info['record_id'], password)

            return {
                'username': user_info['username'],
                'view': user_info.get('view'),
                'role': user_info.get('role', 'viewer'),
                'airtable_collaborator': user_info.get('airtable_collaborator'),
                'record_id': user_info.get('record_id')
            }
        else:
            logger.warning(f"UserManager: كلمة مرور خاطئة للمستخدم '{username}'")
            self._record_failed_attempt(username)
            return None

    def _update_last_login(self, record_id: str) -> None:
        """تحديث آخر تسجيل دخول للمستخدم"""
        try:
            # الحصول على عدد مرات تسجيل الدخول الحالي
            current_login_count = 0
            for user_data in self._users_cache.values():
                if user_data.get('record_id') == record_id:
                    current_login_count = user_data.get('login_count', 0)
                    break

            fields = {
                "Last Login": datetime.now().isoformat(),
                "Login Count": current_login_count + 1
            }
            self.airtable_model.update_record(record_id, fields)

        except Exception as e:
            logger.error(f"UserManager: فشل تحديث آخر تسجيل دخول: {e}")

    def _update_password_hash(self, record_id: str, password: str) -> None:
        """تحديث كلمة المرور لتكون مشفرة"""
        try:
            hashed = self._hash_password(password)

            # محاولة تحديث في حقول مختلفة
            success = False

            # محاولة 1: حقل PasswordHash
            try:
                fields = {"PasswordHash": hashed}
                self.airtable_model.update_record(record_id, fields)
                success = True
                logger.info("تم تحديث كلمة المرور في حقل PasswordHash")
            except Exception as e1:
                logger.warning(f"فشل تحديث PasswordHash: {e1}")

                # محاولة 2: حقل Password
                try:
                    fields = {"Password": hashed}
                    self.airtable_model.update_record(record_id, fields)
                    success = True
                    logger.info("تم تحديث كلمة المرور في حقل Password")
                except Exception as e2:
                    logger.error(f"فشل تحديث Password أيضاً: {e2}")

            if success:
                # تحديث الكاش
                for user_data in self._users_cache.values():
                    if user_data.get('record_id') == record_id:
                        user_data['password'] = hashed
                        break

        except Exception as e:
            logger.error(f"UserManager: فشل تحديث كلمة المرور المشفرة: {e}")

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """تغيير كلمة مرور المستخدم"""
        if not self.authenticate(username, old_password):
            return False

        if not self._validate_password_strength(new_password):
            logger.warning(f"UserManager: كلمة المرور الجديدة ضعيفة للمستخدم '{username}'")
            return False

        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)
        if user_info:
            self._update_password_hash(user_info['record_id'], new_password)
            logger.info(f"UserManager: تم تغيير كلمة مرور المستخدم '{username}' بنجاح")
            return True

        return False

    def _validate_password_strength(self, password: str) -> bool:
        """التحقق من قوة كلمة المرور"""
        if len(password) < 8:
            return False

        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)

        return has_letter and has_digit

    def reset_password(self, username: str, new_password: str, admin_token: str) -> bool:
        """إعادة تعيين كلمة مرور المستخدم"""
        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)

        if not user_info:
            logger.error(f"UserManager: محاولة إعادة تعيين كلمة مرور لمستخدم غير موجود '{username}'")
            return False

        if not self._validate_password_strength(new_password):
            return False

        self._update_password_hash(user_info['record_id'], new_password)
        logger.info(f"UserManager: تم إعادة تعيين كلمة مرور المستخدم '{username}' بواسطة المدير")

        self._clear_failed_attempts(username)

        return True

    def reload_users(self) -> None:
        """إعادة تحميل بيانات المستخدمين من Airtable"""
        logger.debug("UserManager: إعادة تحميل بيانات المستخدمين")
        self._load_users()

    def get_user_view(self, username: str) -> Optional[str]:
        """الحصول على الـ View المخصص للمستخدم"""
        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)
        return user_info.get('view') if user_info else None

    def get_user_collaborator(self, username: str) -> Optional[Any]:
        """الحصول على Airtable Collaborator للمستخدم"""
        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)
        return user_info.get('airtable_collaborator') if user_info else None

    def get_user_role(self, username: str) -> str:
        """الحصول على دور المستخدم"""
        lookup_key = username.strip().lower()
        user_info = self._users_cache.get(lookup_key)
        return user_info.get('role', 'viewer') if user_info else 'viewer'

    def get_all_users(self) -> Dict[str, Dict[str, Any]]:
        """الحصول على جميع المستخدمين"""
        safe_users = {}
        for key, user in self._users_cache.items():
            safe_user = user.copy()
            safe_user.pop('password', None)
            safe_users[key] = safe_user
        return safe_users

    def user_exists(self, username: str) -> bool:
        """التحقق من وجود مستخدم"""
        lookup_key = username.strip().lower()
        return lookup_key in self._users_cache

    def create_user(self, username: str, password: str, role: str = "viewer",
                   admin_token: str = None) -> Optional[str]:
        """إنشاء مستخدم جديد"""
        if self.user_exists(username):
            logger.error(f"UserManager: المستخدم '{username}' موجود بالفعل")
            return None

        if not self._validate_password_strength(password):
            logger.error(f"UserManager: كلمة مرور ضعيفة للمستخدم الجديد '{username}'")
            return None

        password_hash = self._hash_password(password)

        try:
            # محاولة استخدام حقول مختلفة
            fields = {
                "Username": username,
                "Role": role,
                "Active": True,
                "Created Date": datetime.now().isoformat()
            }

            # محاولة إضافة كلمة المرور المشفرة
            try:
                fields["PasswordHash"] = password_hash
            except:
                # إذا فشل، استخدم حقل Password
                fields["Password"] = password_hash

            result = self.airtable_model.create_record(fields)
            if result:
                logger.info(f"UserManager: تم إنشاء المستخدم '{username}' بنجاح")
                self.reload_users()
                return result.get('id')

        except Exception as e:
            logger.error(f"UserManager: فشل إنشاء المستخدم '{username}': {e}")

        return None