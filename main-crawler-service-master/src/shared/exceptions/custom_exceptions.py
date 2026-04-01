"""
Custom exceptions for the application
"""


class CrawlerBaseException(Exception):
    """Base exception for all crawler-related errors"""
    pass


class ValidationError(CrawlerBaseException):
    """Raised when validation fails"""
    pass


class BusinessRuleError(CrawlerBaseException):
    """Raised when a business rule is violated"""
    pass


class DatabaseError(CrawlerBaseException):
    """Raised when a database operation fails"""
    pass


class ExternalServiceError(CrawlerBaseException):
    """Raised when an external service call fails"""
    pass


class IQAirError(ExternalServiceError):
    """Raised when IQAir service fails"""
    pass


class BrowserError(CrawlerBaseException):
    """Raised when browser automation fails"""
    pass

