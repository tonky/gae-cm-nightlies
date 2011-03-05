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

from lovely.jsonrpc import dispatcher
import logging

_log = logging.getLogger(__name__)

class WSGIJSONRPCApplication(object):

    """Ac WSGI Application for generic JSONRPC requests."""

    def __init__(self, dispatchers):
        self.dispatchers = dispatchers

    def handler(self, environ, start_response):
        """A WSGI handler for generic JSONRPC requests."""

        if environ['REQUEST_METHOD'].endswith('POST'):
            entry_point = environ.get('PATH_INFO', '')[1:]
            dispatcher = self.dispatchers.get(entry_point)
            if not dispatcher:
                start_response('404 NotFound',
                               [('Cache-Control','no-cache'),
                                ('Content-Type', 'text/plain')])
                return ['404 Not found']
            body = None
            if environ.get('CONTENT_LENGTH'):
                length = int(environ['CONTENT_LENGTH'])
                body = environ['wsgi.input'].read(length)

            try:
                _log.debug('Sending %s to dispatcher' % body)
                response = dispatcher.dispatch(body)
                start_response('200 OK',
                               [('Cache-Control','no-cache'),
                                ('Pragma','no-cache'),
                                ('Content-Type', 'application/json')])
                return [response]
            except Exception, e:
                _log.exception(
                    'WSGIJSONRPCApplication Dispatcher encountered exception')
                start_response(
                    '500 Internal Server Error',
                    [('Cache-Control','no-cache'),
                     ('Content-Type', 'text/plain')])
                return ['500 Internal Server Error']

        else:
            start_response('405 Method Not Allowed',
                           [('Cache-Control','no-cache'),
                            ('Content-Type', 'text/plain')])
            return ['405 Method Not Allowed. This JSONRPC interface only supports POST. Method used was "'+str(environ['REQUEST_METHOD'])+'"']

    def __call__(self, environ, start_response):
        return self.handler(environ, start_response)


