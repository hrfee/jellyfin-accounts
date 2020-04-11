from flask import request, jsonify
from jellyfin_accounts.jf_api import Jellyfin
import json
import datetime
import secrets
from __main__ import config, app, g
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

jf.authenticate(config['jellyfin']['username'], 
                config['jellyfin']['password'])


@app.route('/newUser', methods=['GET', 'POST'])
def newUser():
    data = request.get_json()
    if checkInvite(data['code'], delete=True):
        user = jf.newUser(data['username'], data['password'])
        if user.status_code == 200:
            try:
                with open(config['files']['user_template'], 'r') as f:
                    default_policy = json.load(f)
                jf.setPolicy(user.json()['Id'], default_policy)
            except:
                pass
            if config['ui']['emails_enabled'] == 'true':
                try:
                    with open(config['files']['emails'], 'r') as f:
                        emails = json.load(f)
                except (FileNotFoundError, json.decoder.JSONDecodeError):
                    emails = {}
                emails[data['username']] = data['email']
                with open(config['files']['emails'], 'w') as f:
                    f.write(json.dumps(emails, indent=4))
            return resp()
        else:
            return resp(False)
    else:
        return resp(False, code=401)


@app.route('/generateInvite', methods=['GET', 'POST'])
@auth.login_required
def generateInvite():
    current_time = datetime.datetime.now()
    data = request.get_json()
    delta = datetime.timedelta(hours=int(data['hours']), 
                               minutes=int(data['minutes']))
    invite = {'code': secrets.token_urlsafe(16)}
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
    return resp()


@app.route('/getInvites', methods=['GET'])
@auth.login_required
def getInvites():
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
    return resp()


@app.route('/getToken')
@auth.login_required
def get_token():
    token = g.user.generate_token()
    return jsonify({'token': token.decode('ascii')})



