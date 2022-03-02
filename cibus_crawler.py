import logging
import os
import time
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By


def convert_to_float(numeric_str: str):
    value = float('nan')
    try:
        value = float(numeric_str)
    except ValueError:
        pass
    finally:
        return value


@dataclass
class Credentials:
    username: str
    password: str
    company: str


class CibusCrawler:
    url = 'https://www.mysodexo.co.il/'

    def __init__(self, credentials: Credentials, open_window: bool = False):
        self.credentials = credentials
        self.open_window = open_window

    @staticmethod
    def get_web_driver(open_window: bool) -> webdriver.Chrome:
        os.environ['WDM_LOG_LEVEL'] = '0'
        chrome_options = Options()
        if not open_window:
            chrome_options.add_argument('--headless')
        driver_manager = ChromeDriverManager(version='98.0.4758.102').install()
        logging.info(f'Instantiating ChromeWebDriver object {"with" if open_window else "without"} open window')
        driver = webdriver.Chrome(driver_manager, options=chrome_options)
        return driver

    @staticmethod
    def close_chrome_driver(driver: webdriver.Chrome):
        driver.close()
        logging.info('Closed ChromeWebDriver')

    def get_current_budget(self) -> float:
        self._prepare_crawl()
        self.sign_in()
        budget_span = self.driver.find_element(By.CSS_SELECTOR, 'span.bdg.space')
        filtered_text = filter(lambda c: c.isdigit() or c == '.', budget_span.text)
        numeric_str = ''.join(filtered_text)
        budget = convert_to_float(numeric_str)
        self._tear_down()
        return budget

    def get_search_page(self) -> str:
        self._prepare_crawl()
        self.sign_in()
        self.driver.find_element(By.CSS_SELECTOR, '#ctl00_lnkRound2').click()
        search = self.driver.find_element(By.CSS_SELECTOR, '#ctl00_cphMain_right_bar_txtSearchRest')
        search.send_keys('שופרסל דיל יגאל אלון')
        search.send_keys(Keys.ENTER)
        time.sleep(2)
        url = self.driver.current_url
        self._tear_down()
        return url

    def _prepare_crawl(self):
        self.driver = CibusCrawler.get_web_driver(self.open_window)
        self.driver.get(self.url)

    def sign_in(self):
        name_input = self.driver.find_element(By.CSS_SELECTOR, '#txtUsr')
        name_input.send_keys(self.credentials.username)
        pass_input = self.driver.find_element(By.CSS_SELECTOR, '#txtPas')
        pass_input.send_keys(self.credentials.password)
        company_input = self.driver.find_element(By.CSS_SELECTOR, '#txtCmp')
        company_input.send_keys(self.credentials.company)
        login_button = self.driver.find_element(By.CSS_SELECTOR, '#btnLogin')
        login_button.click()

    def _tear_down(self):
        self.driver.close()
        self.driver = None
