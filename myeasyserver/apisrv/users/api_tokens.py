#  Copyright (c) 2022  stefapi
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#

from datetime import timedelta

from fastapi import HTTPException, status
from fastapi.param_functions import Depends
from webserver.core.security import create_access_token
from webserver.db.database import db
from webserver.db.db_setup import generate_session
from webserver.rest_api.deps import get_current_user
from webserver.rest_api.routers import UserAPIRouter
from webserver.schema.user import CreateToken, LongLiveTokenIn, LongLiveTokenInDB, UserInDB
from sqlalchemy.orm.session import Session

router = UserAPIRouter(prefix="/api/users", tags=["User API Tokens"])


@router.post("/api-tokens", status_code=status.HTTP_201_CREATED)
async def create_api_token(
    token_name: LongLiveTokenIn,
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(generate_session),
):
    """
    The create_api_token function creates an api_token in the database.
    It takes a token name, current user and session as parameters.
    The function returns a new token in the database.

    :param token_name:LoingLiveTokenIn: Used to Specify the name of the token.
    :param current_user:UserInDB=Depends(get_current_user): Used to Get the current user from the database.
    :param session:Session=Depends(generate_session): Used to Create a session for the database.
    :param : Used to Create a token that is only valid for 5 years.
    :return: The token_model.
    """

    token_data = {"long_token": True, "id": current_user.id}

    five_years = timedelta(1825)
    token = create_access_token(token_data, five_years)

    token_model = CreateToken(
        name=token_name.name,
        token=token,
        parent_id=current_user.id,
    )

    new_token_in_db = db.api_tokens.create(session, token_model)

    if new_token_in_db:
        return {"token": token}


@router.delete("/api-tokens/{token_id}")
async def delete_api_token(
    token_id: int,
    current_user: UserInDB = Depends(get_current_user),
    session: Session = Depends(generate_session),
):
    """
    The delete_api_token function deletes an API token from the database.
    It takes two parameters:
        - token_id: The id of the API token to be deleted. This is a required parameter.
        - current_user: The user who is requesting this action, which will be used to check if they are authorized to perform it. This is a required parameter.

    :param token_id:int: Used to Identify the token to be deleted.
    :param current_user:UserInDB=Depends(get_current_user): Used to Get the current user from the database.
    :param session:Session=Depends(generate_session): Used to Pass the session to the function.
    :param : Used to Ensure that the user is logged in and to get their email address.
    :return: A dictionary with the key token_delete and the value of the deleted token.
    """
    token: LongLiveTokenInDB = db.api_tokens.get(session, token_id)

    if not token:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Could not locate token with id '{token_id}' in database")

    if token.user.email == current_user.email:
        deleted_token = db.api_tokens.delete(session, token_id)
        return {"token_delete": deleted_token.name}
    else:
        raise HTTPException(status.HTTP_403_FORBIDDEN)
