from pydantic import BaseModel

class Product(BaseModel):
    name: str
    unit: str
    amount: float = 1.0

class CalculationException(Exception):
    """Description - Exception for case an unexpected error is thrown 
    when calculating a product's carbon footprint.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)