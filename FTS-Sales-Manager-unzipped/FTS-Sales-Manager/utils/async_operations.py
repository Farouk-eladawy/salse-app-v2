# utils/async_operations.py
from concurrent.futures import ThreadPoolExecutor
import threading

class AsyncOperationManager:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_operations = {}

    def run_async(self, operation_id: str, func, *args, **kwargs):
        """تشغيل عملية بشكل غير متزامن"""
        if operation_id in self.pending_operations:
            return self.pending_operations[operation_id]

        future = self.executor.submit(func, *args, **kwargs)
        self.pending_operations[operation_id] = future
        return future

    def shutdown(self):
        """إيقاف المدير"""
        self.executor.shutdown(wait=True)