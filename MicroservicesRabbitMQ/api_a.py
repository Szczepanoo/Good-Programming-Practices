from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI()
db: Dict[str, dict] = {}

class Result(BaseModel):
    task_id: str
    image_url: str
    detected_people: int

@app.post("/results")
def save_result(result: Result):
    db[result.task_id] = result.dict()
    return {"status": "saved"}

@app.get("/results/{task_id}")
def get_result(task_id: str):
    return db.get(task_id, {"status": "not_found"})

@app.get("/results")
def get_all_results():
    return list(db.values())

