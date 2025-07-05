# -*- coding: utf-8 -*-
"""
core/session_manager.py

مدير الجلسات
Session Manager
"""

import secrets
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import threading
import time

from core.logger import logger
from core.security.encryption import EncryptionManager


class SessionManager:
    """مدير جلسات المستخدمين"""

    def __init__(
        self,
        session_timeout: int = 1800,  # 30 minutes
        max_sessions_per_user: int = 5,
        enable_encryption: bool = True,
        storage_path: str = "data/sessions"
    ):
        """
        Initialize session manager

        Args:
            session_timeout: Session timeout in seconds
            max_sessions_per_user: Maximum concurrent sessions per user
            enable_encryption: Enable session data encryption
            storage_path: Path to store session data
        """
        self.session_timeout = session_timeout
        self.max_sessions_per_user = max_sessions_per_user
        self.enable_encryption = enable_encryption
        self.storage_path = storage_path

        # Storage
        self.sessions: Dict[str, dict] = {}
        self._lock = threading.RLock()

        # Encryption
        if self.enable_encryption:
            self.encryption = EncryptionManager()

        # Create storage directory
        os.makedirs(self.storage_path, exist_ok=True)

        # Load existing sessions
        self._load_sessions()

        # Start cleanup thread
        self._start_cleanup_thread()

    def create_session(
        self,
        user_info: dict,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create new session

        Args:
            user_info: User information dictionary
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session ID
        """
        with self._lock:
            # Generate session ID
            session_id = secrets.token_urlsafe(32)

            # Check concurrent sessions
            username = user_info.get('username')
            if username:
                self._check_concurrent_sessions(username)

            # Create session data
            session_data = {
                'id': session_id,
                'user': user_info,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat(),
                'ip_address': ip_address,
                'user_agent': user_agent,
                'active': True,
                'activity_count': 0
            }

            # Store session
            self.sessions[session_id] = session_data

            # Save to disk
            self._save_session(session_id, session_data)

            logger.info(f"Session created for user: {username} (ID: {session_id[:8]}...)")

            return session_id

    def validate_session(self, session_id: str) -> Optional[dict]:
        """
        Validate session

        Args:
            session_id: Session ID to validate

        Returns:
            Session data if valid, None otherwise
        """
        with self._lock:
            session = self.sessions.get(session_id)

            if not session:
                # Try loading from disk
                session = self._load_session(session_id)
                if session:
                    self.sessions[session_id] = session

            if not session:
                return None

            # Check if active
            if not session.get('active', False):
                logger.warning(f"Inactive session: {session_id[:8]}...")
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                logger.warning(f"Expired session: {session_id[:8]}...")
                self.invalidate_session(session_id)
                return None

            # Update last activity
            session['last_activity'] = datetime.now().isoformat()
            session['activity_count'] = session.get('activity_count', 0) + 1

            # Extend session if active
            session['expires_at'] = (datetime.now() + timedelta(seconds=self.session_timeout)).isoformat()

            # Save updated session
            self._save_session(session_id, session)

            return session

    def invalidate_session(self, session_id: str) -> bool:
        """
        Invalidate session

        Args:
            session_id: Session ID to invalidate

        Returns:
            True if successful
        """
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['active'] = False
                session['invalidated_at'] = datetime.now().isoformat()

                # Save to disk
                self._save_session(session_id, session)

                # Remove from memory
                del self.sessions[session_id]

                username = session.get('user', {}).get('username', 'Unknown')
                logger.info(f"Session invalidated for user: {username}")

                return True

            return False

    def get_user_sessions(self, username: str) -> List[dict]:
        """
        Get all sessions for a user

        Args:
            username: Username

        Returns:
            List of active sessions
        """
        with self._lock:
            user_sessions = []

            for session_id, session in self.sessions.items():
                if session.get('user', {}).get('username') == username and session.get('active'):
                    user_sessions.append({
                        'id': session_id,
                        'created_at': session['created_at'],
                        'last_activity': session['last_activity'],
                        'ip_address': session.get('ip_address'),
                        'user_agent': session.get('user_agent')
                    })

            return sorted(user_sessions, key=lambda x: x['created_at'], reverse=True)

    def invalidate_user_sessions(self, username: str, except_session: Optional[str] = None) -> int:
        """
        Invalidate all sessions for a user

        Args:
            username: Username
            except_session: Session ID to keep active

        Returns:
            Number of sessions invalidated
        """
        with self._lock:
            count = 0

            for session_id in list(self.sessions.keys()):
                session = self.sessions.get(session_id)
                if session and session.get('user', {}).get('username') == username:
                    if session_id != except_session:
                        self.invalidate_session(session_id)
                        count += 1

            logger.info(f"Invalidated {count} sessions for user: {username}")
            return count

    def extend_session(self, session_id: str, duration: Optional[int] = None) -> bool:
        """
        Extend session timeout

        Args:
            session_id: Session ID
            duration: Extension duration in seconds (default: session_timeout)

        Returns:
            True if successful
        """
        with self._lock:
            session = self.validate_session(session_id)

            if session:
                duration = duration or self.session_timeout
                session['expires_at'] = (datetime.now() + timedelta(seconds=duration)).isoformat()
                self._save_session(session_id, session)
                return True

            return False

    def get_session_info(self, session_id: str) -> Optional[dict]:
        """
        Get session information

        Args:
            session_id: Session ID

        Returns:
            Session info dictionary
        """
        session = self.validate_session(session_id)

        if session:
            return {
                'id': session_id,
                'username': session.get('user', {}).get('username'),
                'created_at': session['created_at'],
                'last_activity': session['last_activity'],
                'expires_at': session['expires_at'],
                'activity_count': session.get('activity_count', 0),
                'ip_address': session.get('ip_address'),
                'active': session.get('active', False)
            }

        return None

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        with self._lock:
            now = datetime.now()
            expired = []

            for session_id, session in self.sessions.items():
                expires_at = datetime.fromisoformat(session['expires_at'])
                if now > expires_at:
                    expired.append(session_id)

            for session_id in expired:
                self.invalidate_session(session_id)

            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")

    def _check_concurrent_sessions(self, username: str):
        """Check and limit concurrent sessions"""
        user_sessions = self.get_user_sessions(username)

        if len(user_sessions) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest = user_sessions[-1]
            self.invalidate_session(oldest['id'])
            logger.warning(f"Removed oldest session for user: {username} (limit: {self.max_sessions_per_user})")

    def _save_session(self, session_id: str, session_data: dict):
        """Save session to disk"""
        try:
            filename = os.path.join(self.storage_path, f"{session_id}.json")

            # Prepare data
            data = json.dumps(session_data, ensure_ascii=False)

            # Encrypt if enabled
            if self.enable_encryption:
                data = self.encryption.encrypt_data(data)
                save_data = {"encrypted": True, "data": data}
            else:
                save_data = session_data

            # Write to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Error saving session: {e}")

    def _load_session(self, session_id: str) -> Optional[dict]:
        """Load session from disk"""
        try:
            filename = os.path.join(self.storage_path, f"{session_id}.json")

            if not os.path.exists(filename):
                return None

            with open(filename, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            # Decrypt if needed
            if save_data.get("encrypted") and self.enable_encryption:
                decrypted = self.encryption.decrypt_data(save_data["data"])
                session_data = json.loads(decrypted)
            else:
                session_data = save_data

            return session_data

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None

    def _load_sessions(self):
        """Load all sessions from disk"""
        try:
            if not os.path.exists(self.storage_path):
                return

            for filename in os.listdir(self.storage_path):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json
                    session = self._load_session(session_id)

                    if session and session.get('active'):
                        # Check if not expired
                        expires_at = datetime.fromisoformat(session['expires_at'])
                        if datetime.now() <= expires_at:
                            self.sessions[session_id] = session

        except Exception as e:
            logger.error(f"Error loading sessions: {e}")

    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(300)  # Run every 5 minutes
                    self.cleanup_expired_sessions()
                except Exception as e:
                    logger.error(f"Cleanup thread error: {e}")

        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

    def get_statistics(self) -> dict:
        """
        Get session statistics

        Returns:
            Statistics dictionary
        """
        with self._lock:
            total_sessions = len(self.sessions)

            # Count by user
            users = {}
            for session in self.sessions.values():
                username = session.get('user', {}).get('username', 'Unknown')
                users[username] = users.get(username, 0) + 1

            return {
                'total_active_sessions': total_sessions,
                'unique_users': len(users),
                'sessions_per_user': users,
                'session_timeout': self.session_timeout,
                'max_sessions_per_user': self.max_sessions_per_user
            }