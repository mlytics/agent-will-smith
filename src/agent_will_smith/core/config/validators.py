"""Shared validators for configuration fields.

Reusable validation functions and types to avoid duplication across config classes.
"""

from typing import Annotated

from pydantic import BeforeValidator
from semver import Version


def validate_semver_with_v_prefix(version: str, field_name: str = "semantic version") -> str:
    """Validate semantic version, accepting optional 'v' prefix.
    
    Strips 'v' prefix if present (team convention) and validates as semver.
    
    Can be used in two ways:
    1. With @field_validator for explicit error messages with field name
    2. Via the SemVer type annotation for simpler usage
    
    Args:
        version: Version string (e.g., "v0.1.0" or "0.1.0")
        field_name: Name of field being validated (for error messages)
    
    Returns:
        Clean version string without 'v' prefix (e.g., "0.1.0")
    
    Raises:
        ValueError: If version is not valid semantic versioning
    
    Examples:
        >>> validate_semver_with_v_prefix("v0.1.0")
        "0.1.0"
        >>> validate_semver_with_v_prefix("0.1.0", "application version")
        "0.1.0"
        >>> validate_semver_with_v_prefix("invalid", "agent version")
        ValueError: Invalid agent version: invalid
    """
    if not Version.is_valid(version.lstrip("v")):
        raise ValueError(f"Invalid {field_name}: {version}")
    
    return version


# Reusable type annotation for semantic version fields
# Usage: field_name: SemVer = Field(..., description="...")
SemVer = Annotated[str, BeforeValidator(lambda v: validate_semver_with_v_prefix(v))]
