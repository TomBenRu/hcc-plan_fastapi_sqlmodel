from sqlmodel import Session

from .database import create_db_and_tables, engine
from .models import Project, Team, Person, Admin, Dispatcher, Actor, PlanPeriod, Availables, AvailDay


def main():
    create_db_and_tables()

