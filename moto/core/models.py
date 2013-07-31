import functools
import re

from httpretty import httpretty
from .responses import metadata_response


class MockAWS(object):
    def __init__(self, backend):
        self.backend = backend

    def __call__(self, func):
        return self.decorate_callable(func)

    def __enter__(self):
        self.start()

    def __exit__(self, *args):
        self.stop()

    def start(self):
        self.backend.reset()
        httpretty.enable()

        for method in httpretty.METHODS:
            for key, value in self.backend.urls.iteritems():
                httpretty.register_uri(
                    method=method,
                    uri=re.compile(key),
                    body=value,
                )

            # Mock out localhost instance metadata
            httpretty.register_uri(
                method=method,
                uri=re.compile('http://169.254.169.254/latest/meta-data/.*'),
                body=metadata_response
            )

    def stop(self):
        httpretty.disable()

    def decorate_callable(self, func):
        def wrapper(*args, **kwargs):
            with self:
                result = func(*args, **kwargs)
            return result
        functools.update_wrapper(wrapper, func)
        return wrapper


class BaseBackend(object):

    def reset(self):
        self.__dict__ = {}
        self.__init__()

    @property
    def _url_module(self):
        backend_module = self.__class__.__module__
        backend_urls_module_name = backend_module.replace("models", "urls")
        backend_urls_module = __import__(backend_urls_module_name, fromlist=['url_bases', 'url_paths'])
        return backend_urls_module

    @property
    def urls(self):
        """
        A dictionary of the urls to be mocked with this service and the handlers
        that should be called in their place
        """
        url_bases = self._url_module.url_bases
        unformatted_paths = self._url_module.url_paths

        urls = {}
        for url_base in url_bases:
            for url_path, handler in unformatted_paths.iteritems():
                url = url_path.format(url_base)
                urls[url] = handler

        return urls

    @property
    def url_paths(self):
        """
        A dictionary of the paths of the urls to be mocked with this service and
        the handlers that should be called in their place
        """
        unformatted_paths = self._url_module.url_paths

        paths = {}
        for unformatted_path, handler in unformatted_paths.iteritems():
            path = unformatted_path.format("")
            paths[path] = handler

        return paths

    def decorator(self, func=None):
        if func:
            return MockAWS(self)(func)
        else:
            return MockAWS(self)
