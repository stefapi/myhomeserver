from myeasyserver.backend import config
from myeasyserver.core.root_logger import get_logger


class BaseService:
    def __init__(self) -> None:
        self.settings = config
        self.logger = get_logger()
