import datetime

from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import EmailStr, json, BaseModel

from database.models import Dispatcher, PersonCreate, PlanPeriodCreate
from database.pydantic_models import Token, TeamBase, PersonBase, ActorCreateBaseRemote, TokenData
from database.services import (create_actor__remote, find_user_by_email, create_new_plan_period, get_past_plan_priods,
                                change_status_planperiod)
from oauth2_authentication import (verify_supervisor_username, verify_supervisor_password, create_access_token,
                                   verify_access_token, verify_su_access_token,
                                   get_current_dispatcher)
from utilities import utils

router = APIRouter(prefix='/dispatcher', tags=['Dispatcher'])


@router.post('/login', response_model=Token)
def dispatcher_login(email: str, password: str):
    if not (dispatcher := find_user_by_email(email, Dispatcher)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(password, dispatcher.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': dispatcher.id})
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.post('/actor')
def create_new_actor(person: PersonCreate, team: dict[str, int], token: Token):
    try:
        token_data = verify_access_token(token.access_token)
        disp_id = token_data.id
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e)

    team_id = team['team_id']

    try:
        new_actor = create_actor__remote(person, team_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'dieser Fehler trat auf: {e}')

    return new_actor


@router.post('/new-planperiod')
def new_planperiod(planperiod: PlanPeriodCreate, token: Token):
    try:
        token_data = verify_access_token(token.access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = token_data.id

    try:
        new_plan_period = create_new_plan_period(planperiod, dispatcher_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Fehler: {e}')

    return new_plan_period


@router.get('/get-planperiods')
def get_planperiods(nbr_past_planperiods: int, only_not_closed: int, access_token: str):
    """nbr_past_planperiods: positiver Wert -> Anzahl zurückliegender Planperioden.
       0 -> alle Planperioden"""
    try:
        token_data = verify_access_token(access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = int(token_data.id)
    nbr_past_planperiods = int(nbr_past_planperiods)
    only_not_closed = bool(only_not_closed)

    plan_periods = get_past_plan_priods(dispatcher_id, nbr_past_planperiods, only_not_closed)

    return plan_periods


@router.patch('/status-planperiod')
def status_planperiod(access_token: str, plan_period_id: int, closed: int):
    print('bin drin')
    try:
        token_data = verify_access_token(access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='wrong cedentials')
    dispatcher_id = int(token_data.id)

    plan_period_id = int(plan_period_id)
    closed = bool(closed)

    try:
        plan_period = change_status_planperiod(plan_period_id, closed, dispatcher_id)
    except KeyError as e:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Error: {e}')

    return plan_period



