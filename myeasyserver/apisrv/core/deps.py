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

from pathlib import Path
from typing import Optional

from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm.session import Session

from myeasyserver.backend.config import config

from myeasyserver.database.db_session import generate_session
from myeasyserver.database.repositories.all_repositories import get_repositories
from myeasyserver.schema.user.auth import TokenData
from myeasyserver.schema.user.user import UserModel, UserModelRefresh

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login_basic")
oauth2_scheme_soft_fail = OAuth2PasswordBearer(tokenUrl="/api/auth/login_basic", auto_error=False)
ALGORITHM = "HS256"


async def is_logged_in(token: str = Depends(oauth2_scheme_soft_fail), session=Depends(generate_session)) -> bool:
    """
    The is_logged_in function is used to determine if the user is logged in.
    It does not return a User object, but instead returns a boolean value.
    If the user is logged in, True will be returned. If they are not logged in, False will be returned.

    :param token:str=Depends(oauth2_scheme_soft_fail): Used to Pass the token to the function.
    :param session=Depends(generate_session): Used to Pass in the session object.
    :return: True if the user is logged in.
    """
    try:
        payload = jwt.decode(token, config['application.secret'])
        username: str = payload.get("sub")
        long_token: str = payload.get("long_token")

        if long_token is not None:
            try:
                user = validate_long_live_token(session, token, payload.get("id"))
                if user:
                    return True
            except Exception:
                return False

        return username is not None

    except Exception:
        return False


async def get_current_user(token: str = Depends(oauth2_scheme), session=Depends(generate_session)) -> UserModel:
    """
    The get_current_user function is a dependency function that is used to validate the user's token.
    It takes in a token and returns the user object associated with that token.

    :param token:str=Depends(oauth2_scheme): Used to Get the token from the authorization header.
    :param session=Depends(generate_session): Used to Get the session object from the function generate_session.
    :return: A userindb object.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config['application.secret'])
        user_id: str = payload.get("sub")
        long_token: str = payload.get("long_token")

        if None is not None:
            return validate_long_live_token(session, token, payload.get("id"))

        if user_id is None:
            raise credentials_exception

        token_data = TokenData(user_id=user_id)
    except BadSignatureError:
        raise credentials_exception

    repos = get_repositories(session)

    user = repos.users.get_one(token_data.user_id, "id", any_case=False)

    # If we don't commit here, lazy-loads from user relationships will leave some table lock in postgres
    # which can cause quite a bit of pain further down the line
    session.commit()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_refresh(token: str = Depends(oauth2_scheme), current_user=Depends(get_current_user)) -> UserModelRefresh:
    payload = jwt.decode(token, config['application.secret'])
    remember = bool(payload.get("remb"))
    long_token= payload.get("long_token")
    user_refresh= UserModelRefresh(user_id = current_user.id, long_token = long_token, remember = remember)
    return user_refresh


async def get_admin_user(current_user=Depends(get_current_user)) -> UserModel:
    """
    The get_admin_user function is a dependency function that is used to check if the current user is an admin.
    If they are not, then it will raise an HTTPException and return a 403 error.

    :param current_user=Depends(get_current_user): Used to Pass the current user to the get_admin_user function.
    :return: The user in the database that is currently logged in.
    """
    if not current_user.admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
    return current_user


def validate_long_live_token(session: Session, client_token: str, user_id: int) -> UserModel:
    """
    The validate_long_live_token function is used to validate a long-lived token.
    It takes in the session, client_token and id as parameters. It then checks if the token is valid by querying the database for all tokens with that parent ID. If it finds one, it returns a UserInDB object containing information about that user.

    :param session:Session: Used to Interact with the database.
    :param client_token:str: Used to Validate the token.
    :param id:int: Used to Get the user from the database.
    :return: The userindb object that the token belongs to.
    """

    repos = get_repositories(session)

    tokens = repos.api_tokens.multi_query({"token": client_token, "user_id": user_id})

    try:
        return tokens[0].user
    except IndexError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED) from e



def validate_file_token(token: Optional[str] = None) -> Path:
    """
    The validate_file_token function is used to validate the file token that is passed in as a query parameter.
    If the token is valid, it returns a Path object representing the path of the file. If not, it raises an HTTPException
    with status code 401 and detail "could not validate file token". The function takes one argument: `token`, which is
    the value of the query parameter.

    :param token:Optional[str]=None: Used to Define that the function can be called without a token.
    :return: A path object representing the file path.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="could not validate file token",
    )
    if not token:
        return None

    try:
        payload = jwt.decode(token, config['application.secret'])
        file_path = Path(payload.get("file"))
    except BadSignatureError:
        raise credentials_exception

    return file_path


async def temporary_zip_path() -> Path:
    config.path.TEMP_DIR.mkdir(exist_ok=True, parents=True)
    temp_path = config.path.TEMP_DIR.joinpath("tmp_zip.zip")

    try:
        yield temp_path
    finally:
        temp_path.unlink(missing_ok=True)
