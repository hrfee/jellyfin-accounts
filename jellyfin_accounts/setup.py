from flask import request, jsonify, render_template
from configparser import RawConfigParser
from jellyfin_accounts.jf_api import Jellyfin
from jellyfin_accounts import config, config_path, app, first_run
from jellyfin_accounts import web_log as log
from jellyfin_accounts.web_api import resp
import os

if first_run:

    def tempJF(server):
        return Jellyfin(
            server,
            config["jellyfin"]["client"],
            config["jellyfin"]["version"],
            config["jellyfin"]["device"] + "_temp",
            config["jellyfin"]["device_id"] + "_temp",
        )

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("404.html"), 404

    @app.route("/", methods=["GET", "POST"])
    def setup():
        return render_template("setup.html")

    @app.route("/<path:path>")
    def static_proxy(path):
        if "html" not in path:
            return app.send_static_file(path)
        else:
            return render_template("404.html"), 404

    @app.route("/modifyConfig", methods=["POST"])
    def modifyConfig():
        log.info("Config modification requested")
        data = request.get_json()
        temp_config = RawConfigParser(comment_prefixes="/", allow_no_value=True)
        temp_config.read(config_path)
        for section in data:
            if section in temp_config:
                for item in data[section]:
                    if item in temp_config[section]:
                        temp_config[section][item] = data[section][item]
                        data[section][item] = True
                        log.debug(f"{section}/{item} modified")
                    else:
                        data[section][item] = False
                        log.debug(f"{section}/{item} does not exist in config")
        with open(config_path, "w") as config_file:
            temp_config.write(config_file)
        log.debug("Config written")
        # ugly exit, sorry
        os._exit(1)
        return resp()

    @app.route("/testJF", methods=["GET", "POST"])
    def testJF():
        data = request.get_json()
        tempjf = tempJF(data["jfHost"])
        try:
            tempjf.authenticate(data["jfUser"], data["jfPassword"])
            tempjf.getUsers(public=False)
            return resp()
        except:
            return resp(False)
