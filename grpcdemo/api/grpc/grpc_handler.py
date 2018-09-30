import asyncio
import functools
import json

import grpcdemo.global_vars as g

from grpcdemo.common.internal.internal_pb2_grpc import InternalServerServicer
from grpcdemo.common.internal.internal_pb2 import Resource, ResourceReply
from grpcdemo.common.internal.common_pb2 import JSONTYPE


def convert_to_JSONTYPE_dict(params):
    if params is None:
        return None
    jsontype_params = {key: JSONTYPE(json_str=json.dumps(value))
                       for key, value in params.items()}
    return jsontype_params


def wrap_async_generator(async_iterator, loop, timeout=None):
    while True:
        try:
            coro = async_iterator.__anext__()
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            yield future.result(timeout=timeout)
        except StopAsyncIteration:
            raise StopIteration
        finally:
            try:
                asyncio.run_coroutine_threadsafe(async_iterator.aclose()).result(timeout=5)
            except Exception:
                pass


def wrap_async(f):
    @functools.wraps(f)
    def _f(*args, **kwargs):
        future = asyncio.run_coroutine_threadsafe(f(*args, **kwargs), g.loop)
        return future.result()
    return _f


def wrap_async_stream(f):
    @functools.wraps(f)
    def _f(*args, **kwargs):
        yield from wrap_async_generator(f(*args, **kwargs), loop=g.loop)
    return _f


class WrappedIterator(object):
    """
    Wrap an grpc_iterator to an async iterator
    """

    def __init__(self, grpc_iterator, loop, executor=None, stream_executor=None):
        self._iterator = grpc_iterator
        self._loop = loop
        self._executor = executor
        if stream_executor is None:
            self._shared_executor = True
            self._stream_executor = executor
        else:
            self._shared_executor = False
            self._stream_executor = stream_executor
        self._next_future = None

    def __aiter__(self):
        return self

    def _next(self):
        if self._iterator is None:
            raise StopAsyncIteration
        try:
            return next(self._iterator)
        except StopIteration:
            raise StopAsyncIteration
        except Exception:
            if self._iterator._state.client == "cancelled":
                # FIXME(ZhengYue): Connection closed at client, workaround for avoid the GRPC exception
                raise StopAsyncIteration
            raise

    async def __anext__(self):
        if self._next_future is None:
            if self._iterator is None:
                raise StopAsyncIteration
            self._next_future = self._loop.run_in_executor(self._stream_executor, self._next)
        try:
            return await asyncio.shield(self._next_future, loop=self._loop)
        finally:
            if self._next_future and self._next_future.done():
                self._next_future = None

    def __del__(self):
        if self._iterator is not None:
            self._iterator = None
        if self._next_future is not None:
            if not self._loop.is_closed():
                self._loop.call_soon_threadsafe(lambda f=self._next_future: f.cancel())
            self._next_future = None
        if not self._shared_executor and self._stream_executor is not None:
            self._stream_executor.shutdown()
            self._stream_executor = None

    async def aclose(self):
        self.__del__()


class AsyncIter(object):
    def __init__(self):
        pass

    async def __aiter__(self):
        timeout = 3
        while timeout:
            timeout -= 1
            asyncio.sleep(2)
            yield timeout

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class GrpcServer(InternalServerServicer):

    def __init__(self):
        pass

    @wrap_async
    async def Describe(self, request, context):
        resource_type = request.resource_type
        params = {key: json.loads(value.json_str) for key, value in request.params.items()}
        print(params, resource_type)
        resources = []
        for _id in params['resource_ids']:
            _resource = Resource(
                info=convert_to_JSONTYPE_dict({"name": f"test-{_id}"}),
                id=_id,
                type=resource_type,
                is_error=False
            )
            resources.append(_resource)
        reply = ResourceReply(
            request_id=request.request_id,
            resources=resources,
            is_final=True,
            is_error=False
        )
        return reply

    @wrap_async_stream
    async def Create(self, request, context):
        resource_type = request.resource_type
        params = {key: json.loads(value.json_str) for key, value in request.params.items()}
        async for res in AsyncIter():
            resources = []
            _resource = Resource(
                info=convert_to_JSONTYPE_dict({"name": f"test-{res}"}),
                id="adsaf",
                type=resource_type,
                is_error=False
            )
            resources.append(_resource)
            is_final = False
            if res == 0:
                is_final = True
            reply = ResourceReply(
                request_id=request.request_id,
                resources=resources,
                is_final=is_final,
                is_error=False
            )
            yield reply

    @wrap_async_stream
    async def Update(self, request, context):
        cancel = False
        futures = []
        request_id = None

        response_queue = asyncio.Queue()

        async def _cleanup():
            # Cleanup is use for disconnection by client-side
            while context.is_active():
                await asyncio.sleep(5)
            else:
                # Context is inactive for request, cleanup
                nonlocal cancel
                cancel = True
                await response_queue.put(None)

        async def _handle_request(request, response_queue):
            request_count = 0
            async for param in WrappedIterator(request, loop=g.loop):
                request_count += 1
                request_id = param.request_id
                if param.resource_id:
                    resource_id = param.resource_id
                if request_count >= 1 and not param.cancel:
                    await response_queue.put(resource_id)
                    asyncio.ensure_future(_cleanup())
                if param.cancel:
                    nonlocal cancel
                    cancel = True
                    await response_queue.put(None)

        futures.append(asyncio.ensure_future(_handle_request(request, response_queue)))

        while not cancel:
            r_id = await response_queue.get()
            if r_id is None:
                for future in futures:
                    future.cancel()
                # Request canceled
                break
            resources = []
            _resource = Resource(
                info=convert_to_JSONTYPE_dict({"name": f"test-{r_id}"}),
                id=r_id,
                type="test",
                is_error=False
            )
            resources.append(_resource)
            reply = ResourceReply(
                request_id=r_id,
                resources=resources,
                is_final=False,
                is_error=False
            )
            yield reply
