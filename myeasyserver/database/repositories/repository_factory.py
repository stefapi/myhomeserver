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

from functools import cached_property
from sqlalchemy.orm import Session

from .repository_generic import RepositoryGeneric
from .repository_group import RepositoryGroup
from .repository_users import RepositoryUsers
from ..models.group import Group, GroupInviteToken, GroupPreferencesModel
from ..models.server import ServerTaskModel, DataExportsModel, ReportModel, ReportEntryModel, EventNotifierModel, \
    WebhooksModel
from ..models.users import UserKey, User, PasswordResetModel
from ...schema.group import ReadGroupPreferences, ReadInviteToken
from ...schema.reports import ReportOut, ReportEntryOut
from ...schema.server import ServerTask, DataExport, ReadWebhook
from ...schema.server.events import EventNotifierOut
from ...schema.user import UserKeyInDB, UserModel, PrivatePasswordResetToken
from ...schema.user.user import GroupInDB

PK_ID = "id"
PK_TOKEN = "token"
PK_GROUP_ID = "group_id"

class AllRepositories:
    def __init__(self, session: Session) -> None:
        """
        `AllRepositories` class is the data access layer for all database actions within
        Myeasyserver. Database uses composition from classes derived from AccessModel. These
        can be substantiated from the AccessModel class or through inheritance when
        additional methods are required.
        """

        self.session = session

    # ================================================================
    # User

    @cached_property
    def users(self) -> RepositoryUsers:
        return RepositoryUsers(self.session, PK_ID, User, UserModel)

    @cached_property
    def api_keys(self) -> RepositoryGeneric[UserKeyInDB, UserKey]:
        return RepositoryGeneric(self.session, PK_ID, UserKey, UserKeyInDB)

    @cached_property
    def tokens_pw_reset(self) -> RepositoryGeneric[PrivatePasswordResetToken, PasswordResetModel]:
        return RepositoryGeneric(self.session, PK_TOKEN, PasswordResetModel, PrivatePasswordResetToken)

    @cached_property
    def server_tasks(self) -> RepositoryGeneric[ServerTask, ServerTaskModel]:
        return RepositoryGeneric(self.session, PK_ID, ServerTaskModel, ServerTask)

    @cached_property
    def groups(self) -> RepositoryGroup:
        return RepositoryGroup(self.session, PK_ID, Group, GroupInDB)

    @cached_property
    def group_invite_tokens(self) -> RepositoryGeneric[ReadInviteToken, GroupInviteToken]:
        return RepositoryGeneric(self.session, PK_TOKEN, GroupInviteToken, ReadInviteToken)

    @cached_property
    def group_preferences(self) -> RepositoryGeneric[ReadGroupPreferences, GroupPreferencesModel]:
        return RepositoryGeneric(self.session, PK_GROUP_ID, GroupPreferencesModel, ReadGroupPreferences)

    @cached_property
    def exports(self) -> RepositoryGeneric[DataExport, DataExportsModel]:
        return RepositoryGeneric(self.session, PK_ID, DataExportsModel, DataExport)

    @cached_property
    def reports(self) -> RepositoryGeneric[ReportOut, ReportModel]:
        return RepositoryGeneric(self.session, PK_ID, ReportModel, ReportOut)

    @cached_property
    def report_entries(self) -> RepositoryGeneric[ReportEntryOut, ReportEntryModel]:
        return RepositoryGeneric(self.session, PK_ID, ReportEntryModel, ReportEntryOut)

    @cached_property
    def webhooks(self) -> RepositoryGeneric[ReadWebhook, WebhooksModel]:
        return RepositoryGeneric(self.session, PK_ID, WebhooksModel, ReadWebhook)

    @cached_property
    def event_notifier(self) -> RepositoryGeneric[EventNotifierOut, EventNotifierModel]:
        return RepositoryGeneric(self.session, PK_ID, EventNotifierModel, EventNotifierOut)
