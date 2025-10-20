"""Custom exception classes for the Astro MVP Backend."""

from typing import Optional, Dict, Any


class AstroException(Exception):
    """Base exception for Astro MVP Backend."""
    
    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AstroException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class CalculationError(AstroException):
    """Raised when astronomical calculations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CALCULATION_ERROR",
            status_code=503,
            details=details
        )


class LLMError(AstroException):
    """Raised when LLM operations fail."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="LLM_ERROR",
            status_code=500,
            details=details
        )


class AuthenticationError(AstroException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details
        )


class AuthorizationError(AstroException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class NotFoundError(AstroException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details
        )


class RateLimitError(AstroException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details
        )


# Specific error codes from the spec
class InvalidTimezoneError(ValidationError):
    """Raised when timezone is invalid."""
    
    def __init__(self, timezone: str):
        super().__init__(
            message=f"Invalid timezone: {timezone}",
            details={"timezone": timezone}
        )


class BirthDateOutOfRangeError(ValidationError):
    """Raised when birth date is out of allowed range."""
    
    def __init__(self, year: int, min_year: int = 1900, max_year: int = 2100):
        super().__init__(
            message=f"Birth year {year} is out of range ({min_year}-{max_year})",
            details={"year": year, "min_year": min_year, "max_year": max_year}
        )


class MissingLatLonError(ValidationError):
    """Raised when latitude/longitude are missing."""
    
    def __init__(self):
        super().__init__(
            message="Latitude and longitude are required",
            details={"required_fields": ["lat", "lon"]}
        )


class EphemerisLoadFailedError(CalculationError):
    """Raised when Swiss Ephemeris fails to load."""
    
    def __init__(self, ephemeris_path: str):
        super().__init__(
            message=f"Failed to load ephemeris from {ephemeris_path}",
            details={"ephemeris_path": ephemeris_path}
        )


class LLMJsonParseFailedError(LLMError):
    """Raised when LLM response cannot be parsed as JSON."""
    
    def __init__(self, response_text: str):
        super().__init__(
            message="Failed to parse LLM response as JSON",
            details={"response_preview": response_text[:100] + "..." if len(response_text) > 100 else response_text}
        )


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    
    def __init__(self, timeout_ms: int):
        super().__init__(
            message=f"LLM request timed out after {timeout_ms}ms",
            details={"timeout_ms": timeout_ms}
        )


class InputHashCollisionError(CalculationError):
    """Raised when input hash collision is detected."""
    
    def __init__(self, input_hash: str):
        super().__init__(
            message=f"Input hash collision detected: {input_hash}",
            details={"input_hash": input_hash}
        )

