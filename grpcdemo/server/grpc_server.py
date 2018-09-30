import grpc

from concurrent import futures


def create_grpc_server(host, port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1024))
    server.add_insecure_port(f'{host}:{port}')
    return server
