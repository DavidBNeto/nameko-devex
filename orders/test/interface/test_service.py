import pytest

from mock import call
from mock.mock import Mock
from nameko.events import EventDispatcher
from nameko.exceptions import RemoteError
from nameko_sqlalchemy import DatabaseSession

from orders.models import Order, OrderDetail
from orders.schemas import OrderSchema, OrderDetailSchema

from orders.exceptions import NotFound


@pytest.fixture
def order(db_session):
    order = Order()
    db_session.add(order)
    db_session.commit()
    return order


@pytest.fixture
def order_details(db_session, order):
    db_session.add_all([
        OrderDetail(
            order=order, product_id="the_odyssey", price=99.51, quantity=1
        ),
        OrderDetail(
            order=order, product_id="the_enigma", price=30.99, quantity=8
        )
    ])
    db_session.commit()
    return order_details

def test_get_order(orders_rpc, order, db_session):
    orders_rpc.db = db_session
    response = orders_rpc.get_order(1)
    assert response['id'] == order.id


def test_will_raise_when_order_not_found(orders_rpc, db_session):
    orders_rpc.db = db_session
    with pytest.raises(NotFound) as err:
        orders_rpc.get_order(1)
    assert str(err.value) == 'Order with id 1 not found'


def test_can_create_order(orders_rpc, db_session):
    orders_rpc.db = db_session
    orders_rpc.event_dispatcher = Mock(EventDispatcher)
    order_details = [
        {
            'product_id': "the_odyssey",
            'price': 99.99,
            'quantity': 1
        },
        {
            'product_id': "the_enigma",
            'price': 5.99,
            'quantity': 8
        }
    ]
    new_order = orders_rpc.create_order(
        OrderDetailSchema(many=True).dump(order_details).data
    )
    assert new_order['id'] > 0
    assert len(new_order['order_details']) == len(order_details)


def test_can_update_order(orders_rpc, order, order_details, db_session):
    orders_rpc.db = db_session
    order_payload = OrderSchema().dump(order).data
    for order_detail in order_payload['order_details']:
        order_detail['quantity'] += 1

    updated_order = orders_rpc.update_order(order_payload)

    assert updated_order['order_details'] == order_payload['order_details']


def test_can_delete_order(orders_rpc, order, db_session):
    orders_rpc.db = db_session
    orders_rpc.delete_order(order.id)
    assert not db_session.query(Order).filter_by(id=order.id).count()