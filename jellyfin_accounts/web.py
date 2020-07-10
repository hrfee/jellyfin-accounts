from pathlib import Path
from flask import Flask, send_from_directory, render_template

from jellyfin_accounts import app, g, css_file, data_store
from jellyfin_accounts import web_log as log
from jellyfin_accounts.web_api import config, checkInvite, validator


if config.getboolean("ui", "bs5"):
    bsVersion = 5
else:
    bsVersion = 4


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html",
            bs5=config.getboolean("ui", "bs5"),
            css_file=css_file,
            contactMessage=config["ui"]["contact_message"],
        ),
        404,
    )


@app.route("/", methods=["GET", "POST"])
def admin():
    # return app.send_static_file('admin.html')
    return render_template(
        "admin.html",
        bs5=config.getboolean("ui", "bs5"),
        css_file=css_file,
        contactMessage="",
        email_enabled=config.getboolean("invite_emails", "enabled"),
    )


@app.route("/<path:path>")
def static_proxy(path):
    if "html" not in path:
        if "admin.js" in path:
            return (
                render_template("admin.js", bsVersion=bsVersion, css_file=css_file),
                200,
                {"Content-Type": "text/javascript"},
            )
        return app.send_static_file(path)
    return (
        render_template(
            "404.html",
            bs5=config.getboolean("ui", "bs5"),
            css_file=css_file,
            contactMessage=config["ui"]["contact_message"],
        ),
        404,
    )


@app.route("/invite/<path:path>")
def inviteProxy(path):
    if checkInvite(path):
        log.info(f"Invite {path} used to request form")
        try:
            email = data_store.invites[path]["email"]
        except KeyError:
            email = ""
        return render_template(
            "form.html",
            bs5=config.getboolean("ui", "bs5"),
            css_file=css_file,
            contactMessage=config["ui"]["contact_message"],
            helpMessage=config["ui"]["help_message"],
            successMessage=config["ui"]["success_message"],
            jfLink=config["jellyfin"]["public_server"],
            validate=config.getboolean("password_validation", "enabled"),
            requirements=validator.getCriteria(),
            email=email,
            username=(not config.getboolean("email", "no_username")),
        )
    elif "admin.html" not in path and "admin.html" not in path:
        return app.send_static_file(path)
    else:
        log.debug("Attempted use of invalid invite")
        return render_template(
            "invalidCode.html",
            bs5=config.getboolean("ui", "bs5"),
            css_file=css_file,
            contactMessage=config["ui"]["contact_message"],
        )
