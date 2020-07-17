# Runs it!
__version__ = "0.3.7"

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
from flask import Flask, jsonify, g
from jellyfin_accounts.data_store import JSONStorage
from jellyfin_accounts.config import Config

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
parser.add_argument(
    "-i", "--install", help="attempt to install a system service.", action="store_true"
)

args, leftovers = parser.parse_known_args()

if args.data is not None:
    data_dir = Path(args.data)
else:
    data_dir = Path.home() / ".jf-accounts"

local_dir = (Path(__file__).parent / "data").resolve()
config_base_path = local_dir / "config-base.json"

first_run = False
if data_dir.exists() is False or (data_dir / "config.ini").exists() is False:
    if not data_dir.exists():
        Path.mkdir(data_dir)
        print(f"Config dir not found, so generating at {str(data_dir)}")
    if args.config is None:
        config_path = data_dir / "config.ini"
        from jellyfin_accounts.generate_ini import generate_ini

        default_path = local_dir / "config-default.ini"
        generate_ini(config_base_path, default_path, __version__)
        shutil.copy(str(default_path), str(config_path))
        print("Setup through the web UI, or quit and edit the configuration manually.")
        first_run = True
    else:
        config_path = Path(args.config)
    print(f"config.ini can be found at {str(config_path)}")
else:
    config_path = data_dir / "config.ini"

# Temp config so logger knows whether to use debug mode or not
temp_config = configparser.RawConfigParser()
temp_config.read(config_path)


def create_log(name):
    log = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    if temp_config.getboolean("ui", "debug"):
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

config = Config(config_path, secrets.token_urlsafe(16), data_dir, local_dir, log)

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


try:
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
except FileNotFoundError:
    pass


data_store = JSONStorage(
    config["files"]["emails"],
    config["files"]["invites"],
    config["files"]["user_template"],
    config["files"]["user_displayprefs"],
    config["files"]["user_configuration"],
)

if config.getboolean("ui", "bs5"):
    css_file = "bs5-jf.css"
    log.debug("Using Bootstrap 5")
else:
    css_file = "bs4-jf.css"


with open(config_base_path, "r") as f:
    themes = json.load(f)["ui"]["theme"]

theme_options = themes["options"]

if "theme" not in config["ui"] or config["ui"]["theme"] not in theme_options:
    config["ui"]["theme"] = themes["value"]

if config.getboolean("ui", "bs5"):
    num = 5
else:
    num = 4

current_theme = config["ui"]["theme"]

if "Bootstrap" in current_theme:
    css_file = f"bs{num}.css"
elif "Jellyfin" in current_theme:
    css_file = f"bs{num}-jf.css"
elif "Custom" in current_theme and "custom_css" in config["files"]:
    if config["files"]["custom_css"] != "":
        try:
            css_path = Path(config["files"]["custom_css"])
            shutil.copy(css_path, (local_dir / "static" / css_path.name))
            log.debug(f'Loaded custom CSS "{css_path.name}"')
            css_file = css_path.name
        except FileNotFoundError:
            log.error(
                f'Custom CSS {config["files"]["custom_css"]} not found, using default.'
            )


def resp(success=True, code=500):
    if success:
        r = jsonify({"success": True})
        if code == 500:
            r.status_code = 200
        else:
            r.status_code = code
    else:
        r = jsonify({"success": False})
        r.status_code = code
    return r


def main():
    if args.install:
        executable = sys.argv[0]
        print(f'Assuming executable path "{executable}".')
        options = ["systemd"]
        for i, opt in enumerate(options):
            print(f"{i+1}: {opt}")
        success = False
        while not success:
            try:
                method = options[int(input(">: ")) - 1]
                success = True
            except IndexError:
                pass
        if method == "systemd":
            with open(local_dir / "services" / "jf-accounts.service", "r") as f:
                data = f.read()
                data = data.replace("{executable}", executable)
            service_path = str(Path("jf-accounts.service").resolve())
            with open(service_path, "w") as f:
                f.write(data)
            print(f"service written to the current directory\n({service_path}).")
            print("Place this in the appropriate directory, and reload daemons.")
    elif args.get_defaults:
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
        global app
        app = Flask(__name__, root_path=str(local_dir))
        app.config["DEBUG"] = config.getboolean("ui", "debug")
        app.config["SECRET_KEY"] = secrets.token_urlsafe(16)
        app.config["JSON_SORT_KEYS"] = False

        from waitress import serve

        if first_run:

            def signal_handler(sig, frame):
                print("Quitting...")
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            import jellyfin_accounts.setup

            host = config["ui"]["host"]
            port = config["ui"]["port"]
            log.info("Starting web UI for first run setup...")
            serve(app, host=host, port=port)
        else:
            import jellyfin_accounts.web_api
            import jellyfin_accounts.web
            import jellyfin_accounts.invite_daemon

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

            def signal_handler(sig, frame):
                print("Quitting...")
                if config.getboolean("notifications", "enabled"):
                    jellyfin_accounts.invite_daemon.inviteDaemon.stop()
                sys.exit(0)

            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            serve(app, host=host, port=int(port))
