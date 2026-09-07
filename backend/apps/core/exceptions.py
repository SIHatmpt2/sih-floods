class CoreError(Exception):
    """Base exception for Core application failures."""


class InvalidCoordinatesError(CoreError):
    """Raised when coordinates are outside valid geographic bounds."""


class DashboardUnavailableError(CoreError):
    """Raised when the dashboard cannot be assembled."""
