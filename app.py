# app.py
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="NewProj")

class Item(BaseModel):
    name: str
    value: int

# --- GET routes ---
@app.get("/")
def read_root():
    print("GET / called")
    return {"message": "Hello from FastAPI!"}

@app.get("/hello")
def say_hello():
    print("GET /hello called")
    return {"greet": "Hi there!"}

# --- POST route ---
@app.post("/submit")
async def submit_item(item: Item, request: Request):
    print(f"POST /submit called with data: {item.dict()}")
    return {"status": "received", "data": item.dict()}

# Run with:  uvicorn main:app --reload


