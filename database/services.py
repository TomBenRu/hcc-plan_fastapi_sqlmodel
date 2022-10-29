import datetime
import secrets
import time
from typing import Type

from pydantic import EmailStr
from sqlmodel import Session, select
from .database import engine
# from pony.orm import Database, db_session, select, TransactionIntegrityError

from utilities import utils
from .models import (Team, Person, Actor, PlanPeriod, Availables, AvailDay, Dispatcher, Project, Admin, PersonCreate,
                     ProjectCreate, AdminRead, ActorCreate, ActorRead, TeamRead, AdminReadAllFields)
from .enums import ProdType, TimeOfDay
# from .pydantic_models import (ActorCreateBase, PlanPerEtFilledIn, PlanPeriodBase, ActorBase, DispatcherCreateBase,
#                               TeamBase, ActorCreateBaseRemote, DispatcherShowBase, DispatcherBase, TeamShowBase,
#                               ActorShowBase, AdminCreateBase, ProjectBase, AdminShowBase, PersonBase, AdminBase)


def save_new_actor(user: ActorCreate):
    hashed_psw = utils.hash_psw(user.password)
    user.password = hashed_psw

    with Session(engine) as session:
        try:
            team = Team.get(lambda t: t.name == user.team.name)
            print(team)
            person = Person(**user.person.dict())
            user_in_db = Actor(password=user.password, person=person, team=team)
        except Exception as e:
            raise ValueError(e)
    return user_in_db


def find_user_by_email(email: str, user: Type[Actor] | Type[Dispatcher] | Type[Admin]) -> Actor | Dispatcher | Admin | None:
    with Session(engine) as session:
        user_sel = session.exec(select(user).where(user.email == email)).one()
    return user_sel


def available_days_to_db(avail_days: dict[str, str], actor_id: int):
    available_days = {}
    for key, val in avail_days.items():
        date_av, plan_period_id = key.split('_')
        if date_av != 'infos':
            date_av = datetime.date(*[int(i) for i in date_av.split('-')])

        if plan_period_id not in available_days:
            available_days[plan_period_id] = {}
        available_days[plan_period_id][date_av] = val

    plan_periods = []
    with db_session:
        for pp_id, dates in available_days.items():
            avalables_in_db = Availables.get(lambda a:
                                             a.actor == Actor[actor_id] and a.plan_period == PlanPeriod[pp_id])
            if avalables_in_db:
                availables = avalables_in_db
                availables.avail_days.clear()
            else:
                availables = Availables(plan_period=PlanPeriod[pp_id], actor=Actor[actor_id])
            availables.notes = dates.pop('infos')

            av_days = {AvailDay(day=d, time_of_day=TimeOfDay(v), availables=availables)
                       for d, v in dates.items() if v != 'x'}
            plan_periods.append(ppp := PlanPeriodBase.from_orm(PlanPeriod[pp_id]))

    return plan_periods

"""
def get_open_plan_periods(actor_id: int) -> list[PlanPerEtFilledIn]:
    with db_session:
        actor = Actor.get(lambda a: a.id == actor_id)
        actor_team = actor.team
        plan_periods = PlanPeriod.select(lambda pp: pp.team == actor_team and not pp.closed)

        plan_p_et_filled_in: list[PlanPerEtFilledIn] = []
        for pp in plan_periods:
            filled_in = True if pp.availables.select(lambda av: av.actor == actor) else False
            plan_p_et_filled_in.append(PlanPerEtFilledIn(plan_period=PlanPeriodBase.from_orm(pp), filled_in=filled_in))
    return plan_p_et_filled_in
"""

def get_plan_periods_from_ids(planperiods: list[int]):
    with db_session:
        plan_periods = [PlanPeriodBase.from_orm(PlanPeriod[i]) for i in planperiods]
    return plan_periods


def get_past_plan_priods(dispatcher_id: int, nbr_past_planperiods: int, only_not_closed: bool = False):
    """nbr_past_planperiods: positiver Wert -> Anzahl zurückliegender Planperioden.
       0 -> alle Planperioden"""
    with db_session:
        planperiods = PlanPeriod.select(lambda pp: (dispatcher_id in pp.dispatchers.id))
        if nbr_past_planperiods > 0:
            planperiods = planperiods.order_by(PlanPeriod.end)[:nbr_past_planperiods]
        if only_not_closed:
            planperiods = (pp for pp in planperiods if not pp.closed)

        planperiods = [PlanPeriodBase.from_orm(pp) for pp in planperiods]
    return planperiods


def get_all_actors():
    with db_session:
        actors = [ActorBase.from_orm(a) for a in Actor.select()]
    return actors


def get_actor_by_id(actor_id: int) -> ActorRead:
    with db_session:
        actor = Actor[actor_id]
        return ActorBase.from_orm(actor)


def create_new_team(name: str, admin_id: int, dispatcher_id):  # aktuell
    with db_session:
        if Team.select(lambda t: t.name == name):
            raise EOFError
        team = Team(name=name, project=Admin[admin_id].project, dispatcher=Dispatcher[dispatcher_id])
        return TeamShowBase.from_orm(team)


def create_admin(person: PersonCreate, project: ProjectCreate):  # aktuell
    password = secrets.token_urlsafe(8)
    hashed_psw = utils.hash_psw(password)
    with Session(engine) as session:
        pers_in_db = session.exec(select(Person).where(Person.email == person.email)).first()
        proj_in_db = session.exec(select(Project).where((Project.name == project.name))).first()
        if proj_in_db:
            raise ValueError('Es gibt bereits ein Projekt dieses Namens.')
        if pers_in_db:
            if pers_in_db.f_name != person.f_name or pers_in_db.l_name != person.l_name:
                raise ValueError('Es gibt bereits eine Person mit dieser Email.')
            else:
                person = pers_in_db

        pers = Person.from_orm(person)
        proj = Project.from_orm(project)
        session.add_all([pers, proj])
        session.commit()
        admin = Admin(person_id=pers.id, project_id=proj.id, password=hashed_psw)
        session.add(admin)
        session.commit()
        session.refresh(admin)

        return AdminReadAllFields.from_orm(admin)



    # person, project = admin.person, admin.project
    # with db_session:
    #     if Admin.select(lambda a: a.project.name == admin.project.name):
    #         raise ValueError('Es gibt bereits ein Projekt dieses Namens.')
    #     if pers := Person.get(lambda p: p.email == admin.person.email):
    #         if pers.f_name != admin.person.f_name or pers.l_name != admin.person.l_name:
    #             raise ValueError('Es gibt bereits eine Person mit dieser Email.')
    #         else:
    #             person = PersonBase.from_orm(pers)
    #     if proj := Project.get(lambda pr: pr.name == admin.project.name):
    #         project = ProjectBase.from_orm(proj)
    #
    #     person = Person(**person.dict())
    #     project = Project(**project.dict())
    #     new_admin = Admin(password=hashed_psw, person=person, project=project)
    #     new_admin.to_dict()
    #     return AdminShowBase.from_orm(new_admin), password


def create_dispatcher(person: PersonCreate, admin_id):  # aktuell
    print('in create')
    with db_session:
        if pers_db := Person.get(lambda p: p.email == person.email):
            if pers_db.f_name != person.f_name or pers_db.l_name != person.l_name:
                print('in exception 1')
                raise Exception(f'Eine Person mit Email {person.email} ist schon vorhanden, '
                                f'aber die restlichen Personendaten stimmen nicht überein.')
            else:
                person_db = pers_db
                if Dispatcher.get(lambda d: d.person == person_db):
                    print('in exception 2')
                    raise Exception(f'Ein*e Disponent*in mit dieser Person ist schon vorhanden.')
        else:
            person_db = Person(**person.dict())
        password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        new_dispatcher = Dispatcher(password=hashed_psw, person=person_db)
        new_dispatcher.to_dict()
        dispatcher_base = DispatcherShowBase.from_orm(new_dispatcher)
    return {'dispatcher': dispatcher_base, 'password': password}


def create_actor__remote(person: PersonCreate, team_id: int):  # aktuell
    class CustomError(Exception):
        pass

    with db_session:
        team_db = Team[team_id]
        if Actor.get(lambda a: a.email == person.email):
            raise CustomError("Es ist schon ein Mitarbeiter mit dieser Email vorhanden.")
        if pers := Person.get(lambda p: p.email == person.email):
            if pers.f_name != person.f_name or pers.l_name != person.l_name:
                raise CustomError('Es gibt bereits eine Person mit dieser Email, '
                                  'aber die sonstigen Personendaten stimmen nicht überein.')
            else:
                person_db = pers
        else:
            person_db = Person(**person.dict())
        password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        new_actor = Actor(person=person_db, team=team_db, password=hashed_psw)
        return {'actor': ActorShowBase.from_orm(new_actor), 'password': password}


def get_team_by_name(name: str) -> TeamRead:
    with db_session:
        team = Team.get(lambda t: t.name == name)
        if not team:
            raise KeyError({'detail': f'Kein Team mit Namen: {name}'})
        return TeamBase.from_orm(team)


def create_new_plan_period(team_id: int, date_start: datetime.date | None, date_end: datetime.date, notes: str):  # aktuell
    with db_session:
        max_date: datetime.date | None = None
        if planperiods := PlanPeriod.select(lambda pp: pp.team.id == team_id):
            print(list(pp.end for pp in planperiods))
            max_date: datetime.date = max(pp.end for pp in planperiods)
        if not date_start:
            if not max_date:
                raise ValueError('Sie müssen ein Startdatum angeben.')
            else:
                date_start = max_date + datetime.timedelta(days=1)

        elif max_date and date_start <= max_date:
            raise ValueError('Das Startdatum befindet sich in der letzten Planungsperiode.')
        if date_end < date_start:
            raise ValueError('Das Enddatum darf nicht vor dem Startdatum liegen.')

        plan_period = PlanPeriod(start=date_start, end=date_end, notes=notes, team=Team.get(lambda t: t.id == team_id))
        return PlanPeriodBase.from_orm(plan_period)


def change_status_planperiod(plan_period_id: int, closed: bool, dispatcher_id: int):
    with db_session:
        try:
            plan_period = PlanPeriod[plan_period_id]
        except Exception as e:
            raise KeyError(f'Die Planperiode mit ID: {plan_period_id} ist nicht vorhanden')
        if Dispatcher[dispatcher_id] not in PlanPeriod[plan_period_id].dispatchers:
            raise KeyError(f'Die Planperiode mit ID: {plan_period_id} ist nicht vorhanden.')
        plan_period.closed = closed
        return PlanPeriodBase.from_orm(plan_period)


if __name__ == '__main__':
    pass
