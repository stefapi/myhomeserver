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
from uuid import UUID

from pydantic import ConfigDict, Field, BaseModel

class ServerTaskNames(str, enum.Enum):
    default = "Background Task"
    backup_task = "Database Backup"
    bulk_recipe_import = "Bulk Recipe Import"


class ServerTaskStatus(str, enum.Enum):
    running = "running"
    finished = "finished"
    failed = "failed"


class ServerTaskCreate(BaseModel):
    group_id: UUID
    name: ServerTaskNames = ServerTaskNames.default
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    status: ServerTaskStatus = ServerTaskStatus.running
    log: str = ""

    def set_running(self) -> None:
        self.status = ServerTaskStatus.running

    def set_finished(self) -> None:
        self.status = ServerTaskStatus.finished

    def set_failed(self) -> None:
        self.status = ServerTaskStatus.failed

    def append_log(self, message: str) -> None:
        # Prefix with Timestamp and append new line and join to log
        self.log += f"{datetime.datetime.now()}: {message}\n"


class ServerTask(ServerTaskCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)
