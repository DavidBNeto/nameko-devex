import logging
import logging.config
from typing import List, Dict, Union

import yaml
from os import path

from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import DatabaseSession

from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail
from orders.schemas import OrderSchema
from sqlalchemy import Row

logging_file = path.abspath('logging_config.yaml')

with open(logging_file, 'r') as config_file:
    config = yaml.safe_load(config_file)
    logging.config.dictConfig(config)

logger = logging.getLogger("orders.service")


class OrdersService:
    name = 'orders'

    db = DatabaseSession(DeclarativeBase)
    event_dispatcher = EventDispatcher()

    @rpc
    def list_orders(self) -> List[Dict[str, Union[int, str, float]]]:

        try:
            orders = self.db.query(Order).all()
            if not orders:
                return []
            dumped_orders = OrderSchema(many=True).dump(orders).data
        except Exception as e:
            logger.error("Error listing orders: %s", e)
            raise e

        logger.info("%s orders listed", len(dumped_orders))

        return dumped_orders

    @rpc
    def get_order(self, order_id: int) -> Dict[str, Union[int, str, float]]:
        order = self.db.query(Order).filter(Order.id == order_id).first()

        if not order:
            logger.error('Order with id %s not found', order_id)
            raise NotFound('Order with id {} not found'.format(order_id))

        logger.info("Order with id %s successfully retrieved", order_id)

        dumped_order = OrderSchema().dump(order).data
        return dumped_order

    @rpc
    def create_order(self, order_details: Dict[str, Union[int, str, float]]) -> Dict[str, Union[int, str, float]]:

        order = Order(
            order_details=[
                OrderDetail(
                    product_id=order_detail['product_id'],
                    price=order_detail['price'],
                    quantity=order_detail['quantity']
                )
                for order_detail in order_details
            ]
        )
        self.db.add(order)
        self.db.commit()
        order = OrderSchema().dump(order).data

        self.event_dispatcher('order_created', {'order': order})

        logger.info("Order with id %s successfully created", order['id'])

        return order

    @rpc
    def update_order(self, order: Dict[str, Union[int, str, float]]) -> Dict[str, Union[int, str, float]]:
        order_details = {
            order_details['id']: order_details
            for order_details in order['order_details']
        }

        order = self.db.query(Order).get(order['id'])

        for order_detail in order.order_details:
            order_detail.price = order_details[order_detail.id]['price']
            order_detail.quantity = order_details[order_detail.id]['quantity']

        self.db.commit()
        return OrderSchema().dump(order).data

    @rpc
    def delete_order(self, order_id: int) -> None:
        order = self.db.query(Order).get(order_id)
        self.db.delete(order)
        self.db.commit()

    @rpc
    def delete_orders_with_product_id(self, product_id: str) -> None:
        try:
            details: List[Row] = self.db.query(OrderDetail.order_id).filter(OrderDetail.product_id == product_id).all()
            order_ids = list(map(lambda detail: detail._asdict()['order_id'], details))
        except Exception as e:
            logger.error("Failed to fetch orders with product id %s. %s", product_id, e)
            raise e

        try:
            self.db.commit()
            self.db.query(OrderDetail).filter(OrderDetail.order_id.in_(order_ids)).delete()
            self.db.query(Order).filter(Order.id.in_(order_ids)).delete()
            self.db.commit()
            logger.info("%s orders with product id %s deleted to ensure data consistency", len(details), product_id)
        except Exception as e:
            logger.error("Failed to delete orders with product id %s. %s", product_id, e)
            self.db.rollback()
            raise e

    @rpc
    def test_connection(self) -> None:
        try:
            self.db.query(Order).get(-1)
            logger.info("Connection to database successfully established")
        except Exception as e:
            logger.error("Connection to database failed: %s", e)
            raise e