#  Copyright (c) 2024.  stef.
#
#      ______                 _____
#     / ____/___ ________  __/ ___/___  ______   _____  _____
#    / __/ / __ `/ ___/ / / /\__ \/ _ \/ ___/ | / / _ \/ ___/
#   / /___/ /_/ (__  ) /_/ /___/ /  __/ /   | |/ /  __/ /
#  /_____/\__,_/____/\__, //____/\___/_/    |___/\___/_/
#                   /____/
#
#  Apache License
#  ================
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import ConfigDict
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from myeasyserver.backend import config
from myeasyserver.helper.guid import GUID
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from ..group import Group
    from .password_reset import PasswordResetModel


class UserKey(SqlAlchemyBase, BaseMixins):
    __tablename__ = "user_keys"
    name: Mapped[str] = mapped_column(String, nullable=False)
    key: Mapped[str] = mapped_column(String, nullable=False, index=True)
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    user_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("users.id"), index=True)
    user: Mapped[Optional["User"]] = orm.relationship("User")

    def __init__(self, name, key, user_id, **_) -> None:
        self.name = name
        self.key = key
        self.user_id = user_id


class AuthMethod(enum.Enum):
    INTERNAL = "INTERNAL"
    LDAP = "LDAP"
    OIDC = "OIDC"


class User(SqlAlchemyBase, BaseMixins):
    __tablename__ = "users"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    full_name: Mapped[str | None] = mapped_column(String, index=True)
    username: Mapped[str | None] = mapped_column(String, index=True, unique=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    password: Mapped[str | None] = mapped_column(String)
    auth_method: Mapped[Enum[AuthMethod]] = mapped_column(Enum(AuthMethod), default=AuthMethod.INTERNAL)
    admin: Mapped[bool | None] = mapped_column(Boolean, default=False)
    advanced: Mapped[bool | None] = mapped_column(Boolean, default=False)

    group_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("groups.id"), nullable=False, index=True)
    group: Mapped["Group"] = orm.relationship("Group", back_populates="users")

    cache_key: Mapped[str | None] = mapped_column(String, default="1234")
    login_attemps: Mapped[int | None] = mapped_column(Integer, default=0)
    login_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    # Group Permissions
    can_manage: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_invite: Mapped[bool | None] = mapped_column(Boolean, default=False)
    can_organize: Mapped[bool | None] = mapped_column(Boolean, default=False)

    sp_args = {
        "back_populates": "user",
        "cascade": "all, delete, delete-orphan",
        "single_parent": True,
    }

    keys: Mapped[list[UserKey]] = orm.relationship(UserKey, **sp_args)
    password_reset_tokens: Mapped[list["PasswordResetModel"]] = orm.relationship("PasswordResetModel", **sp_args)

    model_config = ConfigDict(
        exclude={
            "password",
            "admin",
            "can_manage",
            "can_invite",
            "can_organize",
            "group",
        }
    )

    @auto_init()
    def __init__(self, session, full_name, password, group: str | None = None, **kwargs) -> None:
        if group is None:
            group = config["application.default_group"]

        from ..group import Group

        self.group = Group.get_by_name(session, group)

        self.rated_recipes = []

        self.password = password

        if self.username is None:
            self.username = full_name

        self._set_permissions(**kwargs)

    @auto_init()
    def update(self, full_name, email, group, username, session=None, **kwargs):
        self.username = username
        self.full_name = full_name
        self.email = email

        from ..group import Group

        self.group = Group.get_by_name(session, group)

        if self.username is None:
            self.username = full_name

        self._set_permissions(**kwargs)

    def update_password(self, password):
        self.password = password

    def _set_permissions(self, admin, can_manage=False, can_invite=False, can_organize=False, **_):
        """Set user permissions based on the admin flag and the passed in kwargs

        Args:
            admin (bool):
            can_manage (bool):
            can_invite (bool):
            can_organize (bool):
        """
        self.admin = admin
        if self.admin:
            self.can_manage = True
            self.can_invite = True
            self.can_organize = True
            self.advanced = True
        else:
            self.can_manage = can_manage
            self.can_invite = can_invite
            self.can_organize = can_organize
