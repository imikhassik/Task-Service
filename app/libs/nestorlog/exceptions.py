class NestorLogError(Exception):
    pass


class ConfigurationError(NestorLogError):
    pass


class HandlerError(NestorLogError):
    pass