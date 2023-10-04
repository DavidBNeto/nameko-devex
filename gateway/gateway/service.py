import json

from marshmallow import ValidationError
from nameko import config
from nameko.exceptions import BadRequest
from nameko.rpc import RpcProxy
from werkzeug import Response

from gateway.entrypoints import http
from gateway.exceptions import OrderNotFound, ProductNotFound
from gateway.schemas import CreateOrderSchema, GetOrderSchema, ProductSchema


class GatewayService(object):

    name = 'gateway'

    orders_rpc = RpcProxy('orders')
    products_rpc = RpcProxy('products')

    @http("GET", "/test")
    def test_connections(self, request: str):
        """Simple method to test connections in the beggining of the smoke test
        """
        try:
            self.orders_rpc.test_connection()
            self.products_rpc.test_connection()
            return Response(status=200)
        except Exception:
            return Response(status=418)


    @http("GET", "/products")
    def list_products(self, request: str):
        products = self.products_rpc.list()

        products = list(map(lambda product: ProductSchema().dumps(product).data, products))

        return Response(products, mimetype='application/json')


    @http("GET", "/products/<string:product_id>", expected_exceptions=ProductNotFound)
    def get_product(self, request: str, product_id: str):
        """Gets product by `product_id`
        """
        product = self.products_rpc.get(product_id)

        return Response(ProductSchema().dumps(product).data, mimetype='application/json')


    @http("POST", "/products", expected_exceptions=(ValidationError, BadRequest))
    def create_product(self, request: str):
        """Create a new product - product data is posted as json

        Example request ::

            {
                "id": "the_odyssey",
                "title": "The Odyssey",
                "passenger_capacity": 101,
                "maximum_speed": 5,
                "in_stock": 10
            }


        The response contains the new product ID in a json document ::

            {"id": "the_odyssey"}

        """

        schema = ProductSchema(strict=True)

        try:
            # load input data through a schema (for validation)
            # Note - this may raise `ValueError` for invalid json,
            # or `ValidationError` if data is invalid.
            product_data = schema.loads(request.get_data(as_text=True)).data
        except ValueError as exc:
            raise BadRequest("Invalid json: {}".format(exc))

        # Create the product
        self.products_rpc.create(product_data)
        return Response(
            json.dumps({'id': product_data['id']}), mimetype='application/json'
        )


    @http("DELETE", "/products/<string:product_id>", expected_exceptions=ProductNotFound)
    def delete_product(self, request: str, product_id: str):
        """Delete a product by its ID
        """

        self.products_rpc.delete(product_id)

        self.orders_rpc.delete_orders_with_product_id(product_id)

        return Response(status=204, mimetype='application/json')


    @http("GET", "/orders")
    def list_orders(self, request):
        orders = self.orders_rpc.list_orders()

        orders = list(map(lambda order: GetOrderSchema().dumps(order).data, orders))

        return Response(orders, mimetype='application/json')



    @http("GET", "/orders/<int:order_id>", expected_exceptions=OrderNotFound)
    def get_order(self, request: str, order_id: int):
        """Gets the order details for the order given by `order_id`.

        Enhances the order details with full product details from the
        products-service.
        """
        order = self.orders_rpc.get_order(order_id)
        detailed_order = self._detail_order(order)
        return Response(
            GetOrderSchema().dumps(detailed_order).data,
            mimetype='application/json'
        )


    def _detail_order(self, order):
        # get the configured image root
        image_root = config['PRODUCT_IMAGE_ROOT']

        # Enhance order details with product and image details.
        for item in order['order_details']:
            product_id = item['product_id']

            item['product'] = self.products_rpc.get(product_id)
            # Construct an image url.
            item['image'] = '{}/{}.jpg'.format(image_root, product_id)

        return order

    @http("POST", "/orders",expected_exceptions=(ValidationError, ProductNotFound, BadRequest))
    def create_order(self, request):
        """Create a new order - order data is posted as json

        Example request ::

            {
                "order_details": [
                    {
                        "product_id": "the_odyssey",
                        "price": "99.99",
                        "quantity": 1
                    },
                    {
                        "price": "5.99",
                        "product_id": "the_enigma",
                        "quantity": 2
                    },
                ]
            }


        The response contains the new order ID in a json document ::

            {"id": 1234}

        """

        schema = CreateOrderSchema(strict=True)

        try:
            # load input data through a schema (for validation)
            # Note - this may raise `ValueError` for invalid json,
            # or `ValidationError` if data is invalid.
            order_data = schema.loads(request.get_data(as_text=True)).data
        except ValueError as exc:
            raise BadRequest("Invalid json: {}".format(exc))

        # Create the order
        # Note - this may raise `ProductNotFound`
        id_ = self._create_order(order_data)
        return Response(json.dumps({'id': id_}), mimetype='application/json')

    def _create_order(self, order_data):
        # check order product ids are valid
        for item in order_data['order_details']:
            valid_id = self.products_rpc.get(item['product_id'])
            if not valid_id:
                raise ProductNotFound("Product Id {}".format(item['product_id']))

        # Call orders-service to create the order.
        # Dump the data through the schema to ensure the values are serialized
        # correctly.
        serialized_data = CreateOrderSchema().dump(order_data).data
        result = self.orders_rpc.create_order(
            serialized_data['order_details']
        )
        return result['id']