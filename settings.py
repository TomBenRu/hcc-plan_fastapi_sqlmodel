from pydantic import BaseSettings


class Settings(BaseSettings):
    """Reads the variables of the most recent .env file in hirarchy. Variable names are not case sensitiv."""
    provider: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    db_actors: str
    supervisor_username: str
    supervisor_password: str

    class Config:
        env_file = '.env'


settings = Settings()
