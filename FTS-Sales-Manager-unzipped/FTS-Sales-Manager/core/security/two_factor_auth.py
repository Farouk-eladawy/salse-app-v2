# -*- coding: utf-8 -*-
"""
core/security/two_factor_auth.py

مدير المصادقة الثنائية
Two-Factor Authentication Manager
"""

import pyotp
import qrcode
import io
import base64
import secrets
from typing import Optional, List, Tuple
from datetime import datetime
import json

from core.logger import logger


class TwoFactorAuth:
    """مدير المصادقة الثنائية"""

    def __init__(self, issuer_name: str = "FTS Sales Manager"):
        """
        Initialize 2FA manager

        Args:
            issuer_name: Name shown in authenticator apps
        """
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """
        Generate a new secret key for 2FA

        Returns:
            Base32 encoded secret key
        """
        return pyotp.random_base32()

    def generate_qr_code(self, username: str, secret: str) -> str:
        """
        Generate QR code for authenticator app setup

        Args:
            username: User's username
            secret: Secret key

        Returns:
            Base64 encoded QR code image
        """
        try:
            # Create provisioning URI
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=username,
                issuer_name=self.issuer_name
            )

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"

        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            raise

    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token

        Args:
            secret: User's secret key
            token: 6-digit token from authenticator
            window: Time window for validity (default 1 = ±30 seconds)

        Returns:
            True if token is valid
        """
        try:
            # Remove spaces and validate format
            token = token.replace(" ", "").strip()

            if not token.isdigit() or len(token) != 6:
                return False

            # Verify token
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)

        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return False

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate

        Returns:
            List of backup codes
        """
        codes = []

        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
            # Format as XXXX-XXXX
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)

        return codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for storage

        Args:
            code: Backup code to hash

        Returns:
            Hashed code
        """
        import hashlib

        # Remove formatting
        clean_code = code.replace("-", "").upper()

        # Hash with salt
        salt = "FTS_2FA_BACKUP"
        return hashlib.sha256(f"{salt}{clean_code}".encode()).hexdigest()

    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code

        Args:
            code: Backup code to verify
            hashed_codes: List of hashed backup codes

        Returns:
            Tuple of (is_valid, used_code_hash)
        """
        hashed = self.hash_backup_code(code)

        if hashed in hashed_codes:
            return True, hashed

        return False, None

    def get_current_token(self, secret: str) -> str:
        """
        Get current TOTP token (for testing)

        Args:
            secret: Secret key

        Returns:
            Current 6-digit token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def get_time_remaining(self) -> int:
        """
        Get seconds remaining for current token

        Returns:
            Seconds until token expires
        """
        import time
        return 30 - int(time.time() % 30)

    def export_setup_data(self, username: str, secret: str, backup_codes: List[str]) -> dict:
        """
        Export 2FA setup data for user

        Args:
            username: Username
            secret: Secret key
            backup_codes: List of backup codes

        Returns:
            Dictionary with setup data
        """
        return {
            "username": username,
            "secret": secret,
            "issuer": self.issuer_name,
            "backup_codes": backup_codes,
            "setup_date": datetime.now().isoformat(),
            "algorithm": "SHA1",
            "digits": 6,
            "period": 30
        }

    def validate_setup(self, secret: str, token1: str, token2: str) -> bool:
        """
        Validate 2FA setup with two consecutive tokens

        Args:
            secret: Secret key
            token1: First token
            token2: Second token (should be different)

        Returns:
            True if setup is valid
        """
        # Verify first token
        if not self.verify_token(secret, token1):
            return False

        # Ensure tokens are different
        if token1 == token2:
            return False

        # Wait and verify second token
        import time
        time.sleep(1)

        return self.verify_token(secret, token2)


class TwoFactorDialog(ctk.CTkToplevel):
    """نافذة إدخال رمز المصادقة الثنائية"""

    def __init__(self, parent, lang_manager, theme_manager):
        super().__init__(parent)

        self.parent = parent
        self.lang_manager = lang_manager
        self.theme_manager = theme_manager
        self.result = None

        # Setup window
        self.title(self.lang_manager.get("2fa_title", "Two-Factor Authentication"))
        self.geometry("400x300")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Build UI
        self._build_ui()

        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 400) // 2
        y = (self.winfo_screenheight() - 300) // 2
        self.geometry(f"400x300+{x}+{y}")

        # Focus on entry
        self.after(100, lambda: self.code_entry.focus_set())

    def _build_ui(self):
        """Build dialog UI"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Icon and title
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 20))

        icon_label = ctk.CTkLabel(
            title_frame,
            text="🔐",
            font=ctk.CTkFont(size=48)
        )
        icon_label.pack()

        title_label = ctk.CTkLabel(
            title_frame,
            text=self.lang_manager.get("2fa_prompt", "Enter Authentication Code"),
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 0))

        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text=self.lang_manager.get(
                "2fa_instructions",
                "Enter the 6-digit code from your authenticator app"
            ),
            font=ctk.CTkFont(size=12),
            text_color="gray60",
            wraplength=350
        )
        instructions.pack(pady=(0, 20))

        # Code entry
        self.code_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="000 000",
            font=ctk.CTkFont(size=24, weight="bold"),
            justify="center",
            height=50,
            width=200
        )
        self.code_entry.pack()

        # Bind events
        self.code_entry.bind("<Return>", lambda e: self._verify())
        self.code_entry.bind("<KeyRelease>", self._format_code)

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(30, 0))

        self.verify_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("verify", "Verify"),
            command=self._verify,
            width=120,
            height=40
        )
        self.verify_btn.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text=self.lang_manager.get("cancel", "Cancel"),
            command=self._cancel,
            width=120,
            height=40,
            fg_color="transparent",
            border_width=2
        )
        self.cancel_btn.pack(side="left")

        # Use backup code link
        backup_link = ctk.CTkButton(
            main_frame,
            text=self.lang_manager.get("use_backup_code", "Use backup code"),
            font=ctk.CTkFont(size=12, underline=True),
            fg_color="transparent",
            text_color=("blue", "lightblue"),
            hover=False,
            command=self._use_backup_code
        )
        backup_link.pack(pady=(15, 0))

    def _format_code(self, event=None):
        """Format code as XXX XXX"""
        text = self.code_entry.get().replace(" ", "")

        # Only allow digits
        text = ''.join(c for c in text if c.isdigit())[:6]

        # Format with space
        if len(text) > 3:
            text = f"{text[:3]} {text[3:]}"

        # Update entry
        self.code_entry.delete(0, "end")
        self.code_entry.insert(0, text)

    def _verify(self):
        """Verify code"""
        code = self.code_entry.get().replace(" ", "")

        if len(code) != 6 or not code.isdigit():
            self.code_entry.configure(border_color="red")
            return

        self.result = code
        self.destroy()

    def _cancel(self):
        """Cancel dialog"""
        self.result = None
        self.destroy()

    def _use_backup_code(self):
        """Switch to backup code entry"""
        # Change UI for backup code entry
        self.code_entry.configure(placeholder_text="XXXX-XXXX")
        self.title(self.lang_manager.get("backup_code_title", "Enter Backup Code"))

    def get_code(self) -> Optional[str]:
        """Get entered code"""
        self.wait_window()
        return self.result