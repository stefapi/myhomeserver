from sqlite3 import IntegrityError


class UnexpectedNone(Exception):
    """Exception raised when a value is None when it should not be."""

    def __init__(self, message: str = "Unexpected None Value"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"


class PermissionDenied(Exception):
    """
    This exception is raised when a user tries to access a resource that they do not have permission to access.
    """

    pass


class NoEntryFound(Exception):
    """
    This exception is raised when a user tries to access a resource that does not exist.
    """

    pass


def registered_exceptions() -> dict:
    """
    This function returns a dictionary of all the globally registered exceptions in the myeasyserver application.
    """

    return {
        PermissionDenied: "exceptions.permission-denied",
        NoEntryFound: "exceptions.no-entry-found",
        IntegrityError: "exceptions.integrity-error",
    }


class UserLockedOut(Exception): ...