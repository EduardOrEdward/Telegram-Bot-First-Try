from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn
from typing import Optional
class Settings(BaseSettings):
    '''Application settings loaded from enviroment variables'''
    #Bot settings
    BOT_TOKEN:str
    
    
    #PostGreSQL settings
    POSTGRES_DSN:PostgresDsn
    
    
    #Redis settings
    REDIS_DSN:RedisDsn
    
    
    #Enviroment settings
    DEBUG:bool=False
    
    #TELEGRAM_API_BASE_URL:str="https://tg-bot-api-worker.eduardbenke01.workers.dev"
    
    BOT_PROXY:Optional[str]=None
    
    model_config=SettingsConfigDict(env_file='.env',env_file_encoding='utf-8',extra='ignore')

settings = Settings()