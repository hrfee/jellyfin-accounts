import json
import datetime


class JSONFile(dict):
    """
    Behaves like a dictionary, but automatically
    reads and writes to a JSON file (most of the time).
    """

    @staticmethod
    def readJSON(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    @staticmethod
    def writeJSON(path, data):
        with open(path, "w") as f:
            return f.write(json.dumps(data, indent=4, default=str))

    def __init__(self, path, data=None):
        self.path = path
        if data is None:
            super(JSONFile, self).__init__(self.readJSON(self.path))
        else:
            super(JSONFile, self).__init__(data)
            self.writeJSON(self.path, data)

    def __getitem__(self, key):
        super(JSONFile, self).__init__(self.readJSON(self.path))
        return super(JSONFile, self).__getitem__(key)

    def __setitem__(self, key, value):
        data = self.readJSON(self.path)
        data[key] = value
        self.writeJSON(self.path, data)
        super(JSONFile, self).__init__(data)

    def __delitem__(self, key):
        data = self.readJSON(self.path)
        super(JSONFile, self).__init__(data)
        del data[key]
        self.writeJSON(self.path, data)
        super(JSONFile, self).__delitem__(key)

    def __str__(self):
        super(JSONFile, self).__init__(self.readJSON(self.path))
        return json.dumps(super(JSONFile, self))


class JSONStorage:
    def __init__(
        self, emails, invites, user_template, user_displayprefs, user_configuration
    ):
        self.emails = JSONFile(path=emails)
        self.invites = JSONFile(path=invites)
        self.user_template = JSONFile(path=user_template)
        self.user_displayprefs = JSONFile(path=user_displayprefs)
        self.user_configuration = JSONFile(path=user_configuration)

    def __setattr__(self, name, value):
        if hasattr(self, name):
            path = self.__dict__[name].path
            self.__dict__[name] = JSONFile(path=path, data=value)
        else:
            self.__dict__[name] = value
