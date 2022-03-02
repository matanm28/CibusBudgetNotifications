import logging
import requests
from typing import Set, List, NamedTuple
from calendar import Calendar
from datetime import date, datetime
from enum import Enum

Date = date


class Day(Enum):
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    @classmethod
    def from_weekday_int(cls, day: int) -> 'Day':
        return list(Day)[day % len(Day)]

    @classmethod
    def weekdays(cls) -> Set['Day']:
        return {day for day in Day if day.value < Day.FRIDAY.value}

    @classmethod
    def is_weekday(cls, day: int) -> bool:
        return cls.from_weekday_int(day) in cls.weekdays()


class JewishHoliday(NamedTuple):
    name: str
    hebrew_name: str
    date: Date


class LastWorkingDay:
    def __init__(self, year: int = None, month: int = None) -> None:
        self.year = year if year is not None else date.today().year
        self.month = month if month is not None else date.today().month

    def get_all_dates_of_month(self) -> List[Date]:
        calendar = Calendar()
        return [d for d in calendar.itermonthdates(self.year, self.month) if d.month == self.month]

    def get_last_working_day(self) -> Date:
        jewish_dates = self.get_jewish_dates()
        month_dates = self.get_all_dates_of_month()
        last_working_day = month_dates[0]
        for d in reversed(self.get_all_dates_of_month()):
            if not Day.is_weekday(d.isoweekday()):
                continue
            if any([d == jewish_date.date for jewish_date in jewish_dates]):
                continue
            last_working_day = d
            break
        return last_working_day

    def get_jewish_dates(self) -> List[JewishHoliday]:
        url = f'https://www.hebcal.com/hebcal?v=1&cfg=json&maj=on&min=on&mod=on&year={self.year}&month={self.month}&mf=on'
        response = requests.get(url)
        if response.status_code != 200:
            logging.error(f'request to {url} failed.\n{response.reason=}, {response.status_code=}')
            return []
        jewish_holidays = []
        for item in response.json()['items']:
            jewish_holidays.append(JewishHoliday(item['title'],
                                                 item['hebrew'],
                                                 datetime.strptime(item['date'], '%Y-%m-%d').date()))
        return jewish_holidays
