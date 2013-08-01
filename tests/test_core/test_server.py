import functools

from mock import patch, Mock
from moto.server import main, Server
from moto.testing import MemSocket, MemIOLoop, TestClient


# @patch('sys.stderr', Mock())    # Supressing argparse complaints
# def test_wrong_arguments():
#     (main.when.called_with(["name", "test1", "test2", "test3"])
#      .should.throw(SystemExit))


# @patch('moto.server.app.run')
# def test_right_arguments(app_run):
#     main(["s3"])
#     app_run.assert_called_once_with(host='0.0.0.0', port=5000)


# @patch('moto.server.app.run')
# def test_port_argument(app_run):
#     main(["s3", "--port", "8080"])
#     app_run.assert_called_once_with(host='0.0.0.0', port=8080)


# def test_in_mem_ioloop():

#     def connection_ready(sock, fd, events):
#         while True:
#             try:
#                 connection, address = sock.accept()
#             except socket.error as exc:
#                 if exc.args[0] not in (erno.EWOULDBLOCK, errno.EAGAIN):
#                     raise
#                 return
#             connection.setblocking(False)
#             handle_connection(connection, address)

#     sock = MemSocket()
#     sock.connect(None)

#     callback = functools.partial(connection_ready, sock)
#     sock.send('yo')

#     ioloop = MemIOLoop()
#     ioloop.add_handler(sock.fileno(), callback, ioloop.WRITE)
#     ioloop.start()


def test_server_from_socket():
    # Given that I have server associated with a fake socket instance and a
    # path mapping
    sock = MemSocket()
    io_loop = MemIOLoop()

    server = Server(
        mapping={'/$': lambda: (200, {}, '<h1>Fake socket rulz!</h1>')},
        socket=sock,
        io_loop=io_loop,
    )
    server.listen()

    # When I create a new test-client based on that same socket
    client = TestClient(socket=sock)

    # Then I see I can perform requests to that server
    response = client.get('/').data.should.equal('<h1>Fake socket rulz!</h1>')


# def test_server_url_binding():

#     # Given that I have a controller and a url mapping that maps the path `/`
#     # to our controller
#     def handler():
#         return 200, {}, '<h1>Yo!</h1>'

#     paths = {'/$': handler}

#     # When I create a new server
#     app = Server(paths)

#     # Then I see that the recently registered url mapping is available for
#     # requests
#     response = app.get('/')
#     response.status_code.should.equal(200)
#     response.data.should.contain('<h1>Yo!</h1>')

    

# def test_server_url_binding_with_parameters():

#     # Given that I have a controller that takes a parameter and a url mapping
#     # that maps the path `/` to our controller
#     def handler(name):
#         return 200, {}, '<h1>Hi {0}!</h1>'.format(name)

#     url_paths = {
#         '/(?P<name>[a-zA-Z0-9\-_.]+)': handler,
#     }

#     paths = {'{0}/$': handler}

#     # When I create a new server
#     app = Server(paths)

#     # Then I see that the recently registered url mapping is available for
#     # requests
#     response = app.get('/lincoln')
#     response.status_code.should.equal(200)
#     response.data.should.contain('<h1>lincoln!</h1>')
