from marshmallow.exceptions import ValidationError
from mock import Mock
import random

import pytest

from products.dependencies import NotFound
from products.service import ProductsService


@pytest.fixture
def service(test_config):
    service = ProductsService()
    service.storage = Mock()
    return service


def test_get_product(create_product, service):

    stored_product = create_product()

    service.storage.get.return_value = stored_product
    loaded_product = service.get(stored_product['id'])

    assert service.storage.get.call_count == 1
    assert stored_product == loaded_product


def test_get_product_fails_on_not_found(service):

    product_id = str(random.randint(1, 9999999999))

    service.storage.get.side_effect = NotFound('Product ID {} does not exist'.format(product_id))

    with pytest.raises(NotFound) as excinfo:
        service.get(product_id)

    assert str(excinfo.value) == ('Product ID {} does not exist').format(product_id)
    assert service.storage.get.call_count == 1


def test_list_products(products, service):

    service.storage.list.return_value = products

    listed_products = sorted(map(lambda p: p['id'], service.list()))

    products = sorted(map(lambda p: p['id'], products))

    assert service.storage.list.call_count == 1
    assert products == listed_products


def test_list_product_when_empty(service):

    service.storage.list.return_value = []

    listed_products = service.list()

    assert service.storage.list.call_count == 1

    assert [] == listed_products


def test_create_product(product, service):

    service.create(product)

    assert service.storage.create.call_count == 1


def test_delete_product(product, service):
    service.storage.delete.return_value = 5
    service.delete(product['id'])

    assert service.storage.delete.call_count == 1


@pytest.mark.parametrize('product_overrides, expected_errors', [
    ({'id': 111}, {'id': ['Not a valid string.']}),
    ({'passenger_capacity': 'not-an-integer'}, {'passenger_capacity': ['Not a valid integer.']}),
    ({'maximum_speed': 'not-an-integer'}, {'maximum_speed': ['Not a valid integer.']}),
    ({'in_stock': 'not-an-integer'}, {'in_stock': ['Not a valid integer.']})
])
def test_create_product_validation_error(product_overrides, expected_errors, product, service):
    product.update(product_overrides)

    with pytest.raises(ValidationError) as excinfo:
        service.create(product)

    assert expected_errors == excinfo.value.args[0]
    assert service.storage.create.call_count == 0


@pytest.mark.parametrize('field', ['id', 'title', 'passenger_capacity', 'maximum_speed', 'in_stock'])
def test_create_product_validation_error_on_required_fields(field, product, service):

    product.pop(field)

    with pytest.raises(ValidationError) as exc_info:
        service.create(product)

    assert ({field: ['Missing data for required field.']} == exc_info.value.args[0])
    assert service.storage.create.call_count == 0


@pytest.mark.parametrize('field', ['id', 'title', 'passenger_capacity', 'maximum_speed', 'in_stock'])
def test_create_product_validation_error_on_non_nullable_fields(field, product, service):

    product[field] = None

    with pytest.raises(ValidationError) as exc_info:
        service.create(product)

    assert (
        {field: ['Field may not be null.']} ==
        exc_info.value.args[0])
    assert service.storage.create.call_count == 0


def test_handle_order_created(test_config, product, service):

    service.storage.create.return_value = None

    service.create(product)

    assert service.storage.create.call_count == 1
