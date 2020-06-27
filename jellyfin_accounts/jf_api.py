#!/usr/bin/env python3
import requests
import time


class Error(Exception):
    pass


class Jellyfin:
    """
    Basic Jellyfin API client, providing account related function only.
    """

    class UserExistsError(Error):
        """
        Thrown if a user already exists with the same name
        when creating an account.
        """

        pass

    class UserNotFoundError(Error):
        """Thrown if account with specified user ID/name does not exist."""

        pass

    class AuthenticationError(Error):
        """Thrown if authentication with Jellyfin fails."""

        pass

    class AuthenticationRequiredError(Error):
        """
        Thrown if privileged action is attempted without authentication.
        """

        pass

    class UnknownError(Error):
        """
        Thrown if i've been too lazy to figure out an error's meaning.
        """

        pass

    def __init__(self, server, client, version, device, deviceId):
        """
        Initializes the Jellyfin object. All parameters except server
        have no effect on the client's capability.

        :param server: Web address of the server to connect to.
        :param client: Name of the client. Appears on Jellyfin
                       server dashboard.
        :param version: Version of the client.
        :param device: Name of the device the client is running on.
        :param deviceId: ID of the device the client is running on.
        """
        self.server = server
        self.client = client
        self.version = version
        self.device = device
        self.deviceId = deviceId
        self.timeout = 30 * 60
        self.userCacheAge = time.time() - self.timeout - 1
        self.userCachePublicAge = self.userCacheAge
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
            "X-Emby-Authorization": self.auth,
        }
        self.info = requests.get(self.server + "/System/Info/Public").json()

    def getUsers(self, username: str = "all", userId: str = "all", public: bool = True):
        """
        Returns details on user(s), such as ID, Name, Policy.

        :param username: (optional) Username to get info about.
                         Leave blank to get all users.
        :param userId: (optional) User ID to get info about.
                   Leave blank to get all users.
        :param public: True = Get publicly visible users only (no auth required),
                        False = Get all users (auth required).
        """
        if public is True:
            if (time.time() - self.userCachePublicAge) >= self.timeout:
                response = requests.get(self.server + "/emby/Users/Public").json()
                self.userCachePublic = response
                self.userCachePublicAge = time.time()
            else:
                response = self.userCachePublic
        elif (
            public is False and hasattr(self, "username") and hasattr(self, "password")
        ):
            if (time.time() - self.userCacheAge) >= self.timeout:
                response = requests.get(
                    self.server + "/emby/Users",
                    headers=self.header,
                    params={"Username": self.username, "Pw": self.password},
                )
                if response.status_code == 200:
                    response = response.json()
                    self.userCache = response
                    self.userCacheAge = time.time()
                else:
                    try:
                        self.authenticate(self.username, self.password)
                        return self.getUsers(username, userId, public)
                    except self.AuthenticationError:
                        raise self.AuthenticationRequiredError
            else:
                response = self.userCache
        else:
            raise self.AuthenticationRequiredError
        if username == "all" and userId == "all":
            return response
        elif userId == "all":
            match = False
            for user in response:
                if user["Name"] == username:
                    match = True
                    return user
            if not match:
                raise self.UserNotFoundError
        else:
            match = False
            for user in response:
                if user["Id"] == userId:
                    match = True
                    return user
            if not match:
                raise self.UserNotFoundError

    def authenticate(self, username: str, password: str):
        """
        Authenticates by name with Jellyfin.

        :param username: Plaintext username.
        :param password: Plaintext password.
        """
        self.username = username
        self.password = password
        response = requests.post(
            self.server + "/emby/Users/AuthenticateByName",
            headers=self.header,
            params={"Username": self.username, "Pw": self.password},
        )
        if response.status_code == 200:
            json = response.json()
            self.userId = json["User"]["Id"]
            self.accessToken = json["AccessToken"]
            self.auth = "MediaBrowser "
            self.auth += f"Client={self.client}, "
            self.auth += f"Device={self.device}, "
            self.auth += f"DeviceId={self.deviceId}, "
            self.auth += f"Version={self.version}"
            self.auth += f", Token={self.accessToken}"
            self.header["X-Emby-Authorization"] = self.auth
            self.info = requests.get(
                self.server + "/System/Info", headers=self.header
            ).json()
            return True
        else:
            raise self.AuthenticationError

    def setPolicy(self, userId: str, policy: dict):
        """
        Sets a user's policy (Admin rights, Library Access, etc.) by user ID.

        :param userId: ID of the user to modify.
        :param policy: User policy in dictionary form.
        """
        return requests.post(
            self.server + "/Users/" + userId + "/Policy",
            headers=self.header,
            params=policy,
        )

    def newUser(self, username: str, password: str):
        for user in self.getUsers():
            if user["Name"] == username:
                raise self.UserExistsError
        response = requests.post(
            self.server + "/emby/Users/New",
            headers=self.header,
            params={"Name": username, "Password": password},
        )
        if response.status_code == 401:
            if hasattr(self, "username") and hasattr(self, "password"):
                self.authenticate(self.username, self.password)
                return self.newUser(username, password)
            else:
                raise self.AuthenticationRequiredError
        return response

    def getViewOrder(self, userId: str, public: bool = True):
        if not public:
            param = "?IncludeHidden=true"
        else:
            param = ""
        views = requests.get(
            self.server + "/Users/" + userId + "/Views" + param, headers=self.header
        ).json()["Items"]
        orderedViews = []
        for library in views:
            orderedViews.append(library["Id"])
        return orderedViews

    def setConfiguration(self, userId: str, configuration: dict):
        """
        Sets a user's configuration (Settings the user can change themselves).
        :param userId: ID of the user to modify.
        :param configuration: Configuration to write in dictionary form.
        """
        resp = requests.post(
            self.server + "/Users/" + userId + "/Configuration",
            headers=self.header,
            params=configuration,
        )
        if resp.status_code == 200 or resp.status_code == 204:
            return True
        elif resp.status_code == 401:
            if hasattr(self, "username") and hasattr(self, "password"):
                self.authenticate(self.username, self.password)
                return self.setConfiguration(userId, configuration)
            else:
                raise self.AuthenticationRequiredError
        else:
            raise self.UnknownError

    def getConfiguration(self, username: str = "all", userId: str = "all"):
        """
        Gets a user's Configuration. This can also be found in getUsers if
        public is set to False.
        :param username: The user's username.
        :param userId: The user's ID.
        """
        return self.getUsers(username=username, userId=userId, public=False)[
            "Configuration"
        ]

    def getDisplayPreferences(self, userId: str):
        """
        Gets a user's Display Preferences (Home layout).
        :param userId: The user's ID.
        """
        resp = requests.get(
            (
                self.server
                + "/DisplayPreferences/usersettings"
                + "?userId="
                + userId
                + "&client=emby"
            ),
            headers=self.header,
        )
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 401:
            if hasattr(self, "username") and hasattr(self, "password"):
                self.authenticate(self.username, self.password)
                return self.getDisplayPreferences(userId)
            else:
                raise self.AuthenticationRequiredError
        else:
            raise self.UnknownError

    def setDisplayPreferences(self, userId: str, preferences: dict):
        """
        Sets a user's Display Preferences (Home layout).
        :param userId: The user's ID.
        :param preferences: The preferences to set.
        """
        tempheader = self.header
        tempheader["Content-type"] = "application/json"
        resp = requests.post(
            (
                self.server
                + "/DisplayPreferences/usersettings"
                + "?userId="
                + userId
                + "&client=emby"
            ),
            headers=tempheader,
            json=preferences,
        )
        if resp.status_code == 200 or resp.status_code == 204:
            return True
        elif resp.status_code == 401:
            if hasattr(self, "username") and hasattr(self, "password"):
                self.authenticate(self.username, self.password)
                return self.setDisplayPreferences(userId, preferences)
            else:
                raise self.AuthenticationRequiredError
        else:
            return resp
