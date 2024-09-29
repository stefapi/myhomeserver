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

import datetime
import enum

from pydantic import ConfigDict, Field, BaseModel
from pydantic.types import UUID4
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from myeasyserver.database.models.server import ReportModel


class ReportCategory(str, enum.Enum):
    backup = "backup"
    restore = "restore"
    migration = "migration"
    bulk_import = "bulk_import"


class ReportSummaryStatus(str, enum.Enum):
    in_progress = "in-progress"
    success = "success"
    failure = "failure"
    partial = "partial"


class ReportEntryCreate(BaseModel):
    report_id: UUID4
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    success: bool = True
    message: str
    exception: str = ""


class ReportEntryOut(ReportEntryCreate):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)


class ReportCreate(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    category: ReportCategory
    group_id: UUID4
    name: str
    status: ReportSummaryStatus = ReportSummaryStatus.in_progress


class ReportSummary(ReportCreate):
    id: UUID4


class ReportOut(ReportSummary):
    entries: list[ReportEntryOut] = []
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [joinedload(ReportModel.entries)]
