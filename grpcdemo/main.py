import asyncio
import logging.config
import sys

import grpcdemo.global_vars as g

from grpcdemo.server.grpc_server import create_grpc_server
from grpcdemo.api.grpc import add_servicer


logger = logging.getLogger(__name__)


def main(argv):
    loop = asyncio.get_event_loop()
    g.loop = loop

    server = create_grpc_server("0.0.0.0", "50002")
    add_servicer(server)
    server.start()
    logger.info("Grpc server started at 0.0.0.0:50002")
    print("fefefe")

    try:
        loop.run_forever()
    finally:
        server.stop()
        loop.close()


if __name__ == '__main__':
    main(sys.argv[1:])