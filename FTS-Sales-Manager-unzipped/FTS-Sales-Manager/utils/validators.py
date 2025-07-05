# -*- coding: utf-8 -*-
"""
utils/validators.py

التحقق من صحة المدخلات
"""

import re
from typing import Tuple, Dict, List, Optional
import string
from datetime import datetime

from core.logger import logger


class InputValidator:
    """مدير التحقق من المدخلات"""

    # Common patterns
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    PHONE_PATTERN = re.compile(r'^\+?[0-9\s\-\(\)]+$')

    # Common weak passwords
    COMMON_PASSWORDS = {
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password1', 'password123', 'admin', 'letmein', 'welcome',
        'monkey', '1234567890', 'qwertyuiop', 'admin123', 'root',
        'toor', 'pass', 'test', 'guest', 'master', 'god', '666666',
        '123123', '12345', '1234567', '12345678', '111111',
        '123321', 'pass123', 'pass1234'
    }

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        التحقق من صحة اسم المستخدم

        Args:
            username: Username to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if empty
        if not username:
            return False, "Username is required"

        # Check length
        if len(username) < 3:
            return False, "Username must be at least 3 characters"

        if len(username) > 50:
            return False, "Username must not exceed 50 characters"

        # Check format
        if not InputValidator.USERNAME_PATTERN.match(username):
            return False, "Username can only contain letters, numbers, dots, hyphens and underscores"

        # Check for consecutive special characters
        if '..' in username or '--' in username or '__' in username:
            return False, "Username cannot contain consecutive special characters"

        # Check start/end
        if username[0] in '.-_' or username[-1] in '.-_':
            return False, "Username cannot start or end with special characters"

        return True, ""

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        التحقق من صحة البريد الإلكتروني

        Args:
            email: Email to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is required"

        # Basic format check
        if not InputValidator.EMAIL_PATTERN.match(email.lower()):
            return False, "Invalid email format"

        # Check length
        if len(email) > 255:
            return False, "Email address too long"

        # Check local part
        local = email.split('@')[0]
        if len(local) > 64:
            return False, "Email local part too long"

        return True, ""

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """
        التحقق من صحة كلمة المرور الأساسية

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"

        if len(password) < 8:
            return False, "Password must be at least 8 characters"

        if len(password) > 128:
            return False, "Password too long"

        return True, ""

    @staticmethod
    def validate_password_complexity(
        password: str,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_numbers: bool = True,
        require_special: bool = True,
        min_length: int = 8
    ) -> Dict[str, bool]:
        """
        تحليل تعقيد كلمة المرور

        Args:
            password: Password to analyze
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_numbers: Require numbers
            require_special: Require special characters
            min_length: Minimum length required

        Returns:
            Dictionary with complexity checks
        """
        complexity = {
            "length": len(password) >= min_length,
            "uppercase": not require_uppercase or bool(re.search(r'[A-Z]', password)),
            "lowercase": not require_lowercase or bool(re.search(r'[a-z]', password)),
            "numbers": not require_numbers or bool(re.search(r'\d', password)),
            "special": not require_special or bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password)),
            "no_spaces": ' ' not in password,
            "no_common": password.lower() not in InputValidator.COMMON_PASSWORDS,
            "no_repeating": not bool(re.search(r'(.)\1{2,}', password)),  # No 3+ repeating chars
            "no_sequential": not InputValidator._has_sequential_chars(password)
        }

        return complexity

    @staticmethod
    def _has_sequential_chars(password: str, length: int = 3) -> bool:
        """Check for sequential characters"""
        sequences = [
            'abcdefghijklmnopqrstuvwxyz',
            'zyxwvutsrqponmlkjihgfedcba',
            '0123456789',
            '9876543210',
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm'
        ]

        password_lower = password.lower()
        for seq in sequences:
            for i in range(len(seq) - length + 1):
                if seq[i:i+length] in password_lower:
                    return True

        return False

    @staticmethod
    def calculate_password_score(password: str) -> int:
        """
        حساب نقاط قوة كلمة المرور

        Args:
            password: Password to score

        Returns:
            Score from 0-10
        """
        if not password:
            return 0

        score = 0

        # Get complexity
        complexity = InputValidator.validate_password_complexity(password)

        # Base score from requirements
        if complexity['length']:
            score += 2
        if complexity['uppercase']:
            score += 1
        if complexity['lowercase']:
            score += 1
        if complexity['numbers']:
            score += 1
        if complexity['special']:
            score += 1
        if complexity['no_common']:
            score += 1
        if complexity['no_repeating']:
            score += 1
        if complexity['no_sequential']:
            score += 1

        # Bonus for length
        if len(password) >= 12:
            score += 1
        if len(password) >= 16:
            score += 1
        if len(password) >= 20:
            score += 1

        # Cap at 10
        return min(score, 10)

    @staticmethod
    def validate_phone(phone: str, country_code: Optional[str] = None) -> Tuple[bool, str]:
        """
        التحقق من صحة رقم الهاتف

        Args:
            phone: Phone number to validate
            country_code: Optional country code for specific validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Phone number is required"

        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)]', '', phone)

        # Check if it's numeric (with optional +)
        if not re.match(r'^\+?\d+$', cleaned):
            return False, "Invalid phone number format"

        # Check length (international standards)
        if len(cleaned) < 7 or len(cleaned) > 15:
            return False, "Phone number length invalid"

        # Country-specific validation
        if country_code:
            if country_code.upper() == 'EG':  # Egypt
                if not (cleaned.startswith('+20') or cleaned.startswith('01')):
                    return False, "Invalid Egyptian phone number"

                # Remove country code for length check
                local = cleaned[3:] if cleaned.startswith('+20') else cleaned
                if not (len(local) == 10 or len(local) == 11):
                    return False, "Egyptian phone number must be 10 or 11 digits"

        return True, ""

    @staticmethod
    def sanitize_input(text: str, allow_html: bool = False) -> str:
        """
        تنظيف المدخلات من الأكواد الضارة

        Args:
            text: Text to sanitize
            allow_html: Whether to allow HTML tags

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # Remove null bytes
        text = text.replace('\x00', '')

        # Strip leading/trailing whitespace
        text = text.strip()

        if not allow_html:
            # Escape HTML entities
            text = (
                text.replace('&', '&amp;')
                    .replace('<', '&lt;')
                    .replace('>', '&gt;')
                    .replace('"', '&quot;')
                    .replace("'", '&#x27;')
            )

        return text

    @staticmethod
    def validate_date(
        date_str: str,
        format: str = '%Y-%m-%d',
        min_date: Optional[datetime] = None,
        max_date: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        التحقق من صحة التاريخ

        Args:
            date_str: Date string to validate
            format: Expected date format
            min_date: Minimum allowed date
            max_date: Maximum allowed date

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is required"

        try:
            date = datetime.strptime(date_str, format)

            if min_date and date < min_date:
                return False, f"Date must be after {min_date.strftime(format)}"

            if max_date and date > max_date:
                return False, f"Date must be before {max_date.strftime(format)}"

            return True, ""

        except ValueError:
            return False, f"Invalid date format. Expected: {format}"

    @staticmethod
    def validate_url(url: str, require_https: bool = False) -> Tuple[bool, str]:
        """
        التحقق من صحة URL

        Args:
            url: URL to validate
            require_https: Require HTTPS protocol

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is required"

        # URL pattern
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        )

        if not url_pattern.match(url):
            return False, "Invalid URL format"

        if require_https and not url.startswith('https://'):
            return False, "URL must use HTTPS"

        return True, ""

    @staticmethod
    def validate_credit_card(card_number: str) -> Tuple[bool, str]:
        """
        التحقق من صحة رقم بطاقة الائتمان (Luhn algorithm)

        Args:
            card_number: Credit card number

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Remove spaces and dashes
        card_number = re.sub(r'[\s-]', '', card_number)

        if not card_number.isdigit():
            return False, "Card number must contain only digits"

        if len(card_number) < 13 or len(card_number) > 19:
            return False, "Invalid card number length"

        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n

        if total % 10 != 0:
            return False, "Invalid card number"

        return True, ""