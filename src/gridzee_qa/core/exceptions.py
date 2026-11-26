"""Custom errors raised by the framework."""


class FrameworkError(Exception):
    """Base class for all framework errors."""


class ConfigError(FrameworkError):
    """Configuration is missing, malformed or refers to an unknown value."""


class WaitTimeoutError(FrameworkError):
    """A condition did not become true within its time limit."""
