"""Der Supervisor legt den Erstzugang für den Admin an
   Der Admin kann neue Teams anlegen und  den zugehörigen Dispatcher (auch mehrere) einrichten."""

import requests
from pydantic import EmailStr
from requests.exceptions import ConnectionError
import time

from database.models import PersonBase, PersonCreate

from database.auth_models import Token

SERVER_ADDRESS = 'http://127.0.0.1:8000'


def login_supervisor(username: str, password: str):
    connection_error = None
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            response = requests.post(f'{SERVER_ADDRESS}/su/login',
                                     params={'username': username, 'password': password})
            return response.json()
        except ConnectionError as e:
            print(e)
            connection_error = e
            time.sleep(0.2)
    raise connection_error


def create_account(name_project: str, f_name_admin: str, l_name_admin: str, email_admin: str, access_token: dict):
    response = requests.post(f'{SERVER_ADDRESS}/su/account',
                             json={'person': {'f_name': f_name_admin, 'l_name': l_name_admin, 'email': email_admin},
                                   'project': {'name': name_project}, 'access_token': access_token})
    return response.json()


def login_admin(email: str, password: str):
    response = requests.post(f'{SERVER_ADDRESS}/admin/login',
                             params={'username': email, 'password': password})
    return response.json()


def create_new_dispatcher(person: PersonCreate, token: Token):

    response = requests.post(f'{SERVER_ADDRESS}/admin/dispatcher',
                             json={'person': person.dict(), 'token': token})
    return response.json()


def create_new_team(name: str, admin_token: dict, dispatcher_id: int):
    response = requests.post(f'{SERVER_ADDRESS}/admin/team',
                             json={'team_name': {'name': name}, 'token': admin_token,
                                   'dispatcher': {'dispatcher_id': dispatcher_id}})
    return response.json()


def login_dispatcher(email: str, password: str) -> dict[str, str]:
    connection_error = None
    t0 = time.time()
    while time.time() - t0 < 30:
        try:
            response = requests.post(f'{SERVER_ADDRESS}/dispatcher/login',
                                     params={'email': email, 'password': password})
            return response.json()
        except ConnectionError as e:
            connection_error = e
            time.sleep(0.2)
    raise connection_error


def create_new_actor(person: PersonBase, team_id, token: dict):
    response = requests.post(
        f'{SERVER_ADDRESS}/dispatcher/actor',
        json={'person': person.dict(), 'team': {'team_id': team_id}, 'token': token})
    return response.json()


def create_new_plan_period(access_token: str, team_id: int, date_start: str | None, date_end: str, notes: str | None):

    date_start = '' if not date_start else date_start
    notes = '' if not notes else notes

    response = requests.get(f'{SERVER_ADDRESS}/dispatcher/new-planperiod',
                            params={'access_token': access_token, 'team_id': team_id, 'date_start': date_start, 'date_end': date_end,
                                    'notes': notes})
    return response.json()





def get_planperiods(email_dispatcher: str, password_dispatcher: str, nbr_past_planperiods: int, only_not_closed: int):
    try:
        access_token = login_dispatcher(email_dispatcher, password_dispatcher)
    except Exception as e:
        raise e

    response = requests.get(f'{SERVER_ADDRESS}/dispatcher/get-planperiods',
                            params={'access_token': access_token, 'nbr_past_planperiods': nbr_past_planperiods,
                                    'only_not_closed': only_not_closed})
    return response.json()


def get_availables(email_dispatcher: str, password_dispatcher: str, nbr_past_planperiods: int, only_not_closed: int = 1):
    planperiods = get_planperiods(email_dispatcher, password_dispatcher, nbr_past_planperiods, only_not_closed)

    availables = {}

    for pp in planperiods:
        team = pp.pop('team')
        availables[(pp['id'], team['name'])] = {key: val for key, val in pp.items() if key not in ('id', 'notes')}

    return availables


def change_status_plan_period(email_dispatcher: str, password_dispatcher: str, plan_period_id: int, closed: int):
    try:
        access_token = login_dispatcher(email_dispatcher, password_dispatcher)
    except Exception as e:
        raise e

    response = requests.get(f'{SERVER_ADDRESS}/dispatcher/status-planperiod',
                            params={'access_token': access_token, 'plan_period_id': plan_period_id,
                                    'closed': closed})
    return response.json()



if __name__ == '__main__':
    # 'new_admin': {'person_id': 1, 'project_id': 1, 'id': 1, 'created_at': '2022-10-31', 'person': {'f_name': 'Anne', 'l_name': 'Feige', 'email': 'anne.feige@funmail.com', 'id': 1}, 'project': {'name': 'CleveClownCompany', 'id': 1, 'created_at': '2022-10-31'}}
    # 'password': 'WAke8tz24Aw'
    # 'new_admin': {'person_id': 2, 'project_id': 2, 'id': 2, 'created_at': '2022-10-31', 'person': {'f_name': 'Ben', 'l_name': 'Böge', 'email': 'ben.boege@funmail.com', 'id': 2}, 'project': {'name': 'Humor Hilft Heilen', 'id': 2, 'created_at': '2022-10-31'}}
    # 'password': 'u2gNl71xIjs'

    # 'dispatcher': {'person': {'f_name': 'Thomas', 'l_name': 'Ruff', 'email': 'mail@thomas-ruff.de'}, 'teams': [], 'id': 1}
    # 'password': 'FRE5R7KpuHk'

    # 'actor': {'person': {'f_name': 'Rolf', 'l_name': 'Reichel', 'email': 'rolf.reichel@funmail.com'}, 'team': {'name': 'Mainz', 'project': {'name': 'CleveClownCompany'}}, 'id': 2, 'active': True}
    # 'password': 'Oi53MM0xm1g'
    # 'actor': {'person': {'f_name': 'Tanja', 'l_name': 'Thiele', 'email': 'tanja.thiele@funmail.com'}, 'team': {'name': 'Baden-Württemberg', 'project': {'name': 'CleveClownCompany'}}, 'id': 3, 'active': True}
    # 'password': 'bptIH4-2cac'

    # planperiods = get_planperiods('beate.neumann@jokemail.de', 'AoBjrzdNpdA', 0, 0)
    # for pp in planperiods:
    #     print(pp)

    # availables = get_availables('beate.neumann@jokemail.de', 'AoBjrzdNpdA', 0)
    # for avail in availables.items():
    #     print(avail)

    # status_change = change_status_plan_period('beate.neumann@jokemail.de', 'AoBjrzdNpdA', plan_period_id=1, closed=0)
    # print(status_change)
    # actor_post()
    # actor_get()

    # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    # su_login = login_supervisor('supervisor', 'mario')
    # print(su_login)
    #
    # admin = create_account('CleveClownCompany', 'Anne', 'Feige', 'anne.feige@funmail.com', su_login)
    # print(admin)

    admin_login = login_admin('anne.feige@funmail.com', 'WAke8tz24Aw')
    print(admin_login)

    new_dispatcher = create_new_dispatcher(person=PersonCreate(f_name='Thomas', l_name='Ruff',
                                                               email=EmailStr('mail@thomas-ruff.de')),
                                           token=admin_login)
    print(new_dispatcher)




    # new_team = create_new_team('Baden-Württemberg', admin_login, dispatcher_id=1)
    # print(new_team)

    # disp_token = login_dispatcher('mail@thomas-ruff.de', 'Fb8fh6fbQ9Q')
    # print(disp_token)

    # new_actor = create_new_actor(PersonBase(f_name='Tanja', l_name='Thiele', email=EmailStr('tanja.thiele@funmail.com')),
    #                              team_id=2, token=disp_token)
    # print(new_actor)

    # plan_period = create_new_plan_period(disp_token['access_token'], 2, None, '2022-08-31', '2. Planperiode.')
    # print(plan_period)


# todo: Zugang Admin remote und online.
# todo: Rechte Admin und Dispatcher ordnen (siehe Scriptkommentar)