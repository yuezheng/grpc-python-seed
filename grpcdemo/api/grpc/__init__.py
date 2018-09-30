
from grpcdemo.common.internal.internal_pb2_grpc import add_InternalServerServicer_to_server

from grpcdemo.api.grpc.grpc_handler import GrpcServer


def add_servicer(server):
    add_InternalServerServicer_to_server(GrpcServer(), server)
