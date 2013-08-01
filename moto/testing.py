import socket
import threading
import time
from StringIO import StringIO

from tornado.httpclient import HTTPClient
from tornado.ioloop import IOLoop, PollIOLoop
from tornado.iostream import IOStream, SSLIOStream
from tornado.netutil import Resolver as BaseResolver

from tornado.platform import interface
from tornado.platform.select import _Select as BaseLoopImpl

from tornado.simple_httpclient import (
    SimpleAsyncHTTPClient as BaseClient,
    _HTTPConnection as BaseHTTPConnection,
)


def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.next()
        return cr
    return start


class FDTable(object):

    def __init__(self):
        self.fds = {}

    def _get_uniq_fileno(self):
        lastfd = len(self.fds) + 1
        while lastfd in self.fds:
            lastfd += 1
        return lastfd * 100

    def register(self, memfile):
        fd = self._get_uniq_fileno()
        self.fds[fd] = memfile
        return fd

    def check(self, rfds, wfds, efds):
        # output
        r_rfds, r_wfds, r_efds = [], [], []

        for rfd in rfds:
            file_obj = self.fds[rfd]
            if file_obj.output_stream.tell():
                print file_obj.output_stream.tell()
                r_rfds.append(rfd)

        for wfd in wfds:
            file_obj = self.fds[wfd]
            if file_obj.input_stream.tell():
                print file_obj.input_stream.tell()
                r_wfds.append(wfd)

        for efd in efds:
            file_obj = self.fds[efd]
            if file_obj.ioerror:
                r_efds.append(efd)

        return r_rfds, r_wfds, r_efds


fdtable = FDTable()


class MemFile(StringIO):
    def __init__(self, *args, **kwargs):
        StringIO.__init__(self, *args, **kwargs)
        self._fileno = fdtable.register(self)

    def fileno(self):
        return self._fileno

    def write(self, s):
        print 'WRITE {0}'.format(self._fileno)
        StringIO.write(self, s)

    def read(self, n=-1):
        print 'READ {0}'.format(self._fileno)
        val = StringIO.read(self, n)
        return val


def memselect(rfds, wfds, efds, timeout):
    step = 0.1

    while True:
        changes = fdtable.check(rfds, wfds, efds)
        if changes:
            return changes
        time.sleep(step)


class MemIOLoopImpl(BaseLoopImpl):

    def poll(self, timeout):
        readable, writeable, errors = memselect(
            self.read_fds, self.write_fds, self.error_fds, timeout)
        events = {}
        for fd in readable:
            events[fd] = events.get(fd, 0) | IOLoop.READ
        for fd in writeable:
            events[fd] = events.get(fd, 0) | IOLoop.WRITE
        for fd in errors:
            events[fd] = events.get(fd, 0) | IOLoop.ERROR
        return events.items()


class MemWaker(interface.Waker):
    def __init__(self):
        self.reader = MemFile()
        self.writer = MemFile()

    def fileno(self):
        return self.reader.fileno()

    def write_fileno(self):
        return self.writer.fileno()

    def wake(self):
        try:
            self.writer.write(b"x")
        except IOError:
            pass

    def consume(self):
        try:
            while True:
                result = self.reader.read()
                if not result:
                    break
        except IOError:
            pass

    def close(self):
        self.reader.close()
        self.writer.close()



class MemIOLoop(PollIOLoop):
    def initialize(self, impl=None, time_func=None):
        super(PollIOLoop, self).initialize()

        self._impl = impl or MemIOLoopImpl()
        if hasattr(self._impl, 'fileno'):
            set_close_exec(self._impl.fileno())
        self.time_func = time_func or time.time
        self._handlers = {}
        self._events = {}
        self._callbacks = []
        self._callback_lock = threading.Lock()
        self._timeouts = []
        self._cancellations = 0
        self._running = False
        self._stopped = False
        self._closing = False
        self._thread_ident = None
        self._blocking_signal_threshold = None

        # Create a pipe that we send bogus data to when we want to wake
        # the I/O loop when it is idle
        self._waker = MemWaker()
        # self.add_handler(self._waker.fileno(),
        #                  lambda fd, events: self._waker.consume(),
        #                  self.READ)

        # super(MemIOLoop, self).initialize(impl=MemIOLoopImpl(), **kwargs)


@coroutine
def waiter():
    while True:
        event = (yield)
        print event
        yield 'something else'


class MemSocket(socket.socket):

    def __init__(self,
                 family=socket.AF_INET,
                 type_=socket.SOCK_STREAM,
                 proto=0):
        super(MemSocket, self).__init__(family, type_, proto)

        self._fileno = fdtable.register(self)

        self.input_stream = MemFile()
        self.output_stream = MemFile()
        self.unknownhost = False
        self.ioerror = False

    def connect(self, (host, port)):
        if self.unknownhost:
            raise socket.gaierror()
        
        if self.ioerror:
            raise socket.error()

    def makefile(self, mode, size=0):
        if self.ioerror:
            raise socket.error
    
        if mode in ('w', 'wb'):
            return self.output_stream
        elif mode in ('r', 'rb'):
            return self.input_stream
        else:
            raise NotImplementedError('makefile mode not implemented') 

    def close(self):
        self.input_stream.close()
        self.output_stream.close()

    def fileno(self):
        return self._fileno

    def connect(self, addr):
        pass

    def accept(self):
        return (self, ('127.0.0.1', 80))

    def getsockopt(self, level, option, buffersize=0):
        return 0

    def setsockopt(self, level, optname, value):
        pass

    def setblocking(self, value):
        pass


class Resolver(BaseResolver):
    def resolve(self, *args, **kwargs):
        addrs = [(socket.AF_INET, ('127.0.0.1', 80)),]

        callback = kwargs.get('callback')
        if callback:
            callback(addrs)
        else:
            return addrs


class HTTPConnection(BaseHTTPConnection):
    def __init__(self, *args, **kwargs):
        self.socket = kwargs.pop('socket')
        super(HTTPConnection, self).__init__(*args, **kwargs)

    def _create_stream(self, addrinfo):
        af = addrinfo[0][0]
        if self.parsed.scheme == "https":
            ssl_options = {}
            if self.request.validate_cert:
                ssl_options["cert_reqs"] = ssl.CERT_REQUIRED
            if self.request.ca_certs is not None:
                ssl_options["ca_certs"] = self.request.ca_certs
            else:
                ssl_options["ca_certs"] = _DEFAULT_CA_CERTS
            if self.request.client_key is not None:
                ssl_options["keyfile"] = self.request.client_key
            if self.request.client_cert is not None:
                ssl_options["certfile"] = self.request.client_cert

            # SSL interoperability is tricky.  We want to disable
            # SSLv2 for security reasons; it wasn't disabled by default
            # until openssl 1.0.  The best way to do this is to use
            # the SSL_OP_NO_SSLv2, but that wasn't exposed to python
            # until 3.2.  Python 2.7 adds the ciphers argument, which
            # can also be used to disable SSLv2.  As a last resort
            # on python 2.6, we set ssl_version to SSLv3.  This is
            # more narrow than we'd like since it also breaks
            # compatibility with servers configured for TLSv1 only,
            # but nearly all servers support SSLv3:
            # http://blog.ivanristic.com/2011/09/ssl-survey-protocol-support.html
            if sys.version_info >= (2, 7):
                ssl_options["ciphers"] = "DEFAULT:!SSLv2"
            else:
                # This is really only necessary for pre-1.0 versions
                # of openssl, but python 2.6 doesn't expose version
                # information.
                ssl_options["ssl_version"] = ssl.PROTOCOL_SSLv3

            return SSLIOStream(MemSocket(af),
                               io_loop=self.io_loop,
                               ssl_options=ssl_options,
                               max_buffer_size=self.max_buffer_size)
        else:
            return IOStream(MemSocket(af),
                            io_loop=self.io_loop,
                            max_buffer_size=self.max_buffer_size)



class Client(BaseClient):

    def initialize(self, **kwargs):
        self.socket = kwargs.pop('socket')
        super(Client, self).initialize(**kwargs)

    def _handle_request(self, request, release_callback, final_callback):
        HTTPConnection(
            self.io_loop, self,
            request, release_callback, final_callback,
            self.max_buffer_size, self.resolver,
            socket=self.socket)


class HTTPClient(HTTPClient):
    def __init__(self, async_client_class=None, **kwargs):
        self._io_loop = MemIOLoop()
        if async_client_class is None:
            async_client_class = AsyncHTTPClient
        self._async_client = async_client_class(self._io_loop, **kwargs)
        self._closed = False


class TestClient(object):
    def __init__(self, socket):
        self.socket = socket
        self.client = HTTPClient(
            async_client_class=Client,
            socket=socket,
            resolver=Resolver(),
        )

    def get(self, path, headers=None):
        url = 'http://localhost:80{}'.format(path)
        self.client.fetch(url)
