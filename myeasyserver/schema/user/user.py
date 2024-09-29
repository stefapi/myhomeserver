from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated, Any, Generic, TypeVar
from uuid import UUID

from pydantic import UUID4, ConfigDict, Field, StringConstraints, field_validator
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.interfaces import LoaderOption

from ..basic_model import BasicModel
from ..group import ReadGroupPreferences
from ..server import ReadWebhook, CreateWebhook
from ...backend.config import config
from ...database.models.group import Group
from ...database.models.users import AuthMethod, User

DEFAULT_INTEGRATION_ID = "generic"


# define model for objects received from the API

class ChangePassword(BasicModel):
    current_password: str = ""
    new_password: str = Field(..., min_length=8)

class GroupBase(BasicModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]  # type: ignore
    model_config = ConfigDict(from_attributes=True)


class UserKeyIn(BasicModel):
    """
    Defines the structure of a user key when creating it from the API
    """
    name: str
    integration_id: str = DEFAULT_INTEGRATION_ID

class Createkey(UserKeyIn):
    """
    Defines the structure of a user key when creating it in database
    """
    user_id: UUID4
    key: str
    model_config = ConfigDict(from_attributes=True)

class UserBase(BasicModel):
    id: UUID4 | None = None
    username: str | None = None
    full_name: str | None = None
    email: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)]  # type: ignore
    auth_method: AuthMethod = AuthMethod.INTERNAL
    admin: bool = False
    group: str | None = None
    advanced: bool = False

    can_invite: bool = False
    can_manage: bool = False
    can_organize: bool = False
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "username": "ChangeMe",
                "email": "changeme@example.com",
                "group": config['application.default_group'],
                "admin": "false",
            }
        },
    )

    @field_validator("group", mode="before")
    def convert_group_to_name(cls, v):
        if not v or isinstance(v, str):
            return v

        try:
            return v.name
        except AttributeError:
            return v


class UserIn(UserBase):
    password: str

class UserSummary(BasicModel):
    id: UUID4
    full_name: str
    model_config = ConfigDict(from_attributes=True)

class  UserModel(UserBase):
    password: str
    group_id: UUID4
    keys: list[Createkey] | None = None
    cache_key: str
    login_attemps: int = 0
    locked_at: datetime | None = None
    login_date: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

    @property
    def is_default_user(self) -> bool:
        return self.email == config['application.default_user'].strip().lower()

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [joinedload(User.group), joinedload(User.keys)]

    @field_validator("login_attemps", mode="before")
    @classmethod
    def none_to_zero(cls, v):
        return 0 if v is None else v

    @property
    def is_locked(self) -> bool:
        if self.locked_at is None:
            return False
        return True

class UserModelRefresh(BasicModel):
    user_id: UUID4
    long_token: str | None = None
    remember: bool

class UpdateGroup(GroupBase):
    id: UUID4
    name: str

    webhooks: list[CreateWebhook] = []


class GroupInDB(UpdateGroup):
    users: list[UserSummary] | None = None
    preferences: ReadGroupPreferences | None = None
    webhooks: list[ReadWebhook] = []

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            joinedload(Group.categories),
            joinedload(Group.webhooks),
            joinedload(Group.preferences),
            selectinload(Group.users).joinedload(User.group),
            selectinload(Group.users).joinedload(User.tokens),
        ]


class GroupSummary(GroupBase):
    id: UUID4
    name: str
    slug: str
    preferences: ReadGroupPreferences | None = None

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            joinedload(Group.preferences),
        ]

class UserKeyOut(BasicModel):
    """
    Defines the structure of a user key when sending it to the API
    """
    name: str
    user_id: UUID4
    id: UUID4
    key: str
    integration_id: str = DEFAULT_INTEGRATION_ID
    created_at: datetime | None = None
    model_config = ConfigDict(from_attributes=True)

class UserKeyInDB(Createkey):
    """
    Defines the structure of a user key when getting it from database
    """
    id: UUID4
    user: UserModel
    model_config = ConfigDict(from_attributes=True)
