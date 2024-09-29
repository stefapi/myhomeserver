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

from fastapi import HTTPException, status
from fastapi.param_functions import Depends
from pydantic import UUID4
from sqlalchemy.orm.session import Session

from ...core.security import get_access_key, hash_password
from ..core import UserAPIRouter, get_current_user
from ...database.db_session import generate_session
from ...database.repositories.all_repositories import get_repositories
from ...schema.user import UserKeyIn, UserModel, Createkey, UserKeyInDB, UserKeyOut

router = UserAPIRouter()

@router.post("/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_name: UserKeyIn,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(generate_session),
):
    """
    Creates an api_key in the database.

    It takes a key name and creates the key related to
    the user in the database.

    The function returns the new key
    """

    key = get_access_key()

    key_model = Createkey(
        name=key_name.name,
        key=hash_password(key),
        user_id=current_user.id,
    )

    db = get_repositories(session)
    new_token_in_db = db.api_keys.create(key_model)

    if new_token_in_db:
        return {"key": key}


@router.get("/api-keys", status_code=status.HTTP_200_OK)
async def list_api_key(
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(generate_session),
):
    """
    List all api_key in the database.

   Return a list of api_tokens
    """
    db = get_repositories(session)
    #list= db.api_tokens.get_all(override=LongLiveTokenInDB)
    list= db.api_keys.get_all(override_schema=UserKeyOut)

    return list



@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: UUID4,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(generate_session),
):
    """
    Deletes an API key from the database.

    It takes one parameter:
        - token_id: The id of the API token to be deleted. This is a required parameter.

    """
    db = get_repositories(session)
    key: UserKeyInDB = db.api_keys.get_one(key_id)

    if not key:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Could not locate key with id '{key_id}' in database")

    if key.user.id == current_user.id:
        deleted_key = db.api_keys.delete(key_id)
        return {"key_delete": deleted_key.name}
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
