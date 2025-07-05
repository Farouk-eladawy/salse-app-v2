# -*- coding: utf-8 -*-
"""
core/security/rate_limiter.py

حماية من هجمات Brute Force
"""

import time
import json
import os
from collections import defaultdict
from typing import Tuple, Dict, List
from datetime import datetime, timedelta
import threading

from core.logger import logger


class RateLimiter:
    """مدير حماية معدل المحاولات"""

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,  # 5 minutes
        lockout_seconds: int = 300,  # 5 minutes
        persistent_storage: bool = True
    ):
        """
        Initialize rate limiter

        Args:
            max_attempts: Maximum attempts allowed in window
            window_seconds: Time window for attempts
            lockout_seconds: Lockout duration after max attempts
            persistent_storage: Save state to disk
        """
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self.persistent_storage = persistent_storage

        # Storage
        self.attempts: Dict[str, List[float]] = defaultdict(list)
        self.lockouts: Dict[str, float] = {}
        self.config_file = "data/rate_limiter.json"

        # Thread safety
        self._lock = threading.RLock()

        # Load saved state
        if self.persistent_storage:
            self._load_state()

        # Start cleanup thread
        self._start_cleanup_thread()

    def check_rate_limit(self, identifier: str) -> Tuple[bool, str]:
        """
        التحقق من معدل المحاولات

        Args:
            identifier: Unique identifier (e.g., username:ip)

        Returns:
            Tuple of (allowed, message)
        """
        with self._lock:
            # Clean up old data
            self._cleanup_old_attempts()

            # Check if locked out
            if identifier in self.lockouts:
                remaining = self.lockouts[identifier] - time.time()
                if remaining > 0:
                    minutes = int(remaining // 60)
                    seconds = int(remaining % 60)
                    return False, f"Account locked. Try again in {minutes}m {seconds}s"
                else:
                    # Lockout expired
                    del self.lockouts[identifier]
                    logger.info(f"Lockout expired for: {identifier}")

            # Check attempts in current window
            now = time.time()
            window_start = now - self.window_seconds

            # Filter attempts within window
            self.attempts[identifier] = [
                t for t in self.attempts[identifier]
                if t > window_start
            ]

            # Check if exceeding limit
            current_attempts = len(self.attempts[identifier])

            if current_attempts >= self.max_attempts:
                # Lock out the identifier
                self.lockouts[identifier] = now + self.lockout_seconds
                logger.warning(f"Rate limit exceeded for: {identifier} - Locked out")

                if self.persistent_storage:
                    self._save_state()

                return False, f"Too many attempts. Account locked for {self.lockout_seconds // 60} minutes."

            # Calculate remaining attempts
            remaining = self.max_attempts - current_attempts
            return True, f"{remaining} attempts remaining"

    def record_attempt(self, identifier: str):
        """
        تسجيل محاولة

        Args:
            identifier: Unique identifier
        """
        with self._lock:
            self.attempts[identifier].append(time.time())
            logger.debug(f"Recorded attempt for: {identifier}")

            if self.persistent_storage:
                self._save_state()

    def clear_attempts(self, identifier: str):
        """
        مسح المحاولات عند النجاح

        Args:
            identifier: Unique identifier
        """
        with self._lock:
            if identifier in self.attempts:
                del self.attempts[identifier]
            if identifier in self.lockouts:
                del self.lockouts[identifier]

            logger.info(f"Cleared attempts for: {identifier}")

            if self.persistent_storage:
                self._save_state()

    def is_locked_out(self, identifier: str) -> bool:
        """
        Check if identifier is locked out

        Args:
            identifier: Unique identifier

        Returns:
            True if locked out
        """
        with self._lock:
            if identifier in self.lockouts:
                if self.lockouts[identifier] > time.time():
                    return True
                else:
                    del self.lockouts[identifier]
            return False

    def get_attempts_count(self, identifier: str) -> int:
        """
        Get current attempts count

        Args:
            identifier: Unique identifier

        Returns:
            Number of attempts in current window
        """
        with self._lock:
            now = time.time()
            window_start = now - self.window_seconds

            return len([
                t for t in self.attempts.get(identifier, [])
                if t > window_start
            ])

    def reset_identifier(self, identifier: str):
        """
        Reset all data for an identifier

        Args:
            identifier: Unique identifier
        """
        self.clear_attempts(identifier)

    def _cleanup_old_attempts(self):
        """تنظيف المحاولات القديمة"""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean attempts
        for identifier in list(self.attempts.keys()):
            self.attempts[identifier] = [
                t for t in self.attempts[identifier]
                if t > window_start
            ]
            if not self.attempts[identifier]:
                del self.attempts[identifier]

        # Clean expired lockouts
        for identifier in list(self.lockouts.keys()):
            if self.lockouts[identifier] <= now:
                del self.lockouts[identifier]
                logger.debug(f"Removed expired lockout for: {identifier}")

    def _save_state(self):
        """حفظ الحالة إلى الملف"""
        if not self.persistent_storage:
            return

        try:
            with self._lock:
                state = {
                    "attempts": dict(self.attempts),
                    "lockouts": dict(self.lockouts),
                    "timestamp": datetime.now().isoformat(),
                    "config": {
                        "max_attempts": self.max_attempts,
                        "window_seconds": self.window_seconds,
                        "lockout_seconds": self.lockout_seconds
                    }
                }

                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

                # Write to temporary file first
                temp_file = f"{self.config_file}.tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(state, f, indent=2)

                # Atomic rename
                os.replace(temp_file, self.config_file)

        except Exception as e:
            logger.error(f"Error saving rate limiter state: {e}")

    def _load_state(self):
        """تحميل الحالة من الملف"""
        if not self.persistent_storage:
            return

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)

                with self._lock:
                    # Load attempts
                    self.attempts = defaultdict(list)
                    for key, value in state.get("attempts", {}).items():
                        self.attempts[key] = value

                    # Load lockouts
                    self.lockouts = state.get("lockouts", {})

                    # Clean old data immediately
                    self._cleanup_old_attempts()

                logger.info("Loaded rate limiter state")

        except Exception as e:
            logger.error(f"Error loading rate limiter state: {e}")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(60)  # Run every minute
                    with self._lock:
                        self._cleanup_old_attempts()
                        if self.persistent_storage:
                            self._save_state()
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def get_statistics(self) -> dict:
        """
        Get rate limiter statistics

        Returns:
            Dictionary with statistics
        """
        with self._lock:
            return {
                "total_tracked": len(self.attempts),
                "currently_locked": len(self.lockouts),
                "total_attempts": sum(len(attempts) for attempts in self.attempts.values()),
                "config": {
                    "max_attempts": self.max_attempts,
                    "window_seconds": self.window_seconds,
                    "lockout_seconds": self.lockout_seconds
                }
            }

    def export_blacklist(self) -> List[str]:
        """
        Export list of currently locked identifiers

        Returns:
            List of locked identifiers
        """
        with self._lock:
            self._cleanup_old_attempts()
            return list(self.lockouts.keys())