from nameko import config
from nameko.extensions import DependencyProvider
from redis import StrictRedis
from typing import List, Union, Awaitable, Dict

from .exceptions import NotFound

DEFAULT_HOST = "DEFAULT_REDIS_URI"
PROVIDED_HOST = "REDIS_URI"


class StorageWrapper:

    NotFound = NotFound

    def __init__(self, client):
        self.client = client

    def _format_key(self, product_id: str) -> str:
        return "products:{}".format(product_id)

    def _from_hash(self, document: Union[Awaitable[dict], dict]) -> Dict[str, Union[int, str]]:
        return {
            'id': document[b'id'].decode('utf-8'),
            'title': document[b'title'].decode('utf-8'),
            'passenger_capacity': int(document[b'passenger_capacity']),
            'maximum_speed': int(document[b'maximum_speed']),
            'in_stock': int(document[b'in_stock'])
        }

    def get(self, product_id: str) -> Dict[str, Union[int, str]]:
        product = self.client.hgetall(self._format_key(product_id))
        if not product:
            raise NotFound('Product ID {} does not exist'.format(product_id))
        else:
            return self._from_hash(product)

    def list(self) -> List[Dict[str, Union[int, str]]]:
        keys = self.client.keys(self._format_key('*'))
        for key in keys:
            yield self._from_hash(self.client.hgetall(key))

    def create(self, product: Dict[str, Union[int, str]]) -> None:
        self.client.hmset(self._format_key(product['id']), product)

    def decrement_stock(self, product_id: str, amount: int) -> Union[Awaitable[int], int]:
        return self.client.hincrby(self._format_key(product_id), 'in_stock', -amount)

    def delete(self, product_id: str) -> int:
        return self.client.hdel(self._format_key(product_id), "id", "title", "passenger_capacity", "maximum_speed", "in_stock")

    def test_connection(self) -> None:
        self.client.hgetall(self._format_key('*'))


class Storage(DependencyProvider):
    client: StrictRedis

    def setup(self):
        if config.get(PROVIDED_HOST) is None:
            self.client = StrictRedis.from_url(config.get(DEFAULT_HOST))
        else:
            self.client = StrictRedis.from_url(config.get(PROVIDED_HOST))

    def get_dependency(self, worker_ctx) -> StorageWrapper:
        return StorageWrapper(self.client)
