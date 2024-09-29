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

from sqlalchemy import ForeignKey, Integer, String, orm
from sqlalchemy.orm import Mapped, mapped_column

from myeasyserver.helper import guid
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from group import Group


class GroupInviteToken(SqlAlchemyBase, BaseMixins):
    __tablename__ = "invite_tokens"
    token: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    uses_left: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    group_id: Mapped[guid.GUID | None] = mapped_column(guid.GUID, ForeignKey("groups.id"), index=True)
    group: Mapped[Optional["Group"]] = orm.relationship("Group", back_populates="invite_tokens")

    @auto_init()
    def __init__(self, **_):
        pass
