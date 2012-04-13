from config.config import use_kang_extension, allow_db_clear, branch_device, device_specific, Change, qs_branch, qs_device, qs_kang_name, qs_kang_id

import logging
import os
import time
import re

from datetime import datetime, timedelta
from urllib import urlopen
from lovely.jsonrpc import proxy
from django.utils import simplejson as json

#from operator import itemgetter

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


def json_datetime_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError, 'Object of type %s with value of %s is not JSON serializable' % (type(obj), repr(obj))

# tests if all elements of array a are in array b
def is_subset(a, b):
    for i in a:
      if not i in b:
        return False

    return True

def last_changes(branch):
    if branch == 'None' or branch == '' or branch is None:
        branch = 'gingerbread'
    last_changes = memcache.get('last_changes', branch)

    if last_changes is not None:
        # logging.debug("-----------> last changes cache hit")
        return last_changes
    
    
    #q = db.GqlQuery("SELECT * FROM Change WHERE branch = :1 ORDER BY last_updated DESC", branch)
    if branch == '--all--':
        q = Change.gql("ORDER BY last_updated DESC")
    else:
        q = Change.gql("WHERE branch = :branch ORDER BY last_updated DESC", branch=branch)
        
    last_changes = q.fetch(400)

    memcache.set('last_changes', last_changes, namespace=branch)

    return last_changes

class ShowDb(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)
        self.response.headers['Content-Type'] = 'text/html'
        
        if self.request.get('filter') and self.request.get('filter') == "1":
             q = Change.gql("WHERE branch = :branch ORDER BY last_updated DESC", branch=branch)
        else:
             q = db.GqlQuery("SELECT * FROM Change ORDER BY last_updated, id")
        ch = q.fetch(500)
        
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>branch</td><td>id</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for r in ch:
            #r.subject = time.strftime('%Y-%m-%d %H:%M')+' - '
            self.response.out.write("<tr><td>"+str(r.branch)+"</td>\n")
            self.response.out.write("<td>"+str(r.id)+"</td>\n")
            self.response.out.write("<td>"+str(r.subject)+"</td>\n")
            self.response.out.write("<td>"+str(r.project)+"</td>\n")
            self.response.out.write("<td>"+str(r.last_updated)+"</td></tr>\n")
        self.response.out.write("</tbody></table>")
        
        self.response.out.write("<pre>")
        self.response.out.write(json.dumps(Ajax().filter(device, branch)))
        self.response.out.write("</pre>")
        return

class RmDuplicate(webapp.RequestHandler):
    def get(self):
        device = qs_device(self)
        
        self.response.headers['Content-Type'] = 'text/html'
        memcache.flush_all()
        
        q = db.GqlQuery("SELECT * FROM Change ORDER BY id")
        ch = q.fetch(500)
        
        seen = []
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>action</td><td>branch</td><td>id</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for r in ch:
            action = 'keep'
            if r.id in seen:
                action = 'remove'
                r.delete()
            
            if r.branch is None:
                r.branch = 'gingerbread'
                r.put()
            
            if r.project == 'KANG' and not re.search("^.*#dev:.*$", r.subject):
                r.subject = r.subject+"#dev:"+device
                r.put()
            if r.project == 'KANG' and re.search("^.*?#dev:.*?#dev:.*$", r.subject):
                r.subject = re.sub(r"^(.*?#dev:.*?)#dev:.*?$", r'\1', r.subject)
                r.put()
            if r.project == 'KANG' and re.search("^\d\d\d\d-\d\d-\d\d \d\d:\d\d - (.*#dev:.*)$", r.subject):
                r.subject = re.sub(r"^\d\d\d\d-\d\d-\d\d \d\d:\d\d - (.*#dev:.*)$", r'\1', r.subject)
                r.put()
            
            seen.append(r.id)
            #r.subject = time.strftime('%Y-%m-%d %H:%M')+' - '
            self.response.out.write("<tr>")
            self.response.out.write("<td>"+action+"</td>\n")
            self.response.out.write("<td>"+str(r.branch)+"</td>\n")
            self.response.out.write("<td>"+str(r.id)+"</td>\n")
            self.response.out.write("<td>"+str(r.subject)+"</td>\n")
            self.response.out.write("<td>"+str(r.project)+"</td>\n")
            self.response.out.write("<td>"+str(r.last_updated)+"</td></tr>\n")
        
        self.response.out.write("</tbody></table>")
        memcache.flush_all()
        return

class ChangesAvailableDevice(webapp.RequestHandler):
    def get(self):
        kang = qs_kang_name(self)
        branch = qs_branch(self)
        device = qs_device(self)
        lc = Ajax().filter(device, branch)
        
        self.response.headers['Content-Type'] = 'text/plain'
        status = 200
        for c in lc:
            #self.response.out.write(str(c.id) + ": " + c.project + ", " + c.subject + "\n")
            if c['project'] == 'KANG' and re.search("^"+kang+"(#dev:"+device+")?$", c['subject']):
                status = 201
                break
            elif c['project'] != 'KANG':
                break
        self.response.out.write("Changes available ("+str(status)+"): ")
        if status == 200:
            self.response.out.write("yes")
        else:
            self.response.out.write("no")
        self.response.out.write("\n")
        
        self.response.set_status(status)
        return status

class ChangesAvailable(webapp.RequestHandler):
    def get(self):
        kang = qs_kang_name(self)
        branch = qs_branch(self)
        device = qs_device(self)
        lc = last_changes(branch)
        
        self.response.headers['Content-Type'] = 'text/plain'
        status = 200
        for c in lc:
            #self.response.out.write(str(c.id) + ": " + c.project + ", " + c.subject + "\n")
            if c.project == 'KANG' and re.search("^"+kang+"(#dev:"+device+")?$", c.subject):
                status = 201
                break
            elif c.project != 'KANG':
                break
        self.response.out.write("Changes available ("+str(status)+"): ")
        if status == 200:
            self.response.out.write("yes")
        else:
            self.response.out.write("no")
        self.response.out.write("\n")
        
        self.response.set_status(status)
        return status

class ReviewsCron(webapp.RequestHandler):
    def _known_ids(self):
        known = memcache.get('known_ids')

        if known is not None:
            # logging.debug("-----------> known ids cache hit")
            return known

        known_ids = [int(c.id) for c in last_changes('--all--')]

        memcache.set('known_ids', known_ids)

        return known_ids

    def _update_changes(self, changes=[], known_ids=[]):
        skipped = 0

        for c in changes:
            if c['id']['id'] in known_ids:
                skipped += 1
                continue

            change = Change(id=c['id']['id'],
                    branch=c['branch'],
                    project=c['project']['key']['name'].split("/")[1],
                    subject=c['subject'],
                    last_updated=c['lastUpdatedOn']
                    )
            change.put()

        # flush all memcache on new changes for people to see them immediately
        memcache.flush_all()

        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Skipped %d of %d changes" % (skipped, len(changes)) + "\n")

    def get(self):
        branch = qs_branch(self)
        
        if self.request.get('update_memcache'):
            return self._update_changes()

        amount = 60
        qa = self.request.get('amount')

        if qa:
            amount = int(qa)
            memcache.flush_all()

        change_proxy = proxy.ServerProxy('http://review.cyanogenmod.com/gerrit/rpc/ChangeListService')
        changes = change_proxy.allQueryNext("status:merged","z",amount)['changes']
        #changes = change_proxy.allQueryNext("status:merged branch:ics","z",amount)['changes']
        #changes = change_proxy.allQueryNext("status:merged branch:gingerbread","z",amount)['changes']
        #self.response.out.write(json.dumps(changes))

        known_ids = self._known_ids()

        received_ids = [c['id']['id'] for c in changes]

        if is_subset(received_ids, known_ids):
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("Skipped all %d changes" % len(changes) + "\n")
            return

        return self._update_changes(changes, known_ids)

class KangExtension(webapp.RequestHandler):
    def check(self, webapp):
        if use_kang_extension == True: return use_kang_extension
        webapp.response.headers['Content-Type'] = 'text/plain'
        webapp.response.out.write("KANG extension: disabled")
        webapp.response.set_status(404)
        return use_kang_extension

class NewKang(webapp.RequestHandler):
    def get(self):
        if KangExtension().check(self) == False: return
        kang = qs_kang_name(self)
        branch = qs_branch(self)
        device = qs_device(self)
        
        change = Change(id=int(time.time() * -1),
                branch = branch,
                project = 'KANG',
                subject = kang+'#dev:'+device,
                last_updated = time.strftime('%Y-%m-%d %H:%M:%S.000000000')
                )
        change.put()
        memcache.flush_all()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("KEY: '"+str(change.key().id())+"'\n")
        self.response.out.write("Added KANG: '"+kang+"'\n")


class RemoveKang(webapp.RequestHandler):
    def get(self):
        if KangExtension().check(self) == False: return
        kang = qs_kang_name(self)
        kangId = qs_kang_id(self)
        branch = qs_branch(self)
        
        q = db.GqlQuery("SELECT * FROM Change WHERE project = 'KANG' AND branch=:branch", branch=branch)
        kangs = q.fetch(500)
        
        cmd_done = 0;
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>id (click to rename)</td><td>info</td><td>branch</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for k in kangs:
            self.response.out.write('<tr><td><a href="/remove_kang/?branch='+str(k.branch)+'&kang='+kang+'&kangId='+str(k.id)+'">'+str(k.id)+'</a></td><td>Checking KANG</td><td>'+str(k.branch)+'</td><td>'+str(k.subject)+'</td><td>'+str(k.project)+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
            if (k.subject == kang) or (str(k.id) == kangId):
                db.delete(k)
                memcache.flush_all()
                self.response.out.write('<tr><td>'+str(k.id)+'</td><td>Removed KANG</td><td>'+str(k.branch)+'</td><td>'+str(k.subject)+'</td><td>'+str(k.project)+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
                cmd_done = 1;
                break
        self.response.out.write("</tbody></table>")
        
        if cmd_done == 0:
            self.response.out.write("<h2>KANG not found: "+kangId+" - '"+kang+"'</h2>\n")


class RenameKang(webapp.RequestHandler):
    def get(self):
        if KangExtension().check(self) == False: return
        branch = qs_branch(self)
        device = qs_device(self)
        kang = qs_kang_name(self)
        kangId = qs_kang_id(self)
        
        q = db.GqlQuery("SELECT * FROM Change WHERE branch = :branch AND project = 'KANG'", branch=branch)
        kangs = q.fetch(90)
        
        cmd_done = 0
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write("<h2>New KANG name '"+kang+"'</h2>\n")
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>id (click to rename)</td><td>info</td><td>branch</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for k in kangs:
            self.response.out.write('<tr><td><a href="/rename_kang/?branch='+str(k.branch)+'&kang='+kang+'--NewName&kangId='+str(k.id)+'">'+str(k.id)+'</a></td><td>Checking KANG</td><td>'+str(k.branch)+'</td><td>'+str(k.subject)+'</td><td>'+str(k.project)+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
            if (str(k.id) == kangId):
                old_name = k.subject
                k.subject = kang+"#dev:"+device
                k.put()
                memcache.flush_all()
                self.response.out.write('<tr><td><a href="">'+str(k.id)+'</a></td><td>Renamed KANG (old: '+old_name+'; new: '+kang+')</td><td>'+str(k.branch)+'</td><td>'+str(k.subject)+'</td><td>'+str(k.project)+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
                cmd_done = 1
                break
        self.response.out.write("</tbody></table>")
        
        if cmd_done == 0:
            self.response.out.write("<h2>KANG not found: "+kangId+"</h2>\n")


class ClearDB(webapp.RequestHandler):
    def get(self):
        if allow_db_clear == False:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write("This feature is disabled...\n")
            webapp.response.set_status(401)
            return
        db.delete(Change.all())
        memcache.flush_all()
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write("Database is empty...\n")

class FlushCache(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        memcache.flush_all()
        self.response.out.write("Cache flushed...\n")


class Admin(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)
        
        path = os.path.join(os.path.dirname(__file__), 'admin.html')
        self.response.out.write(template.render(path, {"for_device": device, "for_branch": branch}))


class Test(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'test.html')
        self.response.out.write(template.render(path, {}))


class RssFeed(webapp.RequestHandler):
    def merge_build(self, device, branch):
        cache_ns = device+"-"+branch
        builds = memcache.get('merge-cm-builds', cache_ns)

        if builds is not None:
            return builds
        
        build_branch  = CmBuilds().getBuilds(device, False)
        builds        = build_branch[branch]
        changes       = Ajax().filter(device, branch)
        builds_len    = len(builds) - 1
        for i, c in enumerate(changes):
            if c['project'] == 'KANG': continue
            
            c_date = datetime.strptime(c['last_updated'], "%Y-%m-%d %H:%M:%S.000000000")
            for j, b in enumerate(builds):
                if c_date >  b[3]:
                    continue
                if j < builds_len:
                    if builds[j][3] < c_date:
                        continue
                if c_date < b[3]:
                    if len(b) < 5: b.append([])
                    b[4].append((c['subject']+" ("+c['project']+")"))
        
        memcache.set('merge-cm-builds', builds, 600, namespace=cache_ns)
        return builds
        
    def get(self):
        device = qs_device(self)
        branch = qs_branch(self)
        
        path = os.path.join(os.path.dirname(__file__), 'rss.xml')
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(template.render(path, 
             {"now": datetime.now(), "device": device, "branch": branch, "builds": self.merge_build(device, branch)}))


class CmDevices(webapp.RequestHandler):
    def getAliasName(self, device, current_branch='ics'):
        if current_branch == 'ics':
            if device == 'i777': return 'galaxys2att'
        elif current_branch == 'gingerbread':
            if device == 'galaxys2att': return 'i777'
    
    def getBranch(self, device, default_branch='ics'):
        dev_branch = ''
        for br_name, br_devs in branch_device.items():
            if (br_name == default_branch or dev_branch == '') and device in br_devs:
                dev_branch = br_name
                break
        if dev_branch == '': return default_branch
        return dev_branch
    
    def getManufacturer(self, device_projects):
        for p in device_projects:
            manufacturer = re.sub(r"^android_device_([^_]+)_.*$", r'\1', p)
            if manufacturer:
                if manufacturer == "moto":
                    manufacturer = "motorola"
                return manufacturer
    
    def getDevices(self, force=False):
        cm_devices = memcache.get('cm-devices')

        if force == False and cm_devices is not None:
            return cm_devices

        cm_devices = {"dev": {}, "dev_sort": [], "man": {}, "man_sort": [], "nav_list": [], "-unknown-": {}, "-unknown-_sort": []}
        html = urlopen("http://download.cyanogenmod.com/").read()
        html = re.sub(r"[\n\r\t]", r'', html)
        html = re.sub(r"^.*?<ul.*?class.*?nav.*?>(.*)</ul>.*$", r'\1', html)
        for r in re.finditer('<li.*?id=["\']device_([^"\']+)["\'].*?>', html):
            c_dev = r.group(1)
            if c_dev == "all": continue
            
            if c_dev in device_specific:
                c_branch = self.getBranch(c_dev)
                c_manufacturer = self.getManufacturer(device_specific[c_dev])
                
                if c_manufacturer in cm_devices['man']:
                    cm_devices['man'][c_manufacturer].append(c_dev)
                else:
                    cm_devices['man'][c_manufacturer] = [c_dev]
                
                cm_devices['dev'][c_dev] = {
                    "name":         c_dev,
                    "projects":     device_specific[c_dev],
                    "manufacturer": c_manufacturer,
                    "alias":        self.getAliasName(c_dev, c_branch),
                    "branch":       c_branch
                    }
            else:
                cm_devices['-unknown-'][c_dev] = { "name": c_dev, "branch": 'ics' }
        
        # sort by key
        cm_devices['dev_sort'] = sorted(cm_devices['dev'])
        cm_devices['man_sort'] = sorted(cm_devices['man'])
        cm_devices['-unknown-_sort'] = sorted(cm_devices['-unknown-'])
        
        # build nav list
        for m in cm_devices['man_sort']:
            nl_dev = []
            for d in sorted(cm_devices['man'][m]):
                nl_dev.append(cm_devices['dev'][d])
            cm_devices['nav_list'].append({"name": m, "dev_list": nl_dev})
        nl_dev = []
        for d in cm_devices['-unknown-_sort']:
            nl_dev.append(cm_devices['-unknown-'][d])
        cm_devices['nav_list'].append({"name": 'unknown', "dev_list": nl_dev})
        
        memcache.set('cm-devices', cm_devices, 1800)
        return cm_devices
        
    def get(self):
        content_type = self.request.get('content_type')
        if content_type == '':
            content_type = 'application/json'
        
        force = self.request.get('force')
        if force == '':
            force = False
        else:
            force = True
        
        self.response.headers['Content-Type'] = content_type
        cm_devices = CmDevices().getDevices(force)
        self.response.out.write(json.dumps(cm_devices))


class CmBuilds(webapp.RequestHandler):
    def getBuilds(self, device, force=False):
        builds = memcache.get('cm-builds', device)

        if force == False and builds is not None:
            return builds

        html = urlopen("http://download.cyanogenmod.com/?device="+device).read()
        html = re.sub(r"[\n\r\t]", r'', html)
        html = re.sub(r"^.*?Browse Files.*?<tbody>(.*)</tbody>.*$", r'\1', html)
        builds = ''
        nightlies_branch = {}
        nightlies_branch['ics'] = []
        nightlies_branch['gingerbread'] = []
        nightlies_branch['-unknown-'] = []
        for r in re.finditer("<tr>(.*?device=.*?)<\/tr>", html):
            for b in re.finditer("((?:nightly)|(?:RC)|(?:stable)).*?((update-cm-(\d)|cm_ace_full)[^<>\/]+?.zip).*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", r.group(1)):
                #  1: "RC"
                #  2: "update-cm-7.2.0-RC1-ace-signed.zip"
                #  3: "update-cm-7"
                #  4: "7"
                #  5: "2012-03-14 14:19:01"
                
                if b:
                    if b.group(5):
                        naive_dt = datetime.strptime(b.group(5), "%Y-%m-%d %H:%M:%S")
                        utc_dt = naive_dt # - timedelta(hours=2)
                        if b.group(4) == '9':
                            nightlies_branch['ics'].append([b.group(2), b.group(5), b.group(1), utc_dt])
                        elif b.group(4) == '7' or b.group(3) == 'cm_ace_full':
                            nightlies_branch['gingerbread'].append([b.group(2), b.group(5), b.group(1), utc_dt])
                        else:
                            nightlies_branch['-unknown-'].append([b.group(2), b.group(5), b.group(1), utc_dt])
            builds = nightlies_branch
        
        memcache.set('cm-builds', builds, 600, namespace=device)
        return builds
        
    def get(self):
        device = qs_device(self)
        
        content_type = self.request.get('content_type')
        if content_type == '':
            content_type = 'application/json'
        
        force = self.request.get('force')
        if force == '':
            force = False
        else:
            force = True
        
        self.response.headers['Content-Type'] = content_type
        builds = CmBuilds().getBuilds(device, force)
        self.response.out.write(json.dumps(builds, default=json_datetime_handler))


class MainPage(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)
        device_config = CmDevices().getDevices()
        
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path,
            {"for_device": device, "for_branch": branch, 'devices': device_config, 'branches': branch_device}))


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

    def filter(self, device, branch):
        filter_ns = device+branch
        filtered = memcache.get('filtered', filter_ns)
        
        if filtered is not None:
            # logging.debug("-----------> filtered cache hit")
            return filtered

        filtered = []
        lc = last_changes(branch)

        common = self.common_projects()

        for c in lc:
            if c.project in common or c.project in device_specific[device] or (c.project == 'KANG' and re.search("^.*#dev:"+device+"$", c.subject)):
                filtered.append({"id": c.id, "branch": c.branch, "project": c.project,
                    "subject": c.subject, "last_updated": c.last_updated})

        memcache.set('filtered', filtered, 600, namespace=filter_ns)

        return filtered

    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)

        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(self.filter(device, branch)))


application = webapp.WSGIApplication(
                                     [('/', MainPage), ('/changelog/', Ajax),
                                         ('/pull_reviews/', ReviewsCron),
                                         ('/get_builds/', CmBuilds),
                                         ('/get_devices/', CmDevices),
                                         ('/clear_db/', ClearDB),
                                         ('/rm_duplicate/', RmDuplicate),
                                         ('/flush/', FlushCache),
                                         ('/show_db/', ShowDb),
                                         ('/changes_available/', ChangesAvailable),
                                         ('/changes_available_dev/', ChangesAvailableDevice),
                                         ('/new_kang/', NewKang),
                                         ('/remove_kang/', RemoveKang),
                                         ('/rename_kang/', RenameKang),
                                         ('/admin', Admin),
                                         ('/admin.html', Admin),
                                         ('/rss', RssFeed),
                                         ('/rss.xml', RssFeed),
                                         ('/test', Test)],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
