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

from datetime import datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String, Time, orm
from sqlalchemy.orm import Mapped, mapped_column

from myeasyserver.helper.guid import GUID
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from ..group import Group


class WebhooksModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "webhook_urls"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    group: Mapped[Optional["Group"]] = orm.relationship("Group", back_populates="webhooks", single_parent=True)
    group_id: Mapped[GUID | None] = mapped_column(GUID, ForeignKey("groups.id"), index=True)

    enabled: Mapped[bool | None] = mapped_column(Boolean, default=False)
    name: Mapped[str | None] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String)

    # New Fields
    webhook_type: Mapped[str | None] = mapped_column(String, default="")  # Future use for different types of webhooks
    scheduled_time: Mapped[time | None] = mapped_column(Time, default=lambda: datetime.now().time())

    # Columne is no longer used but is kept for since it's super annoying to
    # delete a column in SQLite and it's not a big deal to keep it around
    time: Mapped[str | None] = mapped_column(String, default="00:00")

    @auto_init()
    def __init__(self, **_) -> None: ...
