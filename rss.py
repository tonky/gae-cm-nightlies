from config.config import device_specific, Change, qs_device

from datetime import datetime, timedelta
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

        nightlies = []

        conn = httplib.HTTPConnection("download.cyanogenmod.com")
        conn.request("GET", "/?device=%s" % device)

        html = conn.getresponse().read()

        name_date = "(?P<filename>update.*?\.zip).*?(?P<date>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})"

        nightlies_raw  = re.findall(name_date, html, re.S);

        for name, date in nightlies_raw:
            naive_dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

            utc_dt = naive_dt - timedelta(hours=2)

            nightlies.append((name, utc_dt))

        memcache.set('rss', nightlies, 600, namespace=device)

        return nightlies

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
