from datetime import timedelta, datetime

import ldap
from ldap.ldapobject import LDAPObject
from sqlalchemy.orm.session import Session

from .credentials_provider import CredentialsProvider
from ..root_logger import get_logger
from ...backend.config import config
from ...database.models.users import AuthMethod
from ...database.repositories.all_repositories import get_repositories
from ...schema.user import CredentialsRequest, UserModel


class LDAPProvider(CredentialsProvider):
    """Authentication provider that authenticats a user against an LDAP server using username/password combination"""

    _logger = get_logger("ldap_provider")

    def __init__(self, session: Session, data: CredentialsRequest) -> None:
        super().__init__(session, data)
        self.conn = None

    async def authenticate(self) -> tuple[str, timedelta] | None:
        """Attempt to authenticate a user given a username and password"""
        user = self.try_get_user(self.data.username)
        if not user or user.password == "LDAP" or user.auth_method == AuthMethod.LDAP:
            user = self.get_user()
            if user:
                user.login_attemps = 0
                user.login_date = datetime.now()
                db = get_repositories(self.session)
                db.users.update(user.id, user)
                return self.get_access_token(user, self.data.remember_me)

        return await super().authenticate()

    def search_user(self, conn: LDAPObject) -> list[tuple[str, dict[str, list[bytes]]]] | None:
        """
        Searches for a user by LDAP_ID_ATTRIBUTE, LDAP_MAIL_ATTRIBUTE, and the provided LDAP_USER_FILTER.
        If none or multiple users are found, return False
        """
        if not self.data:
            return None

        user_filter = ""
        if config["application.ldap_user_filter"]:
            # fill in the template provided by the user to maintain backwards compatibility
            user_filter = config["application.ldap_user_filter"].format(
                id_attribute=config["application.ldap_id_attribute"],
                mail_attribute=config["application.ldap_mail_attribute"],
                input=self.data.username,
            )
        # Don't assume the provided search filter has (|({id_attribute}={input})({mail_attribute}={input}))
        search_filter = "(&(|({id_attribute}={input})({mail_attribute}={input})){filter})".format(
            id_attribute=config["application.ldap_id_attribute"],
            mail_attribute=config["application.ldap_mail_attribute"],
            input=self.data.username,
            filter=user_filter,
        )

        user_entry: list[tuple[str, dict[str, list[bytes]]]] | None = None
        try:
            self._logger.debug(f"[LDAP] Starting search with filter: {search_filter}")
            user_entry = conn.search_s(
                config["application.ldap_base_dn"],
                ldap.SCOPE_SUBTREE,
                search_filter,
                [config["application.ldap_id_attribute"], config["application.ldap_name_attribute"], config["application.ldap_mail_attribute"]],
            )
        except ldap.FILTER_ERROR:
            self._logger.error("[LDAP] Bad user search filter")

        if not user_entry:
            conn.unbind_s()
            self._logger.error("[LDAP] No user was found with the provided user filter")
            return None

        # we only want the entries that have a dn
        user_entry = [(dn, attr) for dn, attr in user_entry if dn]

        if len(user_entry) > 1:
            self._logger.warning("[LDAP] Multiple users found with the provided user filter")
            self._logger.debug(f"[LDAP] The following entries were returned: {user_entry}")
            conn.unbind_s()
            return None

        return user_entry

    def get_user(self) -> UserModel | None:
        """Given a username and password, tries to authenticate by BINDing to an
        LDAP server

        If the BIND succeeds, it will either create a new user of that username on
        the server or return an existing one.
        Returns False on failure.
        """

        db = get_repositories(self.session)
        if not self.data:
            return None
        data = self.data

        if config["application.ldap_tls_insecure"]:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)

        conn = ldap.initialize(config["application.ldap_server_url"])
        conn.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        conn.set_option(ldap.OPT_REFERRALS, 0)

        if config["application.ldap_tls_cacertfile"]:
            conn.set_option(ldap.OPT_X_TLS_CACERTFILE, config["application.ldap_tls_cacertfile"])
            conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)

        if config["application.ldap_enable_starttls"]:
            conn.start_tls_s()

        try:
            conn.simple_bind_s(config["application.ldap_query_bind"], config["application.ldap_query_password"])
        except (ldap.INVALID_CREDENTIALS, ldap.NO_SUCH_OBJECT):
            self._logger.error("[LDAP] Unable to bind to with provided user/password")
            conn.unbind_s()
            return None

        user_entry = self.search_user(conn)
        if not user_entry:
            return None
        user_dn, user_attr = user_entry[0]

        # Check the credentials of the user
        try:
            self._logger.debug(f"[LDAP] Attempting to bind with '{user_dn}' using the provided password")
            conn.simple_bind_s(user_dn, data.password)
        except (ldap.INVALID_CREDENTIALS, ldap.NO_SUCH_OBJECT):
            self._logger.error("[LDAP] Bind failed")
            conn.unbind_s()
            return None

        user = self.try_get_user(data.username)

        if user is None:
            self._logger.debug("[LDAP] User is not in myeasyserver. Creating a new account")

            attribute_keys = {
                config["application.ldap_id_attribute"]: "username",
                config["application.ldap_name_attribute"]: "name",
                config["application.ldap_mail_attribute"]: "mail",
            }
            attributes = {}
            for attribute_key, attribute_name in attribute_keys.items():
                if attribute_key not in user_attr or len(user_attr[attribute_key]) == 0:
                    self._logger.error(
                        f"[LDAP] Unable to create user due to missing '{attribute_name}' ('{attribute_key}') attribute"
                    )
                    self._logger.debug(f"[LDAP] User has the following attributes: {user_attr}")
                    conn.unbind_s()
                    return None
                attributes[attribute_key] = user_attr[attribute_key][0].decode("utf-8")

            user = db.users.create(
                {
                    "username": attributes[config["application.ldap_id_attribute"]],
                    "password": "LDAP",
                    "full_name": attributes[config["application.ldap_name_attribute"]],
                    "email": attributes[config["application.ldap_mail_attribute"]],
                    "admin": False,
                    "auth_method": AuthMethod.LDAP,
                },
            )

        if config["application.ldap_admin_filter"]:
            should_be_admin = len(conn.search_s(user_dn, ldap.SCOPE_BASE, config["application.ldap_admin_filter"], [])) > 0
            if user.admin != should_be_admin:
                self._logger.debug(f"[LDAP] {'Setting' if should_be_admin else 'Removing'} user as admin")
                user.admin = should_be_admin
                db.users.update(user.id, user)

        conn.unbind_s()
        return user
