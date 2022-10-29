from pydantic import EmailStr

from database.models import PersonCreate, ProjectCreate
from database.services import create_admin
from database import app as db_app


if __name__ == '__main__':
    db_app.main()
    admin_1 = create_admin(person=PersonCreate(f_name='Hans', l_name='Huber', email=EmailStr('hans.huber@funmail.com')),
                           project=ProjectCreate(name='Mainz'))
    admin_2 = create_admin(person=PersonCreate(f_name='Franz', l_name='Fehler',
                                               email=EmailStr('franz.fehler@funmail.com')),
                           project=ProjectCreate(name='Baden-Württemberg'))
    print(admin_1)
    print(admin_2)
