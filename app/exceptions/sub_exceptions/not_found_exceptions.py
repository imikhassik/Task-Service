from ..main_exceptions import NotFoundException


class ProfilesNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(message="Profiles not found.")


class RegistryObjectDeactivatedException(NotFoundException):
    def __init__(self):
        super().__init__(message="The record has been deleted.")


class ProcessNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(message="Process not found.")


class TaskNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(message="Task not found.")


class TasksNotFoundException(NotFoundException):
    def __init__(self):
        super().__init__(message="Tasks not found.")
        
