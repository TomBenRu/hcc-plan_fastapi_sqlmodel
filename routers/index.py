from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from starlette.responses import RedirectResponse


templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='', tags=['home'])


@router.get('/')
def home(request: Request):
    return templates.TemplateResponse('index.html', context={'request': request})
