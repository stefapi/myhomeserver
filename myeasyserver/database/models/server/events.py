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

from sqlalchemy import Boolean, ForeignKey, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from myeasyserver.helper.guid import GUID
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from ..group import Group


class EventNotifierOptionsModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "events_notifier_options"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    event_notifier_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("events_notifiers.id"), nullable=False)

    # list of events
    user_signup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class EventNotifierModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "events_notifiers"

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    name: Mapped[str] = mapped_column(String, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    apprise_url: Mapped[str] = mapped_column(String, nullable=False)

    group: Mapped[Optional["Group"]] = orm.relationship(
        "Group", back_populates="event_notifiers", single_parent=True
    )
    group_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("groups.id"), index=True)

    options: Mapped[EventNotifierOptionsModel] = orm.relationship(
        EventNotifierOptionsModel, uselist=False, cascade="all, delete-orphan"
    )

    @auto_init()
    def __init__(self, **_) -> None:
        pass
