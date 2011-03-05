##############################################################################
#
# Copyright 2008 Lovely Systems GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################

from lovely.jsonrpc import wsgi
import threading
from wsgiref.simple_server import make_server
from lovely.jsonrpc import dispatcher
from lovely.jsonrpc import proxy

class TestingAPI(object):

    def echo(self, *args, **kwargs):
        return args, kwargs


class App(object):

    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __call__(self, environ, start_response):
        for k in [k for k in sorted(environ) if k.startswith('HTTP_')]:
            print k, environ[k]
        res = self.wrapped(environ, lambda s, h: self.start_response(
            start_response, s, h))
        return res

    def start_response(self, sr, status, headers):
        headers += (('Set-Cookie', 'x=1'),)
        return sr(status, headers)

def get_server(port=12345):
    api = TestingAPI()
    app = wsgi.WSGIJSONRPCApplication({'':dispatcher.JSONRPCDispatcher(api)})
    return  make_server('localhost', 12345, App(app))

class OneRequest(threading.Thread):

    def __init__(self, server):
        super(OneRequest, self).__init__()
        self.server = server

    def run(self):
        self.server.handle_request()

def one_request(server):
    OneRequest(server).start()


class TestJSONRPCTransport(object):
    """transport for testing"""

    def __init__(self, base, app):
        self.base = base
        self._client = app

    def request(self, requestBody):
        self._client.lastRequestBody = requestBody
        resp = self._client.post(self.base, requestBody,
                                 content_type="application/json")
        return resp.status_int, resp.body

def TestJSONRPCProxy(base, app):
    import simplejson
    return proxy.ServerProxy(
        base,
        json_impl = simplejson,
        transport_impl=TestJSONRPCTransport,
        app=app)

