"""
Tests for email validation service (Phase 3.2).
Testing feature: Enhanced email validation with disposable email detection.
"""
import pytest
from src.services.email_validation_service import EmailValidator


class TestEmailFormatValidation:
    """Tests for basic email format validation."""
    
    def test_valid_email_formats(self):
        """Test various valid email formats."""
        valid_emails = [
            "user@example.com",
            "test.user@example.com",
            "test+tag@example.co.uk",
            "user123@test-domain.org",
            "a@b.co"
        ]
        for email in valid_emails:
            is_valid, error = EmailValidator.is_valid_format(email)
            assert is_valid, f"Email {email} should be valid but got error: {error}"
    
    def test_invalid_email_formats(self):
        """Test various invalid email formats."""
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user@.com",
            "user @example.com",
            "user@example",
            "",
            "user@@example.com",
            "user@example..com"
        ]
        for email in invalid_emails:
            is_valid, error = EmailValidator.is_valid_format(email)
            assert not is_valid, f"Email {email} should be invalid"
            assert error is not None
    
    def test_email_with_special_characters(self):
        """Test emails with special characters."""
        special_char_emails = [
            "user+tag@example.com",
            "first.last@example.com",
            "user_name@example.com",
            "user-name@example.com"
        ]
        for email in special_char_emails:
            is_valid, error = EmailValidator.is_valid_format(email)
            assert is_valid, f"Email {email} should be valid"


class TestDisposableEmailDetection:
    """Tests for disposable email service detection."""
    
    def test_recognizes_disposable_emails(self):
        """Test that common disposable email services are detected."""
        disposable_emails = [
            "user@tempmail.com",
            "test@10minutemail.com",
            "temp@guerrillamail.com",
            "fake@mailinator.com",
            "trash@throwaway.email",
            "junk@temp-mail.io"
        ]
        for email in disposable_emails:
            assert EmailValidator.is_disposable_email(email), \
                f"Email {email} should be detected as disposable"
    
    def test_recognizes_legitimate_emails(self):
        """Test that legitimate emails are not flagged as disposable."""
        legitimate_emails = [
            "user@gmail.com",
            "user@yahoo.com",
            "user@company.com",
            "user@university.edu",
            "user@example.org"
        ]
        for email in legitimate_emails:
            assert not EmailValidator.is_disposable_email(email), \
                f"Email {email} should not be detected as disposable"
    
    def test_case_insensitive_disposable_detection(self):
        """Test that disposable detection is case-insensitive."""
        email_variants = [
            "user@TempMail.com",
            "user@TEMPMAIL.COM",
            "user@Tempmail.COM"
        ]
        for email in email_variants:
            assert EmailValidator.is_disposable_email(email), \
                f"Email {email} should be detected as disposable (case-insensitive)"


class TestCorporateEmailDetection:
    """Tests for corporate email domain detection."""
    
    def test_public_email_providers(self):
        """Test detection of public email providers."""
        public_emails = [
            "user@gmail.com",
            "user@yahoo.com",
            "user@hotmail.com",
            "user@outlook.com",
            "user@protonmail.com"
        ]
        for email in public_emails:
            assert not EmailValidator.is_corporate_email(email), \
                f"Email {email} should not be detected as corporate"
    
    def test_corporate_domains(self):
        """Test detection of corporate domain emails."""
        corporate_emails = [
            "user@company.com",
            "user@tech-startup.io",
            "user@university.edu",
            "user@research-lab.org",
            "user@enterprise.co.uk"
        ]
        for email in corporate_emails:
            assert EmailValidator.is_corporate_email(email), \
                f"Email {email} should be detected as corporate"


class TestValidationReport:
    """Tests for comprehensive validation reports."""
    
    def test_validation_report_valid_email(self):
        """Test report for a valid corporate email."""
        report = EmailValidator.get_validation_report("user@company.com")
        assert report["is_valid"] is True
        assert report["is_disposable"] is False
        assert report["is_corporate"] is True
        assert report["format_error"] is None
    
    def test_validation_report_disposable_email(self):
        """Test report for a disposable email."""
        report = EmailValidator.get_validation_report("user@tempmail.com")
        assert report["is_valid"] is True
        assert report["is_disposable"] is True
        assert "temporary service" in report["recommendations"][0].lower()
    
    def test_validation_report_invalid_email(self):
        """Test report for an invalid email."""
        report = EmailValidator.get_validation_report("invalid-email")
        assert report["is_valid"] is False
        assert report["format_error"] is not None
        assert len(report["recommendations"]) > 0
    
    def test_validation_report_public_email(self):
        """Test report for a public email provider."""
        report = EmailValidator.get_validation_report("user@gmail.com")
        assert report["is_valid"] is True
        assert report["is_disposable"] is False
        assert report["is_corporate"] is False


class TestRegistrationValidation:
    """Tests for registration-specific validation."""
    
    def test_register_valid_corporate_email(self):
        """Test registration with valid corporate email."""
        is_valid, error = EmailValidator.validate_for_registration(
            "user@company.com",
            strict=True
        )
        assert is_valid is True
        assert error is None
    
    def test_register_disposable_email_strict(self):
        """Test registration rejects disposable emails in strict mode."""
        is_valid, error = EmailValidator.validate_for_registration(
            "user@tempmail.com",
            strict=True
        )
        assert is_valid is False
        assert "disposable" in error.lower()
    
    def test_register_disposable_email_lenient(self):
        """Test registration accepts disposable emails in lenient mode."""
        is_valid, error = EmailValidator.validate_for_registration(
            "user@tempmail.com",
            strict=False
        )
        assert is_valid is True
        assert error is None
    
    def test_register_invalid_email_strict(self):
        """Test registration rejects invalid emails in strict mode."""
        is_valid, error = EmailValidator.validate_for_registration(
            "invalid-email",
            strict=True
        )
        assert is_valid is False
        assert "invalid" in error.lower()
    
    def test_register_invalid_email_lenient(self):
        """Test registration still rejects invalid emails in lenient mode."""
        is_valid, error = EmailValidator.validate_for_registration(
            "invalid-email",
            strict=False
        )
        assert is_valid is False
        assert error is not None
    
    def test_register_public_email_strict(self):
        """Test registration accepts public email providers in strict mode."""
        is_valid, error = EmailValidator.validate_for_registration(
            "user@gmail.com",
            strict=True
        )
        assert is_valid is True
        assert error is None


class TestEmailEdgeCases:
    """Tests for email validation edge cases."""
    
    def test_empty_string(self):
        """Test empty string email."""
        is_valid, error = EmailValidator.is_valid_format("")
        assert is_valid is False
    
    def test_whitespace_email(self):
        """Test email with whitespace."""
        is_valid, error = EmailValidator.is_valid_format("  user@example.com  ")
        # Depending on implementation, may trim or reject
        # Should handle gracefully
        assert isinstance(is_valid, bool)
    
    def test_very_long_email(self):
        """Test very long email address."""
        long_email = "a" * 200 + "@example.com"
        is_valid, error = EmailValidator.is_valid_format(long_email)
        # Should either accept or reject gracefully
        assert isinstance(is_valid, bool)
    
    def test_unicode_email(self):
        """Test email with unicode characters."""
        # Most email validators don't accept unicode in local part
        unicode_email = "üser@example.com"
        is_valid, error = EmailValidator.is_valid_format(unicode_email)
        assert isinstance(is_valid, bool)
    
    def test_plus_addressing(self):
        """Test email with plus addressing (Gmail feature)."""
        plus_email = "user+filter@gmail.com"
        is_valid, error = EmailValidator.is_valid_format(plus_email)
        assert is_valid is True
    
    def test_subdomain_email(self):
        """Test email with subdomain."""
        subdomain_email = "user@mail.example.com"
        is_valid, error = EmailValidator.is_valid_format(subdomain_email)
        assert is_valid is True


class TestDisposableEmailDomains:
    """Tests for comprehensive disposable email domain coverage."""
    
    def test_all_common_disposable_services_detected(self):
        """Test that we detect a variety of disposable services."""
        test_cases = [
            ("test@tempmail.com", True),
            ("test@10minutemail.com", True),
            ("test@mailinator.com", True),
            ("test@guerrillamail.com", True),
            ("test@fake-mail.net", True),
            ("test@trashmail.com", True),
            ("test@example.com", False),
            ("test@gmail.com", False),
            ("test@corporate.com", False),
        ]
        for email, should_be_disposable in test_cases:
            result = EmailValidator.is_disposable_email(email)
            assert result == should_be_disposable, \
                f"Email {email} disposable={result}, expected {should_be_disposable}"
