from abc import ABC, abstractmethod

from cipug.service import Service
from cipug.tools import Tool
from cipug.typing import Success


class ContainerTool(Tool, ABC):

    @abstractmethod
    def start(self, svc: Service) -> Success:
        ...

    @abstractmethod
    def stop(self, svc: Service) -> Success:
        ...

    @abstractmethod
    def pull(self, svc: Service) -> Success:
        ...

    def restart(self, svc: Service) -> Success:
        return self.stop(svc) and self.start(svc)
