from datetime import date, datetime

from pydantic import EmailStr

from database.enums import TimeOfDay

from typing import List, Optional
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class ProjectBase(SQLModel):
    name: str


class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: date = Field(default_factory=datetime.utcnow)
    teams: List['Team'] = Relationship(back_populates='project')
    admin: Optional['Admin'] = Relationship(back_populates='project')


class ProjectRead(ProjectBase):
    id: int
    created_at: date


class ProjectReadAllFields(ProjectRead):
    teams: List['TeamRead']
    admin: Optional['AdminRead']


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    name: Optional[str] = None


class TeamBase(SQLModel):
    name: str
    project_id: int = Field(foreign_key='project.id')
    dispatcher_id: int = Field(foreign_key='dispatcher.id')


class Team(TeamBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actors: List['Actor'] = Relationship(back_populates='team')
    project: Project = Relationship(back_populates='teams')
    dispatcher: 'Dispatcher' = Relationship(back_populates='teams')
    plan_periods: List['PlanPeriod'] = Relationship(back_populates='team')
    created_at: date = Field(default_factory=datetime.utcnow)


class TeamRead(TeamBase):
    id: int
    created_at: date


class TeamReadAllFields(TeamRead):
    project: ProjectRead
    actors: List['ActorRead']
    dispatcher: 'DispatcherRead'
    plan_periods: List['PlanPeriodRead']


class TeamCreate(TeamBase):
    pass


class TeamUpdate(SQLModel):
    name: Optional[str] = None
    project_id: Optional[int] = None
    dispatcher_id: Optional[int] = None


class PersonBase(SQLModel):
    f_name: str
    l_name: str
    email: EmailStr


class Person(PersonBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor: Optional['Actor'] = Relationship(sa_relationship_kwargs={'uselist': False}, back_populates='person')
    dispatcher: Optional['Dispatcher'] = Relationship(sa_relationship_kwargs={'uselist': False}, back_populates='person')
    admin: Optional['Admin'] = Relationship(sa_relationship_kwargs={'uselist': False}, back_populates='person')


class PersonRead(PersonBase):
    id: int


class PersonCreate(PersonBase):
    pass


class PersonUpdate(SQLModel):
    f_name: Optional[str] = None
    l_name: Optional[str] = None
    email: Optional[EmailStr] = None


class AdminBase(SQLModel):
    person_id: int = Field(foreign_key='person.id')
    project_id: int = Field(foreign_key='project.id')


class Admin(AdminBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: date = Field(default_factory=datetime.utcnow)
    person: Person = Relationship(back_populates='admin')
    project: Project = Relationship(back_populates='admin')

    @property
    def email(self):
        return self.person.email


class AdminRead(AdminBase):
    id: int
    created_at: date


class AdminReadAllFields(AdminRead):
    person: PersonRead
    project: 'ProjectRead'


class AdminCreate(AdminBase):
    pass


class AdminUpdate(SQLModel):
    person_id: Optional[int] = None
    project_id: Optional[int] = None


class DispatcherBase(SQLModel):
    person_id: int = Field(foreign_key='person.id')
    project_id: int
    activ: bool = True


class Dispatcher(DispatcherBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: date = Field(default_factory=datetime.utcnow)
    person: Person = Relationship(back_populates='dispatcher')
    teams: List[Team] = Relationship(back_populates='dispatcher')

    @property
    def f_name(self):
        return self.person.f_name

    @property
    def l_name(self):
        return self.person.l_name

    @property
    def email(self):
        return self.person.email


class DispatcherRead(DispatcherBase):
    id: int
    created_at: date


class DispatcherReadAllFields(DispatcherRead):
    person: PersonRead
    teams: List['TeamRead']


class DispatcherCreate(DispatcherBase):
    pass


class DispatcherUpdate(SQLModel):
    person_id: Optional[int] = None
    activ: Optional[bool] = None


class ActorBase(SQLModel):
    person_id: int = Field(foreign_key='person.id')
    team_id: int = Field(foreign_key='team.id')
    activ: bool = True


class Actor(ActorBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: date = Field(default_factory=datetime.utcnow)
    person: Person = Relationship(back_populates='actor')
    team: Team = Relationship(back_populates='actors')
    availables: List['Availables'] = Relationship(back_populates='actor')

    @property
    def f_name(self):
        return self.person.f_name

    @property
    def l_name(self):
        return self.person.l_name

    @property
    def email(self):
        return self.person.email


class ActorRead(ActorBase):
    id: int
    created_at: date


class ActorReadAllFields(ActorRead):
    person: PersonRead
    team: TeamRead
    availables: 'AvailablesRead'


class ActorCreate(ActorBase):
    pass


class ActorUpdate(SQLModel):
    person_id: Optional[int] = None
    team_id: Optional[int] = None
    activ: Optional[bool] = None


class PlanPeriodBase(SQLModel):
    start: date
    end: date
    notes: Optional[str]
    team_id: int = Field(foreign_key='team.id')
    closed: bool = False


class PlanPeriod(PlanPeriodBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    availables: List['Availables'] = Relationship(back_populates='plan_period')
    team: Team = Relationship(back_populates='plan_periods')

    @property
    def dispatchers(self):
        return self.team.dispatcher


class PlanPeriodRead(PlanPeriodBase):
    id: int


class PlanPeriodReadAllFields(PlanPeriodRead):
    team: TeamRead
    availables: List['AvailablesRead']


class PlanPeriodCreate(PlanPeriodBase):
    pass


class PlanPeriodUpdate(SQLModel):
    start: Optional[date] = None
    end: Optional[date] = None
    notes: Optional[str] = None
    team_id: Optional[int] = None
    closed: Optional[bool] = None


class AvailablesBase(SQLModel):
    actor_id: int = Field(foreign_key='actor.id')
    plan_period_id: int = Field(foreign_key='planperiod.id')
    notes: Optional[str]


class Availables(AvailablesBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    actor: Actor = Relationship(back_populates='availables')
    plan_period: PlanPeriod = Relationship(back_populates='availables')
    avail_days: List['AvailDay'] = Relationship(back_populates='availables')


class AvailablesRead(AvailablesBase):
    id: int


class AvailablesReadAllFields(AvailablesRead):
    actor: ActorRead
    plan_period: PlanPeriodRead
    avail_days: 'AvailDayRead'


class AvailablesCreate(AvailablesBase):
    pass


class AvailablesUpdate(SQLModel):
    actor_id: Optional[int] = None
    plan_period_id: Optional[int] = None
    notes: Optional[str] = None


class AvailDayBase(SQLModel):
    day: date
    time_of_day: TimeOfDay
    availables_id: int = Field(foreign_key='availables.id')


class AvailDay(AvailDayBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    availables: Availables = Relationship(back_populates='avail_days')


class AvailDayRead(AvailDayBase):
    id: int


class AvailDayReadAllFields(AvailDayRead):
    availables: AvailablesRead


class AvailDayCreate(AvailDayBase):
    pass


class AvailDaysUpdate(SQLModel):
    day: Optional[date] = None
    time_of_day: Optional[TimeOfDay] = None
    availables_id: Optional[int] = None

