from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://sastanak:sastanak@db:5432/sastanak"
    jwt_secret: str = "promeniti_u_produkciji"
    jwt_algorithm: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()