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

from ...database.repositories import AllRepositories
from ...schema.user import UserModel
from ...services.base_service import BaseService


class UserService(BaseService):
    def __init__(self, repos: AllRepositories) -> None:
        self.repos = repos
        super().__init__()

    def get_locked_users(self) -> list[UserModel]:
        return self.repos.users.get_locked_users()

    def reset_locked_users(self, force: bool = False) -> int:
        """
        Queriers that database for all locked users and resets their locked_at field to None
        if more than the set time has passed since the user was locked
        """
        locked_users = self.get_locked_users()

        unlocked = 0

        for user in locked_users:
            if force or not user.is_locked and user.locked_at is not None:
                self.unlock_user(user)
                unlocked += 1

        return unlocked

    def lock_user(self, user: UserModel) -> UserModel:
        user.locked_at = datetime.now()
        return self.repos.users.update(user.id, user)

    def unlock_user(self, user: UserModel) -> UserModel:
        user.locked_at = None
        user.login_attemps = 0
        return self.repos.users.update(user.id, user)
