import logging.config
from typing import Dict, Union, List

import yaml
from os import path

from nameko.events import event_handler
from nameko.rpc import rpc

from products import dependencies, schemas

logging_file = path.abspath('logging_config.yaml')

with open(logging_file, 'r') as config_file:
    config = yaml.safe_load(config_file)
    logging.config.dictConfig(config)

logger = logging.getLogger("products.service")


class ProductsService:

    name = 'products'

    storage = dependencies.Storage()

    @rpc
    def test_connection(self) -> None:
        try:
            self.storage.test_connection()
            logger.info("Connection to Redis successfully established")
        except Exception as e:
            logger.error("Connection to Redis failed: %s", e)
            raise e

    @rpc
    def get(self, product_id: str) -> Dict[str, Union[int, str]]:
        product = self.storage.get(product_id)
        logger.info("Product with id %s successfully retrieved", product_id)
        return schemas.Product().dump(product).data

    @rpc
    def list(self) -> List[Dict[str, Union[int, str]]]:
        products = self.storage.list()
        dumped_products = schemas.Product(many=True).dump(products).data
        logger.info("%s products successfully retrieved", len(dumped_products))
        return dumped_products

    @rpc
    def create(self, product: Dict[str, Union[int, str]]) -> None:
        product = schemas.Product(strict=True).load(product).data
        self.storage.create(product)
        logger.info("Product with id %s created successfully", product['id'])

    @rpc
    def delete(self, product_id: str) -> None:
        deleted_fields = self.storage.delete(product_id)
        logger.info("%s fields deleted successfully for product with id %s", deleted_fields, product_id)

    @event_handler('orders', 'order_created')
    def handle_order_created(self, payload):
        for product in payload['order']['order_details']:
            self.storage.decrement_stock(
                product['product_id'], product['quantity'])
