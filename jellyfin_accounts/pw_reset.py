import time
import json
import os
import datetime
import pytz
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dateutil import parser as date_parser
from jinja2 import Environment, FileSystemLoader, Template
from __main__ import config
from __main__ import email_log as log


class Email():
    def __init__(self, address):
        self.address = address
        log.debug(f'{self.address}: Creating email')
        self.content = {}
        self.subject = config['email']['subject']
        log.debug(f'{self.address}: Using subject {self.subject}')
        self.from_address = config['email']['address']
        self.from_name = config['email']['from']
        log.debug((
            f'{self.address}: Sending from {self.from_address} ' +
            f'({self.from_name})'))

    def construct(self, reset):
        log.debug(f'{self.address}: Constructing email content')
        try:
            expiry = date_parser.parse(reset['ExpirationDate'])
            expiry = expiry.replace(tzinfo=None)
        except:
            log.error(f"{self.address}: Couldn't parse expiry time")
            return False
        current_time = datetime.datetime.now()
        if expiry >= current_time:
            log.debug(f'{self.address}: Invite valid')
            date = expiry.strftime(config['email']['date_format'])
            if config.getboolean('email', 'use_24h'):
                log.debug(f'{self.address}: Using 24h time')
                time = expiry.strftime('%H:%M')
            else:
                log.debug(f'{self.address}: Using 12h time')
                time = expiry.strftime('%-I:%M %p')
            expiry_delta = (expiry - current_time).seconds
            expires_in = {'hours': expiry_delta//3600,
                          'minutes': (expiry_delta//60) % 60}
            if expires_in['hours'] == 0:
                expires_in = f'{str(expires_in["minutes"])}m'
            else:
                expires_in = (f'{str(expires_in["hours"])}h ' +
                              f'{str(expires_in["minutes"])}m')
            log.debug(f'{self.address}: Expires in {expires_in}')
            sp = Path(config['email']['email_template']) / '..'
            sp = str(sp.resolve()) + '/'
            templateLoader = FileSystemLoader(searchpath=sp)
            templateEnv = Environment(loader=templateLoader)
            file_text = Path(config['email']['email_plaintext']).name
            file_html = Path(config['email']['email_template']).name
            template = {}
            template['text'] = templateEnv.get_template(file_text)
            template['html'] = templateEnv.get_template(file_html)
            email_message = config['email']['message']
            for key in template:
                c = template[key].render(username=reset['UserName'],
                                         expiry_date=date,
                                         expiry_time=time,
                                         expires_in=expires_in,
                                         pin=reset['Pin'],
                                         message=email_message)
                self.content[key] = c
                log.info(f'{self.address}: {key} constructed')
            return True
        else:
            err = ((f"{self.address}: " +
                    "Reset has reportedly already expired. " +
                    "Ensure timezones are correctly configured."))
            log.error(err)
            return False


class Mailgun(Email):
    def __init__(self, address):
        super().__init__(address)
        self.api_url = config['mailgun']['api_url']
        self.api_key = config['mailgun']['api_key']
        self.from_mg = f'{self.from_name} <{self.from_address}>'

    def send(self):
        response = requests.post(self.api_url,
                                 auth=("api", self.api_key),
                                 data={"from": self.from_mg,
                                       "to": [self.address],
                                       "subject": self.subject,
                                       "text": self.content['text'],
                                       "html": self.content['html']})
        if response.ok:
            log.info(f'{self.address}: Sent via mailgun.')
            return True
        log.debug(f'{self.address}: Mailgun: {response.status_code}')
        return response


class Smtp(Email):
    def __init__(self, address):
        super().__init__(address)
        self.server = config['smtp']['server']
        self.password = config['smtp']['password']
        try:
            self.port = int(config['smtp']['port'])
        except ValueError:
            self.port = 465
            log.debug(f'{self.address}: Defaulting to port {self.port}')
        self.context = ssl.create_default_context()

    def send(self):
        message = MIMEMultipart("alternative")
        message["Subject"] = self.subject
        message["From"] = self.from_address
        message["To"] = self.address
        text = MIMEText(self.content['text'], 'plain')
        html = MIMEText(self.content['html'], 'html')
        message.attach(text)
        message.attach(html)
        try:
            with smtplib.SMTP_SSL(self.server,
                                  self.port,
                                  context=self.context) as server:
                server.login(self.from_address, self.password)
                server.sendmail(self.from_address,
                                self.address,
                                message.as_string())
            log.info(f'{self.address}: Sent via smtp')
            return True
        except Exception as e:
            err = f'{self.address}: Failed to send via smtp: '
            err += type(e).__name__
            log.error(err)


class Watcher:
    def __init__(self, dir):
        self.observer = Observer()
        self.dir = str(dir)

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.dir, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            log.info('Watchdog stopped')


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif (event.event_type == 'created' and
              'passwordreset' in event.src_path):
            with open(event.src_path, 'r') as f:
                reset = json.load(f)
                log.info(f'New password reset for {reset["UserName"]}')
                try:
                    with open(config['files']['emails'], 'r') as f:
                        emails = json.load(f)
                        address = emails[reset['UserName']]
                    method = config['email']['method']
                    if method == 'mailgun':
                        email = Mailgun(address)
                    elif method == 'smtp':
                        email = Smtp(address)
                    if email.construct(reset):
                        email.send()
                except (FileNotFoundError,
                        json.decoder.JSONDecodeError,
                        IndexError) as e:
                    err = f'{address}: Failed: ' + type(e).__name__
                    log.error(err)

def start():
    log.info(f'Monitoring {config["email"]["watch_directory"]}')
    w = Watcher(config['email']['watch_directory'])
    w.run()
