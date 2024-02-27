import webbrowser
from fastapi import FastAPI
from routes.main2 import app 
 
main= FastAPI()
main.include_router(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=4000, log_level="info", reload=True)
    webbrowser.open("http://localhost:4000")