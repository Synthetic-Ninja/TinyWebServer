#!./venv/bin/python3

from WebServer import WebServer, render

server = WebServer()


@server.router_register('/', method='get')
def index(request) -> str:
    return render('./test.html')


if __name__ == '__main__':
    exit(server.run())
