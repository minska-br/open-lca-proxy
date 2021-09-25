from pydantic import BaseModel

class Product(BaseModel):
    name: str
    unit: str
    amount: float = 1.0
