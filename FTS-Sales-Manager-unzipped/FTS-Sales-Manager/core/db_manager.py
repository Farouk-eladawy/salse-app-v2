# -*- coding: utf-8 -*-
"""
core/db_manager.py

تدير هذه الفئة الاتصال بقاعدة بيانات SQLite المحلية لاستخدامها ككاش (Cache) للبيانات
المستخرجة من Airtable. توفر واجهات لحفظ واسترجاع السجلات المؤقتة مع دعم جداول متعددة.
"""

# ------------------------------------------------------------
# استيرادات المكتبات القياسية
# ------------------------------------------------------------
import sqlite3
import threading
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------
# استيرادات وحدات المشروع
# ------------------------------------------------------------
from core.logger import logger


class DatabaseManager:
    """
    فئة DatabaseManager تتولى:
    - إنشاء اتصال بقاعدة بيانات SQLite (ملف db_path).
    - تهيئة جداول الكاش المتعددة (users_cache, bookings_cache, records_cache).
    - إتاحة طرق للحفظ والاسترجاع من الكاش لكل جدول.
    """

    def __init__(self, db_path: str) -> None:
        """
        تهيئة DatabaseManager.

        :param db_path: مسار ملف قاعدة بيانات SQLite (مثل "fts_sales_cache.db").
        """
        self.db_path: str = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._lock: threading.Lock = threading.Lock()
        self._connect_and_init()

    def _connect_and_init(self) -> None:
        """
        إنشاء اتصال بقاعدة البيانات وتهيئة جداول الكاش لكل جدول Airtable.
        """
        try:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self._conn.cursor()

            # إنشاء جدول منفصل لكل نوع من البيانات
            # جدول للمستخدمين
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users_cache (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    table_name TEXT DEFAULT 'Users'
                );
            """)

            # جدول للحجوزات
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bookings_cache (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    table_name TEXT DEFAULT 'List V2'
                );
            """)

            # جدول عام للكاش (للتوافق مع الكود القديم)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS records_cache (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    table_name TEXT
                );
            """)

            self._conn.commit()
            logger.info(f"DatabaseManager: متصل بقاعدة البيانات '{self.db_path}' وتم تهيئة جداول الكاش.")
        except Exception as exc:
            logger.error(f"DatabaseManager: فشل في إنشاء/تهيئة قاعدة البيانات '{self.db_path}': {exc}", exc_info=True)

    def get_cached_record(self, record_id: str, table_name: str = None) -> Optional[str]:
        """
        استرجاع السجل المؤقت المخزن في الكاش من الجدول المناسب.
        :param record_id: معرف السجل الذي نبحث عنه.
        :param table_name: اسم الجدول (اختياري)
        :return: البيانات (json) كسلسلة نصية إذا وُجدت، وإلا None.
        """
        if not self._conn:
            logger.warning("DatabaseManager: محاولة استرجاع سجل قبل وجود اتصال بقاعدة البيانات.")
            return None

        try:
            with self._lock:
                cursor = self._conn.cursor()

                # تحديد الجدول المناسب بناءً على table_name
                if table_name == "Users":
                    cursor.execute("SELECT data FROM users_cache WHERE id = ?;", (record_id,))
                elif table_name == "List V2":
                    cursor.execute("SELECT data FROM bookings_cache WHERE id = ?;", (record_id,))
                else:
                    cursor.execute("SELECT data FROM records_cache WHERE id = ?;", (record_id,))

                result = cursor.fetchone()

            if result:
                logger.debug(f"DatabaseManager: وجد السجل '{record_id}' في الكاش (جدول: {table_name}).")
                return result[0]
            logger.debug(f"DatabaseManager: السجل '{record_id}' غير موجود في الكاش.")
            return None
        except Exception as exc:
            logger.error(f"DatabaseManager: خطأ أثناء استرجاع السجل '{record_id}' من الكاش: {exc}", exc_info=True)
            return None

    def set_cached_record(self, record_id: str, data: str, table_name: str = None) -> None:
        """
        تخزين السجل المؤقت في جدول الكاش المناسب.
        :param record_id: معرف السجل.
        :param data: البيانات المراد تخزينها كسلسلة نصية (عادة JSON).
        :param table_name: اسم الجدول (اختياري)
        """
        if not self._conn:
            logger.warning("DatabaseManager: محاولة تخزين سجل قبل وجود اتصال بقاعدة البيانات.")
            return

        try:
            with self._lock:
                cursor = self._conn.cursor()

                # تحديد الجدول المناسب
                if table_name == "Users":
                    cursor.execute("""
                        INSERT INTO users_cache (id, data) VALUES (?, ?)
                        ON CONFLICT(id) DO UPDATE SET data=excluded.data;
                    """, (record_id, data))
                elif table_name == "List V2":
                    cursor.execute("""
                        INSERT INTO bookings_cache (id, data) VALUES (?, ?)
                        ON CONFLICT(id) DO UPDATE SET data=excluded.data;
                    """, (record_id, data))
                else:
                    cursor.execute("""
                        INSERT INTO records_cache (id, data, table_name) VALUES (?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET data=excluded.data, table_name=excluded.table_name;
                    """, (record_id, data, table_name))

                self._conn.commit()
            logger.debug(f"DatabaseManager: تم تخزين/تحديث السجل '{record_id}' في الكاش (جدول: {table_name}).")
        except Exception as exc:
            logger.error(f"DatabaseManager: خطأ أثناء تخزين السجل '{record_id}' في الكاش: {exc}", exc_info=True)

    def get_all_cached_ids(self, table_name: str = None) -> List[str]:
        """
        إرجاع قائمة بجميع معرفات السجلات المخزنة في جدول الكاش المحدد.
        :param table_name: اسم الجدول (اختياري)
        :return: قائمة معرفات كسلاسل نصية.
        """
        if not self._conn:
            logger.warning("DatabaseManager: محاولة جلب جميع معرفات قبل وجود اتصال بقاعدة البيانات.")
            return []

        try:
            with self._lock:
                cursor = self._conn.cursor()

                if table_name == "Users":
                    cursor.execute("SELECT id FROM users_cache;")
                elif table_name == "List V2":
                    cursor.execute("SELECT id FROM bookings_cache;")
                else:
                    cursor.execute("SELECT id FROM records_cache;")

                rows = cursor.fetchall()

            ids = [row[0] for row in rows]
            logger.debug(f"DatabaseManager: جُلبت جميع المعرفات من الكاش ({len(ids)} سجلاً) - جدول: {table_name}.")
            return ids
        except Exception as exc:
            logger.error(f"DatabaseManager: خطأ أثناء جلب جميع المعرفات من الكاش: {exc}", exc_info=True)
            return []

    def clear_cache(self, table_name: str = None) -> None:
        """
        حذف جميع السجلات من جدول الكاش المحدد.
        :param table_name: اسم الجدول (None = حذف الكل)
        """
        if not self._conn:
            logger.warning("DatabaseManager: محاولة مسح الكاش قبل وجود اتصال بقاعدة البيانات.")
            return

        try:
            with self._lock:
                cursor = self._conn.cursor()

                if table_name == "Users":
                    cursor.execute("DELETE FROM users_cache;")
                elif table_name == "List V2":
                    cursor.execute("DELETE FROM bookings_cache;")
                elif table_name is None:
                    # حذف جميع الجداول
                    cursor.execute("DELETE FROM users_cache;")
                    cursor.execute("DELETE FROM bookings_cache;")
                    cursor.execute("DELETE FROM records_cache;")
                else:
                    cursor.execute("DELETE FROM records_cache WHERE table_name = ?;", (table_name,))

                self._conn.commit()
            logger.info(f"DatabaseManager: تم مسح السجلات من الكاش (جدول: {table_name or 'الكل'}).")
        except Exception as exc:
            logger.error(f"DatabaseManager: خطأ أثناء مسح الكاش: {exc}", exc_info=True)

    def delete_cached_record(self, record_id: str, table_name: str = None) -> bool:
        """
        حذف سجل محدد من جدول الكاش.
        :param record_id: معرف السجل المراد حذفه.
        :param table_name: اسم الجدول (اختياري)
        :return: True إذا تم الحذف بنجاح، False خلاف ذلك.
        """
        if not self._conn:
            logger.warning("DatabaseManager: محاولة حذف سجل قبل وجود اتصال بقاعدة البيانات.")
            return False

        try:
            with self._lock:
                cursor = self._conn.cursor()

                # تحديد الجدول المناسب وحذف السجل
                if table_name == "Users":
                    cursor.execute("DELETE FROM users_cache WHERE id = ?;", (record_id,))
                elif table_name == "List V2":
                    cursor.execute("DELETE FROM bookings_cache WHERE id = ?;", (record_id,))
                else:
                    cursor.execute("DELETE FROM records_cache WHERE id = ?;", (record_id,))

                self._conn.commit()

                # التحقق من أن السجل تم حذفه فعلاً
                if cursor.rowcount > 0:
                    logger.debug(f"DatabaseManager: تم حذف السجل '{record_id}' من الكاش (جدول: {table_name}).")
                    return True
                else:
                    logger.debug(f"DatabaseManager: السجل '{record_id}' لم يكن موجوداً في الكاش.")
                    return False

        except Exception as exc:
            logger.error(f"DatabaseManager: خطأ أثناء حذف السجل '{record_id}' من الكاش: {exc}", exc_info=True)
            return False

    def close(self) -> None:
        """
        إغلاق اتصال قاعدة البيانات عند إنهاء التطبيق.
        """
        if self._conn:
            try:
                self._conn.close()
                logger.info("DatabaseManager: تم إغلاق اتصال قاعدة البيانات.")
            except Exception as exc:
                logger.error(f"DatabaseManager: خطأ أثناء إغلاق اتصال قاعدة البيانات: {exc}", exc_info=True)
            finally:
                self._conn = None