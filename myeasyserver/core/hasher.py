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

from functools import lru_cache
from typing import Protocol

import bcrypt
from argon2 import PasswordHasher

from myeasyserver.backend.config import config


class Hasher(Protocol):
    def hash(self, password: str) -> str: ...

    def verify(self, password: str, hashed: str) -> bool: ...


class FakeHasher:
    def hash(self, password: str) -> str:
        return password

    def verify(self, password: str, hashed: str) -> (bool, str):
        return password == hashed, None


class BcryptHasher:
    def hash(self, password: str) -> str:
        password_bytes = password.encode("utf-8")
        hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify(self, password: str, hashed: str) -> (bool, str):
        password_bytes = password.encode("utf-8")
        hashed_bytes = hashed.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes), None

class Argon2Hasher:
    def hash(self, password: str) -> str:
        ph = PasswordHasher()
        hashed = ph.hash(password)
        return hashed

    def verify(self, password: str, hashed: str) -> (bool, str):
        ph = PasswordHasher()
        check = ph.verify(hashed, password)
        if check:
            if ph.check_needs_rehash(hashed):
                return True, ph.hash(password)
            return True, None
        return False, None

@lru_cache(maxsize=1)
def get_hasher() -> Hasher:
    if config['internal.development'] == True:
        return FakeHasher()

    if config['application.default_hasher'] == 'bcrypt':
        return BcryptHasher()
    return Argon2Hasher()
