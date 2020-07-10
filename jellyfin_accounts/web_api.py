from flask import request, jsonify
from jellyfin_accounts.jf_api import Jellyfin
import json
import datetime
import secrets
import time
from jellyfin_accounts import (
    config,
    config_path,
    load_config,
    data_dir,
    app,
    g,
    data_store,
    resp,
    configparser,
    config_base_path,
)
from jellyfin_accounts import web_log as log
from jellyfin_accounts.validate_password import PasswordValidator


def format_datetime(dt):
    result = dt.strftime(config["email"]["date_format"])
    if config.getboolean("email", "use_24h"):
        result += f' {dt.strftime("%H:%M")}'
    else:
        result += f' {dt.strftime("%I:%M %p")}'
    return result


def checkInvite(code, used=False, username=None):
    current_time = datetime.datetime.now()
    invites = dict(data_store.invites)
    match = False
    for invite in invites:
        if (
            "remaining-uses" not in invites[invite]
            and "no-limit" not in invites[invite]
        ):
            invites[invite]["remaining-uses"] = 1
        expiry = datetime.datetime.strptime(
            invites[invite]["valid_till"], "%Y-%m-%dT%H:%M:%S.%f"
        )
        if current_time >= expiry or (
            "no-limit" not in invites[invite] and invites[invite]["remaining-uses"] < 1
        ):
            log.debug(f"Housekeeping: Deleting expired invite {invite}")
            del data_store.invites[invite]
        elif invite == code:
            match = True
            if used:
                delete = False
                inv = dict(data_store.invites[code])
                if "used-by" not in inv:
                    inv["used-by"] = []
                if "remaining-uses" in inv:
                    if inv["remaining-uses"] == 1:
                        delete = True
                        del data_store.invites[code]
                    elif "no-limit" not in invites[invite]:
                        inv["remaining-uses"] -= 1
                inv["used-by"].append([username, format_datetime(current_time)])
                if not delete:
                    data_store.invites[code] = inv
    return match


jf = Jellyfin(
    config["jellyfin"]["server"],
    config["jellyfin"]["client"],
    config["jellyfin"]["version"],
    config["jellyfin"]["device"],
    config["jellyfin"]["device_id"],
)

from jellyfin_accounts.login import auth

jf_address = config["jellyfin"]["server"]
success = False
for i in range(3):
    try:
        jf.authenticate(config["jellyfin"]["username"], config["jellyfin"]["password"])
        success = True
        log.info(f"Successfully authenticated with {jf_address}")
        break
    except Jellyfin.AuthenticationError:
        log.error(f"Failed to authenticate with {jf_address}, Retrying...")
        time.sleep(5)

if not success:
    log.error("Could not authenticate after 3 tries.")
    exit()

# Temporary fixes below.


def switchToIds():
    try:
        with open(config["files"]["emails"], "r") as f:
            emails = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        emails = {}
    users = jf.getUsers(public=False)
    new_emails = {}
    match = False
    for key in emails:
        for user in users:
            if user["Name"] == key:
                match = True
                new_emails[user["Id"]] = emails[key]
            elif user["Id"] == key:
                new_emails[user["Id"]] = emails[key]
    if match:
        from pathlib import Path

        email_file = Path(config["files"]["emails"]).name
        log.info(
            (
                f"{email_file} modified to use userID instead of "
                + "usernames. These will be used in future."
            )
        )
        emails = new_emails
        with open(config["files"]["emails"], "w") as f:
            f.write(json.dumps(emails, indent=4))


# Temporary, switches emails.json over from using Usernames to User IDs.
switchToIds()


from packaging import version

if (
    version.parse(jf.info["Version"]) >= version.parse("10.6.0")
    and bool(data_store.user_template) is not False
):
    log.info("Updating user_template for Jellyfin >= 10.6.0")
    if (
        data_store.user_template["AuthenticationProviderId"]
        == "Emby.Server.Implementations.Library.DefaultAuthenticationProvider"
    ):
        data_store.user_template[
            "AuthenticationProviderId"
        ] = "Jellyfin.Server.Implementations.Users.DefaultAuthenticationProvider"
    if (
        data_store.user_template["PasswordResetProviderId"]
        == "Emby.Server.Implementations.Library.DefaultPasswordResetProvider"
    ):
        data_store.user_template[
            "PasswordResetProviderId"
        ] = "Jellyfin.Server.Implementations.Users.DefaultPasswordResetProvider"


if config.getboolean("password_validation", "enabled"):
    validator = PasswordValidator(
        config["password_validation"]["min_length"],
        config["password_validation"]["upper"],
        config["password_validation"]["lower"],
        config["password_validation"]["number"],
        config["password_validation"]["special"],
    )
else:
    validator = PasswordValidator(0, 0, 0, 0, 0)


@app.route("/newUser", methods=["POST"])
def newUser():
    data = request.get_json()
    log.debug("Attempted newUser")
    if checkInvite(data["code"]):
        validation = validator.validate(data["password"])
        valid = True
        for criterion in validation:
            if validation[criterion] is False:
                valid = False
        if valid:
            log.debug("User password valid")
            try:
                user = jf.newUser(data["username"], data["password"])
            except Jellyfin.UserExistsError:
                error = f'User already exists named {data["username"]}'
                log.debug(error)
                return jsonify({"error": error})
            except:
                return jsonify({"error": "Unknown error"})
            checkInvite(data["code"], used=True, username=data["username"])
            if user.status_code == 200:
                try:
                    policy = data_store.user_template
                    if policy != {}:
                        jf.setPolicy(user.json()["Id"], policy)
                    else:
                        log.debug("user policy was blank")
                except:
                    log.error("Failed to set new user policy")
                try:
                    configuration = data_store.user_configuration
                    displayprefs = data_store.user_displayprefs
                    if configuration != {} and displayprefs != {}:
                        if jf.setConfiguration(user.json()["Id"], configuration):
                            jf.setDisplayPreferences(user.json()["Id"], displayprefs)
                            log.debug("Set homescreen layout.")
                    else:
                        log.debug(
                            "user configuration and/or " + "displayprefs were blank"
                        )
                except:
                    log.error("Failed to set new user homescreen layout")
                if config.getboolean("password_resets", "enabled"):
                    data_store.emails[user.json()["Id"]] = data["email"]
                    log.debug("Email address stored")
                log.info("New user created")
            else:
                log.error(f"New user creation failed: {user.status_code}")
                return resp(False)
        else:
            log.debug("User password invalid")
        return jsonify(validation)
    else:
        log.debug("Attempted newUser unauthorized")
        return resp(False, code=401)


@app.route("/generateInvite", methods=["POST"])
@auth.login_required
def generateInvite():
    current_time = datetime.datetime.now()
    data = request.get_json()
    delta = datetime.timedelta(
        days=int(data["days"]), hours=int(data["hours"]), minutes=int(data["minutes"])
    )
    invite_code = secrets.token_urlsafe(16)
    invite = {}
    invite["created"] = format_datetime(current_time)
    if data["multiple-uses"]:
        if data["no-limit"]:
            invite["no-limit"] = True
        else:
            invite["remaining-uses"] = int(data["remaining-uses"])
    else:
        invite["remaining-uses"] = 1
    log.debug(f"Creating new invite: {invite_code}")
    valid_till = current_time + delta
    invite["valid_till"] = valid_till.strftime("%Y-%m-%dT%H:%M:%S.%f")
    if "email" in data and config.getboolean("invite_emails", "enabled"):
        address = data["email"]
        invite["email"] = address
        log.info(f"Sending invite to {address}")
        method = config["email"]["method"]
        if method == "mailgun":
            from jellyfin_accounts.email import Mailgun

            email = Mailgun(address)
        elif method == "smtp":
            from jellyfin_accounts.email import Smtp

            email = Smtp(address)
        email.construct_invite({"expiry": valid_till, "code": invite_code})
        response = email.send()
        if response is False or type(response) != bool:
            invite["email"] = f"Failed to send to {address}"
    data_store.invites[invite_code] = invite
    log.info(f"New invite created: {invite_code}")
    return resp()


@app.route("/getInvites", methods=["GET"])
@auth.login_required
def getInvites():
    log.debug("Invites requested")
    current_time = datetime.datetime.now()
    invites = dict(data_store.invites)
    for code in invites:
        checkInvite(code)
    invites = dict(data_store.invites)
    response = {"invites": []}
    for code in invites:
        expiry = datetime.datetime.strptime(
            invites[code]["valid_till"], "%Y-%m-%dT%H:%M:%S.%f"
        )
        valid_for = expiry - current_time
        invite = {
            "code": code,
            "days": valid_for.days,
            "hours": valid_for.seconds // 3600,
            "minutes": (valid_for.seconds // 60) % 60,
        }
        if "created" in invites[code]:
            invite["created"] = invites[code]["created"]
        if "used-by" in invites[code]:
            invite["used-by"] = invites[code]["used-by"]
        if "no-limit" in invites[code]:
            invite["no-limit"] = invites[code]["no-limit"]
        if "remaining-uses" in invites[code]:
            invite["remaining-uses"] = invites[code]["remaining-uses"]
        else:
            invite["remaining-uses"] = 1
        if "email" in invites[code]:
            invite["email"] = invites[code]["email"]
        response["invites"].append(invite)
    return jsonify(response)


@app.route("/deleteInvite", methods=["POST"])
@auth.login_required
def deleteInvite():
    code = request.get_json()["code"]
    invites = dict(data_store.invites)
    if code in invites:
        del data_store.invites[code]
    log.info(f"Invite deleted: {code}")
    return resp()


@app.route("/getToken")
@auth.login_required
def get_token():
    token = g.user.generate_token()
    return jsonify({"token": token.decode("ascii")})


@app.route("/getUsers", methods=["GET"])
@auth.login_required
def getUsers():
    log.debug("User and email list requested")
    response = {"users": []}
    users = jf.getUsers(public=False)
    emails = data_store.emails
    for user in users:
        entry = {"name": user["Name"]}
        if user["Id"] in emails:
            entry["email"] = emails[user["Id"]]
        response["users"].append(entry)
    return jsonify(response)


@app.route("/modifyUsers", methods=["POST"])
@auth.login_required
def modifyUsers():
    data = request.get_json()
    log.debug("Email list modification requested")
    for key in data:
        uid = jf.getUsers(key, public=False)["Id"]
        data_store.emails[uid] = data[key]
        log.debug(f'Email for user "{key}" modified')
    return resp()


@app.route("/setDefaults", methods=["POST"])
@auth.login_required
def setDefaults():
    data = request.get_json()
    username = data["username"]
    log.debug(f"Storing default settings from user {username}")
    try:
        user = jf.getUsers(username=username, public=False)
    except Jellyfin.UserNotFoundError:
        log.error(f"Storing defaults failed: Couldn't find user {username}")
        return resp(False)
    uid = user["Id"]
    policy = user["Policy"]
    data_store.user_template = policy
    if data["homescreen"]:
        configuration = user["Configuration"]
        try:
            displayprefs = jf.getDisplayPreferences(uid)
            data_store.user_configuration = configuration
            data_store.user_displayprefs = displayprefs
        except:
            log.error("Storing defaults failed: " + "couldn't store homescreen layout")
            return resp(False)
    return resp()


@app.route("/modifyConfig", methods=["POST"])
@auth.login_required
def modifyConfig():
    global config
    log.info("Config modification requested")
    data = request.get_json()
    temp_config = configparser.RawConfigParser(
        comment_prefixes="/", allow_no_value=True
    )
    temp_config.read(config_path)
    for section in data:
        if section in temp_config:
            for item in data[section]:
                temp_config[section][item] = data[section][item]
                data[section][item] = True
                log.debug(f"{section}/{item} modified")
    with open(config_path, "w") as config_file:
        temp_config.write(config_file)
    config = load_config(config_path, data_dir)
    log.info("Config written. Restart may be needed to load settings.")
    return resp()


# @app.route('/getConfig', methods=["GET"])
# @auth.login_required
# def getConfig():
#     log.debug('Config requested')
#     return jsonify(config._sections), 200


@app.route("/getConfig", methods=["GET"])
@auth.login_required
def getConfig():
    log.debug("Config requested")
    with open(config_base_path, "r") as f:
        config_base = json.load(f)
    # config.read(config_path)
    response_config = config_base
    for section in config_base:
        for entry in config_base[section]:
            if entry in config[section]:
                response_config[section][entry]["value"] = config[section][entry]
    return jsonify(response_config), 200
