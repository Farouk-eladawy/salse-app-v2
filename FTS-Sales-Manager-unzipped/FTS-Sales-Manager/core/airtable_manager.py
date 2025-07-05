# -*- coding: utf-8 -*-
"""
core/airtable_manager.py - الملف الموحد لإدارة Airtable

يجمع وظائف:
- airtable_manager.py (العمليات الأساسية والمتقدمة)
- airtable_model.py (النموذج البسيط والكاش)
- airtable_integration_helper.py (الجداول المرتبطة)

مع إزالة التكرار وتحسين الأداء وإصلاح مشكلة حقل Assigned To
"""

import os
import json
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta
import requests
import re

logger = logging.getLogger(__name__)


class AirtableManager:
    """
    مدير موحد لجميع عمليات Airtable
    يجمع العمليات الأساسية والمتقدمة والجداول المرتبطة
    مع إصلاح مشكلة حقل Assigned To
    """

    # إعدادات الكاش والأداء
    CACHE_DURATION = timedelta(minutes=30)
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.5
    MAX_WORKERS = 3

    def __init__(self,
                 config_manager=None,
                 db_manager=None,
                 table_name: str = "",
                 view_name: str = None):
        """
        تهيئة مدير Airtable الموحد

        :param config_manager: مدير الإعدادات
        :param db_manager: مدير قاعدة البيانات
        :param table_name: اسم الجدول
        :param view_name: اسم العرض (اختياري)
        """
        self.config = config_manager
        self.db = db_manager
        self.table_name = table_name
        self.view_name = view_name

        # إعدادات API
        self._setup_api_config()

        # إعدادات الكاش
        self.last_fetch = None
        self.cached_data = []
        self.cache_timestamps = {}
        self._cache_lock = threading.RLock()

        # إعدادات الأخطاء
        self.errors = {}
        self._loading = False

        # البيانات المخزنة للجداول المرتبطة
        self.cached_related_data = {
            'add_on_prices': [],
            'management_options': [],
            'trip_names': [],
            'users': []
        }

        logger.info(f"تم تهيئة AirtableManager للجدول: {table_name}")

    def _setup_api_config(self):
        """إعداد معلومات API"""
        if self.config:
            self.api_key = self.config.get("airtable_api_key", "")
            self.base_id = self.config.get("airtable_base_id", "")
        else:
            self.api_key = os.getenv('AIRTABLE_API_KEY', "")
            self.base_id = os.getenv('AIRTABLE_BASE_ID', "")

        if not all([self.api_key, self.base_id]):
            logger.error("إعدادات Airtable غير مكتملة (API Key أو Base ID)")
            return

        # بناء URL والـ headers
        if self.table_name:
            self.endpoint = f"https://api.airtable.com/v0/{self.base_id}/{self.table_name}"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json; charset=utf-8"
        }

    def set_table(self, table_name: str, view_name: str = None):
        """تغيير الجدول والعرض"""
        self.table_name = table_name
        self.view_name = view_name
        if self.base_id:
            self.endpoint = f"https://api.airtable.com/v0/{self.base_id}/{table_name}"
        logger.info(f"تم تغيير الجدول إلى: {table_name} (العرض: {view_name or 'الكل'})")

    def set_view(self, view_name: str):
        """تغيير العرض المستخدم"""
        self.view_name = view_name
        logger.info(f"تم تغيير العرض إلى: {view_name}")

    # ========================================
    # 🔧 العمليات الأساسية (CRUD)
    # ========================================

    def fetch_records(self,
                     use_cache: bool = True,
                     force_refresh: bool = False,
                     filter_formula: str = None,
                     view: str = None) -> List[Dict[str, Any]]:
        """
        جلب السجلات مع دعم الكاش والفلترة

        :param use_cache: استخدام الكاش
        :param force_refresh: إجبار التحديث
        :param filter_formula: صيغة الفلتر
        :param view: العرض المطلوب
        :return: قائمة السجلات
        """
        # التحقق من الكاش
        if use_cache and not force_refresh and self._is_cache_valid():
            logger.debug(f"استخدام الكاش للجدول: {self.table_name}")
            return self.cached_data

        logger.info(f"جلب السجلات من Airtable للجدول: {self.table_name}")

        all_records = []
        url = self.endpoint
        params = {"pageSize": 100}

        # إضافة المعاملات
        if view or self.view_name:
            params["view"] = view or self.view_name
        if filter_formula:
            params["filterByFormula"] = filter_formula

        while True:
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()

                payload = response.json()
                records = payload.get("records", [])
                all_records.extend(records)

                logger.debug(f"استلام {len(records)} سجل من {self.table_name}")

                # التحقق من الصفحة التالية
                offset = payload.get("offset")
                if offset:
                    params["offset"] = offset
                    time.sleep(0.2)  # تجنب rate limiting
                else:
                    break

            except requests.RequestException as e:
                logger.error(f"خطأ في جلب السجلات من {self.table_name}: {e}")
                # محاولة إرجاع الكاش القديم
                if self.cached_data:
                    logger.warning("إرجاع الكاش القديم بسبب فشل الطلب")
                    return self.cached_data
                raise

        # تحديث الكاش
        with self._cache_lock:
            self.cached_data = all_records
            self.last_fetch = datetime.now()
            self.cache_timestamps[self.table_name] = datetime.now()

        # حفظ في قاعدة البيانات المحلية
        if self.db:
            self._save_to_local_db(all_records)

        logger.info(f"تم جلب {len(all_records)} سجل من {self.table_name}")
        return all_records

    def fetch_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """جلب سجل واحد بواسطة ID"""
        url = f"{self.endpoint}/{record_id}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()

                record = response.json()
                logger.info(f"تم جلب السجل {record_id} من {self.table_name}")
                return record

            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"محاولة {attempt + 1} فشلت لجلب السجل {record_id}: {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"فشل جلب السجل {record_id} نهائياً: {e}")
                    return None

    def create_record(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """إنشاء سجل جديد مع معالجة صحيحة لحقل Assigned To"""
        # معالجة خاصة للحقول المعقدة
        processed_fields = self._process_fields_for_create(fields)
        payload = {"fields": processed_fields}

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"محاولة إنشاء سجل (المحاولة {attempt + 1}): {self.table_name}")
                logger.debug(f"البيانات المرسلة: {json.dumps(payload, indent=2, ensure_ascii=False)}")

                # 🔍 logging خاص لحقل Assigned To
                if 'Assigned To' in processed_fields:
                    assigned_value = processed_fields['Assigned To']
                    logger.info(f"🎯 Assigned To في الـ payload: {type(assigned_value)} = {assigned_value}")

                response = requests.post(
                    self.endpoint,
                    headers=self.headers,
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT
                )

                if response.status_code == 422:
                    logger.error(f"خطأ في بيانات السجل (422): {response.text}")
                    if "Assigned To" in response.text:
                        logger.error("❌ مشكلة في حقل Assigned To")
                        # logging إضافي للتشخيص
                        if 'Assigned To' in processed_fields:
                            assigned_value = processed_fields['Assigned To']
                            logger.error(f"قيمة Assigned To المرسلة: {assigned_value}")
                            logger.error(f"نوع القيمة: {type(assigned_value)}")
                            logger.error(f"محتوى JSON: {json.dumps(assigned_value, ensure_ascii=False)}")
                    return None

                response.raise_for_status()

                # إلغاء الكاش بعد الإنشاء
                self._invalidate_cache()

                created = response.json()
                rec_id = created.get("id")
                logger.info(f"✅ تم إنشاء سجل جديد: {rec_id} في {self.table_name}")
                return created

            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"محاولة إنشاء {attempt + 1} فشلت: {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"❌ فشل إنشاء السجل نهائياً: {e}")
                    if hasattr(e, 'response') and e.response:
                        logger.error(f"تفاصيل الخطأ: {e.response.text}")
                    return None

    def update_record(self, record_id: str, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """تحديث سجل موجود"""
        url = f"{self.endpoint}/{record_id}"

        # معالجة الحقول
        processed_fields = self._process_fields_for_update(fields)
        payload = {"fields": processed_fields}

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"تحديث السجل {record_id} (المحاولة {attempt + 1})")

                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()

                # إلغاء الكاش
                self._invalidate_cache()

                updated = response.json()
                logger.info(f"تم تحديث السجل {record_id} في {self.table_name}")
                return updated

            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"محاولة تحديث {attempt + 1} فشلت: {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"فشل تحديث السجل {record_id}: {e}")
                    return None

    def delete_record(self, record_id: str) -> bool:
        """حذف سجل"""
        url = f"{self.endpoint}/{record_id}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.delete(
                    url,
                    headers=self.headers,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()

                # إلغاء الكاش
                self._invalidate_cache()

                logger.info(f"تم حذف السجل {record_id} من {self.table_name}")
                return True

            except requests.RequestException as e:
                if attempt < self.MAX_RETRIES - 1:
                    logger.warning(f"محاولة حذف {attempt + 1} فشلت: {e}")
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"فشل حذف السجل {record_id}: {e}")
                    return False

    # ========================================
    # 📄 العمليات المتقدمة (Pagination & Search)
    # ========================================

    def get_records_paginated(self, limit=50, offset=None):
        """جلب السجلات مع pagination"""
        url = self.endpoint
        params = {"pageSize": min(limit, 100)}

        if offset:
            params["offset"] = offset
        if self.view_name:
            params["view"] = self.view_name

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            records = data.get("records", [])
            next_offset = data.get("offset", None)

            logger.info(f"جلب {len(records)} سجل في هذه الصفحة من {self.table_name}")
            return records, next_offset

        except requests.RequestException as e:
            logger.error(f"خطأ في جلب الصفحة: {e}")
            return [], None

    def search_records(self, formula: str) -> List[Dict[str, Any]]:
        """البحث باستخدام Airtable formula"""
        try:
            params = {"filterByFormula": formula}
            if self.view_name:
                params["view"] = self.view_name

            response = requests.get(
                self.endpoint,
                headers=self.headers,
                params=params,
                timeout=self.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            records = response.json().get('records', [])
            logger.info(f"وجد {len(records)} سجل مطابق للبحث في {self.table_name}")
            return records

        except requests.RequestException as e:
            logger.error(f"خطأ في البحث: {e}")
            return []

    # ========================================
    # 📋 دوال القوائم المنسدلة
    # ========================================

    def get_all_values(self, field_name: str = "Name", force_refresh: bool = False) -> List[str]:
        """جلب جميع القيم الفريدة من حقل معين"""
        records = self.fetch_records(force_refresh=force_refresh)
        values = []

        for record in records:
            fields = record.get('fields', {})
            value = fields.get(field_name)
            if value and value not in values:
                # تنظيف القيمة
                clean_value = str(value).strip()
                if clean_value and clean_value not in values:
                    values.append(clean_value)

        return sorted(values)

    def insert_if_not_exists(self, value: str, field_name: str = "Name") -> bool:
        """إضافة قيمة جديدة إذا لم تكن موجودة"""
        if not value or not value.strip():
            logger.warning(f"قيمة فارغة للحقل {field_name}")
            return False

        existing_values = self.get_all_values(field_name)
        clean_value = str(value).strip()

        if clean_value not in existing_values:
            result = self.create_record({field_name: clean_value})
            if result:
                logger.info(f"تم إضافة '{clean_value}' إلى {self.table_name}")
                return True
            return False

        logger.debug(f"القيمة '{clean_value}' موجودة بالفعل في {self.table_name}")
        return False

    # دوال متخصصة للجداول المختلفة
    def fetch_agencies(self, field_name: str = "Agency Name") -> List[str]:
        """جلب قائمة الوكالات"""
        return self._fetch_dropdown_values(field_name, ["Agency Name", "Name", "Agency"])

    def fetch_guides(self, field_name: str = "Name") -> List[str]:
        """جلب قائمة المرشدين"""
        return self._fetch_dropdown_values(field_name, ["Guide Name", "Name", "Language"])

    def fetch_destinations(self, field_name: str = "Destination") -> List[str]:
        """جلب قائمة الوجهات"""
        return self._fetch_dropdown_values(field_name, ["Destination", "Name", "City", "Location"])

    def get_dropdown_values(self, field_name: str, default_field: str = "Name") -> List[str]:
        """دالة عامة لجلب قيم أي قائمة منسدلة"""
        return self._fetch_dropdown_values(field_name, [field_name, default_field])

    def _fetch_dropdown_values(self, primary_field: str, fallback_fields: List[str]) -> List[str]:
        """دالة مساعدة لجلب قيم القوائم المنسدلة"""
        try:
            records = self.fetch_records()
            values = []

            for record in records:
                fields = record.get('fields', {})
                value = None

                # البحث في الحقول المحتملة
                for field in fallback_fields:
                    if field in fields and fields[field]:
                        value = fields[field]
                        break

                if value:
                    clean_value = str(value).strip()
                    if clean_value and clean_value not in values:
                        values.append(clean_value)

            values.sort()
            logger.info(f"تم جلب {len(values)} قيمة من {primary_field} في {self.table_name}")
            return values

        except Exception as e:
            logger.error(f"خطأ في جلب قيم {primary_field}: {e}")
            return []

    # ========================================
    # 🔗 الجداول المرتبطة (من integration_helper)
    # ========================================

    def fetch_all_related_data(self, callback=None, error_callback=None):
        """جلب جميع البيانات من الجداول المرتبطة"""
        def fetch_task():
            try:
                # جلب البيانات من كل جدول
                self._fetch_add_on_prices()
                self._fetch_management_options()
                self._fetch_trip_names()
                self._fetch_users()

                logger.info("تم جلب جميع البيانات من الجداول المرتبطة")

                if callback:
                    callback(self.cached_related_data)

                return self.cached_related_data

            except Exception as e:
                logger.error(f"خطأ في جلب البيانات المرتبطة: {e}")
                if error_callback:
                    error_callback(str(e))
                raise

        # تشغيل في خيط منفصل
        threading.Thread(target=fetch_task, daemon=True).start()

    def _fetch_add_on_prices(self):
        """جلب بيانات الإضافات"""
        original_table = self.table_name
        try:
            self.set_table("Add-on prices")
            records = self.fetch_records(use_cache=False)
            add_ons = []

            for record in records:
                fields = record.get('fields', {})
                add_on_name = fields.get('Add-ons', '')
                if add_on_name:
                    add_ons.append(add_on_name)

            self.cached_related_data['add_on_prices'] = sorted(list(set(add_ons)))
            logger.info(f"تم جلب {len(add_ons)} إضافة")

        except Exception as e:
            logger.error(f"خطأ في جلب Add-on prices: {e}")
        finally:
            self.set_table(original_table)

    def _fetch_management_options(self):
        """جلب بيانات خيارات الإدارة"""
        original_table = self.table_name
        try:
            self.set_table("Management Option")
            records = self.fetch_records(use_cache=False)
            options = []

            for record in records:
                fields = record.get('fields', {})
                option_name = fields.get('Main Option', '')
                if option_name:
                    options.append(option_name)

            self.cached_related_data['management_options'] = sorted(list(set(options)))
            logger.info(f"تم جلب {len(options)} خيار إدارة")

        except Exception as e:
            logger.error(f"خطأ في جلب Management Option: {e}")
        finally:
            self.set_table(original_table)

    def _fetch_trip_names(self):
        """جلب أسماء الرحلات"""
        original_table = self.table_name
        try:
            self.set_table("Trip Name Correction")
            records = self.fetch_records(use_cache=False)
            trip_names = []

            for record in records:
                fields = record.get('fields', {})
                old_name = fields.get('Old Name', '')
                new_name = fields.get('New Name', '')

                trip_name = new_name if new_name else old_name
                if trip_name:
                    trip_names.append(trip_name)

            self.cached_related_data['trip_names'] = sorted(list(set(trip_names)))
            logger.info(f"تم جلب {len(trip_names)} اسم رحلة")

        except Exception as e:
            logger.error(f"خطأ في جلب Trip Name Correction: {e}")
        finally:
            self.set_table(original_table)

    def _fetch_users(self):
        """جلب بيانات المستخدمين"""
        original_table = self.table_name
        try:
            self.set_table("Users")
            records = self.fetch_records(use_cache=False)
            users = []

            for record in records:
                fields = record.get('fields', {})
                username = fields.get('Username', '')
                collaborator = fields.get('Airtable Collaborator')

                if username:
                    users.append(username)
                elif collaborator and isinstance(collaborator, dict):
                    user_name = collaborator.get('name', '')
                    if user_name:
                        users.append(user_name)

            self.cached_related_data['users'] = sorted(list(set(users)))
            logger.info(f"تم جلب {len(users)} مستخدم")

        except Exception as e:
            logger.error(f"خطأ في جلب Users: {e}")
        finally:
            self.set_table(original_table)

    def get_cached_related_data(self) -> Dict[str, List[str]]:
        """الحصول على البيانات المرتبطة المخزنة"""
        return self.cached_related_data

    def refresh_related_data(self, table_name: Optional[str] = None):
        """تحديث البيانات المرتبطة"""
        if table_name:
            if table_name == "Add-on prices":
                self._fetch_add_on_prices()
            elif table_name == "Management Option":
                self._fetch_management_options()
            elif table_name == "Trip Name Correction":
                self._fetch_trip_names()
            elif table_name == "Users":
                self._fetch_users()
        else:
            self.fetch_all_related_data()

    # ========================================
    # 🛠️ دوال مساعدة وكاش
    # ========================================

    def _process_fields_for_create(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة الحقول قبل الإنشاء - محدثة لحقل Assigned To"""
        processed = {}

        for key, value in fields.items():
            if key == 'Assigned To':
                # معالجة خاصة لحقل Assigned To - إرجاع object
                processed_value = self._process_assigned_to_field(value)
                if processed_value:  # فقط إذا كان هناك قيمة صالحة
                    processed[key] = processed_value
                    logger.debug(f"✅ Assigned To processed: {processed_value}")
            elif value is not None and str(value).strip():
                processed[key] = value

        return processed

    def _process_fields_for_update(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة الحقول قبل التحديث - محدثة لحقل Assigned To"""
        processed = {}

        for key, value in fields.items():
            if key == 'Assigned To':
                # معالجة خاصة لحقل Assigned To
                processed_value = self._process_assigned_to_field(value)
                if processed_value:
                    processed[key] = processed_value
            else:
                processed[key] = value

        return processed

    def _process_assigned_to_field(self, value: Any) -> Optional[Dict[str, str]]:
        """معالجة خاصة محسنة لحقل Assigned To - إرجاع object بدلاً من string"""
        if value is None:
            return None

        # إذا كان dict بالفعل، تحقق من وجود id أو email
        if isinstance(value, dict):
            if 'id' in value:
                user_id = str(value['id']).strip()
                logger.debug(f"Dict with id found: {user_id}")
                return {"id": user_id}
            elif 'email' in value:
                email = str(value['email']).strip()
                logger.debug(f"Dict with email found: {email}")
                return {"email": email}
            else:
                # البحث عن أي قيمة مفيدة في الـ dict
                for k, v in value.items():
                    if v and str(v).strip():
                        clean_val = str(v).strip()
                        if '@' in clean_val:
                            return {"email": clean_val}
                        elif clean_val.startswith(('usr', 'rec')) or len(clean_val) > 10:
                            return {"id": clean_val}
                return None

        # تحويل إلى string أولاً
        str_value = str(value)

        # إزالة أي escape characters أو quotes زائدة
        cleaned_value = str_value.strip()

        # إزالة quotes خارجية متعددة إذا وجدت
        while cleaned_value.startswith('"') and cleaned_value.endswith('"'):
            cleaned_value = cleaned_value[1:-1]

        while cleaned_value.startswith("'") and cleaned_value.endswith("'"):
            cleaned_value = cleaned_value[1:-1]

        # إزالة أي backslashes زائدة
        cleaned_value = cleaned_value.replace('\\"', '"').replace("\\'", "'")

        # التأكد من أن القيمة بالتنسيق الصحيح لمعرف Airtable User
        final_value = cleaned_value.strip()

        # logging للتشخيص
        if str_value != final_value:
            logger.debug(f"تنظيف Assigned To: '{str_value}' → '{final_value}'")

        # ✅ إرجاع object بالتنسيق الصحيح لـ Airtable
        if final_value:
            # التحقق من نوع القيمة (ID أم Email)
            if final_value.startswith('usr') or final_value.startswith('rec'):
                # معرف Airtable User/Record
                logger.debug(f"إرجاع User ID: {final_value}")
                return {"id": final_value}
            elif '@' in final_value and '.' in final_value:
                # عنوان بريد إلكتروني
                logger.debug(f"إرجاع Email: {final_value}")
                return {"email": final_value}
            else:
                # افتراض أنه معرف حتى لو لم يبدأ بـ usr
                logger.debug(f"إرجاع ID (افتراضي): {final_value}")
                return {"id": final_value}

        return None

    def _validate_user_field_format(self, value: Any) -> bool:
        """التحقق من صحة تنسيق حقل المستخدم"""
        if not value:
            return False

        if isinstance(value, dict):
            return 'id' in value or 'email' in value

        if isinstance(value, str):
            value = value.strip()
            # التحقق من معرف Airtable أو بريد إلكتروني
            return (value.startswith(('usr', 'rec')) and len(value) >= 10) or ('@' in value and '.' in value)

        return False

    def _is_cache_valid(self) -> bool:
        """التحقق من صلاحية الكاش"""
        if not self.last_fetch or not self.cached_data:
            return False

        age = datetime.now() - self.last_fetch
        return age < self.CACHE_DURATION

    def _invalidate_cache(self):
        """إلغاء الكاش"""
        with self._cache_lock:
            self.last_fetch = None
            self.cached_data = []
            if self.table_name in self.cache_timestamps:
                del self.cache_timestamps[self.table_name]

    def _save_to_local_db(self, records: List[Dict[str, Any]]):
        """حفظ البيانات في قاعدة البيانات المحلية"""
        try:
            if self.db and hasattr(self.db, 'save_records'):
                self.db.save_records(self.table_name, records)
        except Exception as e:
            logger.warning(f"فشل حفظ البيانات محلياً: {e}")

    def get_cache_info(self) -> Dict[str, Any]:
        """معلومات الكاش"""
        with self._cache_lock:
            return {
                'table': self.table_name,
                'cached_records': len(self.cached_data),
                'last_fetch': self.last_fetch.isoformat() if self.last_fetch else None,
                'cache_age_seconds': (datetime.now() - self.last_fetch).total_seconds() if self.last_fetch else None,
                'is_valid': self._is_cache_valid()
            }

    def clear_cache(self):
        """مسح الكاش"""
        self._invalidate_cache()
        logger.info(f"تم مسح كاش {self.table_name}")

    def is_connected(self) -> bool:
        """التحقق من الاتصال"""
        return bool(self.api_key and self.base_id)

    def get_status(self) -> Dict[str, Any]:
        """حالة المدير"""
        return {
            'connected': self.is_connected(),
            'table_name': self.table_name,
            'view_name': self.view_name,
            'loading': self._loading,
            'cached_records': len(self.cached_data),
            'cache_valid': self._is_cache_valid(),
            'errors': self.errors.copy(),
            'related_data_cached': {
                key: len(values) for key, values in self.cached_related_data.items()
            }
        }

    # ========================================
    # 🔧 دوال التشخيص والتصحيح
    # ========================================

    def debug_assigned_to_processing(self, test_values: List[Any]) -> Dict[str, Any]:
        """دالة تشخيص لاختبار معالجة حقل Assigned To"""
        results = {}

        logger.info("🔍 بدء اختبار معالجة حقل Assigned To")
        logger.info("=" * 50)

        for i, test_value in enumerate(test_values):
            try:
                logger.info(f"اختبار {i+1}: {type(test_value)} = {test_value}")

                # معالجة القيمة
                processed = self._process_assigned_to_field(test_value)

                # التحقق من صحة التنسيق
                is_valid = self._validate_user_field_format(processed)

                results[f"test_{i+1}"] = {
                    "input": test_value,
                    "input_type": str(type(test_value)),
                    "processed": processed,
                    "processed_type": str(type(processed)),
                    "is_valid": is_valid,
                    "success": processed is not None
                }

                logger.info(f"✅ النتيجة: {processed} (صحيح: {is_valid})")

            except Exception as e:
                logger.error(f"❌ خطأ في المعالجة: {e}")
                results[f"test_{i+1}"] = {
                    "input": test_value,
                    "error": str(e),
                    "success": False
                }

            logger.info("-" * 30)

        logger.info("=" * 50)
        return results

    def test_user_field_creation(self, user_id: str) -> bool:
        """اختبار إنشاء سجل تجريبي مع حقل Assigned To"""
        try:
            logger.info(f"🧪 اختبار إنشاء سجل مع Assigned To: {user_id}")

            # تجهيز بيانات تجريبية
            test_fields = {
                "Customer Name": f"Test User {datetime.now().strftime('%H%M%S')}",
                "Assigned To": user_id,
                "Agency": "Test Agency"
            }

            # معالجة الحقول
            processed = self._process_fields_for_create(test_fields)

            logger.info(f"الحقول المعالجة: {json.dumps(processed, ensure_ascii=False, indent=2)}")

            # التحقق من تنسيق Assigned To
            if 'Assigned To' in processed:
                assigned_to = processed['Assigned To']
                is_valid = self._validate_user_field_format(assigned_to)
                logger.info(f"تنسيق Assigned To صحيح: {is_valid}")
                return is_valid

            return False

        except Exception as e:
            logger.error(f"❌ خطأ في اختبار المستخدم: {e}")
            return False

    def validate_record_fields(self, fields: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """التحقق من صحة حقول السجل قبل الإرسال"""
        errors = []

        # التحقق من الحقول المطلوبة
        required_fields = ['Customer Name']  # يمكن تخصيصها حسب الجدول

        for field in required_fields:
            if field not in fields or not fields[field]:
                errors.append(f"الحقل المطلوب '{field}' مفقود أو فارغ")

        # التحقق من تنسيق حقل Assigned To
        if 'Assigned To' in fields:
            assigned_to = fields['Assigned To']
            if not self._validate_user_field_format(assigned_to):
                errors.append(f"تنسيق حقل 'Assigned To' غير صحيح: {assigned_to}")

        return len(errors) == 0, errors

    def create_record_with_validation(self, fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """إنشاء سجل مع التحقق المسبق من صحة البيانات"""
        # التحقق من صحة الحقول
        is_valid, errors = self.validate_record_fields(fields)

        if not is_valid:
            logger.error("❌ فشل التحقق من صحة الحقول:")
            for error in errors:
                logger.error(f"  - {error}")
            return None

        # إنشاء السجل إذا كانت البيانات صحيحة
        return self.create_record(fields)


# ========================================
# 🏭 دوال Factory للجداول المختلفة
# ========================================

def create_airtable_manager(config_manager=None, db_manager=None, table_name: str = "") -> AirtableManager:
    """إنشاء مدير Airtable عام"""
    return AirtableManager(config_manager, db_manager, table_name)

def create_bookings_manager(config_manager=None, db_manager=None, view_name: str = None) -> AirtableManager:
    """إنشاء مدير لجدول الحجوزات"""
    return AirtableManager(config_manager, db_manager, "Bookings", view_name)

def create_agencies_manager(config_manager=None, db_manager=None) -> AirtableManager:
    """إنشاء مدير لجدول الوكالات"""
    return AirtableManager(config_manager, db_manager, "Agencies")

def create_guides_manager(config_manager=None, db_manager=None) -> AirtableManager:
    """إنشاء مدير لجدول المرشدين"""
    return AirtableManager(config_manager, db_manager, "Guides")

def create_destinations_manager(config_manager=None, db_manager=None) -> AirtableManager:
    """إنشاء مدير لجدول الوجهات"""
    return AirtableManager(config_manager, db_manager, "Destinations")

def create_users_manager(config_manager=None, db_manager=None) -> AirtableManager:
    """إنشاء مدير لجدول المستخدمين"""
    return AirtableManager(config_manager, db_manager, "Users")


# ========================================
# 🔄 دالة التوافق مع الكود القديم
# ========================================

class AirtableModel(AirtableManager):
    """كلاس للتوافق مع الكود القديم - وراثة من AirtableManager"""

    def __init__(self, config_manager, db_manager, table_name: str, view_name: str = None):
        super().__init__(config_manager, db_manager, table_name, view_name)
        logger.info(f"تم إنشاء AirtableModel (توافق) للجدول: {table_name}")

    # دوال التوافق
    def fetch_all_records(self, view: Optional[str] = None, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """دالة توافق - استخدام fetch_records"""
        return self.fetch_records(force_refresh=force_refresh, view=view)

    def get_record_by_id(self, record_id: str) -> Optional[Dict[str, Any]]:
        """دالة توافق - استخدام fetch_record"""
        return self.fetch_record(record_id)