import datetime

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def hash_psw(password: str):
    return pwd_context.hash(password)


def verify(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def all_days_between_dates(date_start: datetime.date, date_end: datetime.date):
    delta: datetime.timedelta = date_start - date_end
    all_days: list[datetime.date] = []
    for i in range(delta.days + 1):
        day = date_start + datetime.timedelta(days=i)
        all_days.append(day)
    return all_days
