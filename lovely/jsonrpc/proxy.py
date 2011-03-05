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

from urlparse import urlparse
import logging
import copy
import time
import Cookie
import base64
from lovely.jsonrpc import DEFAULT_JSON_IMPL, JSONImplementationNotFound

_log = logging.getLogger(__name__)

class RemoteException(Exception):
    """An error occured on the server side"""

class HTTPException(Exception):
    """A http exception occured"""

class JSONDeserializeException(Exception):
    """A json deserialization error occured"""

class Session(object):

    _auth = None

    def __init__(self, username=None, password=None):
        self.cookies = Cookie.SimpleCookie()
        if username and password:
            self._auth = {"AUTHORIZATION": "Basic %s" %
                          base64.encodestring("%s:%s" % (username, password)
                                              ).strip()}

    def save_headers(self, headers):
        if self._auth:
            headers.update(self._auth)
        headers['Cookie'] = self.cookies.output(header="")
        return headers

    def load_headers(self, headers):
        ch = headers.get('set-cookie')
        if ch:
            self.cookies.load(ch)

class BaseTransport(object):

    """Base transport implementation"""

    headers = {}

    def __init__(self, uri, session=None, headers={}):
        self.session = session
        self.headers = self.headers.copy()
        self.headers.update(headers)

    def get_headers(self):
        if self.session:
            headers = self.session.save_headers(self.headers.copy())
        else:
            headers = self.headers
        return headers

    def set_headers(self, headers):
        if headers and self.session:
            self.session.load_headers(headers)

class JSONRPCTransport(BaseTransport):

    """the default httplib transport implementation"""

    headers = {'User-Agent':'lovey.jsonpc.proxy (httplib)',
               'Content-Type':'application/json; charset=utf-8',
               'Accept':'application/json'}

    def __init__(self, uri, session=None, headers={}, timeout=None):
        super(JSONRPCTransport, self).__init__(uri, session=session,
                                               headers=headers)
        self.url = urlparse(uri)
        import httplib
        if self.url.scheme == 'http':
            conn_impl = httplib.HTTPConnection
        elif self.url.scheme == 'https':
            conn_impl = httplib.HTTPSConnection
        else:
            raise Exception, 'Unsupported scheme %r' % self.url.scheme
        if self.url.port:
            loc = ':'.join((self.url.hostname,
                            str(self.url.port)))
        else:
            loc = self.url.hostname
        if timeout is not None:
            self.conn = conn_impl(loc, timeout=timeout)
        else:
            self.conn = conn_impl(loc)

    def request(self, request_body):
        headers = self.get_headers()
        self.conn.request('POST', self.url.path,
                          body=request_body, headers=headers)
        resp = self.conn.getresponse()
        self.set_headers(dict(resp.getheaders()))
        return resp.status, resp.read()

class _Method(object):

    def __init__(self, call, name, json_impl, send_id):
        self.call = call
        self.name = name
        self.json_impl = json_impl
        self.send_id = send_id

    def __call__(self, *args, **kwargs):
        # Need to handle keyword arguments per 1.1 spec
        request = {}
        request['version'] = '1.1'
        request['method'] = self.name
        if self.send_id:
            request['id'] = int(time.time())
        if len(kwargs) is not 0:
            params = copy.copy(kwargs)
            index = 0
            for arg in args:
                params[str(index)] = arg
                index = index + 1
        elif len(args) is not 0:
            params = copy.copy(args)
        else:
            params = None
        request['params'] = params
        _log.debug('Created python request object %s' % str(request))
        return self.call(self.json_impl.dumps(request))

    def __getattr__(self, name):
        return _Method(self.call, "%s.%s" % (self.name, name), self.json_impl)

class ServerProxy(object):

    def __init__(self, uri, transport_impl=JSONRPCTransport,
                 json_impl=DEFAULT_JSON_IMPL, send_id=False, **kwargs):
        """Initialization"""
        self._transport = transport_impl(uri, **kwargs)
        if json_impl is None:
            raise JSONImplementationNotFound()
        self._json_impl = json_impl
        self._send_id = send_id

    def _request(self, payload):
        status, body = self._transport.request(payload)

        if status > 299:
            raise HTTPException, '%s\n%r' % (status, body)
        try:
            res = self._json_impl.loads(body)
        except ValueError:
            raise JSONDeserializeException, "Cannot deserialize json: %r" % body
        if res.get('error'):
            raise RemoteException, res.get('error')
        return res.get('result')

    def __repr__(self):
        return (
            "<ServerProxy for %s%s>" %
            (self.__host, self.__handler)
            )

    __str__ = __repr__

    def __getattr__(self, name):
        return _Method(self._request, name, self._json_impl, self._send_id)

