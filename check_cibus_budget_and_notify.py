import logging
import sys

import schedule
import time
from configparser import ConfigParser
from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin
from cibus_crawler import CibusCrawler, Credentials
from last_working_day import LastWorkingDay
from notify_run import Notify

CONFIG_FILE_PATH = 'config.ini'


@dataclass
class NotifyConfig:
    name: str
    api_token: str
    address: str

    @property
    def endpoint(self):
        return urljoin(self.address, self.api_token)


def parse_config(config_file_path: str, section: str = None) -> ConfigParser:
    config = ConfigParser()
    config.read(config_file_path)
    return config[section] if section is not None and section in config else config


def parse_credentials(config_file_path: str) -> Credentials:
    cibus_credentials = parse_config(config_file_path, 'Cibus Credentials')
    return Credentials(**cibus_credentials)


def parse_notify_config(config_file_path: str) -> NotifyConfig:
    notify_config = parse_config(config_file_path, 'Notify')
    return NotifyConfig(**notify_config)


def parse_days_threshold(config_file_path: str) -> int:
    general_config = parse_config(config_file_path, 'General')
    return general_config.getint('days_threshold')


def check_cibus_budget_and_notify(config_file_path: str = CONFIG_FILE_PATH):
    today = date.today()
    last_work_date = LastWorkingDay(today.year, today.month).get_last_working_day()
    time_left = last_work_date - today
    days_threshold = parse_days_threshold(config_file_path)
    if time_left.days >= days_threshold:
        Notify().send('You still have time')
        return
    credentials = parse_credentials(config_file_path)
    crawler = CibusCrawler(credentials, open_window=True)
    budget = crawler.get_current_budget()
    if budget == 0:
        Notify().send('You finished your budget')
        return
    cibus_link = 'https://www.cibus-sodexo.co.il/'
    notify_config = parse_notify_config(config_file_path)
    notify = Notify(endpoint=notify_config.endpoint)
    message = """Hey {name},
    You still have {budget} NIS this month.
    The last day to use this money is {days_left} days from now.
    """
    notify.send(message.format(name=notify_config.name, budget=budget, days_left=time_left.days), action=cibus_link)


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout,
                        format='%(asctime)s-[%(levelname)4s]: %(message)s (in %(filename)s at %(funcName)s/%(lineno)d)',
                        level=logging.INFO)
    schedule.every().day.at('12:30').do(check_cibus_budget_and_notify, config_file_path=CONFIG_FILE_PATH)
    schedule.every().day.at('16:30').do(check_cibus_budget_and_notify, config_file_path=CONFIG_FILE_PATH)
    while True:
        schedule.run_pending()
        time.sleep(60*60)
