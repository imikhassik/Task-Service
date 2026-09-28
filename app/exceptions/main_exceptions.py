from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder

from app.schemas.base.response_schemas import ResponseDetail


class ServiceException(HTTPException):
    def __init__(self, status_code: int = 500, code: str = None, message: str = None):
        self.status_code = status_code
        self._detail = ResponseDetail(code=code, message=message)
        super().__init__(status_code=self.status_code, detail=jsonable_encoder(self._detail))


class InternalException(ServiceException):
    def __init__(self, code="INTERNAL_SERVER_ERROR", message="Internal error of the server component"):
        super().__init__(code=code, message=message)


class BadRequestException(ServiceException):
    def __init__(self, code="BAD_REQUEST", message="Format error"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, code=code, message=message)


class ForbiddenException(ServiceException):
    def __init__(self, code="FORBIDDEN", message="Access forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, code=code, message=message)


class NotFoundException(ServiceException):
    def __init__(self, code="NOT_FOUND", message="Entity not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, code=code, message=message)


class FailedValidationException(ServiceException):
    def __init__(self, code="FAILED_VALIDATION", message="Logical error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code=code, message=message)


class NotAcceptableException(ServiceException):
    def __init__(self, code="NOT_ACCEPTABLE", message="Data packet integrity control error"):
        super().__init__(status_code=status.HTTP_406_NOT_ACCEPTABLE, code=code, message=message)


class FailedDependencyException(ServiceException):
    def __init__(self, code="FAILED_DEPENDENCY", message="Dependent component interaction error"):
        super().__init__(status_code=status.HTTP_424_FAILED_DEPENDENCY, code=code, message=message)


class NotImplementedException(ServiceException):
    def __init__(self, code="NOT_IMPLEMENTED", message="Functionality not implemented"):
        super().__init__(status_code=status.HTTP_501_NOT_IMPLEMENTED, code=code, message=message)


class BadLogicException(ServiceException):
    def __init__(self, code="FAILED_VALIDATION", message="Logical error"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code=code, message=message)


class AlreadyExistsException(ServiceException):
    def __init__(self, code="ALREADY_EXISTS", message="Entity already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, code=code, message=message)


class DeletedException(ServiceException):
    def __init__(self, code="DELETED", message="Entity deleted"):
        super().__init__(status_code=status.HTTP_204_NO_CONTENT, code=code, message=message)


