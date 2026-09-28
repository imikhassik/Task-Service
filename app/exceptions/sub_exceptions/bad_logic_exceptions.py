from app.exceptions.main_exceptions import BadLogicException


class InvalidStatusUpdateException(BadLogicException):
    def __init__(self):
        super().__init__(message="Current status cannot be changed to the requested status.")
