#!/usr/bin/env python3
# from flask import g

from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
from passlib.apps import custom_app_context as pwd_context
import uuid
from __main__ import config, app, g
from __main__ import auth_log as log


class Account():
    def __init__(self, username, password):
        self.username = username
        self.password_hash = pwd_context.hash(password)
        self.id = str(uuid.uuid4())
    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)
    def generate_token(self, expiration=1200):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_token(token, account):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        if data['id'] == account.id:
            return account

auth = HTTPBasicAuth()


adminAccount = Account(config['ui']['username'], config['ui']['password'])


@auth.verify_password
def verify_password(username, password):
    user = adminAccount.verify_token(username, adminAccount)
    if not user:
        if username == adminAccount.username and adminAccount.verify_password(password):
            g.user = adminAccount
            log.debug("HTTPAuth Allowed")
            return True
        else:
            log.debug("HTTPAuth Denied")
            return False
    g.user = adminAccount
    log.debug("HTTPAuth Allowed")
    return True
 


