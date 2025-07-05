# -*- coding: utf-8 -*-
"""
core/logger.py

تُعد هذه الوحدة مسؤولةً عن تهيئة نظام التدوين (logging) في التطبيق.
تستخدم RotatingFileHandler لتقسيم ملفات السجل (log files) عند بلوغ حجم محدد.
"""

# ------------------------------------------------------------
# استيرادات المكتبات القياسية
# ------------------------------------------------------------
import logging
from logging.handlers import RotatingFileHandler
import os

# ------------------------------------------------------------
# إعداد إعدادات المسار والمجلدات
# ------------------------------------------------------------
LOG_DIR = "logs"
LOG_FILE = "app.log"
MAX_BYTES = 5 * 1024 * 1024   # 5 ميغابايت لكل ملف سجل
BACKUP_COUNT = 3              # الاحتفاظ بثلاث نسخ احتياطية

# ------------------------------------------------------------
# التأكد من وجود مجلد السجلات
# ------------------------------------------------------------
if not os.path.isdir(LOG_DIR):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
    except Exception:
        # في حال فشل إنشاء مجلد السجلات، نستخدم المجلد الحالي بدلًا منه
        LOG_DIR = "."
        # لا نعالج الخطأ هنا لأنه يحدث قبل تهيئة الـlogger بالكامل
# ------------------------------------------------------------
# تهيئة الـLogger العام
# ------------------------------------------------------------
logger = logging.getLogger("fts_sales_manager")
logger.setLevel(logging.DEBUG)  # سجل كافة المستويات بدءًا من DEBUG

# تنسيق رسائل السجل
formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# معالجة تدوير الملفات (RotatingFileHandler)
file_path = os.path.join(LOG_DIR, LOG_FILE)
file_handler = RotatingFileHandler(
    filename=file_path,
    maxBytes=MAX_BYTES,
    backupCount=BACKUP_COUNT,
    encoding="utf-8"
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# معالجة الطباعة على الشاشة (StreamHandler) للمرحلة التطويرية
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
