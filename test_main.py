from fastapi import FastAPI
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_root_api():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World API use /hello_world or /hello_nik/{name} for a personalized message"}

def test_hello_nik_api():
    response = client.get("/hello_nik/Joe")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Joe!"}
def test_hello_world_api():
    response = client.get("/hello_world")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, world!"}  
    
    
