from fastapi import FastAPI
import uvicorn
from mylib.logic import (hello_world,hello_nik)

app = FastAPI()
@app.get("/")
def root():
    return {"message": "Hello World API use /hello_world or /hello_nik/yourname for a personalized message :)"}
        
@app.get("/hello_nik/{name}")
async def hello_nik_api(name: str):
    return {"message": hello_nik(name)}

@app.get("/hello_world")
async def hello_world_api():
    return {"message": hello_world()}





if __name__ == "__main__":
    uvicorn.run(app, port=8080 ,host='0.0.0.0')