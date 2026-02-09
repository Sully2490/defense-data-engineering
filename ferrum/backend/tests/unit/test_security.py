import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import get_settings

_settings = get_settings()
SECRET_KEY = _settings.JWT_SECRET_KEY
ALGORITHM = _settings.JWT_ALGORITHM


class TestTokenOperations:
    """Test suite for JWT token operations."""

    def test_create_access_token_returns_valid_jwt(self):
        """Test that create_access_token returns a valid JWT string."""
        data = {"sub": "user123", "email": "test@example.com"}
        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count('.') == 2  # JWT has 3 parts separated by dots

    def test_decode_token_extracts_correct_claims(self):
        """Test that decode_token correctly extracts token claims."""
        test_data = {
            "sub": "user123",
            "email": "test@example.com",
            "org_id": "org456",
            "role": "analyst"
        }
        token = create_access_token(test_data)

        decoded = decode_token(token)

        assert decoded["sub"] == "user123"
        assert decoded["email"] == "test@example.com"
        assert decoded["org_id"] == "org456"
        assert decoded["role"] == "analyst"
        assert "exp" in decoded  # Expiration should be added

    def test_token_contains_expiration(self):
        """Test that created tokens contain an expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data)
        decoded = decode_token(token)

        assert "exp" in decoded
        exp_timestamp = decoded["exp"]
        assert isinstance(exp_timestamp, (int, float))

        # Verify expiration is in the future (use UTC-aware comparison)
        now_utc = datetime.utcnow()
        exp_dt = datetime.utcfromtimestamp(exp_timestamp)
        assert exp_dt > now_utc

    def test_expired_token_raises_error(self):
        """Test that an expired token raises an error when decoded."""
        data = {"sub": "user123", "email": "test@example.com"}

        # Create token that expired 1 hour ago
        expired_time = datetime.utcnow() - timedelta(hours=1)
        token = jwt.encode(
            {**data, "exp": expired_time},
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        with pytest.raises(JWTError):
            decode_token(token)

    def test_invalid_token_raises_error(self):
        """Test that an invalid token raises an error."""
        invalid_token = "invalid.token.string"

        with pytest.raises(JWTError):
            decode_token(invalid_token)

    def test_token_with_custom_expiration(self):
        """Test creating a token with custom expiration time."""
        data = {"sub": "user123"}
        expires_delta = timedelta(minutes=15)

        token = create_access_token(data, expires_delta=expires_delta)
        decoded = decode_token(token)

        exp_time = datetime.utcfromtimestamp(decoded["exp"])
        now = datetime.utcnow()
        time_diff = exp_time - now

        # Should be approximately 15 minutes (allow 1 minute margin)
        assert 14 <= time_diff.total_seconds() / 60 <= 16


class TestPasswordOperations:
    """Test suite for password hashing and verification."""

    def test_hash_password_returns_hashed_string(self):
        """Test that hash_password returns a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash prefix

    def test_verify_password_with_correct_password(self):
        """Test that verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_with_incorrect_password(self):
        """Test that verify_password returns False for incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_same_password_different_hashes(self):
        """Test that hashing the same password twice produces different hashes (due to salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)

    def test_hash_empty_password(self):
        """Test that empty passwords can be hashed."""
        password = ""
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert verify_password(password, hashed)

    def test_hash_special_characters(self):
        """Test that passwords with special characters are handled correctly."""
        password = "p@$$w0rd!#%^&*()"
        hashed = hash_password(password)

        assert verify_password(password, hashed)
        assert not verify_password("p@$$w0rd", hashed)

    def test_hash_unicode_characters(self):
        """Test that passwords with unicode characters work."""
        password = "пароль密码🔒"
        hashed = hash_password(password)

        assert verify_password(password, hashed)
