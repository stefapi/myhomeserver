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

from datetime import timedelta, datetime

from sqlalchemy.orm.session import Session

from .. import root_logger
from ..exceptions import UserLockedOut
from ..hasher import get_hasher
from ...backend.config import config
from ...database.repositories.all_repositories import get_repositories
from ...schema.user import CredentialsRequest
from .auth_provider import AuthProvider
from ...services.user_services.user_service import UserService


class FakeProvider(AuthProvider[CredentialsRequest]):
    """Fake authentication provider for testing purposes"""

    _logger = root_logger.get_logger("fake_provider")

    def __init__(self, session: Session, data: CredentialsRequest) -> None:
        super().__init__(session, data)

    async def authenticate(self) -> tuple[str, timedelta] | None:
        """Attempt to authenticate a user given a username and password"""
        db = get_repositories(self.session)
        user = self.try_get_user(config["application.default_user"])

        if not user:
            return None

        user.login_attemps = 0
        user.login_date = datetime.now()
        db.users.update(user.id, user)
        return self.get_access_token(self.data.remember_me)  # type: ignore
