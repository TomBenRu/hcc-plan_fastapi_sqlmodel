from enum import Enum


class ProdType(Enum):
    hardware = 'hardware'
    software = 'software'


class TimeOfDay(Enum):
    morning = 'v'
    afternoon = 'n'
    whole_day = 'g'
