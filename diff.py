from config.config import device_specific, Change, qs_device

import logging
import os

from lovely.jsonrpc import proxy
from django.utils import simplejson as json

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


# tests if all elements of array a are in array b
def is_subset(a, b):
    for i in a:
      if not i in b:
        return False

    return True

class ReviewsCron(webapp.RequestHandler):
    def _known_ids(self):
        known = memcache.get('known_ids')

        if known is not None:
            return known

        q = db.GqlQuery("SELECT * FROM Change order by last_updated desc")

        last_changes = q.fetch(300)

        known_ids = [int(c.id) for c in last_changes]

        memcache.set('last_changes', last_changes)
        memcache.set('known_ids', known_ids)

        return known_ids

    def _update_changes(self, changes, known_ids):
        skipped = 0

        for c in changes:
            if c['id']['id'] in known_ids:
                skipped += 1
                continue

            change = Change(id=c['id']['id'],
                    project=c['project']['key']['name'].split("/")[1],
                    subject=c['subject'],
                    last_updated=c['lastUpdatedOn']
                    )
            change.put()

        # update known_ids and last_changes memcache
        memcache.delete('known_ids')
        self._known_ids()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Skipped %d of %d changes" % (skipped, len(changes)))

    def get(self):
        amount = 40

        qa = self.request.get('amount')

        if qa: amount = int(qa)

        change_proxy = proxy.ServerProxy('http://review.cyanogenmod.com/gerrit/rpc/ChangeListService')
        changes = change_proxy.allQueryNext("status:merged","z",amount)['changes']

        known_ids = self._known_ids()

        received_ids = [c['id']['id'] for c in changes]

        if is_subset(received_ids, known_ids):
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("Skipped all %d changes" % len(changes))
            return

        return self._update_changes(changes, known_ids)


class MainPage(webapp.RequestHandler):
    def get(self):
        device = qs_device(self)

        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path,
            {'devices':sorted(device_specific.keys()), "for_device": device}))


class Ajax(webapp.RequestHandler):
    def common_projects(self):
        common = memcache.get('common_projects')

        if common is not None:
            return common

        f = open('common_projects.txt', 'r')
        cp = [p.strip() for p in f.readlines()]
        f.closed

        memcache.set("common_projects", cp, 3600)

        return cp

    def filter(self, device):
        filtered = memcache.get('filtered', device)

        if filtered and filtered is not None:
            return filtered

        filtered = []

        common = self.common_projects()

        for c in self._last_changes():
            if c.project in common or c.project in device_specific[device]:
                filtered.append({"id": c.id, "project": c.project,
                    "subject": c.subject, "last_updated": c.last_updated})

        memcache.set('filtered', filtered, 600, namespace=device)

        return filtered

    def _last_changes(self, amount=300):
        return memcache.get('last_changes') or []

    def get(self):
        device = qs_device(self)

        self.response.headers['Content-Type'] = 'text/json'
        self.response.out.write(json.dumps(self.filter(device)))


application = webapp.WSGIApplication(
                                     [('/', MainPage), ('/changelog/', Ajax),
                                         ('/pull_reviews/', ReviewsCron)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
