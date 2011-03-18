from config.config import device_specific, Change, qs_device

import httplib
import logging
import os
import re

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


class Rss(webapp.RequestHandler):
    def nightlies(self, device):
        rss = memcache.get('rss', device)
        if rss: return rss

        conn = httplib.HTTPConnection("mirror.teamdouche.net")
        conn.request("GET", "/?device=%s" % device)

        html = conn.getresponse().read()

        name_date = "(?P<filename>cm_.*?\.zip).*?(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"

        nightlies_raw  = re.findall(name_date, html, re.S);

        memcache.set('rss', nightlies_raw, 300, namespace=device)

        return nightlies_raw

    def get(self):
        device = qs_device(self)

        path = os.path.join(os.path.dirname(__file__), 'rss.xml')
        self.response.out.write(template.render(path, {"device": device,
            "changes": self.nightlies(device)}))

application = webapp.WSGIApplication([('/rss', Rss)], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
