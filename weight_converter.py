from enum import Enum
import logging
import re

from pydantic import BaseModel
from product import Product, CalculationException

logger = logging.getLogger(__name__)

class ConvertionTypes(Enum):
    POUND = "pound"
    OUNCE = "ounce"
    TEASPOON = "teaspoon"
    CUP = "cup"
    TABLESPOON = "tablespoon"
    QUART = "quart"
    CLOVE = "clove"
    PINCH = "pinch"
    HEAD = "head"
    KILOGRAMS = "kilograms"
    SMALL = "small"
    BUNCH = "bunch"
    SHEET = "sheet"
    DASH = "dash"

class Unit(BaseModel):
    type: ConvertionTypes
    ratio: float

units = [
    Unit(type = ConvertionTypes.POUND, ratio = 0.4535),
    Unit(type = ConvertionTypes.OUNCE, ratio = 0.0283),
    Unit(type = ConvertionTypes.TEASPOON, ratio = 0.0049),
    Unit(type = ConvertionTypes.CUP, ratio = 0.2016),
    Unit(type = ConvertionTypes.TABLESPOON, ratio = 0.0128),
    Unit(type = ConvertionTypes.QUART, ratio = 0.9464),
    Unit(type = ConvertionTypes.CLOVE, ratio = 3.6287),
    Unit(type = ConvertionTypes.PINCH, ratio = 0.0004),
    Unit(type = ConvertionTypes.HEAD, ratio = 0.63),
    Unit(type = ConvertionTypes.KILOGRAMS, ratio = 1),
    Unit(type = ConvertionTypes.BUNCH, ratio = 0.34), # depends on many factors 
    Unit(type = ConvertionTypes.SHEET, ratio = 0.0006),
    Unit(type = ConvertionTypes.DASH, ratio = 0.0007)
]

def convert_to_kg(product: Product):
    logger.info(f"Converting the received unit {product.unit} to the product {product.name}")

    if (product.unit.lower() == "undefined"):
        raise CalculationException(f"Invalid unit for conversion. Product name: ${product.name}")

    unit = next(filter(lambda unit: _verify_unit(value= product.unit.lower(), unit=unit.type.value), units), None)

    if unit is None:
        _save_not_found_unit(product.unit)
        return product.amount

    new_amount = 0
   
    if unit.type is ConvertionTypes.OUNCE:
        amount = _extract_ounce_amount(product.unit)
        if amount is not None:
            new_amount = float(amount.group(0)) * unit.ratio
        
    new_amount = product.amount * unit.ratio
    
    logger.info(f"Product amount converted from [{product.amount} {product.unit}] to [{new_amount} kg]")
    return new_amount

def _save_not_found_unit(name):
    file = open('not_found_units.log', 'a')

    logger.info(f"Saving not found Unit with name: {name}")
    file.writelines(name + '\n')
    
    file.close()

def _verify_unit(value: str, unit: str):
    return True if re.search(unit, value) else False

def _extract_ounce_amount(txt: str):
    return re.search("[+-]?([0-9]*[.])?[0-9]+", txt)
