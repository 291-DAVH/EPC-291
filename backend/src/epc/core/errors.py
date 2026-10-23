"""Domain errors. Services raise these; the API layer turns them into HTTP responses (see epc.main)."""
from typing import Any


class DomainError(Exception):
    status = 400

    def __init__(self, detail: Any = ""):
        super().__init__(str(detail))
        self.detail = detail


class NotFound(DomainError):
    status = 404


class Invalid(DomainError):
    status = 422

    def __init__(self, errors: dict):
        super().__init__({"errors": errors})


class Conflict(DomainError):
    status = 409

    def __init__(self, errors: dict):
        super().__init__({"errors": errors})


class TooLarge(DomainError):
    status = 413

    def __init__(self, errors: dict):
        super().__init__({"errors": errors})


class Unauthorized(DomainError):
    status = 401


class Forbidden(DomainError):
    status = 403


class TooManyRequests(DomainError):
    status = 429


class Failure(DomainError):
    status = 500
