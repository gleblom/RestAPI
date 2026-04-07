from fastapi import FastAPI

from exceptions import register_all_errors
from middleware import register_middleware
from src.config.main import Config

app = FastAPI()

config = Config() # type: ignore

register_all_errors(app)

register_middleware(app)

 
@app.get("/")
def root():
    return {"message": config}
 
@app.get("/about")
def about():
    return {"message": "О сайте"}