"""
Security tests for file upload handling.

Tests for:
- File size limits (prevent DoS)
- Path traversal prevention (prevent arbitrary file writes)
- File type validation
- Malicious file name handling
"""

import pytest
import os
from io import BytesIO
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile


@pytest.fixture
def test_app():
    """Create test app with temporary upload directory."""
    from src.main import app
    from src.core.config import settings
    
    # Save original upload dir
    original_upload_dir = settings.UPLOAD_DIR
    
    # Use temporary directory for tests
    with tempfile.TemporaryDirectory() as temp_dir:
        settings.UPLOAD_DIR = Path(temp_dir)
        yield app
        # Restore original
        settings.UPLOAD_DIR = original_upload_dir


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


# ========== SIZE LIMIT TESTS ==========

def test_single_file_exceeds_max_size_rejected(client):
    """Test that files exceeding MAX_FILE_SIZE_BYTES are rejected."""
    from src.core.config import settings
    
    # Create a file that exceeds max size
    oversized_content = b"x" * (settings.MAX_FILE_SIZE_BYTES + 1)
    
    files = {
        "files": (
            "oversized.txt",
            BytesIO(oversized_content),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 413  # Payload Too Large
    assert "exceeds max size" in response.json()["detail"]


def test_total_upload_size_exceeds_limit_rejected(client):
    """Test that total upload size exceeding limit is rejected."""
    from src.core.config import settings
    
    # Create multiple files that together exceed total limit
    # Each file is within limit but total exceeds MAX_TOTAL_UPLOAD_SIZE_BYTES
    file_size = settings.MAX_FILE_SIZE_BYTES // 2 + 1
    
    files_list = []
    for i in range(6):  # 6 * half-max = 3x the total limit
        files_list.append(
            ("files", (f"file{i}.txt", BytesIO(b"x" * file_size), "text/plain"))
        )
    
    response = client.post("/upload", files=files_list)
    
    assert response.status_code == 413  # Payload Too Large
    assert "Total upload size exceeds" in response.json()["detail"]


# ========== PATH TRAVERSAL TESTS ==========

def test_path_traversal_with_parent_dir_blocked(client, test_app):
    """Test that path traversal using ../ is blocked."""
    from src.core.config import settings
    
    files = {
        "files": (
            "../../../etc/passwd",  # Malicious path traversal attempt
            BytesIO(b"malicious content"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    # Should be rejected
    assert response.status_code == 400
    assert "path traversal" in response.json()["detail"].lower()
    
    # Verify file was NOT created in parent directories
    parent_path = test_app.__dict__.get('settings', settings).UPLOAD_DIR.parent / "etc"
    if parent_path.exists():
        assert not (parent_path / "passwd").exists()


def test_path_traversal_with_backslash_blocked(client):
    """Test that Windows-style path traversal is blocked."""
    files = {
        "files": (
            "..\\..\\..\\windows\\system32\\config",
            BytesIO(b"malicious"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    # Should be rejected or sanitized
    assert response.status_code in [400, 413] or "invalid filename" in response.json().get("detail", "").lower()


def test_absolute_path_blocked(client):
    """Test that absolute paths are blocked."""
    files = {
        "files": (
            "/etc/passwd",  # Absolute path
            BytesIO(b"content"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "invalid filename" in response.json()["detail"].lower()


# ========== FILE TYPE VALIDATION TESTS ==========

def test_invalid_file_type_rejected(client):
    """Test that non-PDF/TXT files are rejected."""
    invalid_types = ["file.exe", "file.jpg", "file.sh", "file.py", "file.zip"]
    
    for filename in invalid_types:
        files = {
            "files": (
                filename,
                BytesIO(b"content"),
                "application/octet-stream"
            )
        }
        
        response = client.post("/upload", files=files)
        
        assert response.status_code == 400
        assert "Only .pdf and .txt allowed" in response.json()["detail"]


def test_valid_file_types_accepted(client):
    """Test that PDF and TXT files are accepted (when size is OK)."""
    valid_files = ["document.pdf", "notes.txt", "data.TXT", "report.PDF"]
    
    for filename in valid_files:
        files = {
            "files": (
                filename,
                BytesIO(b"Valid content for testing"),
                "text/plain" if filename.endswith(".txt") else "application/pdf"
            )
        }
        
        response = client.post("/upload", files=files)
        
        # Should succeed (not 400 for file type)
        assert response.status_code != 400 or "Only .pdf and .txt" not in response.json().get("detail", "")


# ========== FILENAME SANITIZATION TESTS ==========

def test_filename_with_null_bytes_blocked(client):
    """Test that filenames with null bytes are rejected."""
    files = {
        "files": (
            "innocent.txt\x00.exe",  # Null byte injection
            BytesIO(b"content"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    # Should be rejected
    assert response.status_code in [400, 413]


def test_filename_with_special_chars_sanitized(client):
    """Test that filenames with special characters are handled safely."""
    special_filenames = [
        "file name with spaces.txt",
        "file-with-dashes.txt",
        "file_with_underscores.txt",
        "file.multiple.dots.txt",
    ]
    
    for filename in special_filenames:
        files = {
            "files": (
                filename,
                BytesIO(b"Valid content"),
                "text/plain"
            )
        }
        
        response = client.post("/upload", files=files)
        
        # Should be accepted (these are safe)
        assert response.status_code == 200


def test_empty_filename_rejected(client):
    """Test that empty filenames are rejected."""
    files = {
        "files": (
            "",  # Empty filename
            BytesIO(b"content"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code in [400, 422]  # Bad request or unprocessable


# ========== EDGE CASES ==========

def test_empty_file_accepted(client):
    """Test that empty files are accepted (valid edge case)."""
    files = {
        "files": (
            "empty.txt",
            BytesIO(b""),  # Empty file
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    # Should succeed (empty files are valid)
    assert response.status_code == 200


def test_filename_with_dots_only_rejected(client):
    """Test that filenames that are only dots are rejected."""
    dot_filenames = [".", "..", "..."]
    
    for filename in dot_filenames:
        files = {
            "files": (
                filename,
                BytesIO(b"content"),
                "text/plain"
            )
        }
        
        response = client.post("/upload", files=files)
        
        # Should be rejected
        assert response.status_code == 400


# ========== INTEGRATION TESTS ==========

def test_multiple_files_one_invalid_rejects_all(client):
    """Test that if one file is invalid, the entire request is rejected."""
    files_list = [
        ("files", ("valid1.txt", BytesIO(b"content1"), "text/plain")),
        ("files", ("invalid.exe", BytesIO(b"malicious"), "application/octet-stream")),
        ("files", ("valid2.txt", BytesIO(b"content2"), "text/plain")),
    ]
    
    response = client.post("/upload", files=files_list)
    
    # Should reject the entire request
    assert response.status_code == 400
    assert "Only .pdf and .txt allowed" in response.json()["detail"]


def test_successful_upload_creates_file_in_upload_dir(client, test_app):
    """Test that successful uploads create files in the upload directory."""
    from src.core.config import settings
    
    files = {
        "files": (
            "test_document.txt",
            BytesIO(b"Test content"),
            "text/plain"
        )
    }
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    
    # Verify file was created
    uploaded_file_path = settings.UPLOAD_DIR / "test_document.txt"
    assert uploaded_file_path.exists()
    assert uploaded_file_path.read_text() == "Test content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
