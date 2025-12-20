from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_DATABASE: str
    PORT: int = 8000
    SECRET_KEY: str = "supersecretkey" # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    TRAIN_CONFIG_URL: str = "https://8530796ab19b.ngrok-free.app/train/config"
    UPDATE_CONFIG_URL: str = "https://8530796ab19b.ngrok-free.app/train/config"
    START_TRAINING_URL: str = "https://8530796ab19b.ngrok-free.app/train/start"
    EXTERNAL_PREDICTOR_API: str = "https://8530796ab19b.ngrok-free.app/predict"

    @property
    def DATABASE_URL(self):
        from urllib.parse import quote_plus
        return f"mysql+mysqlconnector://{self.MYSQL_USER}:{quote_plus(self.MYSQL_PASSWORD)}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
