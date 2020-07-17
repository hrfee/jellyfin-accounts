import os
import configparser
import secrets
from pathlib import Path


class Config:
    """
    Configuration object that can automatically reload modified settings.
    Behaves mostly like a dictionary.
    :param file: Path to config.ini, where parameters are set.
    :param instance: Used to identify specific jf-accounts instances in environment variables.
    :param data_dir: Path to directory with config, invites, templates, etc.
    :param local_dir: Path to internally stored config base, emails, etc.
    """

    @staticmethod
    def load_config(config_path, data_dir, local_dir, log):
        # Lord forgive me for this mess
        config = configparser.RawConfigParser()
        config.read(config_path)
        for key in config["files"]:
            if config["files"][key] == "":
                if key != "custom_css":
                    log.debug(f"Using default {key}")
                    config["files"][key] = str(data_dir / (key + ".json"))

        for key in ["user_configuration", "user_displayprefs"]:
            if key not in config["files"]:
                log.debug(f"Using default {key}")
                config["files"][key] = str(data_dir / (key + ".json"))

        if "no_username" not in config["email"]:
            config["email"]["no_username"] = "false"
            log.debug("Set no_username to false")
        if (
            "email_html" not in config["password_resets"]
            or config["password_resets"]["email_html"] == ""
        ):
            log.debug("Using default password reset email HTML template")
            config["password_resets"]["email_html"] = str(local_dir / "email.html")
        if (
            "email_text" not in config["password_resets"]
            or config["password_resets"]["email_text"] == ""
        ):
            log.debug("Using default password reset email plaintext template")
            config["password_resets"]["email_text"] = str(local_dir / "email.txt")

        if (
            "email_html" not in config["invite_emails"]
            or config["invite_emails"]["email_html"] == ""
        ):
            log.debug("Using default invite email HTML template")
            config["invite_emails"]["email_html"] = str(local_dir / "invite-email.html")
        if (
            "email_text" not in config["invite_emails"]
            or config["invite_emails"]["email_text"] == ""
        ):
            log.debug("Using default invite email plaintext template")
            config["invite_emails"]["email_text"] = str(local_dir / "invite-email.txt")
        if (
            "public_server" not in config["jellyfin"]
            or config["jellyfin"]["public_server"] == ""
        ):
            config["jellyfin"]["public_server"] = config["jellyfin"]["server"]
        if "bs5" not in config["ui"] or config["ui"]["bs5"] == "":
            config["ui"]["bs5"] = "false"
        if (
            "expiry_html" not in config["notifications"]
            or config["notifications"]["expiry_html"] == ""
        ):
            log.debug("Using default expiry notification HTML template")
            config["notifications"]["expiry_html"] = str(local_dir / "expired.html")
        if (
            "expiry_text" not in config["notifications"]
            or config["notifications"]["expiry_text"] == ""
        ):
            log.debug("Using default expiry notification plaintext template")
            config["notifications"]["expiry_text"] = str(local_dir / "expired.txt")
        if (
            "created_html" not in config["notifications"]
            or config["notifications"]["created_html"] == ""
        ):
            log.debug("Using default user creation notification HTML template")
            config["notifications"]["created_html"] = str(local_dir / "created.html")
        if (
            "created_text" not in config["notifications"]
            or config["notifications"]["created_text"] == ""
        ):
            log.debug("Using default user creation notification plaintext template")
            config["notifications"]["created_text"] = str(local_dir / "created.txt")

        return config

    def __init__(self, file, instance, data_dir, local_dir, log):
        self.config_path = Path(file)
        self.data_dir = data_dir
        self.local_dir = local_dir
        self.instance = instance
        self.log = log
        self.varname = f"JFA_{self.instance}_RELOADCONFIG"
        os.environ[self.varname] = "true"

    def __getitem__(self, key):
        if os.environ[self.varname] == "true":
            self.config = Config.load_config(
                self.config_path, self.data_dir, self.local_dir, self.log
            )
            os.environ[self.varname] = "false"
        return self.config.__getitem__(key)

    def getboolean(self, sect, key):
        if os.environ[self.varname] == "true":
            self.config = Config.load_config(
                self.config_path, self.data_dir, self.local_dir, self.log
            )
            os.environ[self.varname] = "false"
        return self.config.getboolean(sect, key)

    def trigger_reload(self):
        os.environ[self.varname] = "true"
