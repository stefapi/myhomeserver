
import abc
from datetime import timedelta
from typing import Generic, TypeVar

from sqlalchemy.orm.session import Session

from ..security import get_access_token
from ...database.repositories.all_repositories import get_repositories
from ...schema.user import UserModel

T = TypeVar("T")


class AuthProvider(Generic[T], metaclass=abc.ABCMeta):
    """Base Authentication Provider interface"""

    def __init__(self, session: Session, data: T) -> None:
        self.session = session
        self.data = data
        self.user: UserModel | None = None
        self.__has_tried_user = False

    @classmethod
    def __subclasshook__(cls, __subclass: type) -> bool:
        return hasattr(__subclass, "authenticate") and callable(__subclass.authenticate)

    def get_access_token(self, remember_me=False) -> tuple[str, timedelta]:
        return get_access_token(self.user.id, remember_me)

    def try_get_user(self, username: str) -> UserModel | None:
        """Try to get a user from the database, first trying username, then trying email"""
        if self.__has_tried_user:
            return self.user

        db = get_repositories(self.session)

        user = db.users.get_one(username, "username", any_case=True)
        if not user:
            user = db.users.get_one(username, "email", any_case=True)

        self.user = user
        return user

    @abc.abstractmethod
    async def authenticate(self) -> tuple[str, timedelta] | None:
        """Attempt to authenticate a user"""
        raise NotImplementedError
