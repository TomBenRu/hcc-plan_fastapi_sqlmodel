from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status, Request
from fastapi.security.oauth2 import OAuth2PasswordBearer
from jose import JWTError, jwt

from database.models import Admin
from database.auth_models import TokenData, Token
from database.services import find_user_by_email
from settings import settings
from utilities import utils

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
SUPERVISOR_USERNAME = settings.supervisor_username
SUPERVISOR_PASWORD = settings.supervisor_password
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes


oauth2_scheme_su = OAuth2PasswordBearer(tokenUrl='su/login')
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl='admin/login')
oauth2_scheme_dispatcher = OAuth2PasswordBearer(tokenUrl='dispatcher/login')
oauth2_scheme_actor = OAuth2PasswordBearer(tokenUrl='actors/login')


credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                      detail='Could not validate credentials.',
                                      headers={'WWW-Authenticate': 'Bearer'})


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        if not (u_id := payload.get('user_id')):
            raise credentials_exception
        token_data = TokenData(id=u_id)
    except JWTError:
        raise credentials_exception
    return token_data


def verify_su_access_token(token: Token):
    try:
        payload = jwt.decode(token.access_token, SECRET_KEY, algorithms=ALGORITHM)
        if not payload.get('supervisor'):
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return True


def get_current_user_cookie(request: Request, token_key: str):
    token: str | None = request.cookies.get(token_key)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='you have to log in first')

    return verify_access_token(token)


def get_current_supervisor(token: str = Depends(oauth2_scheme_su)):
    print('##############################')
    return verify_access_token(token)


def get_current_admin(token: str = Depends(oauth2_scheme_admin)):
    return verify_access_token(token)


def get_current_dispatcher(token: str = Depends(oauth2_scheme_dispatcher)):
    return verify_access_token(token)


def get_current_actor(token: str = Depends(oauth2_scheme_actor)):
    return verify_access_token(token)


def verify_supervisor_username(username: str):
    if username == SUPERVISOR_USERNAME:
        return True
    return False


def verify_supervisor_password(password: str):
    return utils.verify(password, SUPERVISOR_PASWORD)


def verify_admin_username(username: str) -> Admin | None:
    return find_user_by_email(username, user=Admin)


def verify_admin_password(password: str, admin: Admin):
    return utils.verify(plain_password=password, hashed_password=admin.password)
