from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict
import uvicorn
from langchain_core.messages import HumanMessage
from workflow.main_workflow import wf, GlobalState

from controller import Controller


app = FastAPI()


class HumanInput(BaseModel):
    user_id: int
    user_history : list[Product]
    messages: str
    thread_id: int


@app.post("/process_input/")
async def process_input(input_data: HumanInput):
    response = Controller.chatbot_handler(input_data)
    return response



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

    @classmethod
    def getProducts(cls, Category: str):
        try:
            with open("products.json", "r") as file:
                all_products = [cls(**item) for item in json.load(file)]  # Convert dicts to Product instances
        except FileNotFoundError:
            all_products = []

        products = []
        for product in all_products:
            if product.category.lower() == Category.lower():
                products.append(product)
        return products
 
    @classmethod
    def create_json(cls, data: List['Product']):
        try:
            # Write the list of Product instances to the file
            with open('products.json', 'w') as file:
                json.dump([product.to_dict() for product in data], file, indent=4)
            return {"message": "JSON file created successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @classmethod
    def append_product(cls, data_piece : 'Product'):
        pass


@app.post("/create-json/")
async def create_json(data: List[Product]):
    return Product.create_json(data)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

    