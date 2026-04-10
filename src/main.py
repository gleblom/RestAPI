from fastapi import FastAPI

from exceptions import register_all_errors
from middleware import register_middleware
from src.config.main import Config

from routers.auth import router as auth_router
from routers.company import router as company_router
from routers.documents import router as documents_router
from routers.users import router as users_router
from routers.dictionaries import router as dictionaries_router

app = FastAPI()


register_all_errors(app)

register_middleware(app)


app.include_router(auth_router, prefix="/api")
app.include_router(company_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(dictionaries_router, prefix="/api")
