from enum import Enum
import logging

from pydantic import BaseModel
from product import Product

logger = logging.getLogger(__name__)

class ConvertionTypes(Enum):
    DEFAULT = "default"
    POUND = "pound"
    OUNCE = "ounce"
    TEASPOON = "teaspoon"
    TEASPOONS = "teaspoons"
    CUP = "cup"
    TABLESPOON = "tablespoon"
    TABLESPOONS = "tablespoons"
    QUARTS = "quarts"
    CLOVES = "cloves"

class Unit(BaseModel):
    type: ConvertionTypes
    ratio: float

units = [
    Unit(type = ConvertionTypes.POUND, ratio = 0.454),
    Unit(type = ConvertionTypes.OUNCE, ratio = 0.028),
    Unit(type = ConvertionTypes.OUNCE, ratio = 0.028),
    Unit(type = ConvertionTypes.TEASPOON, ratio = 0.569),
    Unit(type = ConvertionTypes.TEASPOONS, ratio = 0.569),
    Unit(type = ConvertionTypes.CUP, ratio = 0.569),
    Unit(type = ConvertionTypes.TABLESPOON, ratio = 0.569),
    Unit(type = ConvertionTypes.TABLESPOONS, ratio = 0.569),
    Unit(type = ConvertionTypes.QUARTS, ratio = 0.569),
    Unit(type = ConvertionTypes.CLOVES, ratio = 0.569)
]

def convert_to_kg(product: Product):
    logger.info(f"Converting the received unit {product.unit} to the product {product.name}")
    unit = next(filter(lambda unit: unit.type.value == product.unit, units), None)

    if unit is None:
        _save_not_found_unit(product.unit)
        return product.amount
    
    new_amount = product.amount * unit.ratio
    logger.info(f"Product amount converted from [{product.amount} {product.unit}] to [{new_amount} kg]")

    return new_amount

def _save_not_found_unit(name):
    file = open('not_found_units.log', 'a')

    logger.info(f"Saving not found Unit with name: {name}")
    file.writelines(name + '\n')
    
    file.close()
