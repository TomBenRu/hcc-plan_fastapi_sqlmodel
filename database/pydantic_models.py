from datetime import date, datetime, timedelta
from typing import Optional, Set
from pydantic import BaseModel, Field, EmailStr, conint, validator
from .enums import ProdType, TimeOfDay


class PersonBase(BaseModel):
    f_name: str
    l_name: Optional[str]
    email: EmailStr

    class Config:
        orm_mode = True


class ProjectBase(BaseModel):
    name: str

    class Config:
        orm_mode = True


class AdminCreateBase(BaseModel):
    person: PersonBase
    project: ProjectBase

    class Config:
        orm_mode = True


class AdminShowBase(AdminCreateBase):
    id: int
    created_at: date

    class Config:
        orm_mode = True


class AdminBase(AdminCreateBase):
    id: int
    password: str

    class Config:
        orm_mode = True


class TeamBase(BaseModel):
    name: str
    project: ProjectBase

    class Config:
        orm_mode = True


class TeamShowBase(TeamBase):
    id: int
    dispatcher: 'DispatcherShowBase'
    created_at: date

    class Config:
        orm_mode = True


class DispatcherCreateBase(BaseModel):  # password wir erstmalig automatisch vergeben
    person: PersonBase

    class Config:
        orm_mode = True


class DispatcherShowBase(DispatcherCreateBase):
    id: int

    class Config:
        orm_mode = True


class DispatcherBase(DispatcherShowBase):
    password: str
    created_at: date

    class Config:
        orm_mode = True


class ActorCreateBaseRemote(BaseModel):
    person: PersonBase
    team: TeamBase

    class Config:
        orm_mode = True


class ActorCreateBase(ActorCreateBaseRemote):
    password: str

    class Config:
        orm_mode = True


class ActorShowBase(ActorCreateBaseRemote):
    id: int
    active: bool

    class Config:
        orm_mode = True


class ActorBase(ActorCreateBase):
    id: int
    created_at: date

    @property
    def f_name(self):
        return self.person.f_name

    @property
    def l_name(self):
        return self.person.l_name

    class Config:
        orm_mode = True


class AvailDayBase(BaseModel):
    day: date
    time_of_day: TimeOfDay

    class Config:
        orm_mode = True


class AvailablesBase(BaseModel):
    id: int
    actor: ActorShowBase
    avail_days: list[AvailDayBase]
    notes: str

    @validator('avail_days', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]

    class Config:
        orm_mode = True


class PlanPeriodBase(BaseModel):
    id: int | None
    start: date
    end: date
    availables: list[AvailablesBase]
    notes: Optional[str]
    closed: bool
    team: TeamBase

    @property
    def all_days(self):
        delta: timedelta = self.end - self.start
        all_days: list[datetime.date] = []
        for i in range(delta.days + 1):
            day = self.start + timedelta(days=i)
            all_days.append(day)
        return all_days

    @property
    def calender_week_days(self):
        kw__day_wd = {d.isocalendar()[1]: [] for d in self.all_days}
        for day in self.all_days:
            kw__day_wd[day.isocalendar()[1]].append((day, date.weekday(day)))
        return kw__day_wd

    def avail_days(self, actor_id: int) -> dict[date, TimeOfDay]:
        av_days = {}
        for available in self.availables:
            if available.actor.id != actor_id:
                continue
            for av_d in available.avail_days:
                av_days[av_d.day] = av_d.time_of_day.value
        return av_days

    def notes_of_availables(self, actor_id: int) -> str:
        for avail in self.availables:
            if avail.actor.id == actor_id:
                return avail.notes
        return ''

    @validator('availables', pre=True, allow_reuse=True)
    def pony_set_to_list(cls, values):
        return [v for v in values]

    class Config:
        orm_mode = True


class PlanPerEtFilledIn(BaseModel):
    plan_period: PlanPeriodBase
    filled_in: bool


# --------------------------------------------------------------------------------------


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: Optional[int] = None


AvailablesBase.update_forward_refs(**locals())
TeamShowBase.update_forward_refs(**locals())
