# -*- coding: utf-8 -*-
"""
core/app_state_manager.py

مدير حالة التطبيق لمنع التداخل والتجمد
"""

import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Any
from enum import Enum
from core.logger import logger


class OperationType(Enum):
    """أنواع العمليات في التطبيق"""
    DATA_LOADING = "data_loading"
    DROPDOWN_LOADING = "dropdown_loading"
    RECORD_SAVING = "record_saving"
    RECORD_DELETING = "record_deleting"
    USER_AUTHENTICATION = "user_authentication"
    EXPORT_DATA = "export_data"
    UI_UPDATE = "ui_update"


class OperationState(Enum):
    """حالات العمليات"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class Operation:
    """كلاس لتمثيل عملية واحدة"""

    def __init__(self, operation_id: str, operation_type: OperationType,
                 description: str = "", timeout: float = 30.0):
        self.id = operation_id
        self.type = operation_type
        self.description = description
        self.state = OperationState.PENDING
        self.start_time = None
        self.end_time = None
        self.timeout = timeout
        self.progress = 0.0
        self.error_message = None
        self.result = None
        self.metadata = {}

    def start(self):
        """بدء العملية"""
        self.state = OperationState.IN_PROGRESS
        self.start_time = datetime.now()
        logger.debug(f"بدء العملية: {self.id} ({self.type.value})")

    def complete(self, result: Any = None):
        """إكمال العملية بنجاح"""
        self.state = OperationState.COMPLETED
        self.end_time = datetime.now()
        self.progress = 100.0
        self.result = result
        logger.debug(f"اكتملت العملية: {self.id} ({self.type.value})")

    def fail(self, error_message: str):
        """فشل العملية"""
        self.state = OperationState.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message
        logger.warning(f"فشلت العملية: {self.id} ({self.type.value}) - {error_message}")

    def cancel(self):
        """إلغاء العملية"""
        self.state = OperationState.CANCELLED
        self.end_time = datetime.now()
        logger.info(f"تم إلغاء العملية: {self.id} ({self.type.value})")

    def timeout_operation(self):
        """انتهت مهلة العملية"""
        self.state = OperationState.TIMEOUT
        self.end_time = datetime.now()
        logger.warning(f"انتهت مهلة العملية: {self.id} ({self.type.value})")

    def update_progress(self, progress: float):
        """تحديث تقدم العملية"""
        self.progress = max(0.0, min(100.0, progress))

    def is_active(self) -> bool:
        """التحقق من كون العملية نشطة"""
        return self.state in [OperationState.PENDING, OperationState.IN_PROGRESS]

    def is_completed(self) -> bool:
        """التحقق من اكتمال العملية"""
        return self.state == OperationState.COMPLETED

    def is_timed_out(self) -> bool:
        """التحقق من انتهاء مهلة العملية"""
        if not self.start_time or not self.is_active():
            return False

        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed > self.timeout

    def get_elapsed_time(self) -> float:
        """الحصول على الوقت المنقضي"""
        if not self.start_time:
            return 0.0

        end_time = self.end_time or datetime.now()
        return (end_time - self.start_time).total_seconds()


class AppStateManager:
    """مدير حالة التطبيق"""

    def __init__(self):
        self._operations: Dict[str, Operation] = {}
        self._lock = threading.RLock()
        self._operation_counter = 0
        self._global_state = {
            'is_busy': False,
            'current_user': None,
            'last_activity': datetime.now(),
            'session_start': datetime.now()
        }

        # إعدادات المهلة الزمنية
        self._default_timeouts = {
            OperationType.DATA_LOADING: 45.0,
            OperationType.DROPDOWN_LOADING: 30.0,
            OperationType.RECORD_SAVING: 15.0,
            OperationType.RECORD_DELETING: 10.0,
            OperationType.USER_AUTHENTICATION: 20.0,
            OperationType.EXPORT_DATA: 60.0,
            OperationType.UI_UPDATE: 5.0
        }

        # بدء مراقب المهلة الزمنية
        self._start_timeout_monitor()

    def _generate_operation_id(self, operation_type: OperationType) -> str:
        """توليد معرف فريد للعملية"""
        with self._lock:
            self._operation_counter += 1
            timestamp = int(datetime.now().timestamp() * 1000)
            return f"{operation_type.value}_{timestamp}_{self._operation_counter}"

    def start_operation(self, operation_type: OperationType,
                       description: str = "", timeout: float = None) -> str:
        """بدء عملية جديدة"""
        with self._lock:
            # تحديد المهلة الزمنية
            if timeout is None:
                timeout = self._default_timeouts.get(operation_type, 30.0)

            # إنشاء العملية
            operation_id = self._generate_operation_id(operation_type)
            operation = Operation(operation_id, operation_type, description, timeout)

            # بدء العملية
            operation.start()
            self._operations[operation_id] = operation

            # تحديث الحالة العامة
            self._update_global_state()

            logger.info(f"بدء عملية جديدة: {operation_id} - {description}")
            return operation_id

    def complete_operation(self, operation_id: str, result: Any = None) -> bool:
        """إكمال عملية"""
        with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                logger.warning(f"العملية غير موجودة: {operation_id}")
                return False

            if not operation.is_active():
                logger.warning(f"العملية غير نشطة: {operation_id}")
                return False

            operation.complete(result)
            self._update_global_state()

            # تنظيف العمليات القديمة
            self._cleanup_old_operations()

            return True

    def fail_operation(self, operation_id: str, error_message: str) -> bool:
        """فشل عملية"""
        with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                logger.warning(f"العملية غير موجودة: {operation_id}")
                return False

            operation.fail(error_message)
            self._update_global_state()

            return True

    def cancel_operation(self, operation_id: str) -> bool:
        """إلغاء عملية"""
        with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                logger.warning(f"العملية غير موجودة: {operation_id}")
                return False

            if operation.is_active():
                operation.cancel()
                self._update_global_state()
                return True

            return False

    def update_operation_progress(self, operation_id: str, progress: float) -> bool:
        """تحديث تقدم العملية"""
        with self._lock:
            operation = self._operations.get(operation_id)
            if not operation:
                return False

            operation.update_progress(progress)
            return True

    def get_operation(self, operation_id: str) -> Optional[Operation]:
        """الحصول على عملية"""
        with self._lock:
            return self._operations.get(operation_id)

    def get_active_operations(self, operation_type: OperationType = None) -> List[Operation]:
        """الحصول على العمليات النشطة"""
        with self._lock:
            active_ops = [op for op in self._operations.values() if op.is_active()]

            if operation_type:
                active_ops = [op for op in active_ops if op.type == operation_type]

            return active_ops

    def is_busy(self, operation_types: List[OperationType] = None) -> bool:
        """التحقق من انشغال التطبيق"""
        with self._lock:
            if operation_types:
                # التحقق من أنواع محددة من العمليات
                for op in self._operations.values():
                    if op.is_active() and op.type in operation_types:
                        return True
                return False
            else:
                # التحقق من أي عمليات نشطة
                return any(op.is_active() for op in self._operations.values())

    def can_start_operation(self, operation_type: OperationType) -> tuple[bool, str]:
        """التحقق من إمكانية بدء عملية جديدة"""
        with self._lock:
            # قواعد التداخل
            blocking_combinations = {
                OperationType.DATA_LOADING: [OperationType.DATA_LOADING, OperationType.EXPORT_DATA],
                OperationType.DROPDOWN_LOADING: [OperationType.DROPDOWN_LOADING],
                OperationType.RECORD_SAVING: [OperationType.RECORD_SAVING, OperationType.DATA_LOADING],
                OperationType.RECORD_DELETING: [OperationType.RECORD_DELETING, OperationType.DATA_LOADING],
                OperationType.EXPORT_DATA: [OperationType.EXPORT_DATA, OperationType.DATA_LOADING],
                OperationType.USER_AUTHENTICATION: [OperationType.USER_AUTHENTICATION]
            }

            blocking_types = blocking_combinations.get(operation_type, [])

            for op in self._operations.values():
                if op.is_active() and op.type in blocking_types:
                    return False, f"عملية أخرى من نوع {op.type.value} جارية بالفعل"

            return True, ""

    def cancel_operations_by_type(self, operation_type: OperationType) -> int:
        """إلغاء جميع العمليات من نوع معين"""
        with self._lock:
            cancelled_count = 0

            for operation in self._operations.values():
                if operation.is_active() and operation.type == operation_type:
                    operation.cancel()
                    cancelled_count += 1

            self._update_global_state()
            logger.info(f"تم إلغاء {cancelled_count} عملية من نوع {operation_type.value}")

            return cancelled_count

    def force_cancel_all_operations(self) -> int:
        """إلغاء جميع العمليات بالقوة"""
        with self._lock:
            cancelled_count = 0

            for operation in self._operations.values():
                if operation.is_active():
                    operation.cancel()
                    cancelled_count += 1

            self._update_global_state()
            logger.warning(f"تم إلغاء {cancelled_count} عملية بالقوة")

            return cancelled_count

    def _update_global_state(self):
        """تحديث الحالة العامة للتطبيق"""
        self._global_state['is_busy'] = self.is_busy()
        self._global_state['last_activity'] = datetime.now()

    def _start_timeout_monitor(self):
        """بدء مراقب المهلة الزمنية"""
        def monitor():
            while True:
                try:
                    time.sleep(5)  # فحص كل 5 ثوان
                    self._check_timeouts()
                except Exception as e:
                    logger.error(f"خطأ في مراقب المهلة الزمنية: {e}")

        thread = threading.Thread(target=monitor, daemon=True, name="TimeoutMonitor")
        thread.start()

    def _check_timeouts(self):
        """فحص المهلات الزمنية للعمليات"""
        with self._lock:
            timed_out_operations = []

            for operation in self._operations.values():
                if operation.is_timed_out():
                    operation.timeout_operation()
                    timed_out_operations.append(operation.id)

            if timed_out_operations:
                logger.warning(f"انتهت مهلة {len(timed_out_operations)} عملية")
                self._update_global_state()

    def _cleanup_old_operations(self):
        """تنظيف العمليات القديمة المكتملة"""
        with self._lock:
            # إبقاء العمليات لمدة ساعة بعد اكتمالها
            cutoff_time = datetime.now() - timedelta(hours=1)

            operations_to_remove = []
            for op_id, operation in self._operations.items():
                if (not operation.is_active() and
                    operation.end_time and
                    operation.end_time < cutoff_time):
                    operations_to_remove.append(op_id)

            for op_id in operations_to_remove:
                del self._operations[op_id]

            if operations_to_remove:
                logger.debug(f"تم تنظيف {len(operations_to_remove)} عملية قديمة")

    def get_status_summary(self) -> Dict[str, Any]:
        """الحصول على ملخص حالة التطبيق"""
        with self._lock:
            active_ops = self.get_active_operations()

            # تجميع العمليات حسب النوع
            ops_by_type = {}
            for op in active_ops:
                op_type = op.type.value
                if op_type not in ops_by_type:
                    ops_by_type[op_type] = []
                ops_by_type[op_type].append({
                    'id': op.id,
                    'description': op.description,
                    'progress': op.progress,
                    'elapsed_time': op.get_elapsed_time()
                })

            return {
                'is_busy': self._global_state['is_busy'],
                'total_operations': len(self._operations),
                'active_operations': len(active_ops),
                'operations_by_type': ops_by_type,
                'current_user': self._global_state.get('current_user'),
                'session_duration': (datetime.now() - self._global_state['session_start']).total_seconds(),
                'last_activity': self._global_state['last_activity'].isoformat()
            }

    def set_current_user(self, username: str):
        """تعيين المستخدم الحالي"""
        with self._lock:
            self._global_state['current_user'] = username
            logger.info(f"تم تعيين المستخدم الحالي: {username}")

    def clear_current_user(self):
        """مسح المستخدم الحالي"""
        with self._lock:
            self._global_state['current_user'] = None
            logger.info("تم مسح المستخدم الحالي")


# مثيل عام للاستخدام في التطبيق
app_state_manager = AppStateManager()