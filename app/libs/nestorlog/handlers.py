import sys
import os
from abc import ABC, abstractmethod
from .models import SessionLogPackage
from .config import config


class LogHandler(ABC):
    @abstractmethod
    async def send(self, package: SessionLogPackage):
        pass


class StdoutHandler(LogHandler):
    async def send(self, package: SessionLogPackage):
        try:
            print(package.to_json(), flush=True)
        except Exception as e:
            print(f"[NestorLog] Error writing to stdout: {e}", file=sys.stderr)


class FileHandler(LogHandler):
    def __init__(self, file_path: str):
        self.file_path = file_path
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        except Exception as e:
            print(f"[NestorLog] Failed to create log directory: {e}", file=sys.stderr)

    async def send(self, package: SessionLogPackage):
        try:
            with open(self.file_path, 'a', encoding='utf-8') as f:
                f.write(package.to_json() + '\n')
        except Exception as e:
            print(f"[NestorLog] Error writing to file {self.file_path}: {e}", file=sys.stderr)


class SynoraHandler(LogHandler):
    async def send(self, package: SessionLogPackage):
        try:
            print(f"[NestorLog] Synora handler would send: {package.to_json()[:200]}...", file=sys.stderr)
        except Exception as e:
            print(f"[NestorLog] Error in Synora handler: {e}", file=sys.stderr)


def get_handler() -> LogHandler:
    try:
        if config.handler == "file":
            if not config.file_path:
                raise ValueError("NLOG_FILE_PATH must be set for file handler")
            return FileHandler(config.file_path)
        elif config.handler == "synora":
            return SynoraHandler()
        else:
            return StdoutHandler()
    except Exception as e:
        print(f"[NestorLog] Failed to create handler: {e}, falling back to stdout", file=sys.stderr)
        return StdoutHandler()