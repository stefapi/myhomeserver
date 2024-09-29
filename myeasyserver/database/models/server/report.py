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

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import ConfigDict
from sqlalchemy import ForeignKey, orm
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Boolean, DateTime, String

from myeasyserver.helper.guid import GUID
from ..auto_init import auto_init
from ..model_base import SqlAlchemyBase, BaseMixins

if TYPE_CHECKING:
    from ..group import Group


class ReportEntryModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "report_entries"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    success: Mapped[bool | None] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(String, nullable=True)
    exception: Mapped[str] = mapped_column(String, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    report_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("reports.id"), nullable=False, index=True)
    report: Mapped["ReportModel"] = orm.relationship("ReportModel", back_populates="entries")

    @auto_init()
    def __init__(self, **_) -> None:
        pass


class ReportModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "reports"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    entries: Mapped[list[ReportEntryModel]] = orm.relationship(
        ReportEntryModel, back_populates="report", cascade="all, delete-orphan"
    )

    # Relationships
    group_id: Mapped[GUID] = mapped_column(GUID, ForeignKey("groups.id"), nullable=False, index=True)
    group: Mapped["Group"] = orm.relationship("Group", back_populates="reports", single_parent=True)
    model_config = ConfigDict(exclude=["entries"])

    @auto_init()
    def __init__(self, **_) -> None:
        pass
