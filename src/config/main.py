from pydantic import Field, SecretStr 
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):    # @IgnoreException
   
   host: str = Field(..., alias="db_host")
   port: int = Field(..., alias="db_port")
   user: str = Field(..., alias="db_user")
   name: str = Field(..., alias="db_name")  
   password: SecretStr = Field(..., alias="db_password")
   
   api_key: SecretStr = Field(..., alias="resend_api_key")
   from_email: str = Field(..., alias="from_email")
   domain: str = Field(..., alias="domain")
   
   secret_key: SecretStr = Field(..., alias = "secret_key")
   algorithm: str = "HS256"
   access_token_expire_minutes: int = 30
   
   refresh_token_expire_days: int = 30
   
   minio_endpoint: str = Field(..., alias="minio_endpoint")
   minio_bucket: str = Field(..., alias="bucket")
   minio_access_key: SecretStr = Field(..., alias = "minio_access_key")
   minio_secret_key: SecretStr = Field(..., alias = "minio_secret_key")
   minio_secure: bool = Field(..., alias="secure")
   
   model_config = SettingsConfigDict(
        env_file="src/settings/.env",
        env_file_encoding="utf-8",
        extra="ignore",
    )




    