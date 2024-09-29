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

from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from pydantic import ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.orm.session import Session

from myeasyserver.backend import config
from myeasyserver.helper.guid import GUID
from .invite_tokens import GroupInviteToken
from .preferences import GroupPreferencesModel
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins
from ..server import ServerTaskModel, WebhooksModel

if TYPE_CHECKING:
    from ..users import User
    from ..server import EventNotifierModel, DataExportsModel, ReportModel


class Group(SqlAlchemyBase, BaseMixins):
    __tablename__ = "groups"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    name: Mapped[str] = mapped_column(sa.String, index=True, nullable=False, unique=True)
    users: Mapped[list["User"]] = orm.relationship("User", back_populates="group")

    invite_tokens: Mapped[list[GroupInviteToken]] = orm.relationship(
        GroupInviteToken, back_populates="group", cascade="all, delete-orphan"
    )
    preferences: Mapped[GroupPreferencesModel] = orm.relationship(
        GroupPreferencesModel,
        back_populates="group",
        uselist=False,
        single_parent=True,
        cascade="all, delete-orphan",
    )

    # CRUD From Others
    common_args = {
        "back_populates": "group",
        "cascade": "all, delete-orphan",
        "single_parent": True,
    }

    webhooks: Mapped[list[WebhooksModel]] = orm.relationship(WebhooksModel, **common_args)
    server_tasks: Mapped[list[ServerTaskModel]] = orm.relationship(ServerTaskModel, **common_args)
    data_exports: Mapped[list["DataExportsModel"]] = orm.relationship("DataExportsModel", **common_args)
    reports: Mapped[list["ReportModel"]] = orm.relationship("ReportModel", **common_args)
    event_notifiers: Mapped[list["EventNotifierModel"]] = orm.relationship(
        "EventNotifierModel", **common_args
    )

    model_config = ConfigDict(
        exclude={
            "users",
            "webhooks",
            "preferences",
            "invite_tokens",
            "data_exports",
        }
    )

    @auto_init()
    def __init__(self, **_) -> None:
        pass

    @staticmethod
    def get_by_name(session: Session, name: str) -> Optional["Group"]:

        item = session.execute(select(Group).filter(Group.name == name)).scalars().one_or_none()
        if item is None:
            item = session.execute(select(Group).filter(Group.name == config["application.default_group"])).scalars().one_or_none()
        return item
