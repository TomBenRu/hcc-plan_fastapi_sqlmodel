from fastapi import HTTPException, status, APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from starlette.responses import RedirectResponse


from database.models import Actor
from database.services import (save_new_actor, find_user_by_email, available_days_to_db, get_open_plan_periods,
                                get_plan_periods_from_ids, get_all_actors, get_actor_by_id)
from oauth2_authentication import create_access_token, get_current_user_cookie
from utilities import utils

templates = Jinja2Templates(directory='templates')

router = APIRouter(prefix='/actors', tags=['Actors'])


@router.post('/plan-periods')
def actor_plan_periods(request: Request, email: EmailStr = Form(...), password: str = Form(...)):
    if not (user := find_user_by_email(email, Actor)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    if not utils.verify(password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Invalid Credentials')

    access_token = create_access_token(data={'user_id': user.id})

    actor_id = user.id
    plan_per_et_filled_in = get_open_plan_periods(actor_id)

    response = templates.TemplateResponse('index_actor.html',
                                          context={'request': request, 'f_name': user.f_name, 'l_name': user.l_name,
                                                   'plan_periods': plan_per_et_filled_in, 'actor_id': actor_id,
                                                   'success': None})
    response.set_cookie(key='access_token_actor', value=access_token, httponly=True)

    return response


@router.post('/plan-periods-handler')
async def actor_plan_periods_handler(request: Request):
    try:
        token_data = get_current_user_cookie(request, 'access_token_actor')
    except Exception as e:
        raise e
    actor_id = token_data.id

    formdata = await request.form()

    plan_periods = available_days_to_db(dict(formdata), actor_id)

    user = get_actor_by_id(actor_id)
    plan_per_et_filled_in = get_open_plan_periods(actor_id)

    return templates.TemplateResponse('index_actor.html',
                                      context={'request': request, 'f_name': user.f_name, 'l_name': user.l_name,
                                               'plan_periods': plan_per_et_filled_in, 'actor_id': actor_id,
                                               'success': True})
