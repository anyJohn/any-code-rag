from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    in_stock: bool = True

@app.get("/items/{item_id}")
async def read_item(item_id: int,q:Optional[str] = None):
    return {"item_id":item_id,"query_param":q}

@app.post("/items/")
async def create_item(item: Item):
    return {
        "message": f"Created Item: {item.name}",
        "price_with_tax": item.price * 1.1,
        "in_stock": item.in_stock
        
    }

@app.get("/")
def root():
    return {"message": "Hello from RAG Microservice"}