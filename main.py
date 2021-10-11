import uuid
import yaml
import logging
import olca
import elasticsearch_client
import producer
import os
import weight_converter

from product import Product
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

open_lca_client = olca.Client(os.getenv('OPEN_LCA_URL'))

queue_name = os.getenv('QUEUE_NAME')
dlq_queue_name = os.getenv('DLQ_QUEUE_NAME')

with open('config.yml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

_elasticsearch_client = elasticsearch_client.connect_elasticsearch()

class ProcessCalculation(BaseModel):
    name: str
    process_name_found: Optional[str] = None
    value: Optional[float]
    amount: float
    unit: str
    calculated: bool


class FoodCalculation(BaseModel):
    calculation_id: uuid.UUID
    calculated_percentage: float
    process_calculations: List[ProcessCalculation]


class CalculationError(BaseModel):
    calculation_id: uuid.UUID
    error_message: str


class FoodCalculationRequestId(BaseModel):
    value: uuid.UUID


@app.post("/calculate", response_model=FoodCalculationRequestId, status_code=202)
async def calculate(products: List[Product], background_tasks: BackgroundTasks):
    calculation_id = uuid.uuid4()

    background_tasks.add_task(_run_calculation, products, calculation_id)
    return FoodCalculationRequestId(value=calculation_id)


def _run_calculation(products: List[Product], calculation_id=uuid.UUID):
    logger.info( f'Starting calculation for products: {products} with calculation id: {calculation_id}')

    percentage_per_item = 1 / len(products)

    food_calculation = FoodCalculation(
        calculation_id=calculation_id,
        calculated_percentage=0,
        process_calculations=[]
    )

    for product in products:
        try:
            process_found = _find_process(product_name=product.name)
            logger.info(f'Creating product system for the product: {process_found.name} - {process_found.id}')

            open_lca_client.create_product_system(str(process_found.id), default_providers='prefer', preferred_type='UNIT_PROCESS')

            food_calculation.process_calculations.append(
                _calculate_for_product(
                    process_name=process_found.name, product=product
                )
            )
            food_calculation.calculated_percentage += percentage_per_item
        except (NoProcessesFound, CalculationException):
            food_calculation.process_calculations.append(
                ProcessCalculation(
                    name=product.name,
                    value=None,
                    amount=product.amount,
                    unit="kg CO2 eq",
                    calculated=False
                )
            )
            continue
        except Exception as e:
            calculation_error = CalculationError(
                calculation_id=calculation_id,
                error_message=str(e)
            )
            logging.error(e)
            
            producer.send_message(message_body=calculation_error.json(), queue_name=dlq_queue_name)
            return

    producer.send_message(message_body=food_calculation.json(), queue_name=queue_name)


def _get_all_processes():
    logger.info('Searching all processes in the OpenLCA database')
    process_descriptor = open_lca_client.get_descriptors(olca.Process)

    process_list = []
    id_list = []
    for process in process_descriptor:
        process_list.append(process.name)
        id_list.append(process.id)

    logger.info('Finishes search of processes in OpenLCA')
    return list(zip(process_list, id_list))


def _find_process(product_name: str):
    result = elasticsearch_client.search(_elasticsearch_client, product_name)
    processes_found = [Process(id=hit["_source"]["id"], name=hit["_source"]["name"]) for hit in result["hits"]["hits"]]

    if processes_found:
        return processes_found[0]
    else:
        raise NoProcessesFound(f"No Processes Found for product {product_name}")


def _calculate_for_product(process_name: str, product: Product):
    setup = olca.CalculationSetup()

    amount_kg = weight_converter.convert_to_kg(product)

    logger.info('Perform calculation setup')
    setup.amount = amount_kg
    setup.calculation_type = olca.CalculationType.UPSTREAM_ANALYSIS
    setup.impact_method = open_lca_client.find(olca.ImpactMethod, 'IPCC 2013 GWP 100a')
    setup.product_system = open_lca_client.find(olca.ProductSystem, process_name)

    logger.info(f'Starts the calculation process for the product: {process_name}')
    
    calc_result = None
    
    try:
        calc_result = open_lca_client.calculate(setup)
        logger.info(f'Calculation completed for the product: {process_name} with the result: {calc_result.impact_results[0].value}')
    except Exception as e:
        logger.error(e)
        raise NoProcessesFound(f"Error calculating product: {process_name}")

    logger.info(f'Removes the given entity from the memory of the IPC server')
    open_lca_client.dispose(calc_result)

    return ProcessCalculation(
        name=product.name,
        process_name_found=process_name,
        value=calc_result.impact_results[0].value,
        amount=amount_kg,
        unit=calc_result.impact_results[0].impact_category.ref_unit,
        calculated=True
    )


class NoProcessesFound(Exception):
    """Description - Exception for when no product was found or does 
    not have the necessary macth score to proceed with the calculation 
    of the carbon footprint of the processes.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class CalculationException(Exception):
    """Description - Exception for case an unexpected error is thrown 
    when calculating a product's carbon footprint.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

@app.post("/seed", status_code=200)
def seed():
    created = elasticsearch_client.create_index(_elasticsearch_client)

    if created:
        open_lca_processes = _get_all_processes()
        for open_lca_process in open_lca_processes:
            search_object = {'id': open_lca_process[1], 'name': open_lca_process[0]}
            logging.info(f"Saving process with id = {open_lca_process[1]} and name = {open_lca_process[0]}")
            elasticsearch_client.store_record(_elasticsearch_client, search_object)
        logging.info("Data load completed successfully")
    else:
        logging.info("Index already exists, skipping loading data")


@app.delete("/index", status_code=200)
def delete_index():
    elasticsearch_client.delete_index(_elasticsearch_client)

class ProductName(BaseModel):
    value: str

class Process(BaseModel):
    id: uuid.UUID
    name: str

@app.post("/search", status_code=200)
def seed(product_name: ProductName):
    result = elasticsearch_client.search(_elasticsearch_client, product_name.value)
    processes_found = [Process(id=hit["_source"]["id"], name=hit["_source"]["name"]) for hit in result["hits"]["hits"]]
    return processes_found[0] if processes_found else []
