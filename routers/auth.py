from typing import Optional

from fastapi import APIRouter, Depends, status, HTTPException, Response
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from databases.pony_models import Dispatcher
from databases.pydantic_models import Token
from databases.services import find_user_by_email
from oauth2_authentication import create_access_token, verify_supervisor_username, verify_supervisor_password
from utilities import utils

router = APIRouter(tags=['Authentication'])


@router.post('/su/login', response_model=Token)
def supervisor_login(username: str, password: str):
    if not verify_supervisor_username(username):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')
    if not verify_supervisor_password(password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'supervisor': 'supervisor'})

    return {'access_token': access_token, 'token_type': 'bearer'}

