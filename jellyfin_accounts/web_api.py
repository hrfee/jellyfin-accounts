from flask import request, jsonify
from jellyfin_accounts.jf_api import Jellyfin
import json
import datetime
import secrets
import time
from __main__ import config, app, g
from __main__ import web_log as log
from jellyfin_accounts.login import auth

def resp(success=True, code=500):
    if success:
        r = jsonify({'success': True})
        r.status_code = 200
    else:
        r = jsonify({'success': False})
        r.status_code = code
    return r


def checkInvite(code, delete=False):
    current_time = datetime.datetime.now()
    try:
        with open(config['files']['invites'], 'r') as f:
            invites = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        invites = {'invites': []}
    valid = False
    for index, i in enumerate(invites['invites']):
        expiry = datetime.datetime.strptime(i['valid_till'],
                                            '%Y-%m-%dT%H:%M:%S.%f')
        if current_time >= expiry:
            log.debug(('Housekeeping: Deleting old invite ' +
                       invites['invites'][index]['code']))
            del invites['invites'][index]
        else:
            if i['code'] == code:
                valid = True
                if delete:
                    del invites['invites'][index]
    with open(config['files']['invites'], 'w') as f:
        f.write(json.dumps(invites, indent=4, default=str))
    return valid


jf = Jellyfin(config['jellyfin']['server'],
              config['jellyfin']['client'],
              config['jellyfin']['version'],
              config['jellyfin']['device'],
              config['jellyfin']['device_id'])

attempts = 0
while attempts != 3:
    try:
        jf.authenticate(config['jellyfin']['username'],
                        config['jellyfin']['password'])
        log.info(('Successfully authenticated with ' +
                 config['jellyfin']['server']))
        break
    except jellyfin_accounts.jf_api.AuthenticationError:
        attempts += 1
        log.error(('Failed to authenticate with ' +
                   config['jellyfin']['server'] + 
                   '. Retrying...'))
        time.sleep(5)


@app.route('/newUser', methods=['GET', 'POST'])
def newUser():
    data = request.get_json()
    log.debug('Attempted newUser')
    if checkInvite(data['code'], delete=True):
        user = jf.newUser(data['username'], data['password'])
        if user.status_code == 200:
            try:
                with open(config['files']['user_template'], 'r') as f:
                    default_policy = json.load(f)
                jf.setPolicy(user.json()['Id'], default_policy)
            except:
                log.debug('setPolicy failed')
                pass
            if config.getboolean('email', 'enabled'):
                try:
                    with open(config['files']['emails'], 'r') as f:
                        emails = json.load(f)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    emails = {}
                emails[data['username']] = data['email']
                with open(config['files']['emails'], 'w') as f:
                    f.write(json.dumps(emails, indent=4))
                log.debug('Email address stored')
            log.info('New User created.')
            return resp()
        else:
            log.error(f'New user creation failed: {user.status_code}')
            return resp(False)
    else:
        log.debug('Attempted newUser unauthorized')
        return resp(False, code=401)


@app.route('/generateInvite', methods=['GET', 'POST'])
@auth.login_required
def generateInvite():
    current_time = datetime.datetime.now()
    data = request.get_json()
    delta = datetime.timedelta(hours=int(data['hours']), 
                               minutes=int(data['minutes']))
    invite = {'code': secrets.token_urlsafe(16)}
    log.debug(f'Creating new invite: {invite["code"]}')
    invite['valid_till'] = (current_time +
                            delta).strftime('%Y-%m-%dT%H:%M:%S.%f')
    try:
        with open(config['files']['invites'], 'r') as f:
            invites = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        invites = {'invites': []}
    invites['invites'].append(invite)
    with open(config['files']['invites'], 'w') as f:
        f.write(json.dumps(invites, indent=4, default=str))
    log.info(f'New invite created: {invite["code"]}')
    return resp()


@app.route('/getInvites', methods=['GET'])
@auth.login_required
def getInvites():
    log.debug('Invites requested')
    current_time = datetime.datetime.now()
    try:
        with open(config['files']['invites'], 'r') as f:
            invites = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        invites = {'invites': []}
    response = {'invites': []}
    for index, i in enumerate(invites['invites']):
        expiry = datetime.datetime.strptime(i['valid_till'], '%Y-%m-%dT%H:%M:%S.%f')
        if current_time >= expiry:
            log.debug(('Housekeeping: Deleting old invite ' +
                       invites['invites'][index]['code']))
            del invites['invites'][index]
        else:
            valid_for = expiry - current_time
            response['invites'].append({
                'code': i['code'],
                'hours': valid_for.seconds//3600,
                'minutes': (valid_for.seconds//60) % 60})
    with open(config['files']['invites'], 'w') as f:
        f.write(json.dumps(invites, indent=4, default=str))
    return jsonify(response)  


@app.route('/deleteInvite', methods=['POST'])
@auth.login_required
def deleteInvite():
    code = request.get_json()['code']
    try:
        with open(config['files']['invites'], 'r') as f:
            invites = json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        invites = {'invites': []}
    for index, i in enumerate(invites['invites']):
        if i['code'] == code:
            del invites['invites'][index]
            with open(config['files']['invites'], 'w') as f:
                f.write(json.dumps(invites, indent=4, default=str))
    log.info(f'Invite deleted: {code}')
    return resp()


@app.route('/getToken')
@auth.login_required
def get_token():
    token = g.user.generate_token()
    log.debug('Token generated')
    return jsonify({'token': token.decode('ascii')})



