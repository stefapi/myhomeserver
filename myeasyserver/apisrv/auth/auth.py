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

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm.session import Session

from ..core import UserAPIRouter
from ..core.deps import get_current_user_refresh
from ...core.exceptions import UserLockedOut
from ...core.root_logger import get_logger
from ...core.security import get_auth_provider, get_access_long_token, get_access_token
from ...database.db_session import generate_session
from ...schema.user import CredentialsRequestForm
from ...schema.user.user import UserModelRefresh

public_router = APIRouter(tags=["Users: Authentication"])
user_router = UserAPIRouter(tags=["Users: Authentication"])
logger = get_logger("auth")

remember_me_duration = timedelta(days=14)


class AuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"

    @classmethod
    def respond(cls, token: str, token_type: str = "bearer") -> dict:
        return cls(access_token=token, token_type=token_type).model_dump()


@public_router.post("/login_basic")
async def get_token(
    request: Request,
    response: Response,
    data: CredentialsRequestForm = Depends(),
    session: Session = Depends(generate_session),
):
    if "x-forwarded-for" in request.headers:
        ip = request.headers["x-forwarded-for"]
        if "," in ip:  # if there are multiple IPs, the first one is canonically the true client
            ip = str(ip.split(",")[0])
    else:
        # request.client should never be null, except sometimes during testing
        ip = request.client.host if request.client else "unknown"

    try:
        auth_provider = get_auth_provider(session, request, data)
        auth = await auth_provider.authenticate()
    except UserLockedOut as e:
        logger.error(f"User is locked out from {ip}")
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="User is locked out") from e

    if not auth:
        logger.error(f"Incorrect username or password from {ip}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    access_token, duration = auth

    expires_in = duration.total_seconds() if duration else None
    response.set_cookie(
        key="myeasyserver.access_token", value=access_token, httponly=True, max_age=expires_in, expires=expires_in
    )

    return AuthToken.respond(access_token)


@user_router.get("/refresh")
async def refresh_token(response: Response, current_user: UserModelRefresh = Depends(get_current_user_refresh)):
    """Use a valid token to get another token"""
    access_token, duration = get_access_token(current_user.user_id, current_user.remember)

    expires_in = duration.total_seconds() if duration else None
    response.set_cookie(
        key="myeasyserver.access_token", value=access_token, httponly=True, max_age=expires_in, expires=expires_in
    )

    return AuthToken.respond(access_token)


@user_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("myeasyserver.access_token")
    return {"message": "Logged out"}
