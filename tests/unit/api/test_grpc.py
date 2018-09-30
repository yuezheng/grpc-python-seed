import asyncio
import unittest

from tests.unit.api.base import BaseClient
from grpcdemo.common.internal.internal_pb2 import UpdateRequest


loop = asyncio.get_event_loop()


def async_testcase(coro):
    def wrapper(*args, **kwargs):
        return loop.run_until_complete(coro(*args, **kwargs))
    return wrapper


class TestGrpcAPI(unittest.TestCase):
    def setUp(self):
        self.client = BaseClient("0.0.0.0", "50002")

    @async_testcase
    async def test_describe(self):
        response = await self.client.describe(["abc"])
        self.assertTrue(response['isFinal'])
        self.assertFalse(response['isError'])
        self.assertTrue(len(response['resources']) == 1)
        res_resource = response['resources'][0]
        self.assertEqual(res_resource['id'], 'abc')
        print(response)

    @async_testcase
    async def test_create(self):
        res_generator = self.client.create(["cba"])
        async for res in res_generator:
            print(res)

    async def _send_req(self, ids=[], input_q=None):
        while len(ids):
            await asyncio.sleep(2)
            _id = ids.pop()
            req = UpdateRequest(request_id=str(_id))
            req.resource_type = "test"
            req.resource_id = str(_id)
            if not ids:
                req.cancel = True
            await input_q.put(req)

    @async_testcase
    async def test_update(self):
        res_generator, q = await self.client.update()

        ids = [1, 2, 3, 4, 5, 6]
        future = asyncio.ensure_future(self._send_req(ids, q))
        async for res in res_generator:
            message = self.client.message_to_dict(res)
            print(message)

        future.cancel()

