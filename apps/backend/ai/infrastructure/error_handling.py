"""Error Handling — retry, fallback, and graceful degradation strategies.

Strategy Pattern: Different error handling strategies for different failure types.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

from shared.infrastructure.config.app_config import (
    LLM_RETRY_MAX_ATTEMPTS,
    LLM_RETRY_BASE_DELAY,
    LLM_RETRY_MAX_DELAY,
)


class ErrorType(str, Enum):
    """Types of errors that can occur in AI processing."""
    PROVIDER_TIMEOUT = "provider_timeout"
    RATE_LIMIT = "rate_limit"
    INVALID_OUTPUT = "invalid_output"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    QUOTA_EXCEEDED = "quota_exceeded"
    UNKNOWN = "unknown"


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIError:
    """Structured error information."""
    error_type: ErrorType
    message: str
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    retryable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_exception(cls, exc: Exception) -> AIError:
        """Create an AIError from an exception."""
        error_type = ErrorType.UNKNOWN
        retryable = True
        severity = ErrorSeverity.MEDIUM

        error_msg = str(exc).lower()

        if "timeout" in error_msg:
            error_type = ErrorType.PROVIDER_TIMEOUT
            retryable = True
        elif "rate" in error_msg or "limit" in error_msg:
            error_type = ErrorType.RATE_LIMIT
            retryable = True
        elif "auth" in error_msg or "key" in error_msg:
            error_type = ErrorType.AUTHENTICATION_ERROR
            retryable = False
            severity = ErrorSeverity.HIGH
        elif "quota" in error_msg:
            error_type = ErrorType.QUOTA_EXCEEDED
            retryable = False
            severity = ErrorSeverity.CRITICAL
        elif "json" in error_msg or "parse" in error_msg:
            error_type = ErrorType.INVALID_OUTPUT
            retryable = True

        return cls(
            error_type=error_type,
            message=str(exc),
            severity=severity,
            retryable=retryable,
        )


class RetryStrategy:
    """Retry strategy with exponential backoff."""

    def __init__(
        self,
        max_retries: int = LLM_RETRY_MAX_ATTEMPTS,
        base_delay: float = LLM_RETRY_BASE_DELAY,
        max_delay: float = LLM_RETRY_MAX_DELAY,
        exponential_base: float = 2.0,
    ):
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._exponential_base = exponential_base

    def execute(
        self,
        fn: Callable,
        *args,
        retryable_errors: Optional[list[ErrorType]] = None,
        **kwargs,
    ) -> Any:
        """Execute a function with retry logic.

        Args:
            fn: Function to execute.
            *args: Positional arguments.
            retryable_errors: List of error types that should trigger retry.
            **kwargs: Keyword arguments.

        Returns:
            Result of the function.

        Raises:
            Last exception if all retries fail.
        """
        if retryable_errors is None:
            retryable_errors = [
                ErrorType.PROVIDER_TIMEOUT,
                ErrorType.RATE_LIMIT,
                ErrorType.NETWORK_ERROR,
            ]

        last_error = None

        for attempt in range(self._max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                ai_error = AIError.from_exception(e)

                if not ai_error.retryable or ai_error.error_type not in retryable_errors:
                    raise

                if attempt < self._max_retries:
                    delay = min(
                        self._base_delay * (self._exponential_base ** attempt),
                        self._max_delay,
                    )
                    time.sleep(delay)

        raise last_error


class FallbackStrategy:
    """Fallback strategy with provider failover."""

    def __init__(self, providers: list[Any]):
        self._providers = providers
        self._current_index = 0

    def execute(
        self,
        fn: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Execute with fallback to next provider on failure.

        Args:
            fn: Function to execute (should accept provider as first arg).
            *args: Additional positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            Result from the first successful provider.

        Raises:
            Last exception if all providers fail.
        """
        last_error = None

        for i, provider in enumerate(self._providers):
            try:
                return fn(provider, *args, **kwargs)
            except Exception as e:
                last_error = e
                # Move to next provider
                self._current_index = (i + 1) % len(self._providers)

        raise last_error


class GracefulDegradation:
    """Graceful degradation strategy for partial failures."""

    def __init__(self, fallback_value: Any = None):
        self._fallback_value = fallback_value

    def execute(
        self,
        fn: Callable,
        *args,
        fallback_value: Any = None,
        **kwargs,
    ) -> Any:
        """Execute with graceful degradation on failure.

        Args:
            fn: Function to execute.
            *args: Positional arguments.
            fallback_value: Value to return on failure.
            **kwargs: Keyword arguments.

        Returns:
            Result of the function or fallback value.
        """
        try:
            return fn(*args, **kwargs)
        except Exception:
            return fallback_value if fallback_value is not None else self._fallback_value
