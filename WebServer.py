import socket
import re


class Request:
    def __init__(self, path, method, headers):
        self.path = path
        self.method = method
        self.headers = headers


class Default404:
    def __call__(self, *args):
        return '<h1>404</h1><p>Page Not Found</p>'


class Default405:
    def __call__(self, *args, custom_msg: str = None):
        return f'<h1>405</h1><p>Method not allowed for {custom_msg if custom_msg else "this page"}</p>'


class Router:
    def __init__(self, routing_dict: dict):
        self._routing_dict = routing_dict

    @staticmethod
    def _make_headers(status_code: int, custom_msg: str = None) -> str:
        DEFAULT_CODE_MESSAGES = {200: 'OK',
                                 404: 'Not found',
                                 405: 'method not allowed'
                                 }

        header = f'HTTP/1.1 {status_code} {custom_msg if custom_msg else DEFAULT_CODE_MESSAGES[status_code]}\n\n'
        return header

    def _make_response(self, request: Request) -> str:
        controller_func = self._routing_dict.get(request.path)
        if not controller_func:
            status_code = 404
            controller_func = Default404()

        elif controller_func['method'] != request.method.upper():
            status_code = 405
            controller_func = Default405()

        else:
            status_code = 200
            controller_func = controller_func['func']

        headers = self._make_headers(status_code)
        body = controller_func(request)

        return headers + body

    @staticmethod
    def _parse_request(request: str) -> Request:

        # Getting method and path
        method, path = re.findall(r'[A-Z]+ /\S*', request)[0].split()

        # Getting headers and create dict with headers
        headers_raw = re.findall(r'.+: .+\n', request)
        headers = list(map(lambda header: header.strip().split(':'), headers_raw))
        headers_dict = {key: value for key, *value in headers}

        return Request(path, method, headers_dict)

    def get_response(self, request: str) -> str:
        request_obj = self._parse_request(request)
        return self._make_response(request_obj)


class _SocketServer:
    def __init__(self, ip: str, port: int, callback_function: callable):
        self._ip = ip
        self._port = port
        self.callback = callback_function

    def start(self):
        socket_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        socket_server.bind((self._ip, self._port))
        print('Served binded on {0}:{1}'.format(*socket_server.getsockname()))
        socket_server.listen()

        while True:
            try:
                client_socket, addr = socket_server.accept()
                request = client_socket.recv(1024)
                response = self.callback(request)
                client_socket.sendall(response)
                client_socket.close()
            except KeyboardInterrupt:
                return


class WebServer:
    _ip = '127.0.0.1'
    _port = 25565

    def __init__(self, ip: str = None, port: int = None):
        self._ip = ip if ip else self._ip
        self._port = port if port else self._port
        self._routing_dict = {}

    def router_register(self, path: str, method='GET') -> callable:
        def decorator(func: callable) -> callable:
            self._routing_dict[path] = {'method': method.upper(),
                                        'func': func}
            return func

        return decorator

    def _request_callback(self, request: bytes):
        request = request.decode(encoding='utf-8')
        return self.router.get_response(request).encode('utf-8')

    def run(self):
        self.router = Router(self._routing_dict)
        server = _SocketServer(self._ip, self._port, self._request_callback)
        server.start()


def render(path_to_file: str) -> str:
    with open(path_to_file, 'r', encoding='utf-8') as file:
        content = file.read()

    return content
