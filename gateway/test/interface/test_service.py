import json

import pytest
from mock import call

from gateway.exceptions import OrderNotFound, ProductNotFound


class TestGetProduct(object):
    def test_can_get_product(self, service):
        service.products_rpc.get.return_value = {
            "in_stock": 10,
            "maximum_speed": 5,
            "id": "the_odyssey",
            "passenger_capacity": 101,
            "title": "The Odyssey"
        }
        response = service.get_product("req", 'the_odyssey')
        assert response.status_code == 200
        assert service.products_rpc.get.call_args_list == [
            call("the_odyssey")
        ]
        assert response.json == {
            "in_stock": 10,
            "maximum_speed": 5,
            "id": "the_odyssey",
            "passenger_capacity": 101,
            "title": "The Odyssey"
        }

    def test_product_not_found(self, service):
        service.products_rpc.get.side_effect = (ProductNotFound('missing'))

        # call the gateway service to get order #1
        response = service.get_product("req", '/products/foo')
        assert response.status_code == 404
        payload = response.json
        assert payload['error'] == 'PRODUCT_NOT_FOUND'
        assert payload['message'] == 'missing'

# class TestCreateProduct(object):
#     def test_can_create_product(self, service, web_session):
#         response = web_session.post(
#             '/products',
#             json.dumps({
#                 "in_stock": 10,
#                 "maximum_speed": 5,
#                 "id": "the_odyssey",
#                 "passenger_capacity": 101,
#                 "title": "The Odyssey"
#             })
#         )
#         assert response.status_code == 200
#         assert response.json == {'id': 'the_odyssey'}
#         assert service.products_rpc.create.call_args_list == [call({
#                 "in_stock": 10,
#                 "maximum_speed": 5,
#                 "id": "the_odyssey",
#                 "passenger_capacity": 101,
#                 "title": "The Odyssey"
#             })]
#
#     def test_create_product_fails_with_invalid_json(
#         self, service, web_session
#     ):
#         response = web_session.post(
#             '/products', 'NOT-JSON'
#         )
#         assert response.status_code == 400
#         assert response.json['error'] == 'BAD_REQUEST'
#
#     def test_create_product_fails_with_invalid_data(
#         self, service, web_session
#     ):
#         response = web_session.post(
#             '/products',
#             json.dumps({"id": 1})
#         )
#         assert response.status_code == 400
#         assert response.json['error'] == 'VALIDATION_ERROR'
#

class TestDeleteProduct(object):

    def test_delete(self, service):
        service.products_rpc.delete.return_value = None
        service.orders_rpc.delete_orders_with_product_id.return_value = None

        response = service.delete_product("req", "123")

        assert response.status_code == 204
        assert service.products_rpc.delete.call_count == 1
        assert service.orders_rpc.delete_orders_with_product_id.call_count == 1

class TestGetOrder(object):

    def test_can_get_order(self, service):
        # setup mock orders-service response:
        service.orders_rpc.get_order.return_value = {
            'id': 1,
            'order_details': [
                {
                    'id': 1,
                    'quantity': 2,
                    'product_id': 'the_odyssey',
                    'price': '200.00'
                }
            ]
        }

        # setup mock products-service response:
        service.products_rpc.get.return_value = {
            'id': 'the_odyssey',
            'title': 'The Odyssey',
            'maximum_speed': 3,
            'in_stock': 899,
            'passenger_capacity': 100
        }

        # call the gateway service to get order #1
        response = service.get_order("req", '1')
        assert response.status_code == 200

        expected_response = {
            'id': 1,
            'order_details': [
                {
                    'id': 1,
                    'quantity': 2,
                    'product_id': 'the_odyssey',
                    'image':
                        'http://example.com/airship/images/the_odyssey.jpg',
                    'product': {
                        'id': 'the_odyssey',
                        'title': 'The Odyssey',
                        'maximum_speed': 3,
                        'in_stock': 899,
                        'passenger_capacity': 100
                    },
                    'price': '200.00'
                }
            ]
        }
        assert expected_response == response.json

        # check dependencies called as expected
        assert service.orders_rpc.get_order.call_count == 1
        assert service.products_rpc.get.call_count == 1

    def test_order_not_found(self, service):
        service.orders_rpc.get_order.side_effect = (OrderNotFound('missing'))

        with pytest.raises(OrderNotFound) as exc_info:
            service.get_order("req", 1)
        assert exc_info.value.args[0] == 'missing'
        assert service.orders_rpc.get_order.call_count == 1


# class TestCreateOrder(object):
#
#     def test_can_create_order(self, service):
#         # setup mock products-service response:
#         service.products_rpc.list.return_value = [
#             {
#                 'id': 'the_odyssey',
#                 'title': 'The Odyssey',
#                 'maximum_speed': 3,
#                 'in_stock': 899,
#                 'passenger_capacity': 100
#             },
#             {
#                 'id': 'the_enigma',
#                 'title': 'The Enigma',
#                 'maximum_speed': 200,
#                 'in_stock': 1,
#                 'passenger_capacity': 4
#             },
#         ]
#
#         # setup mock create response
#         service.orders_rpc.create_order.return_value = {
#             'id': 11,
#             'order_details': []
#         }
#
#         # call the gateway service to create the order
#         response = web_session.post(
#             '/orders',
#             json.dumps({
#                 'order_details': [
#                     {
#                         'product_id': 'the_odyssey',
#                         'price': '41.00',
#                         'quantity': 3
#                     }
#                 ]
#             })
#         )
#         assert response.status_code == 200
#         assert response.json == {'id': 11}
#         assert service.products_rpc.list.call_args_list == [call()]
#         assert service.orders_rpc.create_order.call_args_list == [
#             call([
#                 {'product_id': 'the_odyssey', 'quantity': 3, 'price': '41.00'}
#             ])
#         ]
#
#     def test_create_order_fails_with_invalid_json(
#         self, service
#     ):
#         # call the gateway service to create the order
#         response = web_session.post(
#             '/orders', 'NOT-JSON'
#         )
#         assert response.status_code == 400
#         assert response.json['error'] == 'BAD_REQUEST'
#
#     def test_create_order_fails_with_invalid_data(
#         self, service
#     ):
#         # call the gateway service to create the order
#         response = web_session.post(
#             '/orders',
#             json.dumps({
#                 'order_details': [
#                     {
#                         'product_id': 'the_odyssey',
#                         'price': '41.00',
#                     }
#                 ]
#             })
#         )
#         assert response.status_code == 400
#         assert response.json['error'] == 'VALIDATION_ERROR'
#
#     def test_create_order_fails_with_unknown_product(
#         self, service
#     ):
#         # setup mock products-service response:
#         service.products_rpc.list.return_value = [
#             {
#                 'id': 'the_odyssey',
#                 'title': 'The Odyssey',
#                 'maximum_speed': 3,
#                 'in_stock': 899,
#                 'passenger_capacity': 100
#             },
#             {
#                 'id': 'the_enigma',
#                 'title': 'The Enigma',
#                 'maximum_speed': 200,
#                 'in_stock': 1,
#                 'passenger_capacity': 4
#             },
#         ]
#
#         # call the gateway service to create the order
#         response = web_session.post(
#             '/orders',
#             json.dumps({
#                 'order_details': [
#                     {
#                         'product_id': 'unknown',
#                         'price': '41',
#                         'quantity': 1
#                     }
#                 ]
#             })
#         )
#         assert response.status_code == 404
#         assert response.json['error'] == 'PRODUCT_NOT_FOUND'
#         assert response.json['message'] == 'Product Id unknown'


class TestListOrders(object):

    def test_list_orders(self, service):
        service.orders_rpc.list_orders.return_value = [{
            'id': 1,
            'order_details': [
                {
                    'id': 1,
                    'quantity': 2,
                    'product_id': 'the_odyssey',
                    'price': '200.00'
                }
            ]
        }]

        response = service.list_orders("req")

        expected_response = {
            'id': 1,
            'order_details': [
                {
                    'id': 1,
                    'quantity': 2,
                    'product_id': 'the_odyssey',
                    'price': '200.00'
                }
            ]
        }
        assert expected_response == response.json

        # check dependencies called as expected
        assert service.orders_rpc.list_orders.call_count == 1
