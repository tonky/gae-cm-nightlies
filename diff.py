import logging
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
    id = db.IntegerProperty()
    project = db.StringProperty()
    subject = db.StringProperty()
    last_updated = db.StringProperty()


class MainPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))


class Ajax(webapp.RequestHandler):
    def common_projects(self):
        f = open('common_projects.txt', 'r')
        cp = [p.strip() for p in f.readlines()]
        f.closed

        return cp

    def filter(self, device):
        filtered = []

        device_specific = {
            "ace": ["android_device_htc_ace"],
            "encore": ["android_device_bn_encore"]
        }

        q = Change.all()

        common = self.common_projects()

        for c in q.fetch(300):
            if c.project in common or c.project in device_specific[device]:
                filtered.append({"id": c.id, "project": c.project,
                    "subject": c.subject, "last_updated": c.last_updated})

        return filtered

    def get(self):
        change_proxy = proxy.ServerProxy('http://review.cyanogenmod.com/gerrit/rpc/ChangeListService')
        changes = change_proxy.allQueryNext("status:merged","z",100)['changes']

        for c in changes:
            q = db.GqlQuery("SELECT * FROM Change " +
                "WHERE id = :1", c['id']['id'])

            if q.fetch(1):
                # logging.debug("%d: already in db" % c['id']['id'])
                continue

            change = Change(id=c['id']['id'],
                    project=c['project']['key']['name'].split("/")[1],
                    subject=c['subject'],
                    last_updated=c['lastUpdatedOn']
                    )
            change.put()

        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(json.dumps(self.filter("ace")))


application = webapp.WSGIApplication(
                                     [('/', MainPage), ('/changelog/', Ajax)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
