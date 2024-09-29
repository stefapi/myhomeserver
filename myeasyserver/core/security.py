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

import secrets
from datetime import datetime, timedelta, timezone

from authlib.jose import jwt
from fastapi import Request
from passlib.utils import getrandbytes
from pyasn1.type.univ import Boolean
from pydantic import UUID4
from sqlalchemy.orm.session import Session
from starlette_admin.auth import AuthProvider

from . import root_logger
from .hasher import get_hasher
from ..backend.config import config
from ..schema.user.auth import CredentialsRequestForm, OIDCRequest, CredentialsRequest

from ..version import __software__

ALGORITHM = "HS256"
ISS = __software__
logger = root_logger.get_logger("security")

remember_me_duration = timedelta(days=13)

def get_auth_provider(session: Session, request: Request, data: CredentialsRequestForm) -> AuthProvider:
    from .providers import OpenIDProvider, LDAPProvider, CredentialsProvider, FakeProvider

    if config['internal.noauth']:
        return FakeProvider(session, CredentialsRequest(**data.__dict__))
    if request.cookies.get(__software__+".auth.strategy") == "oidc":
        return OpenIDProvider(session, OIDCRequest(id_token=request.cookies.get(__software__+".auth._id_token.oidc")))

    var = data.__dict__
    credentials_request = CredentialsRequest(**var)
    if config['auth.ldap.enabled'] == True:
        return LDAPProvider(session, credentials_request)

    return CredentialsProvider(session, credentials_request)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expires_delta = expires_delta or timedelta(
        hours=config['application.token_time'] or config['application.token_time'])

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode["exp"] = expire
    to_encode["iss"] = ISS
    return (jwt.encode({'alg': ALGORITHM}, to_encode, config['application.secret']), expires_delta)

def get_access_token(user_id, remember_me=False) -> tuple[str, timedelta]:
    duration = timedelta(hours=config['application.token_time'])
    if remember_me and remember_me_duration > duration:
        duration = remember_me_duration

    return create_access_token({"sub": str(user_id), "long_token": int(False), "remb":int(remember_me)}, duration)

def get_access_long_token( user_id: UUID4, long_token: Boolean, remember_me=False) -> tuple[str, timedelta]:
    duration = timedelta(hours=config['application.token_long_time'])
    if remember_me and remember_me_duration > duration:
        duration = remember_me_duration

    return create_access_token({"id": str(user_id), "long_token": int(long_token), "remb":int(remember_me)}, duration)

def get_access_key() -> str:
    """Generates a cryptographic token without embedded data. Used for connection keys"""
    return ''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))

def hash_password(password: str) -> str:
    return get_hasher().hash(password)

def url_safe_token() -> str:
    """Generates a cryptographic token without embedded data. Used for password reset tokens and invitation tokens"""
    return secrets.token_urlsafe(24)
