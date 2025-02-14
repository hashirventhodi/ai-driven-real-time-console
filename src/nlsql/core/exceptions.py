class NLSQLException(Exception):
    """Base exception for all NLSQL errors."""
    pass

class SchemaError(NLSQLException):
    """Raised when there are issues with database schema."""
    pass

class QueryGenerationError(NLSQLException):
    """Raised when query generation fails."""
    pass

class ValidationError(NLSQLException):
    """Raised when query validation fails."""
    pass

class SecurityError(NLSQLException):
    """Raised when security checks fail."""
    pass