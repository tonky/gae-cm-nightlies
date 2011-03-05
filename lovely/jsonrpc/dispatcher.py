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

import types
import logging
import sys, traceback
from lovely.jsonrpc import DEFAULT_JSON_IMPL, JSONImplementationNotFound
import functools

_log = logging.getLogger(__name__)

_descriptions = set(['summary', 'help', 'idempotent', 'params', 'return'])

def async(method):
    method.__async__ = True
    return method

class JSONRPCError(Exception):
    """JSONRPC Error"""

class BadJSONRequestError(Exception):
    """Cannot parse JSON-RPC request body"""

def describe_method(method):
    """Check is a callable object has description params set"""
    description = {}
    for key in _descriptions:
        if hasattr(method, key):
            description[key] = getattr(method, key)
    return description


class JSONRPCMethod(object):

    def __init__(self, func, cb):
        self.func = func
        self.cb

    def __call__(self, *args, **kwargs):
        res = self.func(*args, **kwargs)
        

class JSONRPCDispatcher(object):

    def __init__(self, instance=None, methods=None,
                 name='Python JSONRPC Service',
                 summary='Service dispatched by python JSONRPCDispatcher',
                 help=None, address=None, json_impl=DEFAULT_JSON_IMPL):

        """Initialization. Can take an instance to register upon initialization"""

        if json_impl is None:
            raise JSONImplementationNotFound()
        self.json_impl = json_impl
        self.instances = []
        self.name = name
        self.help = help
        self.address = address
        self.summary = summary
        # Store all attributes of class before any methods are added
        # for negative lookup later
        self.base_attributes = set(dir(self))
        self.base_attributes.add('base_attributes')

        self.methods = {
            u'system.list_methods': self.system_list_methods,
            u'system.describe': self.system_describe
            }

        # If instance was given during initialization then register it
        if instance is not None:
            self.register_instance(instance)
        if methods is not None:
            for method in methods:
                self.register_method(method)

    def register_instance(self, instance):
        """Registers all attributes of class instance to dispatcher"""
        for attribute in dir(instance):
            if attribute.startswith('_') is False:
                # All public attributes
                self.register_method(getattr(instance, attribute), name=attribute)

        # Store it in the list for convienience
        self.instances.append(instance)

    def register_method(self, function, name=None):
        """Registers a method with the dispatcher"""
        # If the name isn't passed try to find it. If we can't fail gracefully.
        if name is None:
            try:
                name = function.__name__
            except:
                if hasattr(function, '__call__'):
                    raise """Callable class instances must be passed with name parameter"""
                else:
                    raise """Not a function"""

        if not name in self.methods:
            self.methods[unicode(name)] = function
        else:
            print 'Attribute name conflict -- %s must be removed before attribute of the same name can be added'

    def system_list_methods(self):
        """List all the available methods and return a object parsable
        that conforms to the JSONRPC Service Procedure Description
        specification"""
        method_list = []
        for key, value in self.methods.items():
            method = {}
            method['name'] = key
            method.update(describe_method(value))
            method_list.append(method)
        method_list.sort()
        return method_list

    def system_describe(self):
        """Service description"""
        description = {}
        description['sdversion'] = '1.0'
        description['name'] = self.name
        description['summary'] = self.summary
        if self.help is not None:
            description['help'] = self.help
        if self.address is not None:
            description['address'] = self.address
        description['procs'] = self.system_list_methods()
        return description

    def dispatch(self, json, cb=None):
        """Public dispatcher, verifies that a method exists in it's
        method dictionary and calls it"""
        try:
            rpc_request = self._decode(json)
        except ValueError:
            raise BadJSONRequestError, json
        _log.debug('decoded to python object %s' % str(rpc_request))

        result = None
        error = None
        jsonrpc_id = rpc_request.get('id')

        logged_failure = False

        try:
            method_name = rpc_request.get('method')
            if not method_name:
                raise JSONRPCError('missing method name')

            method = self.methods.get(method_name)
            if method is None:
                raise JSONRPCError('method %r not found' % method_name)

            params = rpc_request.get('params', [])
            args = []
            kwargs = {}
            if type(params) is types.DictType:
                sargs = []
                for k, v in params.items():
                    k = str(k)
                    try:
                        k = int(k)
                        sargs.append((k, v))
                    except ValueError:
                        kwargs[k] = v
                args = [a[1] for a in sorted(sargs)]
            elif type(params) in (list, tuple):
                args =  params
            elif params is not None:
                # If type was something weird just return a JSONRPC Error
                raise JSONRPCError('params not array or object type')
        except JSONRPCError, e:
            res = self._encode(error=e, jsonrpc_id=jsonrpc_id)
            if cb:
                return cb(res)
            else:
                return res

        cb = functools.partial(self._on_result,
                               callback=cb, jsonrpc_id=jsonrpc_id)
        if getattr(method, '__async__', False):
            method = functools.partial(method, callback=cb)
            is_async = True
        else:
            is_async = False
        try:
            result = method(*args, **kwargs)
        except Exception, e:
            error = e
            tb = ''.join(traceback.format_exception(*sys.exc_info()))
            logging.error(tb)
        if error:
            return cb(None, error=error)
        if is_async:
            return result
        else:
            return cb(result)

    def _on_result(self, result, callback=None, jsonrpc_id=None, error=None):
        res =  self._encode(result=result, jsonrpc_id=jsonrpc_id, error=error)
        if callback is None:
            return res
        else:
            callback(res)

    def _encode(self, result=None, error=None, jsonrpc_id=None):
        """Internal encoder method, handles error formatting, id
        persistence, and encoding via the give json_impl"""
        response = {}
        response['result'] = result
        if jsonrpc_id is not None:
            response['id'] = jsonrpc_id
        if error is not None:
            error_message = str(error).strip()
            if hasattr(error, 'type'):
                error_type = str(error.type)
            elif hasattr(error, '__class__'):
                error_type = error.__class__.__name__
            else:
                error_type = 'JSONRPCError'
            response['error'] = {'type':error_type,
                                 'message':error_message}
        _log.debug('serializing %s' % str(response))
        return self.json_impl.dumps(response)

    def _decode(self, json):
        """Internal method for decoding json objects, uses simplejson"""
        return self.json_impl.loads(json)

