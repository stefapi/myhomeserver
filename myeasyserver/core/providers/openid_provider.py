from datetime import timedelta, datetime
from functools import lru_cache

import requests
from authlib.jose import JsonWebToken, KeySet, JsonWebKey, JWTClaims
from authlib.jose.errors import ExpiredTokenError, UnsupportedAlgorithmError
from authlib.oidc.core import CodeIDToken
from sqlalchemy.orm.session import Session

from . import AuthProvider
from .. import root_logger
from ...backend.config import config
from ...database.models.users import AuthMethod
from ...database.repositories.all_repositories import get_repositories
from ...schema.user import OIDCRequest


class OpenIDProvider(AuthProvider[OIDCRequest]):
    """Authentication provider that authenticates a user using a token from OIDC ID token"""

    _logger = root_logger.get_logger("openid_provider")

    def __init__(self, session: Session, data: OIDCRequest) -> None:
        super().__init__(session, data)

    async def authenticate(self) -> tuple[str, timedelta] | None:
        """Attempt to authenticate a user given a username and password"""

        claims = self.get_claims()
        if not claims:
            return None

        repos = get_repositories(self.session)

        user = self.try_get_user(claims.get(config["application.oidc_user_claim"]))
        is_admin = False
        if config["application.oidc_user_group"] or config["application.oidc_admin_group"]:
            group_claim = claims.get(config["application.oidc_groups_claim"], [])
            is_admin = config["application.oidc_admin_group"] in group_claim if config["application.Oidc_admin_group"] else False
            is_valid_user = config["application.oidc_user_group"] in group_claim if config["application.oidc_user_group"] else True

            if not is_valid_user:
                self._logger.debug(
                    "[OIDC] User does not have the required group. Found: %s - Required: %s",
                    group_claim,
                    config["application.oidc_user_group"],
                )
                return None

        if not user:
            if not config["application.oidc_signup_enabled"]:
                self._logger.debug("[OIDC] No user found. Not creating a new user - new user creation is disabled.")
                return None

            self._logger.debug("[OIDC] No user found. Creating new OIDC user.")

            user = repos.users.create(
                {
                    "username": claims.get("preferred_username"),
                    "password": "OIDC",
                    "full_name": claims.get("name"),
                    "email": claims.get("email"),
                    "admin": is_admin,
                    "login_date": datetime.now(),
                    "auth_method": AuthMethod.OIDC,
                }
            )
            self.session.commit()
            return self.get_access_token(user, config["application.Oidc_remember_me"])  # type: ignore

        if user:
            if config["application.oidc_admin_group"] and user.admin != is_admin:
                self._logger.debug(f"[OIDC] {'Setting' if is_admin else 'Removing'} user as admin")
                user.admin = is_admin
            user.login_attemps = 0
            user.login_date = datetime.now()
            repos.users.update(user.id, user)
            return self.get_access_token(user, config["application.oidc_remember_me"])

        self._logger.warning("[OIDC] Found user but their AuthMethod does not match OIDC")
        return None

    def get_claims(self) -> JWTClaims | None:
        """Get the claims from the ID token and check if the required claims are present"""
        required_claims = {"preferred_username", "name", "email", config["application.oidc_user_claim"]}
        jwks = OpenIDProvider.get_jwks()
        if not jwks:
            return None

        algorithm = config["application.oidc_signing_algorithm"]
        try:
            claims = JsonWebToken([algorithm]).decode(s=self.data.id_token, key=jwks, claims_cls=CodeIDToken)
        except UnsupportedAlgorithmError:
            self._logger.error(
                f"[OIDC] Unsupported algorithm '{algorithm}'. Unable to decode id token due to mismatched algorithm."
            )
            return None

        try:
            claims.validate()
        except ExpiredTokenError as e:
            self._logger.error(f"[OIDC] {e.error}: {e.description}")
            return None
        except Exception as e:
            self._logger.error("[OIDC] Exception while validating id_token claims", e)

        if not claims:
            self._logger.error("[OIDC] Claims not found")
            return None
        if not required_claims.issubset(claims.keys()):
            self._logger.error(
                f"[OIDC] Required claims not present. Expected: {required_claims} Actual: {claims.keys()}"
            )
            return None
        return claims

    @lru_cache
    @staticmethod
    def get_jwks() -> KeySet | None:
        """Get the key set from the open id configuration"""

        if not (config["application.oidc_ready"] and config["application.oidc_configuration_url"]):
            return None

        session = requests.Session()
        if config["application.oidc_tls_cacertfile"]:
            session.verify = config["application.oidc_tls_cacertfile"]

        config_response = session.get(config["application.oidc_configuration_url"], timeout=5)
        config_response.raise_for_status()
        configuration = config_response.json()

        if not configuration:
            OpenIDProvider._logger.warning("[OIDC] Unable to fetch configuration from the OIDC_CONFIGURATION_URL")
            session.close()
            return None

        jwks_uri = configuration.get("jwks_uri", None)
        if not jwks_uri:
            OpenIDProvider._logger.warning("[OIDC] Unable to find the jwks_uri from the OIDC_CONFIGURATION_URL")
            session.close()
            return None

        response = session.get(jwks_uri, timeout=5)
        response.raise_for_status()
        session.close()
        return JsonWebKey.import_key_set(response.json())
