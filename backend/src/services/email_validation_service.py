"""
Email validation service (Phase 3.2).
Supporting feature: Enhanced email validation with multiple checks.
"""
import re
import logging
import asyncio
from typing import Tuple
from email_validator import validate_email, EmailNotValidError

logger = logging.getLogger(__name__)

# List of common disposable/temporary email domains
DISPOSABLE_DOMAINS = {
    # Temporary email services
    "tempmail.com", "temp-mail.org", "10minutemail.com", "guerrillamail.com",
    "mailinator.com", "throwaway.email", "maildrop.cc", "yopmail.com",
    "trash-mail.com", "fake-mail.net", "temp-mail.io", "trashmail.com",
    "dispostable.com", "sharklasers.com", "grr.la", "0-mail.com",
    "itsallmail.com", "mailnesia.com", "sharklasers.com", "spam4.me",
    "trashmail.cc", "mailnesia.com", "guerrillamail.info", "fakeinbox.com",
    "mytrashmail.com", "inboxalias.com", "emailondeck.com", "mytrashmail.com",
}


class EmailValidator:
    """Enhanced email validation with multiple checks."""
    
    @staticmethod
    def is_valid_format(email: str) -> Tuple[bool, str | None]:
        """
        Validate email format using RFC 5322 standards.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
        """
        try:
            # Validate using email_validator library
            valid = validate_email(email, check_deliverability=False)
            return True, None
        except EmailNotValidError as e:
            return False, str(e)
    
    @staticmethod
    def is_disposable_email(email: str) -> bool:
        """
        Check if email uses a disposable/temporary email service.
        
        Args:
            email: Email address to check
            
        Returns:
            True if email is from a disposable service, False otherwise
        """
        try:
            domain = email.split("@")[1].lower()
            return domain in DISPOSABLE_DOMAINS
        except (IndexError, AttributeError):
            return False
    
    @staticmethod
    def is_corporate_email(email: str) -> bool:
        """
        Check if email is from a known public email provider (Gmail, Yahoo, etc).
        
        Args:
            email: Email address to check
            
        Returns:
            True if email is from a public provider, False otherwise
        """
        public_providers = {
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
            "aol.com", "mail.com", "protonmail.com", "tutanota.com",
            "icloud.com", "ymail.com"
        }
        try:
            domain = email.split("@")[1].lower()
            return domain not in public_providers
        except (IndexError, AttributeError):
            return False
    
    @staticmethod
    def get_validation_report(email: str) -> dict:
        """
        Get comprehensive validation report for an email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Dictionary with validation results:
            {
                "is_valid": bool,
                "is_disposable": bool,
                "is_corporate": bool,
                "format_error": str | None,
                "recommendations": list[str]
            }
        """
        is_valid, format_error = EmailValidator.is_valid_format(email)
        is_disposable = EmailValidator.is_disposable_email(email)
        is_corporate = EmailValidator.is_corporate_email(email)
        
        recommendations = []
        
        if not is_valid and format_error:
            recommendations.append(format_error)
        
        if is_disposable:
            recommendations.append("Email address appears to be from a temporary service. Please use a permanent email.")
        
        if not is_corporate and is_valid:
            recommendations.append("Consider using a corporate/organization email for verification purposes.")
        
        report = {
            "is_valid": is_valid,
            "is_disposable": is_disposable,
            "is_corporate": is_corporate,
            "format_error": format_error,
            "recommendations": recommendations
        }
        
        logger.info(f"Email validation report for {email.split('@')[0]}@***: {report}")
        
        return report
    
    @staticmethod
    def validate_for_registration(email: str, strict: bool = True) -> Tuple[bool, str | None]:
        """
        Validate email for user registration with configurable strictness.
        
        Args:
            email: Email address to validate
            strict: If True, reject disposable emails. If False, only check format.
            
        Returns:
            Tuple of (is_valid: bool, error_message: str | None)
        """
        # Always check format
        is_valid, format_error = EmailValidator.is_valid_format(email)
        if not is_valid:
            return False, f"Invalid email format: {format_error}"
        
        # In strict mode, reject disposable emails
        if strict and EmailValidator.is_disposable_email(email):
            return False, "Disposable email addresses are not allowed. Please use a permanent email."
        
        logger.info(f"Email {email.split('@')[0]}@*** validated for registration (strict={strict})")
        
        return True, None
