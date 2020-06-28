#!/usr/bin/env python3
__version__ = "0.2.2"

import secrets
import configparser
import shutil
import argparse
import logging
import threading
import signal
import sys
import json
from pathlib import Path
from flask import Flask, g
from jellyfin_accounts.data_store import JSONStorage

parser = argparse.ArgumentParser(description="jellyfin-accounts")

parser.add_argument("-c", "--config", help="specifies path to configuration file.")
parser.add_argument(
    "-d",
    "--data",
    help=("specifies directory to store data in. " + "defaults to ~/.jf-accounts."),
)
parser.add_argument("--host", help="address to host web ui on.")
parser.add_argument("-p", "--port", help="port to host web ui on.")
parser.add_argument(
    "-g",
    "--get_defaults",
    help=(
        "tool to grab a JF users "
        + "policy (access, perms, etc.) and "
        + "homescreen layout and "
        + "output it as json to be used as a user template."
    ),
    action="store_true",
)

args, leftovers = parser.parse_known_args()

if args.data is not None:
    data_dir = Path(args.data)
else:
    data_dir = Path.home() / ".jf-accounts"

local_dir = (Path(__file__).parent / "data").resolve()

first_run = False
if data_dir.exists() is False or (data_dir / "config.ini").exists() is False:
    if not data_dir.exists():
        Path.mkdir(data_dir)
        print(f"Config dir not found, so created at {str(data_dir)}")
    if args.config is None:
        config_path = data_dir / "config.ini"
        shutil.copy(str(local_dir / "config-default.ini"), str(config_path))
        print("Setup through the web UI, or quit and edit the configuration manually.")
        first_run = True
    else:
        config_path = Path(args.config)
    print(f"config.ini can be found at {str(config_path)}")
else:
    config_path = data_dir / "config.ini"

config = configparser.RawConfigParser()
config.read(config_path)


def create_log(name):
    log = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    if config.getboolean("ui", "debug"):
        log.setLevel(logging.DEBUG)
        handler.setLevel(logging.DEBUG)
    else:
        log.setLevel(logging.INFO)
        handler.setLevel(logging.INFO)
    fmt = " %(name)s - %(levelname)s - %(message)s"
    format = logging.Formatter(fmt)
    handler.setFormatter(format)
    log.addHandler(handler)
    log.propagate = False
    return log


log = create_log("main")
web_log = create_log("waitress")
if not first_run:
    email_log = create_log("emails")
    auth_log = create_log("auth")

if args.host is not None:
    log.debug(f"Using specified host {args.host}")
    config["ui"]["host"] = args.host
if args.port is not None:
    log.debug(f"Using specified port {args.port}")
    config["ui"]["port"] = args.port

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

with open(config["files"]["invites"], "r") as f:
    temp_invites = json.load(f)
if "invites" in temp_invites:
    new_invites = {}
    log.info("Converting invites.json to new format, temporary.")
    for el in temp_invites["invites"]:
        i = {"valid_till": el["valid_till"]}
        if "email" in el:
            i["email"] = el["email"]
        new_invites[el["code"]] = i
    with open(config["files"]["invites"], "w") as f:
        f.write(json.dumps(new_invites, indent=4, default=str))


data_store = JSONStorage(
    config["files"]["emails"],
    config["files"]["invites"],
    config["files"]["user_template"],
    config["files"]["user_displayprefs"],
    config["files"]["user_configuration"],
)


def default_css():
    css = {}
    css[
        "href"
    ] = "https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css"
    css[
        "integrity"
    ] = "sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh"
    css["crossorigin"] = "anonymous"
    return css


css = {}
css = default_css()
if "custom_css" in config["files"]:
    if config["files"]["custom_css"] != "":
        try:
            shutil.copy(
                config["files"]["custom_css"], (local_dir / "static" / "bootstrap.css")
            )
            log.debug("Loaded custom CSS")
            css["href"] = "/bootstrap.css"
            css["integrity"] = ""
            css["crossorigin"] = ""
        except FileNotFoundError:
            log.error(
                f'Custom CSS {config["files"]["custom_css"]} not found, using default.'
            )


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


def main():
    if args.get_defaults:
        import json
        from jellyfin_accounts.jf_api import Jellyfin

        jf = Jellyfin(
            config["jellyfin"]["server"],
            config["jellyfin"]["client"],
            config["jellyfin"]["version"],
            config["jellyfin"]["device"],
            config["jellyfin"]["device_id"],
        )
        print("NOTE: This can now be done through the web ui.")
        print(
            """
        This tool lets you grab various settings from a user,
        so that they can be applied every time a new account is
        created. """
        )
        print("Step 1: User Policy.")
        print(
            """
        A user policy stores a users permissions (e.g access rights and
        most of the other settings in the 'Profile' and 'Access' tabs
        of a user). """
        )
        success = False
        msg = "Get public users only or all users? (requires auth) [public/all]: "
        public = False
        while not success:
            choice = input(msg)
            if choice == "public":
                public = True
                print("Make sure the user is publicly visible!")
                success = True
            elif choice == "all":
                jf.authenticate(
                    config["jellyfin"]["username"], config["jellyfin"]["password"]
                )
                public = False
                success = True
        users = jf.getUsers(public=public)
        for index, user in enumerate(users):
            print(f'{index+1}) {user["Name"]}')
        success = False
        while not success:
            try:
                user_index = int(input(">: ")) - 1
                policy = users[user_index]["Policy"]
                success = True
            except (ValueError, IndexError):
                pass
        data_store.user_template = policy
        print(f'Policy written to "{config["files"]["user_template"]}".')
        print("In future, this policy will be copied to all new users.")
        print("Step 2: Homescreen Layout")
        print(
            """
        You may want to customize the default layout of a new user's
        home screen. These settings can be applied to an account through
        the 'Home' section in a user's settings. """
        )
        success = False
        while not success:
            choice = input("Grab the chosen user's homescreen layout? [y/n]: ")
            if choice.lower() == "y":
                user_id = users[user_index]["Id"]
                configuration = users[user_index]["Configuration"]
                display_prefs = jf.getDisplayPreferences(user_id)
                data_store.user_configuration = configuration
                print(
                    f'Configuration written to "{config["files"]["user_configuration"]}".'
                )
                data_store.user_displayprefs = display_prefs
                print(
                    f'Display Prefs written to "{config["files"]["user_displayprefs"]}".'
                )
                success = True
            elif choice.lower() == "n":
                success = True

    else:

        def signal_handler(sig, frame):
            print("Quitting...")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        global app
        app = Flask(__name__, root_path=str(local_dir))
        app.config["DEBUG"] = config.getboolean("ui", "debug")
        app.config["SECRET_KEY"] = secrets.token_urlsafe(16)

        from waitress import serve

        if first_run:
            import jellyfin_accounts.setup

            host = config["ui"]["host"]
            port = config["ui"]["port"]
            log.info("Starting web UI for first run setup...")
            serve(app, host=host, port=port)
        else:
            import jellyfin_accounts.web_api
            import jellyfin_accounts.web

            host = config["ui"]["host"]
            port = config["ui"]["port"]
            log.info(f"Starting web UI on {host}:{port}")
            if config.getboolean("password_resets", "enabled"):

                def start_pwr():
                    import jellyfin_accounts.pw_reset

                    jellyfin_accounts.pw_reset.start()

                pwr = threading.Thread(target=start_pwr, daemon=True)
                log.info("Starting email thread")
                pwr.start()

            serve(app, host=host, port=int(port))
