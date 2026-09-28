from ..main_exceptions import InternalException


class InvalidMethodException(InternalException):
    def __init__(self):
        super().__init__(message="Method is not supported.")

class DebugModeNotFoundException(Exception):
    def __init__(self, message="Specify DEBUG_MODE in AUTH."):
        super().__init__(message)
