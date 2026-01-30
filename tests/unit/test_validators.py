"""Unit tests for config validators.

Tests semantic version validation with v-prefix handling.
Focus: conformance to semver format, error handling for invalid versions.
"""

import pytest

from agent_will_smith.core.config.validators import validate_semver_with_v_prefix


class TestValidateSemverWithVPrefix:
    """Tests for validate_semver_with_v_prefix() validator."""

    def test_version_with_v_prefix_strips_prefix(self):
        """'v1.0.0' should be valid and return 'v1.0.0' (passes through)."""
        result = validate_semver_with_v_prefix("v1.0.0")
        # Note: function returns original string, validation just checks validity
        assert result == "v1.0.0"

    def test_version_without_prefix_valid(self):
        """'1.0.0' should be valid and return '1.0.0'."""
        result = validate_semver_with_v_prefix("1.0.0")
        assert result == "1.0.0"

    def test_version_with_prerelease_valid(self):
        """'v0.1.0-beta' should be valid (semver with prerelease)."""
        result = validate_semver_with_v_prefix("v0.1.0-beta")
        assert result == "v0.1.0-beta"

    def test_version_with_build_metadata_valid(self):
        """'v1.2.3+build.456' should be valid (semver with build metadata)."""
        result = validate_semver_with_v_prefix("v1.2.3+build.456")
        assert result == "v1.2.3+build.456"

    def test_invalid_version_raises_error(self):
        """'invalid' should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("invalid")
        assert "Invalid" in str(exc_info.value)

    def test_incomplete_version_raises_error(self):
        """'v1.2' should raise ValueError (incomplete semver)."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("v1.2")
        assert "Invalid" in str(exc_info.value)

    def test_empty_string_raises_error(self):
        """'' (empty) should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("")
        assert "Invalid" in str(exc_info.value)

    def test_v_only_raises_error(self):
        """'v' alone should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("v")
        assert "Invalid" in str(exc_info.value)

    def test_custom_field_name_in_error_message(self):
        """Error message should include custom field_name."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("invalid", field_name="application version")
        assert "application version" in str(exc_info.value)

    def test_default_field_name_in_error_message(self):
        """Error message should include default field_name 'semantic version'."""
        with pytest.raises(ValueError) as exc_info:
            validate_semver_with_v_prefix("invalid")
        assert "semantic version" in str(exc_info.value)

    def test_major_only_raises_error(self):
        """'1' should raise ValueError (not valid semver)."""
        with pytest.raises(ValueError):
            validate_semver_with_v_prefix("1")

    def test_zero_version_valid(self):
        """'0.0.0' should be valid."""
        result = validate_semver_with_v_prefix("0.0.0")
        assert result == "0.0.0"
