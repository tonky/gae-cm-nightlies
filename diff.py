import os

from lovely.jsonrpc import proxy

from google.appengine.dist import use_library
use_library('django', '1.2')
from django.utils import simplejson as json

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db


class Change(db.Model):
    message = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        change = Change()
        change.message = "ohai"
        change.put()

        change_proxy = proxy.ServerProxy('http://review.cyanogenmod.com/gerrit/rpc/ChangeListService')
        changes = change_proxy.allQueryNext("status:merged","z",50)

        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write('<html><body>')

        template_values = {"changes": changes['changes']}

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
                                     [('/', MainPage)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
