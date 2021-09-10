import uuid
import yaml
import logging
import olca
import producer
import os

from fuzzywuzzy import process
from typing import List, Tuple, Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()
client = olca.Client(os.getenv('OPEN_LCA_URL'))

with open('config.yml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)


class Product(BaseModel):
    name: str
    amount: float = 1.0


class ProcessCalculation(BaseModel):
    name: str
    process_name_found: Optional[str] = None
    value: float
    unit: str
    calculated: bool


class FoodCalculation(BaseModel):
    calculation_id: uuid.UUID
    calculated_percentage: float
    process_calculations: List[ProcessCalculation]


class FoodCalculationRequestId(BaseModel):
    value: uuid.UUID


@app.post("/calculate", response_model=FoodCalculationRequestId, status_code=202)
async def calculate(products: List[Product], background_tasks: BackgroundTasks):
    calculation_id = uuid.uuid4()

    background_tasks.add_task(_run_calculation, products, calculation_id)
    return FoodCalculationRequestId(value=calculation_id)


def _run_calculation(products: List[Product], calculation_id=uuid.UUID):
    logger.info(
        f'Starting calculation for products: {products} with calculation id: {calculation_id}')

    percentage_per_item = 1 / len(products)

    processes = _get_all_processes()

    food_calculation = FoodCalculation(
        calculation_id=calculation_id,
        calculated_percentage=0,
        process_calculations=[]
    )

    for product in products:

        try:
            process_name, process_id = _find_process(
                processes=processes, product_name=product.name)
            logger.info(
                f'Creating product system for the product: {process_name} - {process_id}')

            client.create_product_system(
                process_id, default_providers='prefer', preferred_type='UNIT_PROCESS')

            food_calculation.process_calculations.append(
                _calculate_for_product(
                    product_amount=product.amount, process_name=process_name, product_name=product.name)
            )
            food_calculation.calculated_percentage += percentage_per_item
        except:
            food_calculation.process_calculations.append(
                ProcessCalculation(
                    name=product.name,
                    value=product.amount,
                    unit="kg CO2 eq",
                    calculated=False
                )
            )
            continue

    producer.send_message(message_body=food_calculation.json())


def _get_all_processes():
    logger.info('Searching all processes in the OpenLCA database')
    process_descriptor = client.get_descriptors(olca.Process)

    process_list = []
    id_list = []
    for process in process_descriptor:
        process_list.append(process.name)
        id_list.append(process.id)

    logger.info('Finishes search of processes in OpenLCA')
    return list(zip(process_list, id_list))


def _find_process(processes: List[Tuple], product_name: str):
    logger.info(
        f'Looking for lifecycle processes for the product: {product_name}')
    processes_name_list = list(zip(*processes))[0]
    processes_found_name, match_score = process.extract(
        product_name, processes_name_list, limit=10)[-1]

    logger.info(
        f'Product found: [{processes_found_name}] for product: [{product_name}] with score: {match_score}')
    if match_score <= 60:
        raise NoProcessesFound(product_name)

    processes_found = [item for item in processes if item[0]
                       == processes_found_name][0]
    return processes_found


def _calculate_for_product(product_amount: float, process_name: str, product_name: str):
    setup = olca.CalculationSetup()

    logger.info('Perform calculation setup')
    setup.amount = product_amount
    setup.calculation_type = olca.CalculationType.UPSTREAM_ANALYSIS
    setup.impact_method = client.find(olca.ImpactMethod, 'IPCC 2013 GWP 100a')
    setup.product_system = client.find(olca.ProductSystem, process_name)

    logger.info(
        f'Starts the calculation process for the product: {process_name} with the amount: {product_amount}')
    calc_result = client.calculate(setup)
    logger.info(
        f'Calculation completed for the product: {process_name} with the result: {calc_result.impact_results[0].value}')

    logger.info(f'Removes the given entity from the memory of the IPC server')
    client.dispose(calc_result)

    return ProcessCalculation(
        name=product_name,
        process_name_found=process_name,
        value=calc_result.impact_results[0].value,
        unit=calc_result.impact_results[0].impact_category.ref_unit,
        calculated=True
    )


class NoProcessesFound(Exception):
    """Description - Exception for when no product was found or does 
    not have the necessary macth score to proceed with the calculation 
    of the carbon footprint of the processes.

    Attributes:
        product_name -- Product's name.
    """

    def __init__(self, product_name, message="No Processes Found"):
        self.salary = product_name
        self.message = message
        super().__init__(self.message)
