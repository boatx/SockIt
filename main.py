import sys
import asyncio
import logging

from sockit.server import WebSocketServer


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
log = logging.getLogger(__name__)


class Settings:
    HOST = "127.0.0.1"
    PORT = 8888


def main():
    loop = asyncio.get_event_loop()
    # Each client connection will create a new protocol instance
    coro = loop.create_server(WebSocketServer, Settings.HOST, Settings.PORT)
    log.info("start server on {}:{}".format(Settings.HOST, Settings.PORT))
    server = loop.run_until_complete(coro)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    sys.exit(0)


if __name__ == "__main__":
    main()
