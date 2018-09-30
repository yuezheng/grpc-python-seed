import asyncio
import json
import uuid

from aiogrpc import insecure_channel

from grpcdemo.common.internal.common_pb2 import JSONTYPE
from grpcdemo.common.internal.internal_pb2_grpc import InternalServerStub
from grpcdemo.common.internal.internal_pb2 import DescribeRequest, CreateRequest, UpdateRequest
from google.protobuf.json_format import MessageToDict


def convert_to_JSONTYPE_dict(params):
    if params is None:
        return None
    jsontype_params = {key: JSONTYPE(json_str=json.dumps(value))
                       for key, value in params.items()}
    return jsontype_params


def _covert(raw_dict):
    parsed_dict = {}
    for key, value in raw_dict.items():
        if key == 'jsonStr' and len(raw_dict) == 1:
            parsed_dict = json.loads(value)
        elif type(value) is dict:
            parsed_dict[key] = _covert(value)
        elif type(value) is list:
            items = []
            for item in value:
                items.append(_covert(item))
            parsed_dict[key] = items
        else:
            parsed_dict[key] = value
    return parsed_dict


class BaseClient(object):
    def __init__(self, host, port):
        grpc_uri = f"ipv4:///{host}:{port}"
        rpc_channel = insecure_channel(grpc_uri)
        self.stub = InternalServerStub(rpc_channel)

    def message_to_dict(self, message):
        raw_dict = MessageToDict(message, including_default_value_fields=True)
        pretty_dict = _covert(raw_dict)
        return pretty_dict

    async def describe(self, ids=[], extra={}):
        _param = {
            "resource_ids": ids
        }
        if extra:
            _param.update(extra)
        param = convert_to_JSONTYPE_dict(_param)
        request = DescribeRequest(params=param)
        request.request_id = str(uuid.uuid4())
        request.resource_type = "test"
        response = await self.stub.Describe(request)
        _dict = self.message_to_dict(response)
        return _dict

    async def create(self, ids=[], extra={}):
        _params = {
            "resource_ids": ids
        }
        if extra:
            _params.update(extra)
        params = convert_to_JSONTYPE_dict(_params)
        request = CreateRequest(params=params)
        request.request_id = str(uuid.uuid4())
        request.resource_type = "test"
        async for res in self.stub.Create(request):
            yield self.message_to_dict(res)

    async def update(self):
        async def input(q):
            while True:
                res = await q.get()
                if res is not None:
                    yield res
                else:
                    break
        q = asyncio.Queue()

        res_generator = self.stub.Update(input(q))
        return res_generator, q

