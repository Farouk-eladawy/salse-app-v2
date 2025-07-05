# -*- coding: utf-8 -*-
"""
core/airtable_dropdown_manager.py - نسخة محسنة للأداء ومنع التجمد

مدير القوائم المنسدلة المحسن مع:
- تحميل متوازي للقوائم
- تخزين مؤقت ذكي
- معالجة أفضل للأخطاء
- منع التجمد أثناء التحميل
"""

import os
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json

from core.airtable_manager import AirtableModel

logger = logging.getLogger(__name__)


class AirtableDropdownManager:
    """مدير القوائم المنسدلة المحسن للأداء ومنع التجمد"""

    # ملف التخزين المؤقت
    CACHE_FILE = "cache/dropdown_cache.json"
    CACHE_DURATION = timedelta(hours=1)  # مدة الكاش ساعة واحدة
    LOADING_TIMEOUT = 30  # مهلة زمنية للتحميل (30 ثانية)
    MAX_WORKERS = 3  # عدد الخيوط المتوازية

    def __init__(self, config_manager, db_manager):
        self.config_mgr = config_manager
        self.db_mgr = db_manager
        self.tables = {}
        self.field_names = {}
        self.errors = {}
        self._cache = {}
        self._cache_timestamps = {}
        self._loading = False
        self._load_lock = threading.RLock()
        self._loading_start_time = None
        self._active_futures = set()

        # إنشاء مجلد الكاش
        os.makedirs("cache", exist_ok=True)

        # تحميل الكاش من الملف
        self._load_cache_from_file()

        # تهيئة الجداول
        self._setup_tables()

        # تحميل القوائم في الخلفية
        self._start_background_loading()

    def _load_cache_from_file(self):
        """تحميل الكاش من الملف"""
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # التحقق من صلاحية الكاش
                for key, data in cache_data.items():
                    try:
                        timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                        if datetime.now() - timestamp < self.CACHE_DURATION:
                            self._cache[key] = data.get('values', [])
                            self._cache_timestamps[key] = timestamp
                    except (ValueError, TypeError) as e:
                        logger.warning(f"تعذر تحليل timestamp للمفتاح {key}: {e}")
                        continue

                if self._cache:
                    logger.info(f"تم تحميل {len(self._cache)} قائمة من الكاش")

        except Exception as e:
            logger.warning(f"فشل تحميل الكاش: {e}")

    def _save_cache_to_file(self):
        """حفظ الكاش إلى الملف بطريقة آمنة"""
        try:
            cache_data = {}
            with self._load_lock:
                for key in self._cache:
                    if key in self._cache_timestamps:
                        cache_data[key] = {
                            'values': self._cache[key],
                            'timestamp': self._cache_timestamps[key].isoformat()
                        }

            # كتابة مؤقتة ثم نقل
            temp_file = self.CACHE_FILE + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            # نقل الملف المؤقت فوق الأصلي
            if os.path.exists(self.CACHE_FILE):
                os.remove(self.CACHE_FILE)
            os.rename(temp_file, self.CACHE_FILE)

        except Exception as e:
            logger.warning(f"فشل حفظ الكاش: {e}")
            # تنظيف الملف المؤقت
            temp_file = self.CACHE_FILE + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

    def _setup_tables(self):
        """تهيئة جداول القوائم المنسدلة"""
        dropdown_config = {
            'guides': os.getenv('AIRTABLE_GUIDES_TABLE', 'Guides'),
            'agencies': (os.getenv('AIRTABLE_AGENCIES_TABLE', 'Agencies'), 'Agency Name'),
            'options': (os.getenv('AIRTABLE_OPTIONS_TABLE', 'Trip Options'), 'Option Name'),
            'destinations': (os.getenv('AIRTABLE_DESTINATIONS_TABLE', 'Destinations'), 'Destination'),
            'tripnames': (os.getenv('AIRTABLE_TRIPNAMES_TABLE', 'Trip Names'), 'Trip Name'),
            'management_options': (os.getenv('AIRTABLE_MANAGEMENT_OPTIONS_TABLE', 'Management Option'), 'Option Name'),
            'addons': os.getenv('AIRTABLE_ADDONS_TABLE', 'Add-on'),
        }

        logger.info(f"[Dropdown Manager] تهيئة {len(dropdown_config)} جدول")

        # التحقق من API
        api_key = os.getenv('AIRTABLE_API_KEY')
        base_id = os.getenv('AIRTABLE_BASE_ID')

        if not api_key or not base_id:
            error_msg = "API Key أو Base ID مفقود"
            logger.error(f"[Dropdown Manager] {error_msg}")
            self.errors['config'] = error_msg
            return

        # تهيئة الجداول
        for key, config in dropdown_config.items():
            try:
                if isinstance(config, tuple):
                    table_name, field_name = config
                else:
                    table_name = config
                    field_name = 'Name'

                self.tables[key] = AirtableModel(
                    config_manager=self.config_mgr,
                    db_manager=self.db_mgr,
                    table_name=table_name
                )
                self.field_names[key] = field_name

                logger.debug(f"تم تهيئة جدول {key}: {table_name} (حقل: {field_name})")

            except Exception as e:
                error_msg = f"فشل تهيئة جدول '{key}': {str(e)}"
                logger.error(f"[Dropdown Manager] {error_msg}")
                self.errors[key] = error_msg

    def _start_background_loading(self):
        """بدء تحميل القوائم في الخلفية"""
        def load_all():
            try:
                self._load_all_dropdowns_parallel()
            except Exception as e:
                logger.error(f"خطأ في التحميل الخلفي: {e}")

        thread = threading.Thread(target=load_all, daemon=True, name="DropdownLoader")
        thread.start()

    def _load_all_dropdowns_parallel(self):
        """تحميل جميع القوائم بشكل متوازي مع مهلة زمنية"""
        with self._load_lock:
            if self._loading:
                logger.debug("التحميل جاري بالفعل")
                return
            self._loading = True
            self._loading_start_time = datetime.now()

        start_time = time.time()
        logger.info("[Dropdown Manager] بدء التحميل المتوازي للقوائم")

        # التحقق من وجود جداول للتحميل
        if not self.tables:
            logger.warning("لا توجد جداول للتحميل")
            with self._load_lock:
                self._loading = False
                self._loading_start_time = None
            return

        # تهيئة المتغيرات قبل try block
        completed = 0
        failed = 0
        timeout_count = 0

        try:
            # استخدام ThreadPoolExecutor للتحميل المتوازي
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                futures = {}

                # إطلاق مهام التحميل للجداول التي تحتاج تحديث
                for key in self.tables:
                    if self._is_cache_valid(key):
                        logger.debug(f"تخطي {key} - الكاش صالح")
                        continue

                    future = executor.submit(self._load_single_dropdown_with_timeout, key)
                    futures[future] = key
                    self._active_futures.add(future)

                if not futures:
                    logger.info("جميع القوائم محدثة في الكاش")
                    return

                # انتظار اكتمال المهام مع مهلة زمنية

                try:
                    for future in as_completed(futures, timeout=self.LOADING_TIMEOUT):
                        key = futures[future]
                        self._active_futures.discard(future)

                        try:
                            values = future.result(timeout=5)  # مهلة إضافية للحصول على النتيجة
                            if values is not None:
                                with self._load_lock:
                                    self._cache[key] = values
                                    self._cache_timestamps[key] = datetime.now()
                                completed += 1
                                logger.debug(f"✓ تم تحميل {key}: {len(values)} قيمة")

                                # إزالة الخطأ إذا نجح التحميل
                                self.errors.pop(key, None)
                            else:
                                failed += 1
                                logger.warning(f"✗ فشل تحميل {key}: لم يتم إرجاع بيانات")
                        except TimeoutError:
                            timeout_count += 1
                            logger.error(f"✗ انتهت مهلة تحميل {key}")
                            self.errors[key] = "انتهت المهلة الزمنية للتحميل"
                        except Exception as e:
                            failed += 1
                            logger.error(f"✗ فشل تحميل {key}: {e}")
                            self.errors[key] = str(e)

                except TimeoutError:
                    logger.error("انتهت المهلة الزمنية العامة للتحميل")
                    # إلغاء المهام المتبقية
                    for future in futures:
                        if not future.done():
                            future.cancel()
                            key = futures[future]
                            self.errors[key] = "تم إلغاء التحميل بسبب انتهاء المهلة"

                # تنظيف المهام المكتملة
                self._active_futures.clear()

        except Exception as e:
            logger.error(f"خطأ عام في التحميل المتوازي: {e}")
            # تأكد من تهيئة المتغيرات في حالة الخطأ
            if 'completed' not in locals():
                completed = 0
            if 'failed' not in locals():
                failed = len(self.tables)
            if 'timeout_count' not in locals():
                timeout_count = 0

        finally:
            # حفظ الكاش
            if completed > 0:
                self._save_cache_to_file()

            elapsed = time.time() - start_time
            logger.info(f"[Dropdown Manager] اكتمل التحميل في {elapsed:.2f}ث - "
                       f"نجح: {completed}, فشل: {failed}, انتهت مهلة: {timeout_count}")

            with self._load_lock:
                self._loading = False
                self._loading_start_time = None

    def _load_single_dropdown_with_timeout(self, key: str) -> Optional[List[str]]:
        """تحميل قائمة منسدلة واحدة مع مهلة زمنية"""
        start_time = time.time()

        try:
            if key not in self.tables:
                logger.warning(f"الجدول {key} غير موجود")
                return None

            field_name = self.field_names.get(key, 'Name')
            logger.debug(f"بدء تحميل {key} من الحقل {field_name}")

            # تحميل البيانات مع مهلة زمنية
            values = self.tables[key].get_all_values(field_name=field_name, force_refresh=True)

            elapsed = time.time() - start_time

            if not values:
                logger.warning(f"لم يتم العثور على بيانات في {key} (استغرق {elapsed:.2f}ث)")
                self.errors[key] = f"لم يتم العثور على بيانات في الجدول"
                return []

            logger.debug(f"تم تحميل {key} بنجاح: {len(values)} قيمة (استغرق {elapsed:.2f}ث)")
            return values

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"خطأ في تحميل {key} (استغرق {elapsed:.2f}ث): {e}")
            self.errors[key] = str(e)
            raise

    def _is_cache_valid(self, key: str) -> bool:
        """التحقق من صلاحية الكاش"""
        if key not in self._cache or key not in self._cache_timestamps:
            return False

        age = datetime.now() - self._cache_timestamps[key]
        return age < self.CACHE_DURATION

    def _cancel_loading_operations(self):
        """إلغاء جميع عمليات التحميل الجارية"""
        logger.info("إلغاء عمليات التحميل الجارية...")

        # إلغاء المهام النشطة
        for future in list(self._active_futures):
            if not future.done():
                future.cancel()
                logger.debug(f"تم إلغاء مهمة تحميل")

        self._active_futures.clear()

        with self._load_lock:
            self._loading = False
            self._loading_start_time = None

    def get_dropdown_values(self, key: str, force_refresh: bool = False, timeout: float = 20.0) -> List[str]:
        """الحصول على قيم القائمة المنسدلة مع مهلة زمنية"""
        try:
            # التحقق من وجود الجدول
            if key not in self.tables:
                logger.warning(f"الجدول {key} غير موجود في القوائم المنسدلة")
                return []

            # التحقق من الكاش أولاً
            if not force_refresh and self._is_cache_valid(key):
                logger.debug(f"إرجاع قيم {key} من الكاش")
                return self._cache.get(key, [])

            # إذا كان التحميل جارياً، انتظر قليلاً أو أرجع الكاش القديم
            if self._loading:
                logger.debug(f"التحميل جاري - محاولة انتظار {key}")

                # انتظار مع مهلة زمنية
                start_wait = time.time()
                while self._loading and (time.time() - start_wait) < timeout:
                    time.sleep(0.1)

                    # إذا أصبحت القيمة متاحة في الكاش أثناء الانتظار
                    if self._is_cache_valid(key):
                        logger.debug(f"تم الحصول على {key} من الكاش أثناء الانتظار")
                        return self._cache.get(key, [])

                # إذا انتهت المهلة وما زال التحميل جارياً
                if self._loading:
                    logger.warning(f"انتهت مهلة انتظار {key} - إرجاع كاش قديم أو فارغ")
                    return self._cache.get(key, [])

            # تحميل القائمة في خيط منفصل مع مهلة زمنية
            try:
                logger.debug(f"تحميل {key} مباشرة مع مهلة زمنية")

                # استخدام ThreadPoolExecutor لتحميل واحد
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(self._load_single_dropdown_with_timeout, key)

                    try:
                        values = future.result(timeout=timeout)
                        if values is not None:
                            with self._load_lock:
                                self._cache[key] = values
                                self._cache_timestamps[key] = datetime.now()
                            self._save_cache_to_file()
                            return values
                        return []

                    except TimeoutError:
                        logger.warning(f"انتهت مهلة تحميل {key}")
                        future.cancel()
                        self.errors[key] = "انتهت المهلة الزمنية"
                        # إرجاع الكاش القديم إن وجد
                        return self._cache.get(key, [])

            except Exception as e:
                logger.error(f"خطأ في جلب {key}: {e}")
                self.errors[key] = str(e)
                # إرجاع الكاش القديم إن وجد
                return self._cache.get(key, [])

        except Exception as e:
            logger.error(f"خطأ عام في get_dropdown_values لـ {key}: {e}")
            self.errors[key] = f"خطأ عام: {str(e)}"
            return []

    def add_value_to_dropdown(self, key: str, value: str) -> bool:
        """إضافة قيمة جديدة إلى القائمة المنسدلة"""
        if key not in self.tables:
            logger.warning(f"[Dropdown] جدول غير موجود: {key}")
            return False

        if not value or not value.strip():
            logger.warning(f"[Dropdown] قيمة فارغة لـ {key}")
            return False

        try:
            field_name = self.field_names.get(key, 'Name')
            success = self.tables[key].insert_if_not_exists(value.strip(), field_name=field_name)

            if success:
                # تحديث الكاش
                with self._load_lock:
                    if key in self._cache:
                        if value.strip() not in self._cache[key]:
                            self._cache[key].append(value.strip())
                            self._cache[key].sort()
                            self._save_cache_to_file()

                logger.info(f"[Dropdown] تمت إضافة '{value}' إلى '{key}'")

            return success

        except Exception as e:
            logger.error(f"[Dropdown] فشل إضافة '{value}' إلى '{key}': {e}")
            return False

    def refresh_all(self, force: bool = True):
        """تحديث جميع القوائم المنسدلة"""
        logger.info("[Dropdown] بدء تحديث جميع القوائم")

        # إيقاف أي تحميل جاري
        if self._loading:
            logger.info("إيقاف التحميل الجاري قبل التحديث")
            self._cancel_loading_operations()

            # انتظار قصير للتأكد من الإيقاف
            time.sleep(0.5)

        if force:
            # مسح الكاش
            with self._load_lock:
                self._cache.clear()
                self._cache_timestamps.clear()
                self.errors.clear()

        # إعادة التحميل
        self._start_background_loading()

    def get_all_dropdowns(self, timeout: float = 15.0) -> Dict[str, List[str]]:
        """الحصول على جميع القوائم المنسدلة مع مهلة زمنية"""
        # انتظار اكتمال التحميل إذا كان جارياً
        start_wait = time.time()

        while self._loading and (time.time() - start_wait) < timeout:
            time.sleep(0.2)

        if self._loading:
            logger.warning(f"انتهت مهلة انتظار تحميل جميع القوائم ({timeout}s)")

        result = {}
        for key in self.tables:
            # محاولة الحصول على القيم مع مهلة زمنية قصيرة
            try:
                result[key] = self.get_dropdown_values(key, timeout=3.0)
            except Exception as e:
                logger.error(f"خطأ في جلب {key}: {e}")
                result[key] = []

        return result

    def get_field_mapping(self) -> Dict[str, str]:
        """الحصول على خريطة الحقول"""
        return {
            "Agency": "agencies",
            "Guide": "guides",
            "Option": "options",
            "des": "destinations",
            "trip Name": "tripnames",
            "Management Option": "management_options",
            "Add-on": "addons"
        }

    def get_dropdown_by_field_name(self, field_name: str, timeout: float = 5.0) -> List[str]:
        """الحصول على قيم القائمة المنسدلة بناءً على اسم الحقل"""
        field_mapping = self.get_field_mapping()
        key = field_mapping.get(field_name)

        if key:
            return self.get_dropdown_values(key, timeout=timeout)

        logger.warning(f"[Dropdown] لا يوجد ربط للحقل: {field_name}")
        return []

    def is_connected(self) -> bool:
        """التحقق من الاتصال"""
        return len(self.tables) > 0 and not self.errors.get('config')

    def get_status(self) -> Dict[str, any]:
        """الحصول على حالة المدير بشكل آمن"""
        try:
            with self._load_lock:
                # حساب عدد القوائم المحملة بنجاح
                successful_loads = 0
                if hasattr(self, '_cache') and self._cache:
                    successful_loads = len([k for k in self._cache if k not in self.errors])

                # تقدير وقت التحميل المتبقي
                estimated_time_remaining = None
                if self._loading and self._loading_start_time:
                    elapsed = (datetime.now() - self._loading_start_time).total_seconds()
                    if elapsed < self.LOADING_TIMEOUT:
                        estimated_time_remaining = max(0, self.LOADING_TIMEOUT - elapsed)

                return {
                    'connected': self.is_connected(),
                    'loading': getattr(self, '_loading', False),
                    'tables_count': len(getattr(self, 'tables', {})),
                    'cached_count': len(getattr(self, '_cache', {})),
                    'successful_loads': successful_loads,
                    'tables': list(getattr(self, 'tables', {}).keys()),
                    'cached_tables': list(getattr(self, '_cache', {}).keys()),
                    'api_configured': bool(os.getenv('AIRTABLE_API_KEY') and os.getenv('AIRTABLE_BASE_ID')),
                    'errors': getattr(self, 'errors', {}).copy(),
                    'loading_start_time': self._loading_start_time.isoformat() if getattr(self, '_loading_start_time', None) else None,
                    'estimated_time_remaining': estimated_time_remaining,
                    'active_futures_count': len(getattr(self, '_active_futures', set()))
                }
        except Exception as e:
            logger.error(f"خطأ في الحصول على حالة مدير القوائم المنسدلة: {e}")
            return {
                'connected': False,
                'loading': False,
                'tables_count': 0,
                'cached_count': 0,
                'successful_loads': 0,
                'tables': [],
                'cached_tables': [],
                'api_configured': False,
                'errors': {'status_error': str(e)},
                'loading_start_time': None,
                'estimated_time_remaining': None,
                'active_futures_count': 0
            }

    def get_error_for_key(self, key: str) -> str:
        """الحصول على رسالة الخطأ"""
        return self.errors.get(key, "")

    def has_errors(self) -> bool:
        """التحقق من وجود أخطاء"""
        return len(self.errors) > 0

    def get_all_errors(self) -> Dict[str, str]:
        """الحصول على جميع الأخطاء"""
        return self.errors.copy()

    def clear_errors(self):
        """مسح جميع الأخطاء"""
        with self._load_lock:
            self.errors.clear()

    def get_cache_info(self) -> Dict[str, any]:
        """الحصول على معلومات الكاش"""
        with self._load_lock:
            cache_info = {}
            for key in self._cache:
                timestamp = self._cache_timestamps.get(key)
                cache_info[key] = {
                    'count': len(self._cache[key]),
                    'timestamp': timestamp.isoformat() if timestamp else None,
                    'age_seconds': (datetime.now() - timestamp).total_seconds() if timestamp else None,
                    'is_valid': self._is_cache_valid(key)
                }
            return cache_info

    def force_stop_loading(self):
        """إيقاف التحميل بالقوة"""
        logger.warning("إيقاف تحميل القوائم المنسدلة بالقوة")
        self._cancel_loading_operations()

        # إضافة رسالة خطأ للجداول التي لم يتم تحميلها
        for key in self.tables:
            if key not in self._cache:
                self.errors[key] = "تم إيقاف التحميل بالقوة"

    def __del__(self):
        """تنظيف الموارد عند التدمير"""
        try:
            if hasattr(self, '_loading') and self._loading:
                self._cancel_loading_operations()
        except:
            pass