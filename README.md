# ![jellyfin-accounts](https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/jellyfin-accounts-banner-wide.svg)

A basic account management system for [Jellyfin](https://github.com/jellyfin/jellyfin).
* Provides a web interface for creating invite codes, and a simple account creation form
* Sends out emails when a user requests a password reset
* Uses a basic python jellyfin API client for communication with the server. 
* Uses [Flask](https://github.com/pallets/flask), [HTTPAuth](https://github.com/miguelgrinberg/Flask-HTTPAuth), [itsdangerous](https://github.com/pallets/itsdangerous), and [Waitress](https://github.com/Pylons/waitress)
* Frontend uses [Bootstrap](https://getbootstrap.com), [jQuery](https://jquery.com) and [jQuery-serialize-object](https://github.com/macek/jquery-serialize-object)
* Password resets are handled using smtplib, requests, and [jinja](https://github.com/pallets/jinja)
## Interface
<p align="center">
    <img src="https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/jfa.gif" width="100%"></img>
</p>

<p align="center">
    <img src="https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/jfa.gif" width="48%" style="margin-right: 1.5%;" alt="Admin page"></img> 
    <img src="https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/create.png" width="48%" style="margin-left: 1.5%;" alt="Account creation page"></img>
</p>



## Get it
### Requirements

* This should work anywhere Python does, i've tried to not use anything OS-specific. Drop an issue if there's a problem, of course.
```
* python >= 3.6
* flask
* flask_httpauth
* jinja2
* requests
* itsdangerous
* passlib
* pyOpenSSL
* waitress
* pytz
* python-dateutil
* watchdog
```
### Install

Usually as simple as:
```
pip install jellyfin-accounts
```
If not, or if you want to use docker, see [install](https://github.com/hrfee/jellyfin-accounts/wiki/Install).

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
  -g, --get_defaults    tool to grab a JF users policy (access, perms, etc.)
                        and homescreen layout and output it as json to be used
                        as a user template.
```
### Setup
#### New user template
* You may want to restrict a user from accessing certain libraries (e.g 4K Movies), display their account on the login screen by default, or set a default homecrseen layout. Jellyfin stores these settings in the user's policy, configuration and displayPreferences.
* Make a temporary account and change its settings, then run `jf-accounts --get_defaults`. Choose your user, and this data will be stored at the location you set in `user_template`, `user_configuration` and `user_displayprefs` (or their default locations), and used for all subsequent new accounts.
#### Emails/Password Resets
* When someone initiates forget password on Jellyfin, a file named `passwordreset*.json` is created in its configuration directory. This directory is monitored and when created, the program reads the username, expiry time and PIN, puts it into a template and sends it to whatever address is specified in `emails.json`.
* **The default forget password popup references the `passwordreset*.json` file created. This is confusing for users, so a quick fix is to edit the `MessageForgotPasswordFileCreated` string in Jellyfin's language folder.**
* Currently, jellyfin-accounts supports generic SSL/TLS or STARTTLS secured SMTP, and the [mailgun](https://mailgun.com) REST API. 
* Email html is created using [mjml](https://mjml.io), and [jinja](https://github.com/pallets/jinja) templating is used. If you wish to create your own, ensure you use the same jinja expressions (`{{ pin }}`, etc.) as used in `data/email.mjml` or `invite-email.mjml`, and also create plain text versions for legacy email clients.

#### Configuration
* Note: Make sure to put this behind a reverse proxy with HTTPS.

On first run, access the setup wizard at `0.0.0.0:8056`. When finished, restart the program.

The configuration is stored at `~/.jf-accounts/config.ini`.

For detailed descriptions of each setting, see [setup](https://github.com/hrfee/jellyfin-accounts/wiki/Setup).


```
[jellyfin]
; It is reccommended to create a limited admin account for this program.
username = username
password = password
; Jellyfin server address. Can be public, or local for security purposes.
server = http://jellyfin.local:8096
; Publicly accessible Jellyfin address, used on invite form.
; Leave blank to use the same address as above.
public_server = https://jellyf.in:443
client = jf-accounts
version = 0.1
device = jf-accounts
device_id = jf-accounts-0.1

[ui]
; Set 0.0.0.0 to run localhost
host = 0.0.0.0
port = 8056
; Enable this to use Jellyfin users instead of the below username and pw.
jellyfin_login = true
; Allows only admin users on Jellyfin to access admin page.
admin_only = true
; Username to use on admin page... (leave blank if using jellyfin_login)
username = your username
; ..and its corresponding password (leave blank if using jellyfin_login)
password = your password

debug = false

; Displayed at the bottom of all pages except admin
contact_message = Need help? contact me.
; Displayed at top of form page.
help_message =  Enter your details to create an account.
; Displayed when an account is created.
success_message = Your account has been created. Click below to continue to Jellyfin.

[password_validation]
; Enables password validation.
enabled = true 
; Min. password length
min_length = 8
; Min. number of uppercase characters
upper = 1
; Min. number of lowercase characters
lower = 0
; Min. number of numbers
number = 1
; Min. number of special characters
special = 0

[email]
; Leave this whole section if you aren't using any email-related features.
use_24h = true
; Date format follows datetime's strftime.
date_format = %d/%m/%y
; Displayed at bottom of emails
message = Need help? contact me.
; Mail methods: mailgun, smtp
method = smtp
; Address to send from
address = jellyfin@jellyf.in
; The name of the sender
from = Jellyfin

[password_resets]
; Enable to store provided email addresses, monitor jellyfin directory for pw-resets, and send pin
enabled = true
; Directory to monitor for passwordReset*.json files. Usually the jellyfin config directory
watch_directory = /path/to/jellyfin
; Path to custom email html. If blank, uses the internal template.
email_html =
; Path to alternate plaintext email. If blank, uses the internal template.
email_text = 
; Subject of emails
subject = Password Reset - Jellyfin

[invite_emails]
; If enabled, allows one to send an invite directly to an email address.
enabled = true
; Path to custom email html. If blank, uses the internal template.
email_html =
; Path to alternate plaintext email. If blank, uses the internal template.
email_text = 
subject = Invite - Jellyfin
; Base url for jf-accounts. This necessary because most will use a reverse proxy, so the program has no other way of knowing what URL to send.
url_base = http://accounts.jellyf.in:8056/invite

[mailgun]

api_url = https://api.mailgun.net...
api_key = your api key

[smtp]
; Choose between ssl_tls and starttls. Your provider should tell you which to use, but generally SSL/TLS is 465, STARTTLS 587
encryption = starttls
server = smtp.jellyf.in
; Uses SMTP_SSL, so make sure the port is for this, not starttls.
port = 587
password = smtp password

[files]
; When the below paths are left blank, files are stored in ~/.jf-accounts/.

; Path to store valid invites.
invites = 
; Path to store emails addresses in JSON
emails = 
; Path to the user policy template. Can be acquired with get-defaults (jf-accounts -g).
user_template =
; Path to the user configuration template (part of homescreen layout). Can be acquired with get-defaults (jf-accounts -g).
user_configuration =
; Path to the user display preferences template (part of homescreen layout). Can be acquired with get-defaults (jf-accounts -g).
user_displayprefs =
; Path to custom bootstrap.css
custom_css = 
```


