import json
from pathlib import Path
from flask import Flask, send_from_directory, render_template
from __main__ import config, app, g
from __main__ import web_log as log
from jellyfin_accounts.web_api import checkInvite, validator


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
                           contactMessage=config['ui']['contact_message']), 404


@app.route('/', methods=['GET', 'POST'])
def admin():
    # return app.send_static_file('admin.html')
    return render_template('admin.html',
                           contactMessage='')


@app.route('/<path:path>')
def static_proxy(path):
    if 'html' not in path:
        return app.send_static_file(path)
    return render_template('404.html',
                           contactMessage=config['ui']['contact_message']), 404



@app.route('/invite/<path:path>')
def inviteProxy(path):
    if checkInvite(path):
        log.info(f'Invite {path} used to request form')
        try:
            with open(config['files']['invites'], 'r') as f:
                invites = json.load(f)
        except (FileNotFoundError, json.decoder.JSONDecodeError):
            invites = {'invites': []}
        for invite in invites['invites']:
            if invite['code'] == path:
                try:
                    email = invite['email']
                except KeyError:
                    email = ""
        return render_template('form.html',
                               contactMessage=config['ui']['contact_message'],
                               helpMessage=config['ui']['help_message'],
                               successMessage=config['ui']['success_message'],
                               jfLink=config['jellyfin']['server'],
                               validate=config.getboolean('password_validation',
                                                          'enabled'),
                               requirements=validator.getCriteria(),
                               email=email)
    elif 'admin.html' not in path and 'admin.html' not in path:
        return app.send_static_file(path)
    else:
        log.debug('Attempted use of invalid invite')
        return render_template('invalidCode.html',
                               contactMessage=config['ui']['contact_message'])
