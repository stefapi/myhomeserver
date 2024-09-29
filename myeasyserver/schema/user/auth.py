from typing import Annotated

from fastapi import Form
from pydantic import UUID4, StringConstraints

from ..basic_model import BasicModel


class Token(BasicModel):
    access_token: str
    token_type: str


class TokenData(BasicModel):
    user_id: UUID4 | None = None
    username: Annotated[str, StringConstraints(to_lower=True, strip_whitespace=True)] | None = None  # type: ignore


class UnlockResults(BasicModel):
    unlocked: int = 0


class CredentialsRequest(BasicModel):
    username: str
    password: str
    remember_me: bool = False


class OIDCRequest(BasicModel):
    id_token: str


class CredentialsRequestForm:
    """Class that represents a user's credentials from the login form"""

    def __init__(self, username: str = Form(""), password: str = Form(""), remember_me: bool = Form(False)):
        self.username = username
        self.password = password
        self.remember_me = remember_me
