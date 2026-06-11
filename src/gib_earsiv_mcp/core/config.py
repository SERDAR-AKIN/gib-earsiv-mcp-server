import os
from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class GibEnvironment(str, Enum):
    TEST = "test"
    PRODUCTION = "production"
    MOCK = "mock"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    GIB_ENV: GibEnvironment = Field(default=GibEnvironment.MOCK, description="GIB Environment: test, production, or mock")
    
    GIB_USERNAME: str | None = Field(default=None, description="Username (TCKN/VKN) for GIB Portal")
    GIB_PASSWORD: str | None = Field(default=None, description="Password for GIB Portal")
    
    TEST_URL: str = "https://earsivportaltest.efatura.gov.tr/earsiv-services"
    PROD_URL: str = "https://earsivportal.efatura.gov.tr/earsiv-services"
    
    @property
    def base_url(self) -> str:
        if self.GIB_ENV == GibEnvironment.PRODUCTION:
            return self.PROD_URL
        return self.TEST_URL

settings = Settings()
