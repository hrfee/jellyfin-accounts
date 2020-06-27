import time
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from jellyfin_accounts.email import Mailgun, Smtp
from jellyfin_accounts.web_api import jf
from jellyfin_accounts import config, data_store
from jellyfin_accounts import email_log as log


class Watcher:
    def __init__(self, dir):
        self.observer = Observer()
        self.dir = str(dir)

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.dir, recursive=True)
        try:
            self.observer.start()
        except NotADirectoryError:
            log.error(f"Directory {self.dir} does not exist")
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            log.info("Watchdog stopped")


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None
        elif event.event_type == "modified" and "passwordreset" in event.src_path:
            log.debug(f"Password reset file: {event.src_path}")
            time.sleep(1)
            with open(event.src_path, "r") as f:
                reset = json.load(f)
                log.info(f'New password reset for {reset["UserName"]}')
                try:
                    id = jf.getUsers(reset["UserName"], public=False)["Id"]
                    address = data_store.emails[id]
                    if address != "":
                        method = config["email"]["method"]
                        if method == "mailgun":
                            email = Mailgun(address)
                        elif method == "smtp":
                            email = Smtp(address)
                        if email.construct_reset(reset):
                            email.send()
                    else:
                        raise IndexError
                except (
                    FileNotFoundError,
                    json.decoder.JSONDecodeError,
                    IndexError,
                ) as e:
                    err = f"{address}: Failed: " + type(e).__name__
                    log.error(err)


def start():
    log.info(f'Monitoring {config["password_resets"]["watch_directory"]}')
    w = Watcher(config["password_resets"]["watch_directory"])
    w.run()
