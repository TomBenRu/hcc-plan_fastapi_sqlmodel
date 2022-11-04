import datetime
import secrets
import time
from typing import Type

from pydantic import EmailStr
from sqlmodel import Session, select, or_
from .database import engine
# from pony.orm import Database, db_session, select, TransactionIntegrityError

from utilities import utils
from .models import (Team, Person, Actor, PlanPeriod, Availables, AvailDay, Dispatcher, Project, Admin, PersonCreate,
                     ProjectCreate, AdminRead, ActorCreate, ActorRead, TeamRead, AdminReadAllFields,
                     DispatcherReadAllFields, TeamReadAllFields, TeamCreate, TeamPostCreate, ActorReadAllFields,
                     PlanPeriodRead, PlanPeriodCreate, PlanPeriodReadAllFields, PlanPerEtAvailDays)
from .enums import ProdType, TimeOfDay


# from .pydantic_models import (ActorCreateBase, PlanPerEtFilledIn, PlanPeriodBase, ActorBase, DispatcherCreateBase,
#                               TeamBase, ActorCreateBaseRemote, DispatcherShowBase, DispatcherBase, TeamShowBase,
#                               ActorShowBase, AdminCreateBase, ProjectBase, AdminShowBase, PersonBase, AdminBase)


class CustomError(Exception):
    pass


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


def find_user_by_email(email: str, user: Type[Actor | Dispatcher | Admin]) -> Actor | Dispatcher | Admin | None:
    with Session(engine) as session:
        if user == Admin:
            try:
                admin, person = session.exec(select(Admin, Person).where(user.person_id == Person.id,
                                                                         Person.email == email)).one()
                return admin
            except:
                return
        if user == Dispatcher:
            res = session.exec(select(Dispatcher, Person).where(user.person_id == Person.id,
                                                                Person.email == email)).first()
            dispatcher, _ = res if res else [None, None]
            return dispatcher
        if user == Actor:
            res = session.exec(select(Actor, Person).where(Actor.person_id == Person.id, Person.email == email)).first()
            actor, _ = res if res else [None, None]
            return actor

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
    with Session(engine) as session:
        plan_per_et_avail_days = []
        for pp_id, dates in available_days.items():
            availables_in_db = session.exec(select(Availables).where(Availables.actor_id == actor_id,
                                                                    Availables.plan_period_id == pp_id)).first()
            if availables_in_db:
                for ad in session.exec(select(AvailDay).where(AvailDay.availables_id == availables_in_db.id)).all():
                    session.delete(ad)
                session.commit()
                session.refresh(availables_in_db)

            else:
                availables_in_db = Availables(plan_period_id=pp_id, actor_id=actor_id)
            notes = dates.pop('infos')
            availables_in_db.notes = notes
            session.add(availables_in_db)
            session.commit()
            session.refresh(availables_in_db)

            for d, v in dates.items():
                if v == 'x':
                    continue
                av_day = AvailDay(day=d, time_of_day=TimeOfDay(v), availables_id=availables_in_db.id)
                session.add(av_day)
                session.commit()


def get_open_plan_periods(actor_id: int) -> list[PlanPerEtAvailDays]:
    with Session(engine) as session:
        actor = session.get(Actor, actor_id)
        actor_team = actor.team
        plan_periods = session.exec(select(PlanPeriod).where(PlanPeriod.team_id == actor_team.id,
                                                             PlanPeriod.closed == False)).all()
        plan_p_et_avail_days: list[PlanPerEtAvailDays] = []
        for pp in plan_periods:
            plan_p_et_avail_days.append(PlanPerEtAvailDays(plan_period=pp, avail_days=pp.avail_days(actor_id),
                                                           notes_of_availables=pp.notes_of_availables(actor_id)))
    return plan_p_et_avail_days


# def get_plan_periods_from_ids(planperiods: list[int]):
#     with db_session:
#         plan_periods = [PlanPeriodBase.from_orm(PlanPeriod[i]) for i in planperiods]
#     return plan_periods


def get_past_plan_priods(dispatcher_id: int, nbr_past_planperiods: int, only_not_closed: bool = False):
    """nbr_past_planperiods: positiver Wert -> Anzahl zurückliegender Planperioden.
       0 -> alle Planperioden"""
    with Session(engine) as session:
        statement = select(PlanPeriod, Team).where(PlanPeriod.team_id == Team.id, Team.dispatcher_id == dispatcher_id)
        if only_not_closed:
            statement = statement.where(PlanPeriod.closed == False)
        planperiods = session.exec(statement).all()
        nbr_past_planperiods = nbr_past_planperiods if nbr_past_planperiods <= len(planperiods) else len(planperiods)

        planperiods = [PlanPeriodReadAllFields.from_orm(pp) for pp, _ in planperiods][-nbr_past_planperiods:]

        return planperiods


def change_status_planperiod(plan_period_id: int, closed: bool, dispatcher_id: int):
    with Session(engine) as session:
        if not (planperiod_team := session.exec(select(PlanPeriod, Team).where(PlanPeriod.team_id == Team.id,
                                                                               Team.dispatcher_id == dispatcher_id)).first()):
            raise KeyError(f'Die Planperiode mit ID: {plan_period_id} ist nicht vorhanden')
        planperiod = planperiod_team[0]
        planperiod.closed = closed
        session.commit()
        session.refresh(planperiod)
        return PlanPeriodReadAllFields.from_orm(planperiod)


# def get_all_actors():
#     with db_session:
#         actors = [ActorBase.from_orm(a) for a in Actor.select()]
#     return actors


def get_actor_by_id(actor_id: int) -> ActorRead:
    with Session(engine) as session:
        actor = session.get(Actor, actor_id)
        return actor


def create_new_team(team: TeamPostCreate, admin_id: int):
    with Session(engine) as session:
        try:
            disp_proj_id = session.get(Dispatcher, team.dispatcher_id).project_id
        except Exception as e:
            return e
        adm_proj_id = session.get(Admin, admin_id).project_id
        if adm_proj_id != session.get(Dispatcher, team.dispatcher_id).project_id:
            raise Exception(f'dispatcher belongs not to your project {session.get(Project, disp_proj_id).name}')
        if session.exec(select(Team).where(Team.name == team.name, Team.project_id == adm_proj_id)).first():
            raise Exception(f'A team with name {team.name} is allready in your project.')
        team = Team(name=team.name, project_id=adm_proj_id, dispatcher_id=team.dispatcher_id)
        session.add(team)
        session.commit()
        session.refresh(team)
        return TeamRead.from_orm(team)


def create_admin(person: PersonCreate, project: ProjectCreate) -> tuple[AdminReadAllFields, str]:  # aktuell
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

        return AdminReadAllFields.from_orm(admin), password


def create_dispatcher(person: PersonCreate, admin_id) -> tuple[DispatcherReadAllFields, str]:
    with Session(engine) as session:
        project_id = session.get(Admin, admin_id).project_id
        if pers_db := session.exec(select(Person).where(
                Person.email == person.email)).first():  # Person.get(lambda p: p.email == person.email):
            if pers_db.f_name != person.f_name or pers_db.l_name != person.l_name:
                raise Exception(f'Eine Person mit Email {person.email} ist schon vorhanden, '
                                f'aber die restlichen Personendaten stimmen nicht überein.')
            else:
                person_db = pers_db
                if session.exec(select(Dispatcher).where(
                        Dispatcher.person_id == person_db.id)).first():
                    raise Exception(f'Ein*e Disponent*in mit dieser Person ist schon vorhanden.')
        else:
            person_db = person
            person_db = Person.from_orm(person_db)
            session.add(person_db)
            session.commit()
            session.refresh(person_db)
        password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        new_dispatcher = Dispatcher(password=hashed_psw, person_id=person_db.id, project_id=project_id)
        session.add(new_dispatcher)
        session.commit()
        session.refresh(new_dispatcher)
        return DispatcherReadAllFields.from_orm(new_dispatcher), password


def create_actor__remote(person: PersonCreate, team_id: int):  # aktuell
    with Session(engine) as session:
        if not session.get(Team, team_id):
            raise CustomError(f'No Team with id {team_id} vorhanden.')
        if result := session.exec(select(Actor, Person).where(Actor.person_id == Person.id,
                                                              Person.email == person.email)).first():  # Actor.get(lambda a: a.email == person.email):
            raise CustomError(f"Es ist schon ein Mitarbeiter mit dieser Email vorhanden. {list(result)}")
        if pers := session.exec(select(Person).where(
                Person.email == person.email)).first():  # Person.get(lambda p: p.email == person.email):
            if pers.f_name != person.f_name or pers.l_name != person.l_name:
                raise CustomError('Es gibt bereits eine Person mit dieser Email, '
                                  'aber die sonstigen Personendaten stimmen nicht überein.')
            else:
                person_db = pers
        else:
            person_db = Person.from_orm(person)
            session.add(person_db)
            session.commit()
            session.refresh(person_db)
        password = secrets.token_urlsafe(8)
        hashed_psw = utils.hash_psw(password)
        new_actor = Actor(person_id=person_db.id, team_id=team_id, password=hashed_psw)
        session.add(new_actor)
        session.commit()
        session.refresh(new_actor)
        return {'actor': ActorReadAllFields.from_orm(new_actor), 'password': password}


# def get_team_by_name(name: str) -> TeamRead:
#     with db_session:
#         team = Team.get(lambda t: t.name == name)
#         if not team:
#             raise KeyError({'detail': f'Kein Team mit Namen: {name}'})
#         return TeamBase.from_orm(team)


def create_new_plan_period(planperiod: PlanPeriodCreate, dispatcher_id: int):
    with Session(engine) as session:
        disp_proj_id = session.get(Dispatcher, dispatcher_id).project_id
        if not session.exec(select(Team).where(Team.id == planperiod.team_id, Team.project_id == disp_proj_id)).first():
            raise CustomError(f'Kein Team mit ID {planperiod.team_id} vorhanden.')
        max_date: datetime.date | None = None
        if planperiods := session.exec(select(PlanPeriod).where(
                PlanPeriod.team_id == planperiod.team_id)).all():
            max_date: datetime.date = max(pp.end for pp in planperiods)
        if not planperiod.start:
            if not max_date:
                raise ValueError('Sie müssen ein Startdatum angeben.')
            else:
                planperiod.start = max_date + datetime.timedelta(days=1)

        elif max_date and planperiod.start <= max_date:
            raise ValueError('Das Startdatum befindet sich in der letzten Planungsperiode.')
        if planperiod.end < planperiod.start:
            raise ValueError('Das Enddatum darf nicht vor dem Startdatum liegen.')

        plan_period = PlanPeriod.from_orm(planperiod)
        session.add(plan_period)
        session.commit()
        session.refresh(plan_period)
        return PlanPeriodRead.from_orm(plan_period)


if __name__ == '__main__':
    pass
