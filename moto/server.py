# -*- coding: utf-8; -*-
from __future__ import unicode_literals, print_function

import sys
import argparse

from twisted.python import log
from twisted.web import server
from twisted.web.resource import Resource, NoResource
from twisted.internet import reactor

from moto.backends import BACKENDS

BANNER = '''
hd/                         --.
 mMo                     -hdsssmh+.
 -NM+                   :N-     .+dho.   `/+ys
  /MN-                  sd   `-yhNmhoddo:+MMMd
   oMm.                 `: :dNMMMMMMddNMMNNNy+
   `yMd ```              :dMMMMMMMms.  +Mh./ymds:
    {0}.mMNMMMddso`{1}         hMMMMMho-`    dd     ./shy+-            {0}`:+sss+:`{1}
  {0}`odMMMMMMMMMMMd/{1}  :ohdmds/`         sm.         `/shho-     {0}:sNNhsooohmMms`{1}
 {0}sMMMMMMMMMMMMMMMMm{1}MNyhdmMy`   sMNs: sm.              `:sdho-{0}yMh/`       `oNMs{1}
{0}+MMMMNsyM. :oNMMMMm.{1}  dMMMMy  sMMMMmhm.                    {0}:MMMs:`         `yMs{1}
{0}MMMMN:{1} `mm+ydy{0}NMMMM/{1} .-hMMMMo+MMMNsyN-                     {0}+Mh{1}`:ohhoss-     {0}`MM{1}
{0}MMMMm`{1} `NMMd:`{0}dMMMMo{1}dNyhMMMMMMMMd.+N:                      {0}oMy{1}    `sMMd`    {0}`dM{1}
{0}NMMMMy.{1} `..-oN{0}NMMMM-{1}Mh..mMMMMMdhNsm:                       {0}:Mm.{1}     ..`     {0}:MN{1}
{0}-NMMMMMys/+smMMMMMd+{1}sMMMMMMMMMMMMM:                         {0}oMm:           /NN-{1}
 {0}`hMMMMMMMMMMMMMd:.{1}/+++++++++++++:                           {0}:dMd/.     :odMh`{1}
   {0}`+yNMMMMMNy+-{1}                                               {0}:shNMmdMMNy+`{1}

Moto server is running!
'''.format('\033[1;30m', '\033[0m')


class ResponseWrapper(object):
    def __init__(self, callback):
        self.callback = callback

    @property
    def __name__(self):
        # For instance methods, use class and method names. Otherwise
        # use module and method name
        if inspect.ismethod(self.callback):
            outer = self.callback.im_class.__name__
        else:
            outer = self.callback.__module__
        return "{}.{}".format(outer, self.callback.__name__)

    def __call__(self, args=None, **kwargs):
        headers = dict(request.headers)
        result = self.callback(request, request.url, headers)

        # result is a status, headers, response tuple
        status, headers, response = result
        return response, status, headers


class App(Resource):

    def __init__(self, mapping):
        self.mapping = mapping
        Resource.__init__(self)

    def getChild(self, name, request):
        if not name:
            return self
        return NoResource()

    def render(self, request):
        # Extracting the raw headers from the request we just received from
        # twisted
        request_headers = \
            {x[0]: x[1][0] for x in request.requestHeaders.getAllRawHeaders()}

        # Executing the handler we found
        code, headers, response = self.mapping.get('/')(
            request, request.uri, request_headers)

        # Updating the response with the code received from the backend
        request.setResponseCode(code)

        return response


def main(argv=sys.argv[1:]):
    available_services = BACKENDS.keys()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'service', type=str,
        choices=available_services,
        help='Choose which mechanism you want to run')
    parser.add_argument(
        '-H', '--host', type=str,
        help='Which host to bind',
        default='0.0.0.0')
    parser.add_argument(
        '-p', '--port', type=int,
        help='Port number to use for connection',
        default=5000)

    args = parser.parse_args(argv)

    urls = BACKENDS[args.service].url_paths
    site = server.Site(App(urls))
    log.addObserver(lambda a: print('\n'.join(a['message'])))

    print(BANNER)
    reactor.listenTCP(args.port, site)
    reactor.run()

if __name__ == '__main__':
    main()
