#  Copyright (c) 2024  stefapi
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
import json
import os
from argparse import Namespace
from datetime import datetime, timedelta

from typing import Annotated
from typing import Optional
import base64

from debug_toolbar.middleware import DebugToolbarMiddleware
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN
from starlette.responses import RedirectResponse, Response, JSONResponse

from fastapi import Depends, FastAPI, HTTPException, status, APIRouter, Header
from fastapi.staticfiles import StaticFiles
from fastapi.encoders import jsonable_encoder
from fastapi.security.base import SecurityBase, SecurityBaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, OAuth2, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware

from jose import JWTError, jwt
from secrets import token_urlsafe
from passlib.context import CryptContext
from pydantic import BaseModel

from .main import backend_application
from ..__main__ import params_link, default_config
from ..cli.main import cli_application
from ..core.config import create_config
from ..app import app_store

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
API_KEY_EXPIRE_DAYS = 365


fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashsecret",
        "role": "admin",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Liddell",
        "email": "alice@example.com",
        "hashed_password": "fakehashsecret",
        "role": "mod",
        "disabled": False,
    },
    "pdupont": {
        "username": "pdupont",
        "full_name": "Pierre Dupont",
        "email": "pdupont@example.com",
        "hashed_password": "fakehashsecret",
        "role": "user",
        "disabled": False,
    },
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    role: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")



def verify_password(plain_password, hashed_password):
    if hashed_password.startswith("fakehash"):
        return get_password_hash(plain_password, True) == hashed_password
    else:
        return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password, fakehash):
    if fakehash:
        return "fakehash" + password
    else:
        return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class BasicAuth(SecurityBase):
    def __init__(self, scheme_name: str = None, auto_error: bool = True):
        self.scheme_name = scheme_name or self.__class__.__name__
        self.model = SecurityBaseModel(type="http")
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "basic":
                return None
        return param


basic_auth = BasicAuth(auto_error=False)


class OAuth2PasswordBearerCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[list[str]]:
        header_authorization: str = request.headers.get("Authorization")
        cookie_authorization: str = request.cookies.get("Authorization")
        cookie_token: str = request.cookies.get("access_token")

        header_scheme, header_param = get_authorization_scheme_param(header_authorization)
        cookie_scheme, cookie_param = get_authorization_scheme_param(cookie_authorization)

        if header_scheme.lower() == "basic":
            authorization = True
            scheme = header_scheme
            param = header_param
        elif header_scheme.lower() == "bearer":
            authorization = True
            scheme = header_scheme
            param = header_param
        elif cookie_scheme.lower() == "bearer":
            authorization = True
            scheme = cookie_scheme
            param = cookie_param
        elif cookie_token:
            authorization = True
            scheme = "token"
            param = cookie_token

        else:
            authorization = False

        if not authorization or scheme.lower() not in ["basic", "bearer", "token"]:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return (scheme,param)

oauth2_scheme = OAuth2PasswordBearerCookie(tokenUrl="/api_v1/auth/token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        (scheme, token) = token
        if scheme.lower() not in  ["token", "bearer"]:
            raise credentials_exception
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_active_user_with_admin(current_user: Annotated[User, Depends(get_current_active_user)]):
    if current_user.role == 'admin':
        return current_user
    raise HTTPException(status_code=401, detail="Insufficient rights")

async def get_current_active_user_with_mod(current_user: Annotated[User, Depends(get_current_active_user)]):
    if current_user.role == 'mod' or current_user.role == 'admin':
        return current_user
    raise HTTPException(status_code=401, detail="Insufficient rights")

async def get_current_active_user_with_user(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user

async def get_user_from_key(api_key: str = Header(None)):
    try:
        username = jwt.decode(api_key, SECRET_KEY, algorithms=[ALGORITHM])
        user = get_user(fake_users_db, username["sub"])
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect Api key",
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Api key",
        )

args = Namespace()
if "ENVIRON_FOR_CHILD_PROCESS" in os.environ:
    vars = json.loads(os.environ["ENVIRON_FOR_CHILD_PROCESS"])
    for k, v in vars.items():
        args.__setattr__(k, v)

apps_store = app_store([cli_application(), backend_application()])
params_link_app = apps_store.update_params_link(params_link)
default_config_app = apps_store.update_default_config(default_config)
config = create_config(args.conf, args, params_link_app, default_config_app, args.debug_do_not_use)

app = FastAPI(debug=True)

app.add_middleware(DebugToolbarMiddleware)

@app.on_event("startup")
async def system_startup():

    print("-----SYSTEM STARTUP----- \n")
    print(f"API started on port {config['application.port']}")
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

router = APIRouter(prefix="/api_v1", tags=["apiv1"])
authrouter = APIRouter(prefix="/auth", tags=["auth"])
countrouter = APIRouter(prefix="/counter", tags=["counter"])
boardrouter = APIRouter(prefix="/board", tags=["board"])


@authrouter.get("/logout")
async def logout_and_remove_cookie():
    """ Logout and remove cookie """
    response = RedirectResponse(url="/")
    response.delete_cookie(key="access_token")
    return response




@authrouter.get("/login_basic", response_model=Token)
async def login_basic(request: Request, response: Response, auth: BasicAuth = Depends(basic_auth)):
    """ Login with basic auth and get an access token """
    token = request.cookies.get("access_token")
    if not auth or (auth and token != "ongoing"):
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        response.set_cookie(key="access_token", value="ongoing")
        return response
    try:
        decoded = base64.b64decode(auth).decode("ascii")
        username, _, password = decoded.partition(":")
        user = authenticate_user(fake_users_db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": username}, expires_delta=access_token_expires)

        response.set_cookie(key="access_token", value=access_token)
        return {"access_token": access_token, "token_type": "bearer"}
    except:
        response = Response(headers={"WWW-Authenticate": "Basic"}, status_code=401)
        response.set_cookie(key="access_token", value="ongoing")
        return response


@authrouter.post("/login", response_model=Token)
async def login_for_access_token(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """ Login and get an access token """
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    response.set_cookie(key="access_token", value=access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@authrouter.post("/get_key", response_model=Token)
async def get_api_key(name: str, current_user: Annotated[User, Depends(get_current_active_user)]):
    """ key an API key """
    access_token_expires = timedelta(days=API_KEY_EXPIRE_DAYS)
    #access_token = create_access_token(data={"sub": current_user.username, "type": "key", "name": name}, expires_delta=access_token_expires)
    access_token = jwt.encode({"sub": current_user.username}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "apikey"}



@authrouter.post("/key_login", response_model=Token)
async def key_for_access_token(response: Response, user: Annotated[User, Depends(get_user_from_key)]):
    """ Login with an api key and get an access token """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect API key",
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    response.set_cookie(key="access_token", value=access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@boardrouter.get("/admin")
async def get_admin_content(current_user: Annotated[User, Depends(get_current_active_user_with_admin)]):
    """ Get admin content """
    return {"content": "This is a text only dedicated to Admin Users"}

@boardrouter.get("/mod")
async def get_mod_content(current_user: Annotated[User, Depends(get_current_active_user_with_mod)]):
    """ Get mod content """
    return {"content": "This is a text only dedicated to moderator Users"}

@boardrouter.get("/user")
async def get_user_content(current_user: Annotated[User, Depends(get_current_active_user_with_user)]):
    """ Get user content """
    return {"content": "This is a text only dedicated to standard Users"}

@boardrouter.get("/all")
async def get_public_content():
    """ Get content for everyone """
    return {"content": "This is a text allowed to Everyone"}


@authrouter.get("/me/", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_active_user)]):
    return current_user


@authrouter.get("/me/items/")
async def read_own_items(current_user: Annotated[User, Depends(get_current_active_user)]):
    """ Get own items """
    return [{"item_id": "Foo", "owner": current_user.username}]


class Counter(BaseModel):
    counter: int


counter = Counter(counter=0)


@countrouter.get("/counter", response_model=Counter)
def get_counter():
    """ Get counter """
    global counter
    return counter


@countrouter.post("/counter", response_model=Counter)
def increment_counter(value: Counter):
    """ Increment counter """
    global counter
    counter.counter += value.counter
    return counter

router.include_router(authrouter)
router.include_router(countrouter)
router.include_router(boardrouter)
app.include_router(router)
