from tornado.web import RequestHandler, asynchronous

class JSONRPCRequestHandler(RequestHandler):

    SUPPORTED_METHODS = ("POST",)

    def __init__(self, application, request, dispatcher=None, **kwargs):
        assert dispatcher, 'dispatcher is required'
        super(JSONRPCRequestHandler, self).__init__(
            application, request, **kwargs)
        self.dispatcher = dispatcher

    def _on_result(self, res):
        self.set_header('Content-Type', 'application/json')
        self.write(res)
        self.finish()

    @asynchronous
    def post(self):
        res = self.dispatcher.dispatch(self.request.body, cb=self._on_result)




