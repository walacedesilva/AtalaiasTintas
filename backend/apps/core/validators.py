"""
Enhanced Password Validators for Strong Security

This module provides comprehensive password validation for the Enhanced User Permissions System,
implementing strong password policies that go beyond Django's default validators.

Features:
- Complex password requirements (uppercase, lowercase, digits, symbols)
- Password history tracking
- Common password pattern detection
- Username similarity prevention
- Custom security policies

Author: GitHub Copilot
Date: 2026-04-12
Version: 1.0.0 (T013 Enhanced Authentication Security)

Dependencies:
- Django 6.0.4+
- Enhanced User model with password history
"""

import re
import string
from difflib import SequenceMatcher
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.password_validation import CommonPasswordValidator


class StrongPasswordValidator:
    """
    Enhanced password validator with comprehensive security requirements.
    
    Requirements:
    - Minimum length (configurable, default 12)
    - At least one uppercase letter
    - At least one lowercase letter  
    - At least one digit
    - At least one special character
    - Minimum number of unique characters
    - No common patterns or sequences
    """
    
    def __init__(self, min_length=12, require_uppercase=True, require_lowercase=True,
                 require_digits=True, require_symbols=True, min_unique_chars=8):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_symbols = require_symbols
        self.min_unique_chars = min_unique_chars
        
        # Common weak patterns
        self.weak_patterns = [
            r'123',        # Sequential numbers
            r'abc',        # Sequential letters
            r'qwe',        # Keyboard patterns
            r'asd',        # More keyboard patterns
            r'zxc',        # More keyboard patterns
            r'password',   # Common word
            r'admin',      # Common word
            r'login',      # Common word
            r'user',       # Common word
        ]
        
        # Special characters set
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate(self, password, user=None):
        """
        Validate password against all security requirements.
        
        Args:
            password (str): Password to validate
            user (User, optional): User instance for context validation
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        errors = []
        
        # Length validation
        if len(password) < self.min_length:
            errors.append(
                ValidationError(
                    _(f'Password must be at least {self.min_length} characters long.'),
                    code='password_too_short',
                )
            )
        
        # Character type requirements
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one uppercase letter.'),
                    code='password_no_uppercase',
                )
            )
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one lowercase letter.'),
                    code='password_no_lowercase',
                )
            )
        
        if self.require_digits and not re.search(r'[0-9]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one digit.'),
                    code='password_no_digit',
                )
            )
        
        if self.require_symbols and not re.search(rf'[{re.escape(self.special_chars)}]', password):
            errors.append(
                ValidationError(
                    _('Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?).'),
                    code='password_no_symbol',
                )
            )
        
        # Unique characters requirement
        unique_chars = len(set(password))
        if unique_chars < self.min_unique_chars:
            errors.append(
                ValidationError(
                    _(f'Password must contain at least {self.min_unique_chars} unique characters.'),
                    code='password_not_unique_enough',
                )
            )
        
        # Weak pattern detection
        password_lower = password.lower()
        for pattern in self.weak_patterns:
            if pattern in password_lower:
                errors.append(
                    ValidationError(
                        _(f'Password contains a common weak pattern: {pattern}.'),
                        code='password_weak_pattern',
                    )
                )
        
        # Sequential character detection
        if self._has_sequential_chars(password):
            errors.append(
                ValidationError(
                    _('Password must not contain sequential characters (123, abc, etc.).'),
                    code='password_sequential_chars',
                )
            )
        
        # Repetitive character detection
        if self._has_repetitive_chars(password):
            errors.append(
                ValidationError(
                    _('Password must not contain too many repetitive characters.'),
                    code='password_repetitive_chars',
                )
            )
        
        # User context validation
        if user:
            # Username similarity check
            if self._is_similar_to_username(password, user):
                errors.append(
                    ValidationError(
                        _('Password must not be too similar to your username.'),
                        code='password_too_similar_to_username',
                    )
                )
            
            # User attribute similarity check
            if self._is_similar_to_user_attributes(password, user):
                errors.append(
                    ValidationError(
                        _('Password must not be too similar to your personal information.'),
                        code='password_too_similar_to_user_info',
                    )
                )
        
        if errors:
            raise ValidationError(errors)
    
    def _has_sequential_chars(self, password, min_sequence=3):
        """Check for sequential characters in password."""
        
        # Check for numeric sequences
        for i in range(len(password) - min_sequence + 1):
            substring = password[i:i + min_sequence]
            if substring.isdigit():
                digits = [int(d) for d in substring]
                if self._is_sequence(digits):
                    return True
        
        # Check for alphabetic sequences
        for i in range(len(password) - min_sequence + 1):
            substring = password[i:i + min_sequence].lower()
            if substring.isalpha():
                chars = [ord(c) for c in substring]
                if self._is_sequence(chars):
                    return True
        
        return False
    
    def _is_sequence(self, nums):
        """Check if numbers form an ascending or descending sequence."""
        if len(nums) < 3:
            return False
        
        # Check ascending sequence
        ascending = all(nums[i] + 1 == nums[i + 1] for i in range(len(nums) - 1))
        
        # Check descending sequence
        descending = all(nums[i] - 1 == nums[i + 1] for i in range(len(nums) - 1))
        
        return ascending or descending
    
    def _has_repetitive_chars(self, password, max_repeat=3):
        """Check for repetitive characters in password."""
        
        # Check for consecutive repetitive characters
        for i in range(len(password) - max_repeat + 1):
            char = password[i]
            if all(c == char for c in password[i:i + max_repeat]):
                return True
        
        # Check for overall character frequency
        char_count = {}
        for char in password:
            char_count[char] = char_count.get(char, 0) + 1
        
        # If any character appears more than 1/3 of the password length
        max_allowed_freq = max(2, len(password) // 3)
        for count in char_count.values():
            if count > max_allowed_freq:
                return True
        
        return False
    
    def _is_similar_to_username(self, password, user, threshold=0.7):
        """Check if password is too similar to username."""
        if not hasattr(user, 'username') or not user.username:
            return False
        
        username = user.username.lower()
        password_lower = password.lower()
        
        # Direct substring check
        if username in password_lower or password_lower in username:
            return True
        
        # Similarity ratio check
        similarity = SequenceMatcher(None, username, password_lower).ratio()
        return similarity > threshold
    
    def _is_similar_to_user_attributes(self, password, user, threshold=0.6):
        """Check if password is too similar to user attributes."""
        password_lower = password.lower()
        
        # Attributes to check
        attributes_to_check = [
            'first_name', 'last_name', 'email'
        ]
        
        for attr in attributes_to_check:
            if hasattr(user, attr):
                value = getattr(user, attr)
                if value:
                    value_lower = str(value).lower()
                    
                    # Direct substring check
                    if len(value_lower) > 3 and value_lower in password_lower:
                        return True
                    
                    # Similarity ratio check for longer values
                    if len(value_lower) > 4:
                        similarity = SequenceMatcher(None, value_lower, password_lower).ratio()
                        if similarity > threshold:
                            return True
        
        return False
    
    def get_help_text(self):
        """Return help text for password requirements."""
        requirements = [
            f'Your password must contain at least {self.min_length} characters.'
        ]
        
        if self.require_uppercase:
            requirements.append('Include at least one uppercase letter.')
        
        if self.require_lowercase:
            requirements.append('Include at least one lowercase letter.')
        
        if self.require_digits:
            requirements.append('Include at least one digit.')
        
        if self.require_symbols:
            requirements.append('Include at least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?).')
        
        requirements.extend([
            f'Use at least {self.min_unique_chars} different characters.',
            'Avoid common patterns like \'123\', \'abc\', or \'password\'.',
            'Avoid using your username or personal information.',
        ])
        
        return ' '.join(requirements)


class PasswordHistoryValidator:
    """
    Validator to prevent reuse of recent passwords.
    
    Requires password history tracking in the User model.
    """
    
    def __init__(self, history_count=5):
        self.history_count = history_count
    
    def validate(self, password, user=None):
        """
        Validate password against password history.
        
        Args:
            password (str): New password to validate
            user (User, optional): User instance for history check
            
        Raises:
            ValidationError: If password was recently used
        """
        if not user or not hasattr(user, 'id') or not user.id:
            return  # Skip validation for new users
        
        # Check if password history tracking is available
        if not hasattr(user, 'password_history'):
            return  # Skip if no password history tracking
        
        # Import here to avoid circular imports
        from django.contrib.auth.hashers import check_password
        
        try:
            # Get recent password hashes (implement this in your User model)
            recent_passwords = getattr(user, 'get_password_history', lambda: [])()
            
            # Check against recent passwords
            for old_password_hash in recent_passwords[:self.history_count]:
                if check_password(password, old_password_hash):
                    raise ValidationError(
                        _(f'Password cannot be one of the last {self.history_count} passwords used.'),
                        code='password_recently_used',
                    )
                    
        except AttributeError:
            # Password history not implemented, skip validation
            pass
    
    def get_help_text(self):
        """Return help text for password history requirements."""
        return f'Your password cannot be one of the last {self.history_count} passwords you have used.'


class PasswordComplexityValidator:
    """
    Advanced password complexity validator with entropy calculation.
    
    Calculates password entropy and ensures sufficient randomness.
    """
    
    def __init__(self, min_entropy=50):
        self.min_entropy = min_entropy
    
    def validate(self, password, user=None):
        """
        Validate password complexity using entropy calculation.
        
        Args:
            password (str): Password to validate
            user (User, optional): User instance (not used in this validator)
            
        Raises:
            ValidationError: If password entropy is too low
        """
        entropy = self._calculate_entropy(password)
        
        if entropy < self.min_entropy:
            raise ValidationError(
                _(f'Password complexity is insufficient. '
                  f'Current entropy: {entropy:.1f} bits, minimum required: {self.min_entropy} bits.'),
                code='password_low_entropy',
            )
    
    def _calculate_entropy(self, password):
        """
        Calculate password entropy in bits.
        
        Entropy = log2(character_space^password_length)
        """
        import math
        
        # Determine character space
        char_space = 0
        
        if any(c.islower() for c in password):
            char_space += 26  # lowercase letters
        
        if any(c.isupper() for c in password):
            char_space += 26  # uppercase letters
        
        if any(c.isdigit() for c in password):
            char_space += 10  # digits
        
        # Special characters
        special_chars = set(password) - set(string.ascii_letters + string.digits)
        if special_chars:
            char_space += len(special_chars)
        
        if char_space == 0:
            return 0
        
        # Calculate entropy
        entropy = len(password) * math.log2(char_space)
        
        # Adjust for patterns and repetition
        entropy *= self._pattern_penalty(password)
        
        return entropy
    
    def _pattern_penalty(self, password):
        """
        Apply penalty for patterns and repetition.
        
        Returns a multiplier between 0 and 1.
        """
        penalty = 1.0
        
        # Repetition penalty
        unique_chars = len(set(password))
        total_chars = len(password)
        if total_chars > 0:
            uniqueness_ratio = unique_chars / total_chars
            penalty *= uniqueness_ratio
        
        # Sequential character penalty
        sequential_count = 0
        for i in range(len(password) - 2):
            char1, char2, char3 = password[i:i+3]
            if (ord(char1) + 1 == ord(char2) == ord(char3) - 1) or \
               (ord(char1) - 1 == ord(char2) == ord(char3) + 1):
                sequential_count += 1
        
        if sequential_count > 0:
            penalty *= max(0.5, 1 - (sequential_count / len(password)))
        
        return max(0.1, penalty)  # Minimum penalty of 0.1
    
    def get_help_text(self):
        """Return help text for complexity requirements."""
        return (
            f'Your password must have sufficient complexity (minimum {self.min_entropy} bits of entropy). '
            'Use a mix of character types and avoid patterns to increase complexity.'
        )


# =============================================================================
# UTILITY FUNCTIONS FOR PASSWORD VALIDATION
# =============================================================================

def validate_password_strength(password, user=None):
    """
    Comprehensive password validation using all available validators.
    
    Args:
        password (str): Password to validate
        user (User, optional): User instance for context validation
        
    Returns:
        dict: Validation result with strength score and feedback
    """
    validators = [
        StrongPasswordValidator(),
        PasswordHistoryValidator(),
        PasswordComplexityValidator(),
        CommonPasswordValidator(),
    ]
    
    validation_result = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'strength_score': 0,
        'entropy': 0,
        'feedback': []
    }
    
    # Run all validators
    for validator in validators:
        try:
            validator.validate(password, user)
        except ValidationError as e:
            validation_result['is_valid'] = False
            if hasattr(e, 'messages'):
                validation_result['errors'].extend(e.messages)
            else:
                validation_result['errors'].append(str(e))
    
    # Calculate strength score
    validation_result['strength_score'] = _calculate_strength_score(password)
    
    # Calculate entropy
    complexity_validator = PasswordComplexityValidator()
    validation_result['entropy'] = complexity_validator._calculate_entropy(password)
    
    # Generate feedback
    validation_result['feedback'] = _generate_password_feedback(password, validation_result)
    
    return validation_result


def _calculate_strength_score(password):
    """
    Calculate password strength score (0-100).
    
    Args:
        password (str): Password to score
        
    Returns:
        int: Strength score from 0 to 100
    """
    score = 0
    
    # Length scoring (max 25 points)
    length = len(password)
    if length >= 12:
        score += 25
    elif length >= 8:
        score += 15
    elif length >= 6:
        score += 10
    else:
        score += 5
    
    # Character diversity (max 25 points)
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    diversity_score = sum([has_lower, has_upper, has_digit, has_special]) * 6
    score += min(25, diversity_score)
    
    # Uniqueness (max 20 points)
    unique_chars = len(set(password))
    uniqueness_ratio = unique_chars / len(password) if len(password) > 0 else 0
    score += int(uniqueness_ratio * 20)
    
    # Pattern penalty (max -30 points)
    strong_validator = StrongPasswordValidator()
    
    # Check for weak patterns
    penalties = 0
    if strong_validator._has_sequential_chars(password):
        penalties += 10
    if strong_validator._has_repetitive_chars(password):
        penalties += 10
    
    # Common word penalty
    password_lower = password.lower()
    common_words = ['password', 'admin', 'login', 'user', 'test', '123456']
    for word in common_words:
        if word in password_lower:
            penalties += 5
    
    score = max(0, score - penalties)
    
    # Entropy bonus (max 30 points)
    complexity_validator = PasswordComplexityValidator()
    entropy = complexity_validator._calculate_entropy(password)
    entropy_bonus = min(30, int(entropy / 3))  # 1 point per 3 bits of entropy
    score += entropy_bonus
    
    return min(100, score)


def _generate_password_feedback(password, validation_result):
    """
    Generate human-readable feedback for password improvement.
    
    Args:
        password (str): Password being validated
        validation_result (dict): Current validation result
        
    Returns:
        list: List of feedback messages
    """
    feedback = []
    
    # Strength-based feedback
    strength_score = validation_result['strength_score']
    
    if strength_score >= 90:
        feedback.append("Excellent! Your password is very strong.")
    elif strength_score >= 70:
        feedback.append("Good! Your password is strong.")
    elif strength_score >= 50:
        feedback.append("Fair. Your password could be stronger.")
    else:
        feedback.append("Weak. Your password needs significant improvement.")
    
    # Specific improvement suggestions
    if len(password) < 12:
        feedback.append("Consider using a longer password (12+ characters).")
    
    if not any(c.isupper() for c in password):
        feedback.append("Add some uppercase letters.")
    
    if not any(c.islower() for c in password):
        feedback.append("Add some lowercase letters.")
    
    if not any(c.isdigit() for c in password):
        feedback.append("Include some numbers.")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        feedback.append("Include special characters (!@#$%^&*()_+-=[]{}|;:,.<>?).")
    
    # Entropy feedback
    entropy = validation_result['entropy']
    if entropy < 40:
        feedback.append("Increase complexity by using more diverse characters.")
    
    # Pattern warnings
    strong_validator = StrongPasswordValidator()
    if strong_validator._has_sequential_chars(password):
        feedback.append("Avoid sequential characters like '123' or 'abc'.")
    
    if strong_validator._has_repetitive_chars(password):
        feedback.append("Avoid repetitive characters.")
    
    return feedback