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
   
   webauthn_rp_id: str = Field(..., alias="rp_id")
   webauthn_origins: list[str] = [
        "https://linuxserver.tailea0f78.ts.net",               
        "android:apk-key-hash:vEIYDf5n7XUII42eca3n7clSELZLroWzTnyJF302msU"
    ]
   webauthn_rp_name: str = Field(..., alias="rp_name")
   
   fernet_key: str = Field(..., alias="fernet_key")
   secret_key: SecretStr = Field(..., alias = "secret_key")
   algorithm: str = "HS256"
   
   firebase_service_account_json: str
   
   redis_url: str = 'redis://:redis_password_12345678a!@127.0.0.1:6379/0'
   
   access_token_expire_minutes: int = 15
   refresh_token_expire_days: int = 30
   
   client_id: str = Field(..., alias="client_id")
   client_secret: SecretStr = Field(..., alias="client_secret")
   client_directory: str = Field(..., alias="directory_id")

   
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




    