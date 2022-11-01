import uvicorn as uvicorn
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from database import app as db_app
from routers import auth, supervisor, admin#, actors, dispatcher, index


db_app.main()

app = FastAPI()

app.mount('/static', StaticFiles(directory='static'), name='static')


# app.include_router(index.router)
#
app.include_router(auth.router)
#
# app.include_router(actors.router)
#
app.include_router(admin.router)
#
# app.include_router(dispatcher.router)

app.include_router(supervisor.router)


if __name__ == '__main__':
    uvicorn.run(app)
