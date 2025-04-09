from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn
from langchain_core.messages import HumanMessage
from workflow.main_workflow import wf, GlobalState
from controller import Controller
import json

app = FastAPI()

# Define a Product class with Pydantic
class Product(BaseModel):
    productId: int
    name: str
    price: float
    description: str
    category: str
    subCategory: str
    quantity: int
    status: str

    def to_dict(self):
        return self.dict()

class HumanInput(BaseModel):
    user_id: int
    user_history : list[Product]
    messages: str
    thread_id: str


@app.post("/process_input/")
async def process_input(input_data: HumanInput):
    response =await Controller.chatbot_handler(input_data)
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



