# ![jellyfin-accounts](https://raw.githubusercontent.com/hrfee/jellyfin-accounts/bs5/images/jellyfin-accounts-banner-wide.svg)

A basic account management system for [Jellyfin](https://github.com/jellyfin/jellyfin).
* Provides a web interface for creating/sending invites
* Sends out emails when a user requests a password reset
* Uses a basic python jellyfin API client for communication with the server. 
* Uses [Flask](https://github.com/pallets/flask), [HTTPAuth](https://github.com/miguelgrinberg/Flask-HTTPAuth), [itsdangerous](https://github.com/pallets/itsdangerous), and [Waitress](https://github.com/Pylons/waitress)
* Frontend uses [Bootstrap](https://v5.getbootstrap.com)
* Password resets are handled using smtplib, requests, and [jinja](https://github.com/pallets/jinja)
## Interface
<p align="center">
    <img src="https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/jfa.gif" width="100%"></img>
</p>

<p align="center">
    <img src="https://raw.githubusercontent.com/hrfee/jellyfin-accounts/master/images/admin.png" width="48%" style="margin-right: 1.5%;" alt="Admin page"></img> 
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
* packaging
```
### Install

Usually as simple as:
```
pip install jellyfin-accounts
```
If not, or if you want to use docker, see [install](https://github.com/hrfee/jellyfin-accounts/wiki/Install).

## Usage
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
## Setup
#### New user template
* You may want to restrict a user from accessing certain libraries (e.g 4K Movies), display their account on the login screen by default, or set a default homecrseen layout. Jellyfin stores these settings in the user's policy, configuration and displayPreferences.
* Make a temporary account and configure it, then in the web UI, go into "Settings => Set new account defaults". Choose the account, and its configuration will be stored for future use.
#### Emails/Password Resets
* When someone initiates forget password on Jellyfin, a file named `passwordreset*.json` is created in its configuration directory. This directory is monitored and when created, the program reads the username, expiry time and PIN, puts it into a template and sends it to whatever address is specified in `emails.json`.
* **The default forget password popup references the `passwordreset*.json` file created. This is confusing for users, so a quick fix is to edit the `MessageForgotPasswordFileCreated` string in Jellyfin's language folder.**
* Currently, jellyfin-accounts supports generic SSL/TLS or STARTTLS secured SMTP, and the [mailgun](https://mailgun.com) REST API. 
* Email html is created using [mjml](https://mjml.io), and [jinja](https://github.com/pallets/jinja) templating is used. If you wish to create your own, ensure you use the same jinja expressions (`{{ pin }}`, etc.) as used in `data/email.mjml` or `invite-email.mjml`, and also create plain text versions for legacy email clients.

### Configuration
* Note: Make sure to put this behind a reverse proxy with HTTPS.

On first run, access the setup wizard at `0.0.0.0:8056`. When finished, restart the program.

The configuration is stored at `~/.jf-accounts/config.ini`. Settings can be changed through the web UI, or by manually editing the file.

For detailed descriptions of each setting, see [setup](https://github.com/hrfee/jellyfin-accounts/wiki/Setup).

### Donations
I strongly suggest you send your money to [Jellyfin](https://opencollective.com/jellyfin) or a good charity, but for those who want to help me out, a Paypal link is below.

[Donate](https://www.paypal.me/hrfee)
