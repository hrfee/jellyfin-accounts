#!/usr/bin/env python3

from flask_httpauth import HTTPBasicAuth
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadSignature,
    SignatureExpired,
)
from passlib.apps import custom_app_context as pwd_context
import uuid
from jellyfin_accounts import config, app, g
from jellyfin_accounts import auth_log as log
from jellyfin_accounts.jf_api import Jellyfin
from jellyfin_accounts.web_api import jf

auth_jf = Jellyfin(
    config["jellyfin"]["server"],
    config["jellyfin"]["client"],
    config["jellyfin"]["version"],
    config["jellyfin"]["device"],
    config["jellyfin"]["device_id"] + "_authClient",
)


class Account:
    def __init__(self, username=None, password=None):
        self.username = username
        if password is not None:
            self.password_hash = pwd_context.hash(password)
            self.id = str(uuid.uuid4())
            self.jf = False
        elif username is not None:
            jf.authenticate(
                config["jellyfin"]["username"], config["jellyfin"]["password"]
            )
            self.id = jf.getUsers(self.username, public=False)["Id"]
            self.jf = True

    def verify_password(self, password):
        if not self.jf:
            return pwd_context.verify(password, self.password_hash)
        else:
            try:
                return auth_jf.authenticate(self.username, password)
            except Jellyfin.AuthenticationError:
                return False

    def generate_token(self, expiration=1200):
        s = Serializer(app.config["SECRET_KEY"], expires_in=expiration)
        log.debug(self.id)
        return s.dumps({"id": self.id})

    @staticmethod
    def verify_token(token, accounts):
        log.debug(f"verifying token {token}")
        s = Serializer(app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        if config.getboolean("ui", "jellyfin_login"):
            for account in accounts:
                if data["id"] == accounts[account].id:
                    return account
        else:
            return accounts["adminAccount"]


auth = HTTPBasicAuth()

accounts = {}

if config.getboolean("ui", "jellyfin_login"):
    log.debug("Using jellyfin for admin authentication")
else:
    log.debug("Using configured login details for admin authentication")
    accounts["adminAccount"] = Account(
        config["ui"]["username"], config["ui"]["password"]
    )


@auth.verify_password
def verify_password(username, password):
    user = None
    verified = False
    log.debug("Verifying auth")
    if config.getboolean("ui", "jellyfin_login"):
        try:
            jf_user = jf.getUsers(username, public=False)
            id = jf_user["Id"]
            user = accounts[id]
        except KeyError:
            if config.getboolean("ui", "admin_only"):
                if jf_user["Policy"]["IsAdministrator"]:
                    user = Account(username)
                    accounts[id] = user
                else:
                    log.debug(f"User {username} not admin.")
                    return False
            else:
                user = Account(username)
                accounts[id] = user
        except Jellyfin.UserNotFoundError:
            user = Account().verify_token(username, accounts)
            if user:
                verified = True
            if not user:
                log.debug(f"User {username} not found on Jellyfin")
                return False
    else:
        user = accounts["adminAccount"]
        verified = Account().verify_token(username, accounts)
    if not verified:
        if username == user.username and user.verify_password(password):
            g.user = user
            log.debug("HTTPAuth Allowed")
            return True
        else:
            log.debug("HTTPAuth Denied")
            return False
    g.user = user
    log.debug("HTTPAuth Allowed")
    return True
