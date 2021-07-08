import uuid
import pandas as pd
import olca

from typing import List
from fastapi import FastAPI, BackgroundTasks
from pandas.core.frame import DataFrame
from pydantic import BaseModel

import producer

app = FastAPI()
client = olca.Client(8084)

class Product(BaseModel):
    name: str
    amount: float = 1.0

class ProcessCalculationCompleted(BaseModel):
    name: str
    value: float
    unit: str

class FoodCalculation(BaseModel):
    calculation_id: uuid.UUID
    process_calculations: List[ProcessCalculationCompleted]

class FoodCalculationRequestId(BaseModel): 
    value: uuid.UUID

@app.post("/calculate", response_model=FoodCalculationRequestId, status_code=202)
async def send_notification(products: List[Product], background_tasks: BackgroundTasks):
    calculation_id = uuid.uuid4()
    
    background_tasks.add_task(_run_calculation, products, calculation_id)
    return FoodCalculationRequestId(value = calculation_id)

def _run_calculation(products: List[Product], calculation_id = uuid.UUID): 
    processes = _get_all_processes()

    food_calculation = FoodCalculation(
        calculation_id = calculation_id,
        process_calculations = []
    )

    for product in products:

        process_found = _find_process(processes = processes, product_name = product.name)

        client.create_product_system(list(process_found['id'])[0], default_providers='prefer', preferred_type='UNIT_PROCESS')

        food_calculation.process_calculations.append(
            _calculate_for_product(product_amount = product.amount, process_name = list(process_found['name'])[0])
        )

    producer.send_message(message_body = food_calculation.json())

def _get_all_processes():
    process_descriptor = client.get_descriptors(olca.Process)
    
    process_list = []
    id_list = []
    for process in process_descriptor:
        process_list.append(process.name)
        id_list.append(process.id)

    return pd.DataFrame(list(zip(process_list, id_list)), columns=['name', 'id'])

def _find_process(processes: DataFrame, product_name: str):
    processes_found = processes[processes['name'].str.contains(product_name + " production")]

    processes_found.reset_index(drop=True, inplace=True)

    return processes_found

def _calculate_for_product(product_amount: float, process_name: str):
    setup = olca.CalculationSetup()
    
    setup.amount = product_amount
    setup.calculation_type = olca.CalculationType.UPSTREAM_ANALYSIS
    setup.impact_method = client.find(olca.ImpactMethod, 'IPCC 2013 GWP 100a')
    setup.product_system = client.find(olca.ProductSystem, process_name)

    calc_result = client.calculate(setup)

    client.dispose(calc_result)
    
    return ProcessCalculationCompleted(
        name = setup.product_system.name,
        value = calc_result.impact_results[0].value,
        unit = calc_result.impact_results[0].impact_category.ref_unit
    )
