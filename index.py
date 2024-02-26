from fastapi import FastAPI
from routes.main2 import app 
 
main= FastAPI()
main.include_router(app)