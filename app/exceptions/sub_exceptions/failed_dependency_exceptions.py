from app.exceptions.main_exceptions import FailedDependencyException


class RegistryInteractionException(FailedDependencyException):
    def __init__(self, registry_error: str = None):
        super().__init__(code="REGISTRY_ERROR", message="The registry sevice has returned an error: " + registry_error)


class IncorrectFormatInRegistryException(FailedDependencyException):
    def __init__(self):
        super().__init__(code="REGISTRY_ERROR", message="Error during registry interaction.")


class IncorrectFormatInServiceException(FailedDependencyException):
    def __init__(self):
        super().__init__(code="SERVICE_ERROR", message="Error during external service interaction.")


class ServiceInteractionException(FailedDependencyException):
    def __init__(self, service_error: str = None):
        super().__init__(code="SERVICE_ERROR", message="The service has returned an error: " + service_error)


class FailedLinkingException(FailedDependencyException):
    def __init__(self, link_type: str = None):
        super().__init__(code="FAILED_LINKING", message=f'Error creating {link_type} link.')