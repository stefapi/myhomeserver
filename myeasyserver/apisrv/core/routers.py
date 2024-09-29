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
import contextlib
import json
from collections.abc import Callable
from enum import Enum
from json import JSONDecodeError

from fastapi import APIRouter, Depends, Request, Response
from fastapi.routing import APIRoute
from .deps import get_admin_user, get_current_user

from typing import List, Optional


class AdminAPIRouter(APIRouter):
    """ Router for functions to be protected behind admin authentication """

    def __init__(
        self,
        tags: Optional[List[str | Enum]] = None,
        prefix: str = "", **kwargs
    ):
        super().__init__(tags=tags, prefix=prefix, dependencies=[Depends(get_admin_user)], **kwargs)


class UserAPIRouter(APIRouter):
    """ Router for functions to be protected behind user authentication """

    def __init__(
        self,
        tags: Optional[List[str | Enum]] = None,
        prefix: str = "", **kwargs
    ):
        super().__init__(tags=tags, prefix=prefix, dependencies=[Depends(get_current_user)], **kwargs)


class PublicAPIRouter(APIRouter):
    """ Router for functions to be protected behind user authentication """

    def __init__(
        self,
        tags: Optional[List[str]] = None,
        prefix: str = "",
    ):
        super().__init__(tags=tags, prefix=prefix)

class CrudRoute(APIRoute):
    """Route class to include the last-modified header when returning a MyeasyserverModel, when available"""

    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            with contextlib.suppress(JSONDecodeError):
                response = await original_route_handler(request)
                response_body = json.loads(response.body)
                if isinstance(response_body, dict):
                    if last_modified := response_body.get("updateAt"):
                        response.headers["last-modified"] = last_modified

                        # Force no-cache for all responses to prevent browser from caching API calls
                        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return response

        return custom_route_handler
