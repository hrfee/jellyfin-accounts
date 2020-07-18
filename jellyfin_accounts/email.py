# Handles everything related to emails
import datetime
import pytz
import requests
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from dateutil import parser as date_parser
from jinja2 import Template
from jellyfin_accounts import config
from jellyfin_accounts import email_log as log


def format_datetime(dt):
    result = dt.strftime(config["email"]["date_format"])
    if config.getboolean("email", "use_24h"):
        result += f' {dt.strftime("%H:%M")}'
    else:
        result += f' {dt.strftime("%I:%M %p")}'
    return result


class Email:
    def __init__(self, address):
        self.address = address
        log.debug(f"{self.address}: Creating email")
        self.content = {}
        self.from_address = config["email"]["address"]
        self.from_name = config["email"]["from"]
        log.debug(
            (
                f"{self.address}: Sending from {self.from_address} "
                + f"({self.from_name})"
            )
        )
        # sp = Path(config["invite_emails"]["email_
        # template_loader = FileSystemLoader(searchpath=sp)
        # template_loader = PackageLoader("jellyfin_accounts", "data")
        # self.template_env = Environment(loader=template_loader)

    def pretty_time(self, expiry, tzaware=False):
        if tzaware:
            current_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        else:
            current_time = datetime.datetime.now()
        date = expiry.strftime(config["email"]["date_format"])
        if config.getboolean("email", "use_24h"):
            log.debug(f"{self.address}: Using 24h time")
            time = expiry.strftime("%H:%M")
        else:
            log.debug(f"{self.address}: Using 12h time")
            time = expiry.strftime("%-I:%M %p")
        expiry_delta = (expiry - current_time).seconds
        expires_in = {
            "hours": expiry_delta // 3600,
            "minutes": (expiry_delta // 60) % 60,
        }
        if expires_in["hours"] == 0:
            expires_in = f'{str(expires_in["minutes"])}m'
        else:
            expires_in = f'{str(expires_in["hours"])}h {str(expires_in["minutes"])}m'
        log.debug(f"{self.address}: Expires in {expires_in}")
        return {"date": date, "time": time, "expires_in": expires_in}

    def construct_invite(self, invite):
        self.subject = config["invite_emails"]["subject"]
        log.debug(f"{self.address}: Using subject {self.subject}")
        log.debug(f"{self.address}: Constructing email content")
        expiry = invite["expiry"]
        expiry.replace(tzinfo=None)
        pretty = self.pretty_time(expiry)
        email_message = config["email"]["message"]
        invite_link = config["invite_emails"]["url_base"]
        invite_link += "/" + invite["code"]
        for key in ["text", "html"]:
            fpath = Path(config["invite_emails"]["email_" + key])
            with open(fpath, 'r') as f:
                template = Template(f.read())
            c = template.render(
                expiry_date=pretty["date"],
                expiry_time=pretty["time"],
                expires_in=pretty["expires_in"],
                invite_link=invite_link,
                message=email_message,
            )
            self.content[key] = c
            log.info(f"{self.address}: {key} constructed")

    def construct_expiry(self, invite):
        self.subject = "Notice: Invite expired"
        log.debug(f'Constructing expiry notification for {invite["code"]}')
        expiry = format_datetime(invite["expiry"])
        for key in ["text", "html"]:
            fpath = Path(config["notifications"]["expiry_" + key])
            with open(fpath, 'r') as f:
                template = Template(f.read())
            c = template.render(code=invite["code"], expiry=expiry)
            self.content[key] = c
            log.info(f"{self.address}: {key} constructed")
        return True

    def construct_created(self, invite):
        self.subject = "Notice: User created"
        log.debug(f'Constructing user creation notification for {invite["code"]}')
        created = format_datetime(invite["created"])
        if config.getboolean("email", "no_username"):
            email = "n/a"
        else:
            email = invite["address"]
        for key in ["text", "html"]:
            fpath = Path(config["notifications"]["created_" + key])
            with open(fpath, 'r') as f:
                template = Template(f.read())
            c = template.render(
                code=invite["code"],
                username=invite["username"],
                address=email,
                time=created,
            )
            self.content[key] = c
            log.info(f"{self.address}: {key} constructed")
        return True

    def construct_reset(self, reset):
        self.subject = config["password_resets"]["subject"]
        log.debug(f"{self.address}: Using subject {self.subject}")
        log.debug(f"{self.address}: Constructing email content")
        try:
            expiry = date_parser.parse(reset["ExpirationDate"])
        except:
            log.error(f"{self.address}: Couldn't parse expiry time")
            return False
        current_time = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        if expiry >= current_time:
            log.debug(f"{self.address}: Invite valid")
            pretty = self.pretty_time(expiry, tzaware=True)
            email_message = config["email"]["message"]
            for key in ["text", "html"]:
                fpath = Path(config["password_resets"]["email_" + key])
                with open(fpath, 'r') as f:
                    template = Template(f.read())
                c = template.render(
                    username=reset["UserName"],
                    expiry_date=pretty["date"],
                    expiry_time=pretty["time"],
                    expires_in=pretty["expires_in"],
                    pin=reset["Pin"],
                    message=email_message,
                )
                self.content[key] = c
                log.info(f"{self.address}: {key} constructed")
            return True
        else:
            err = (
                f"{self.address}: "
                + "Reset has reportedly already expired. "
                + "Ensure timezones are correctly configured."
            )
            log.error(err)
            return False


class Mailgun(Email):
    errors = {
        400: "Mailgun failed with 400: Bad request",
        401: "Mailgun failed with 401: Invalid API key",
    }

    def __init__(self, address):
        super().__init__(address)
        self.api_url = config["mailgun"]["api_url"]
        self.api_key = config["mailgun"]["api_key"]
        self.from_mg = f"{self.from_name} <{self.from_address}>"

    def send(self):
        response = requests.post(
            self.api_url,
            auth=("api", self.api_key),
            data={
                "from": self.from_mg,
                "to": [self.address],
                "subject": self.subject,
                "text": self.content["text"],
                "html": self.content["html"],
            },
        )
        if response.ok:
            log.info(f"{self.address}: Sent via mailgun.")
            return True
        elif response.status_code in Mailgun.errors:
            log.error(f"{self.address}: {Mailgun.errors[response.status_code]}")
        else:
            log.error(
                f"{self.address}: Mailgun failed with error {response.status_code}"
            )
        return response


class Smtp(Email):
    def __init__(self, address):
        super().__init__(address)
        self.server = config["smtp"]["server"]
        self.password = config["smtp"]["password"]
        try:
            self.port = int(config["smtp"]["port"])
        except ValueError:
            self.port = 465
            log.debug(f"{self.address}: Defaulting to port {self.port}")

    def send(self):
        message = MIMEMultipart("alternative")
        message["Subject"] = self.subject
        message["From"] = self.from_address
        message["To"] = self.address
        text = MIMEText(self.content["text"], "plain")
        html = MIMEText(self.content["html"], "html")
        message.attach(text)
        message.attach(html)
        try:
            if config["smtp"]["encryption"] == "ssl_tls":
                self.context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    self.server, self.port, context=self.context
                ) as server:
                    server.ehlo()
                    server.login(self.from_address, self.password)
                    server.sendmail(
                        self.from_address, self.address, message.as_string()
                    )
                log.info(f"{self.address}: Sent via smtp (ssl/tls)")
                return True
            elif config["smtp"]["encryption"] == "starttls":
                with smtplib.SMTP(self.server, self.port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(self.from_address, self.password)
                    server.sendmail(
                        self.from_address, self.address, message.as_string()
                    )
                    log.info(f"{self.address}: Sent via smtp (starttls)")
                    return True
        except Exception as e:
            log.error(
                f"{self.address}: Failed to send via smtp ({type(e).__name__}: {e.args})"
            )
            try:
                log.error(e.smtp_error)
            except:
                pass
            return False
