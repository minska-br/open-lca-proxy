import uuid
import logging
import pandas as pd
import olca

from typing import List
from fastapi import FastAPI, BackgroundTasks
from pandas.core.frame import DataFrame
from pydantic import BaseModel

import producer

app = FastAPI()
client = olca.Client(8084)

logger = logging.getLogger(__name__)
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
    logger.info(f'Starting calculation for products: {products} with calculation id: {calculation_id}')
    processes = _get_all_processes()

    food_calculation = FoodCalculation(
        calculation_id = calculation_id,
        process_calculations = []
    )

    for product in products:

        process_found = _find_process(processes = processes, product_name = product.name)

        logger.info(f'Creating product system for the product: {process_found}')
        client.create_product_system(list(process_found['id'])[0], default_providers='prefer', preferred_type='UNIT_PROCESS')

        food_calculation.process_calculations.append(
            _calculate_for_product(product_amount = product.amount, process_name = list(process_found['name'])[0])
        )

    producer.send_message(message_body = food_calculation.json())

def _get_all_processes():
    logger.info('Searching all processes in the OpenLCA database')
    process_descriptor = client.get_descriptors(olca.Process)
    
    process_list = []
    id_list = []
    for process in process_descriptor:
        process_list.append(process.name)
        id_list.append(process.id)

    logger.info('Finishes search of processes in OpenLCA')
    return pd.DataFrame(list(zip(process_list, id_list)), columns=['name', 'id'])

def _find_process(processes: DataFrame, product_name: str):
    logger.info(f'Looking for lifecycle processes for the product: {product_name}')
    processes_found = processes[processes['name'].str.contains(product_name + " production")]
    logger.info(f'{processes_found.size} processes were found for the product:{product_name}')

    processes_found.reset_index(drop=True, inplace=True)

    return processes_found

def _calculate_for_product(product_amount: float, process_name: str):
    setup = olca.CalculationSetup()
    
    logger.info('Perform calculation setup')
    setup.amount = product_amount
    setup.calculation_type = olca.CalculationType.UPSTREAM_ANALYSIS
    setup.impact_method = client.find(olca.ImpactMethod, 'IPCC 2013 GWP 100a')
    setup.product_system = client.find(olca.ProductSystem, process_name)

    logger.info(f'Starts the calculation process for the product: {process_name} with the amount: {product_amount}')
    calc_result = client.calculate(setup)
    logger.info(f'Calculation completed for the product: {process_name} with the result: {calc_result.impact_results[0].value}')

    logger.info(f'Removes the given entity from the memory of the IPC server')
    client.dispose(calc_result)
    
    return ProcessCalculationCompleted(
        name = setup.product_system.name,
        value = calc_result.impact_results[0].value,
        unit = calc_result.impact_results[0].impact_category.ref_unit
    )
