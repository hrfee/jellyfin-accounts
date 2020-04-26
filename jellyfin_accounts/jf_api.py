#!/usr/bin/env python3
import requests


class Error(Exception):
    pass

class Jellyfin:
    class UserExistsError(Error):
        pass
    class UserNotFoundError(Error):
        pass
    class AuthenticationError(Error):
        pass
    class AuthenticationRequiredError(Error):
        pass
    def __init__(self, server, client, version, device, deviceId):
        self.server = server
        self.client = client
        self.version = version
        self.device = device
        self.deviceId = deviceId
        self.useragent = f"{self.client}/{self.version}"
        self.auth = "MediaBrowser "
        self.auth += f"Client={self.client}, "
        self.auth += f"Device={self.device}, "
        self.auth += f"DeviceId={self.deviceId}, "
        self.auth += f"Version={self.version}"
        self.header = {
           "Accept": "application/json",
           "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
           "X-Application": f"{self.client}/{self.version}",
           "Accept-Charset": "UTF-8,*",
           "Accept-encoding": "gzip",
           "User-Agent": self.useragent,
           "X-Emby-Authorization": self.auth
        }
    def getUsers(self, username="all", id="all", public=True):
        if public is True:
            response = requests.get(self.server+"/emby/Users/Public").json()
        elif public is False and hasattr(self, 'username') and hasattr(self, 'password'):
            response = requests.get(self.server+"/emby/Users",
                                    headers=self.header,
                                    params={'Username': self.username,
                                            'Pw': self.password})
            if response.status_code == 200:
                response = response.json()
            else:
                try:
                    self.authenticate(self.username, self.password)
                    return self.getUsers(username, id, public)
                except self.AuthenticationError:
                    raise self.AuthenticationRequiredError
        else:
            raise self.AuthenticationRequiredError
        if username == "all" and id == "all":
            return response
        elif id == "all":
            match = False
            for user in response:
                if user['Name'] == username:
                    match = True
                    return user
            if not match:
                raise self.UserNotFoundError
        else:
            match = False
            for user in response:
                if user['Id'] == id:
                    match = True
                    return user
            if not match:
                raise self.UserNotFoundError
    def authenticate(self, username, password):
        self.username = username
        self.password = password
        response = requests.post(self.server+"/emby/Users/AuthenticateByName",
                                 headers=self.header,
                                 params={'Username': self.username,
                                         'Pw': self.password})
        if response.status_code == 200:
            json = response.json()
            self.userId = json['User']['Id']
            self.accessToken = json['AccessToken']
            self.auth = "MediaBrowser "
            self.auth += f"Client={self.client}, "
            self.auth += f"Device={self.device}, "
            self.auth += f"DeviceId={self.deviceId}, "
            self.auth += f"Version={self.version}"
            self.auth += f", Token={self.accessToken}"
            self.header['X-Emby-Authorization'] = self.auth
            return True
        else:
            raise self.AuthenticationError
    def setPolicy(self, userId, policy):
        return requests.post(self.server+"/Users/"+userId+"/Policy",
                             headers=self.header,
                             params=policy)
    def newUser(self, username, password):
        for user in self.getUsers():
            if user['Name'] == username:
                raise self.UserExistsError
        response = requests.post(self.server+"/emby/Users/New",
                                 headers=self.header,
                                 params={'Name': username,
                                         'Password': password})
        if response.status_code == 401:
            if hasattr(self, 'username') and hasattr(self, 'password'):
                self.authenticate(self.username, self.password)
                return self.newUser(username, password)
            else:
                raise self.AuthenticationRequiredError
        return response

# template user's policies should be copied to each new account.
