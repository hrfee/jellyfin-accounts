# jellyfin-accounts
A simple, web-based invite system for [Jellyfin](https://github.com/jellyfin/jellyfin).
* Uses a basic python jellyfin API client for communication with the server. 
* Uses [Flask](https://github.com/pallets/flask), [HTTPAuth](https://github.com/miguelgrinberg/Flask-HTTPAuth), [itsdangerous](https://github.com/pallets/itsdangerous), and [Waitress](https://github.com/Pylons/waitress)
* Frontend uses [Bootstrap](https://getbootstrap.com), [jQuery](https://jquery.com) and [jQuery-serialize-object](https://github.com/macek/jquery-serialize-object)
## Screenshots
<p align="center">
    <img src="images/admin.png" width="45%"></img> <img src="images/create.png" width="45%"></img>
</p>

## Get it
### Requirements
* python >= 3.6
* flask
* flask_httpauth
* requests
* itsdangerous
* passlib
* secrets
* configparser
* waitress

### Install
```
git clone https://github.com/hrfee/jellyfin-accounts.git
cd jellyfin-accounts
python3 setup.py install
```

### Usage
* Passing no arguments will run the server
```
usage: jf-accounts [-h] [-c CONFIG] [-d DATA] [--host HOST] [-p PORT] [-g]

jellyfin-accounts

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        specifies path to configuration file.
  -d DATA, --data DATA  specifies directory to store data in. defaults to
                        ~/.jf-accounts.
  --host HOST           address to host web ui on.
  -p PORT, --port PORT  port to host web ui on.
  -g, --get_policy      tool to grab a JF users policy (access, perms, etc.)
                        and output as json to be used as a user template.
```
### Setup
#### Policy template
* You may want to restrict from accessing certain libraries (e.g 4K Movies), or display their account on the login screen by default. Jellyfin stores these settings as a user's policy.
* Make a temporary account and change its settings, then run `jf-accounts --get_policy`. Choose your user, and the policy will be stored at the location you set in `user_template`, and used for all subsequent new accounts.

### Configuration
* Note: Make sure to put this behind a reverse proxy with HTTPS.

On first run, the default configuration is copied to `~/.jf-accounts/config.ini`.
```
; It is reccommended to create a limited admin account for this program.
[jellyfin]
username = username
password = password
; Server will also be used in the invite form, so make sure it's publicly accessible.
server = https://jellyf.in:443
client = jf-accounts
version = 0.1
device = jf-accounts
device_id = jf-accounts-0.1

[ui]
host = 127.0.0.1
port = 8056
username = your username
password = your password
debug = false
; Enable to store request email address and store. Useful for sending password reset emails.
emails_enabled = false

; Displayed at the bottom of all pages except admin.
contact_message = Need help? contact me.
; Displayed at top of form page.
help_message =  Enter your details to create an account.
; Displayed when an account is created.
success_message = Your account has been created. Click below to continue to Jellyfin.


[files]
; When the below paths are left blank, files are stored in ~/.jf-accounts/.

; Path to store valid invites.
invites = 
; Path to store emails in JSON
emails = 
; Path to the user policy template. Can be acquired with get-template.
user_template = 
```

### Todo
* Fix pip install (possible related to using `data_files` over `package_data`?)
* Properly integrate with a janky password reset email system i've written.
* Improve `generateInvites` in admin.js to refresh each invite's data, instead of deleting and recreating them.
* Fix weird alignment of invite codes and the generate button (I know, i'm very new to web development)
