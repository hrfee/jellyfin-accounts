from pathlib import Path
from flask import Flask, send_from_directory, render_template
from jellyfin_accounts import config, app, g, css, data_store
from jellyfin_accounts import web_log as log
from jellyfin_accounts.web_api import checkInvite, validator


@app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html",
            css_href=css["href"],
            css_integrity=css["integrity"],
            css_crossorigin=css["crossorigin"],
            contactMessage=config["ui"]["contact_message"],
        ),
        404,
    )


@app.route("/", methods=["GET", "POST"])
def admin():
    # return app.send_static_file('admin.html')
    return render_template(
        "admin.html",
        css_href=css["href"],
        css_integrity=css["integrity"],
        css_crossorigin=css["crossorigin"],
        contactMessage="",
        email_enabled=config.getboolean("invite_emails", "enabled"),
    )


@app.route("/<path:path>")
def static_proxy(path):
    if "html" not in path:
        return app.send_static_file(path)
    return (
        render_template(
            "404.html",
            css_href=css["href"],
            css_integrity=css["integrity"],
            css_crossorigin=css["crossorigin"],
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
            css_href=css["href"],
            css_integrity=css["integrity"],
            css_crossorigin=css["crossorigin"],
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
            css_href=css["href"],
            css_integrity=css["integrity"],
            css_crossorigin=css["crossorigin"],
            contactMessage=config["ui"]["contact_message"],
        )
