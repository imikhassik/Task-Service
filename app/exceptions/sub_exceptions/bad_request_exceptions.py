from app.exceptions.main_exceptions import BadRequestException


class EntityExistsException(BadRequestException):
    def __init__(self):
        super().__init__(code="ENTITY_EXISTS", message="Entity is not unique.")
