"""Exceptions for iXmanager integration."""


class IXManagerError(Exception):
    """Base exception for iXmanager integration."""


class IXManagerConnectionError(IXManagerError):
    """Exception raised when connection to iXmanager API fails."""


class IXManagerAuthenticationError(IXManagerError):
    """Exception raised when authentication fails."""


class IXManagerTimeoutError(IXManagerError):
    """Exception raised when API request times out."""