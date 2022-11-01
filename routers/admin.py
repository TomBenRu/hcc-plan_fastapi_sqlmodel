from fastapi import APIRouter, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from database.auth_models import Token
from database.models import Dispatcher, Admin, PersonCreate
# from databases.pony_models import Dispatcher
# from database.pydantic_models import AdminBase, TeamBase, PersonBase
from database.services import find_user_by_email, create_new_team, create_dispatcher
from oauth2_authentication import create_access_token, verify_supervisor_username, verify_supervisor_password, \
    verify_admin_username, verify_admin_password, verify_access_token
from utilities import utils

router = APIRouter(prefix='/admin', tags=['Admin'])


@router.post('/login')
def admin_login(username: str, password: str):
    admin: Admin | None = verify_admin_username(username)
    if not admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')
    if not verify_admin_password(password, admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': admin.id})

    return Token(access_token=access_token, token_type='bearer')


@router.post('/dispatcher')
def add_new_dispatcher(person: PersonCreate, token: Token):
    try:
        token_data = verify_access_token(token.access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e)
    admin_id = token_data.id

    try:
        new_dispatcher = create_dispatcher(person=person, admin_id=admin_id)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e)
    return new_dispatcher


@router.post('/team')
def add_new_team(team_name: dict[str, str], token: Token, dispatcher: dict[str, int]):
    name = team_name['name']
    dispatcher_id = dispatcher['dispatcher_id']
    try:
        token_data = verify_access_token(token.access_token)
    except Exception as e:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e)
    try:
        new_team = create_new_team(name=name, admin_id=token_data.id, dispatcher_id=dispatcher_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f'Teem mit Namen {name} ist schon vorhanden.')
    return new_team

