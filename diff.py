from config.config import (ga_tracking_id, custom_rom, use_kang_extension,
    gerrit_url, git_name, gerrit_time_offset, changelog_server,
    build_url, build_dev_list_regex, build_dev_regex, build_list_regex, build_regex,
    allow_db_clear, branch_device, device_title, device_specific, qs_branch, qs_device,
    qs_kang_name, qs_kang_id, keywords, branches, types,
    query_max, cache_device_timeout, cache_build_timeout, cache_rss_merge_timeout,
    Project, Change, User)

import logging
import os
import time
import re
import sys

from datetime import datetime, timedelta
from operator import itemgetter
from urllib import urlopen
from lovely.jsonrpc import proxy
from django.utils import simplejson as json

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.runtime import DeadlineExceededError
from google.appengine.api.urlfetch_errors import DownloadError


def memcache_set(key, value, timeout=0, namespace=None):
    if namespace:
        key_ns_list = key+':nsl'
        ns_list = memcache.get(key_ns_list)
        if ns_list:
            ns_list.append(namespace)
        else:
            ns_list = [namespace]
        memcache.set(key_ns_list, ns_list)
    memcache.set(key, value, timeout, namespace=namespace)


def memcache_delete_multi(keys, timeout=0):
    for key in keys:
        key_ns_list = key+':nsl'
        ns_list = memcache.get(key_ns_list)
        
        if ns_list:
            for ns in ns_list:
                logging.debug("###> cache: deleting key '%s' in namespace '%s'" % (key, ns))
                memcache.delete(key, timeout, namespace=ns)
                
            logging.debug("###> cache: deleting namespace list '%s'" % key_ns_list)
            memcache.delete(key_ns_list, timeout)
            
        logging.debug("###> cache: deleting key '%s'" % key)
        memcache.delete(key, timeout)


def get_tzd():
	tzd = memcache.get('tzd')
	if tzd is not None:
		# logging.debug("-----------> time zone cache hit")
		return tzd
	
	tzd = {}
	tz_str = '''-12 Y
		-11 X NUT SST
		-10 W CKT HAST HST TAHT TKT
		-9 V AKST GAMT GIT HADT HNY
		-8 U AKDT CIST HAY HNP PST PT
		-7 T HAP HNR MST PDT
		-6 S CST EAST GALT HAR HNC MDT
		-5 R CDT COT EASST ECT EST ET HAC HNE PET
		-4 Q AST BOT CLT COST EDT FKT GYT HAE HNA PYT
		-3 P ADT ART BRT CLST FKST GFT HAA PMST PYST SRT UYT WGT
		-2 O BRST FNT PMDT UYST WGST
		-1 N AZOT CVT EGT
		0 Z EGST GMT UTC WET WT
		1 A CET DFT WAT WEDT WEST
		2 B CAT CEDT CEST EET SAST WAST
		3 C EAT EEDT EEST IDT MSK
		4 D AMT AZT GET GST KUYT MSD MUT RET SAMT SCT
		5 E AMST AQTT AZST HMT MAWT MVT PKT TFT TJT TMT UZT YEKT
		6 F ALMT BIOT BTT IOT KGT NOVT OMST YEKST
		7 G CXT DAVT HOVT ICT KRAT NOVST OMSST THA WIB
		8 H ACT AWST BDT BNT CAST HKT IRKT KRAST MYT PHT SGT ULAT WITA WST
		9 I AWDT IRKST JST KST PWT TLT WDT WIT YAKT
		10 K AEST ChST PGT VLAT YAKST YAPT
		11 L AEDT LHDT MAGT NCT PONT SBT VLAST VUT
		12 M ANAST ANAT FJT GILT MAGST MHT NZST PETST PETT TVT WFT
		13 FJST NZDT
		11.5 NFT
		10.5 ACDT LHST
		9.5 ACST
		6.5 CCT MMT
		5.75 NPT
		5.5 SLT
		4.5 AFT IRDT
		3.5 IRST
		-2.5 HAT NDT
		-3.5 HNT NST NT
		-4.5 HLV VET
		-9.5 MART MIT'''
	
	for tz_descr in map(str.split, tz_str.split('\n')):
		tz_offset = int(float(tz_descr[0]))
		for tz_code in tz_descr[1:]:
			tzd[tz_code] = tz_offset
	
	memcache.set('tzd', tzd)
	return tzd


def parse_timestamp(timestamp):
	if not timestamp: return
	m = re.search("^(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2})(?:\.\d+)?\s*([A-Z]+)?$", timestamp)
	if m:
		tzd = get_tzd()
		dt = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S")
		if m.lastindex >=2 and tzd[m.group(2)]:
			dt = dt - timedelta(hours=tzd[m.group(2)])
	else:
		dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
	return dt


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


def is_not_device_specific(subject):
    dev_list = CustomRomDevices().getDevices()['dev_sort']
    for dev in dev_list:
      if re.search(r'\b%s\b' % dev, subject, re.IGNORECASE):
        return False
    
    return True


def project_type(project):
    dev_p = CustomRomDevices().getDevices()['projects']
    if (
          project in dev_p
          or 'android_device_' in project
          or 'vendor_' in project
          or 'device_' in project
          or 'android_hardware_' in project
          or 'android_kernel_' in project
          or '-kernel-' in project
        ):
        return 'device'
    else:
        return 'common'


def merge_list(a, b):
    a.append('')
    a[-1:] = b
    return a


class Projects():
    def _get_mem(self, branch, type):
        cache_ns = type+"-"+branch
        return memcache.get('project', cache_ns)
    
    def _set_mem(self, p_list, branch, type):
        cache_ns = type+"-"+branch
        memcache_set('project', p_list, namespace=cache_ns)
        return p_list
    
    def append(self, new):
        p_list = self._get_mem(new.branch, new.type)
        if p_list is None:
            logging.debug("###> MemCache: No projects")
            return
        
        p_list = merge_list ([new], p_list)
        return self._set_mem(p_list, new.branch, new.type)
    
    def list(self, branch, type):
        p_list = []
        for p in self.get(branch, type):
            p_list.append(p.project)
        return p_list
    
    def get(self, branch, type, force=False):
        p_list = self._get_mem(branch, type)
        if not force and p_list is not None:
            logging.debug("---> DS: Projects cache hit")
            return p_list
        
        logging.debug("###> DS: Read project: branch '%s', type '%s'" % (branch, type))
        if type == '--all--':
            p_list = Project.gql("WHERE branch = :1 ORDER BY type, project", branch)
        else:
            p_list = Project.gql("WHERE branch = :1 AND type = :2 ORDER BY project", branch, type)
        
        return self._set_mem(p_list, branch, type)


class LastChanges():
    def _get_mem(self, branch):
        return memcache.get('last_changes', branch)
    
    def _set_mem(self, lc_list, branch):
        memcache_set('last_changes', lc_list, namespace=branch)
        return lc_list
    
    def append(self, new):
        lc_list = self._get_mem(new.branch)
        if lc_list is None:
            logging.debug("###> MemCache: No last changes")
            return
        
        lc_list = merge_list([new], lc_list)
        return self._set_mem(lc_list, new.branch)
    
    def sort(self, branch):
        lc_list = self._get_mem(branch)
        if lc_list is None: return
        
        lc_list = sorted(lc_list, key=lambda e: e.last_updated, reverse=True)
        return self._set_mem(lc_list, branch)
    
    def get(self, branch):
        if branch == 'None' or branch == '' or branch is None:
            branch = 'gingerbread'
        lc_list = self._get_mem(branch)
    
        if lc_list is not None:
            logging.debug("---> DS: Last changes cache hit")
            return lc_list
            
        logging.debug("###> DS: read last changes")
        query_limit = query_max + 20
        if branch == '--all--':
            lc_list = Change.gql("ORDER BY last_updated DESC LIMIT %s" % query_limit)
        else:
            lc_list = Change.gql("WHERE branch IN (:branch, 'master') ORDER BY last_updated DESC LIMIT %s" % query_limit, branch=branch)
        
        return self._set_mem(lc_list, branch)


def device_projects():
    projects = memcache.get('device-projects')

    if projects is not None:
        logging.debug("---> DS: Device project cache hit")
        return projects
    
    logging.debug("###> DS: read device projects")
    all_projects = Project.gql("WHERE type = 'device'")
    
    projects = []
    for p in all_projects:
        if not re.search(r'^(android_)?device_', p.project): continue
        projects.append(p.project)
    
    memcache.set('device-projects', projects)
    return projects


class ShowDb(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        
        logging.debug("######> DS: read for DB dump")
        if self.request.get('filter') and self.request.get('filter') == "1":
             q = Change.gql("WHERE branch = :branch ORDER BY last_updated DESC", branch=branch)
        else:
             q = db.GqlQuery("SELECT * FROM Change ORDER BY last_updated DESC, id")
        ch = q.fetch(2000)
        
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>branch</td><td>id</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for r in ch:
            #r.subject = time.strftime('%Y-%m-%d %H:%M')+' - '
            self.response.out.write("<tr><td>"+r.branch+"</td>\n")
            self.response.out.write("<td>"+str(r.id)+"</td>\n")
            self.response.out.write("<td>"+r.subject+"</td>\n")
            self.response.out.write("<td>"+r.project+"</td>\n")
            self.response.out.write("<td>"+str(r.last_updated)+"</td></tr>\n")
        self.response.out.write("</tbody></table>")
        
        return


class ShowProjects(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        type = '--all--'
        
        qs_type = self.request.get('type')
        if qs_type:
            type = qs_type
        
        if self.request.get('flush'):
            memcache_delete_multi(['project']);
        
        p_list = Projects().get(branch, type)
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        for p in p_list:
            self.response.out.write("%s; %s; %s\n" %(p.branch, p.type, p.project))
        
        return


class ShowCommonProjects(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        
        p_list = Projects().get(branch, 'common', True)
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        for p in p_list:
            self.response.out.write("%s; %s; %s\n" %(p.branch, p.type, p.project))
        
        return


class LoadProjects(webapp.RequestHandler):
    def get(self):
        logging.debug("#######> DS: Maint: LoadProjects")
        ch = Change.all()
        
        seen = {}
        db.delete(Project.all())
        dev_p = CustomRomDevices().getDevices()['projects']
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        for c in ch:
            if c.project == 'KANG': continue
            if c.project in seen: continue
            
            p_type = project_type(c.project)
            self.response.out.write(c.project+"\n")
            seen[c.project] = 1
            project = Project(
                        branch=c.branch,
                        type=p_type,
                        project=c.project
                    )
            project.put()
        
        #memcache.flush_all()
        memcache_delete_multi(['filtered', 'merge-builds', 'device-projects'])
        return


class RmDuplicate(webapp.RequestHandler):
    def get(self):
        device = qs_device(self)
        
        logging.debug("#######> DS: Maint: RmDuplicate")
        ch = Change.gql("ORDER BY id")
        
        seen = []
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>action</td><td>remote</td><td>branch</td><td>id</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        timeout = True
        
        while timeout:
            try:
                for r in ch:
                    action = 'keep'
                    if r.id in seen:
                        action = 'remove'
                        r.delete()
                    
                    if r.remote is None:
                        r.remote = git_name
                    
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
                    self.response.out.write("<td>"+r.remote+"</td>\n")
                    self.response.out.write("<td>"+r.branch+"</td>\n")
                    self.response.out.write("<td>"+str(r.id)+"</td>\n")
                    self.response.out.write("<td>"+r.subject+"</td>\n")
                    self.response.out.write("<td>"+r.project+"</td>\n")
                    self.response.out.write("<td>"+str(r.last_updated)+"</td></tr>\n")
                    timeout = False
            
            except DeadlineExceededError:
                timeout = True
        
        self.response.out.write("</tbody></table>")
        memcache.flush_all()
        return


class ChangesAvailableDevice(webapp.RequestHandler):
    def get(self):
        kang = qs_kang_name(self)
        branch = qs_branch(self)
        device = qs_device(self)
        lc = Ajax().filter(device, branch)
        
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
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
        lc = LastChanges().get(branch)
        
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        status = 200
        for c in lc:
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
            logging.debug("---> DS: Known IDs cache hit")
            return known

        logging.debug("###> DS: read id list")
        known_ids = [int(c.id) for c in LastChanges().get('--all--')]
        memcache.set('known_ids', known_ids)

        return known_ids

    def _update_changes(self, changes=[], known_ids=[]):
        skipped = 0
        updates = False
        branches = {}
        cl_projects = Projects()
        cl_last_chg = LastChanges()
        
        for c in changes:
            if c['id']['id'] in known_ids:
                skipped += 1
                continue

            updates = True
            change = Change(id=c['id']['id'],
                    branch=c['branch'],
                    project=c['project']['key']['name'].split("/")[1],
                    subject=c['subject'],
                    last_updated=c['lastUpdatedOn']
                    )
            change.put()
            
            # append change to memcache (last changes)
            known_ids.append(change.id)
            memcache.set('known_ids', known_ids)
            cl_last_chg.append(change)
            branches[change.branch] = 1
            
            # append new project
            p_type = project_type(change.project)
            if not change.project in cl_projects.list(change.branch, p_type):
                project = Project(
                                branch  = change.branch,
                                type    = p_type,
                                project = change.project
                            )
                project.put()
                cl_projects.append(project)
        
        if updates:
            for b in branches:
                cl_last_chg.sort(b)
            
            logging.debug("###> MemCache: Flush after new changes")
            # flush all memcache on new changes for people to see them immediately
            memcache_delete_multi(['filtered', 'merge-builds', 'device-projects'])
            #memcache_delete_multi(['known_ids', 'last_changes', 'filtered', 'merge-builds', 'project', 'project-list'])
            #memcache.flush_all()

        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.response.out.write("Skipped %d of %d changes" % (skipped, len(changes)) + "\n")

    def get(self):
        branch = qs_branch(self)
        
        if self.request.get('update_memcache'):
            return self._update_changes()

        amount = 60
        qa = self.request.get('amount')
        if qa:
            amount = int(qa)
            if amount > query_max: amount = query_max

        change_proxy = proxy.ServerProxy(gerrit_url+'gerrit/rpc/ChangeListService')
        retry_fetch = 10
        while retry_fetch > 0:
            try:
                changes = change_proxy.allQueryNext("status:merged","z",amount)['changes']
                #changes = change_proxy.allQueryNext("status:merged branch:ics","z",amount)['changes']
                #self.response.out.write(json.dumps(changes))
                retry_fetch = 0
            except DownloadError:
                retry_fetch -= 1
                
            except:
                self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
                self.response.out.write("ERROR: cannot fetch changes, error occurred\n")
                self.response.out.write(sys.exc_info())
                return

        known_ids = self._known_ids()
        received_ids = [c['id']['id'] for c in changes]

        if is_subset(received_ids, known_ids):
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            self.response.out.write("Skipped all %d changes" % len(changes) + "\n")
            return

        return self._update_changes(changes, known_ids)


class KangExtension(webapp.RequestHandler):
    def check(self, webapp):
        if use_kang_extension == True: return use_kang_extension
        webapp.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
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
                last_updated = time.strftime('%Y-%m-%d %H:%M:%S.000000000', time.gmtime(time.time()))
                )
        change.put()
        memcache_delete_multi(['last_changes', 'filtered'])
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.response.out.write("KEY: '"+str(change.key().id())+"'\n")
        self.response.out.write("Added KANG: '"+kang+"'\n")


class RemoveKang(webapp.RequestHandler):
    def get(self):
        if KangExtension().check(self) == False: return
        kang = qs_kang_name(self)
        kangId = qs_kang_id(self)
        branch = qs_branch(self)
        
        kangs = Change.gql("WHERE project = 'KANG' AND branch=:branch", branch=branch)
        
        cmd_done = 0;
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>id (click to rename)</td><td>info</td><td>branch</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for k in kangs:
            self.response.out.write('<tr><td><a href="/remove_kang-off/?branch='+k.branch+'&kang='+kang+'&kangId='+str(k.id)+'">'+str(k.id)+'</a></td><td>Checking KANG</td><td>'+k.branch+'</td><td>'+k.subject+'</td><td>'+k.project+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
            if (k.subject == kang) or (str(k.id) == kangId):
                db.delete(k)
                memcache_delete_multi(['last_changes', 'filtered'])
                self.response.out.write('<tr><td>'+str(k.id)+'</td><td>Removed KANG</td><td>'+k.branch+'</td><td>'+k.subject+'</td><td>'+k.project+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
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
        
        kangs = Change.gql("WHERE branch = :branch AND project = 'KANG'", branch=branch)
        
        cmd_done = 0
        self.response.headers['Content-Type'] = 'text/html; charset=UTF-8'
        self.response.out.write("<h2>New KANG name '"+kang+"'</h2>\n")
        self.response.out.write("<table>")
        self.response.out.write("<thead><tr><td>id (click to rename)</td><td>info</td><td>branch</td><td>subject</td><td>project</td><td>last_updated</td></tr></thead><tbody>")
        for k in kangs:
            self.response.out.write('<tr><td><a href="/rename_kang-off/?branch='+k.branch+'&kang='+kang+'--NewName&kangId='+str(k.id)+'">'+str(k.id)+'</a></td><td>Checking KANG</td><td>'+k.branch+'</td><td>'+k.subject+'</td><td>'+k.project+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
            if (str(k.id) == kangId):
                old_name = k.subject
                k.subject = kang+"#dev:"+device
                k.put()
                memcache_delete_multi(['last_changes', 'filtered'])
                self.response.out.write('<tr><td><a href="">'+str(k.id)+'</a></td><td>Renamed KANG (old: '+old_name+'; new: '+kang+')</td><td>'+k.branch+'</td><td>'+k.subject+'</td><td>'+k.project+'</td><td>'+str(k.last_updated)+'</td></tr>\n')
                cmd_done = 1
                break
        self.response.out.write("</tbody></table>")
        
        if cmd_done == 0:
            self.response.out.write("<h2>KANG not found: "+kangId+"</h2>\n")


class ClearDB(webapp.RequestHandler):
    def get(self):
        if allow_db_clear == False:
            self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            self.response.out.write("This feature is disabled...\n")
            self.response.set_status(401)
            return
        db.delete(Project.all())
        db.delete(Change.all())
        memcache.flush_all()
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        self.response.out.write("Database is empty...\n")


class FlushCache(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        logging.debug("######> MemCache: Flushed by user request")
        memcache.flush_all()
        self.response.out.write("Cache flushed...\n")


class FlushTest(webapp.RequestHandler):
    def get(self):
        branch = qs_branch(self)
        delete = qa = self.request.get('delete')
        cache_ns = "flush-test-"+branch
        
        self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
        if delete:
            self.response.out.write("Flush cached values (start: '%s')\n" % cache_ns)
            memcache_delete_multi(['flush-test-ics', 'flush-test-gingerbread', cache_ns])
        
        f_test = memcache.get(cache_ns, branch)
        
        if f_test is not None:
            self.response.out.write("Using cached list '%s'...\n" % cache_ns)
            for t in f_test:
                self.response.out.write("Cached: %s\n" % t)
        else:
            self.response.out.write("Cache '%s' is empty...\n" % cache_ns)
            f_test = ['one', 'two']
            
        memcache_set(cache_ns, f_test, namespace=branch)


class Admin(webapp.RequestHandler):
    def get(self):
        try:
            # Get the db.User that represents the user on whose behalf the
            # consumer is making this request.
            user = users.get_current_user()
        except e:
            # The request was not a valid OAuth request.
            # ...
            #self.response.headers['Content-Type'] = 'text/plain; charset=UTF-8'
            #self.response.out.write('Auth error: The request was not a valid OAuth request.')
            user = None
        
        is_admin = False
        if user:
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
            is_admin = users.is_current_user_admin()
        else:
            greeting = ("<a href=\"%s\">Sign in or register</a>" %
                        users.create_login_url("/admin"))
        
        branch = qs_branch(self)
        device = qs_device(self)

        path = os.path.join(os.path.dirname(__file__), 'admin.html')
        self.response.out.write(template.render(path, {"device": device, "branch": branch,
                                "greeting": greeting, "user": user, "is_admin": is_admin,
                                "custom_rom": custom_rom, "gerrit_url": gerrit_url}))


class Test(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'test.html')
        self.response.out.write(template.render(path, {}))


class RssFeed(webapp.RequestHandler):
    def merge_build(self, device, branch):
        cache_ns = device+"-"+branch
        builds = memcache.get('merge-builds', cache_ns)

        if builds is not None:
            logging.debug("------> RSS Feed: Merge")
            return builds
        
        logging.debug("######> RSS Feed: Merge")
        build_branch  = CustomRomBuilds().getBuilds(device, False)
        if branch not in build_branch: return
        
        builds = build_branch[branch]
        if len(builds) == 0: return
        
        changes       = Ajax().filter(device, branch)
        build_stack   = sorted(builds, key=itemgetter(3), reverse=False)
        c_build       = build_stack.pop()
        n_build       = None
        if len(build_stack) > 0: n_build = build_stack.pop()
        
        for c in changes:
            if c['project'] == 'KANG': continue
            
            c_date = c['last_updated_offset']
            if c_date < c_build[3]:
                build_no = None
                if custom_rom == 'aokp': build_no = re.search (r"build.*?(\d+)", c['subject'])
                
                if n_build is not None:
                    while c_date < n_build[3] or (custom_rom == 'aokp' and build_no and ('-'+build_no.group(1)+'.zip') in c['subject']):
                        c_build = n_build
                        if len(build_stack) > 0:
                            n_build = build_stack.pop()
                        else:
                            n_build = None
                            break
                
                if len(c_build) < 5: c_build.append([])
                c_build[4].append((c['subject']+" ("+c['project']+")"))
        
        memcache_set('merge-builds', builds, cache_rss_merge_timeout, namespace=cache_ns)
        return builds
    
    def get(self, device=None, branch=None):
        if device is None: device = qs_device(self)
        if branch is None: branch = qs_branch(self)
        
        path = os.path.join(os.path.dirname(__file__), 'rss.xml')
        self.response.headers['Content-Type'] = 'application/rss+xml'
        self.response.out.write(template.render(path, 
             {"url": self.request.host, "custom_rom": custom_rom, "now": datetime.now(), 
              "device": device, "branch": branch, "builds": self.merge_build(device, branch)}))


class CustomRomDevices(webapp.RequestHandler):
    def getAliasName(self, device, current_branch='ics'):
        if current_branch == 'ics':
            if device == 'i777': return 'galaxys2att'
        elif current_branch == 'gingerbread':
            if device == 'galaxys2att': return 'i777'
        if device == 'a500': return 'picasso'
        if device == 'harmony': return 'smb_a1002'
        if device == 'vzwtab': return 'galaxytab7c'
    
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
            manufacturer = re.sub(r"^(?:android_)?device_([^_]+)_.*$", r'\1', p)
            if manufacturer:
                if manufacturer == "moto":
                    manufacturer = "motorola"
                return manufacturer
    
    def guessManufacturer(self, device):
        all_p = device_projects()
        
        for p in all_p:
            m = re.search(("_([^_]+)_"+device+"$"), p)
            if m:
                return m.group(1)
        return
        
    def getDevices(self, force=False):
        cr_devices = memcache.get('cr-devices')

        if force == False and cr_devices is not None:
            return cr_devices

        dev_list = [];
        cache_cr_dev_timeout = cache_device_timeout
        try:
            html = urlopen(build_url).read()
            html = re.sub(r"[\n\r\t]", r'', html)
            html = re.sub(build_dev_list_regex, r'\1', html)
            for r in re.finditer(build_dev_regex, html):
                dev_list.append(r.group(1))
        except:
            dev_list = device_specific.keys()
            cache_cr_dev_timeout = 10
        
        cr_devices = {"projects": {}, "dev": {}, "dev_sort": [], "man": {}, "man_sort": [], "nav_list": [], "-unknown-": {}, "-unknown-_sort": []}
        for c_dev in dev_list:
            if c_dev == "all": continue
            
            if c_dev in device_specific:
                c_branch = self.getBranch(c_dev)
                c_manufacturer = self.getManufacturer(device_specific[c_dev])
                
                if c_manufacturer in cr_devices['man']:
                    cr_devices['man'][c_manufacturer].append(c_dev)
                else:
                    cr_devices['man'][c_manufacturer] = [c_dev]
                
                c_title = ''
                if c_dev in device_title: c_title = device_title[c_dev]
                cr_devices['dev'][c_dev] = {
                    "name":         c_dev,
                    "title":        c_title,
                    "projects":     ["android_device_"+c_manufacturer+"_"+c_dev, "device_"+c_manufacturer+"_"+c_dev] + device_specific[c_dev],
                    "manufacturer": c_manufacturer,
                    "alias":        self.getAliasName(c_dev, c_branch),
                    "branch":       c_branch
                    }
                for p in cr_devices['dev'][c_dev]['projects']: cr_devices['projects'][p] = 1
            else:
                guess_manufacturer = self.guessManufacturer(c_dev)
                if guess_manufacturer:
                    c_manufacturer = guess_manufacturer
                    if c_manufacturer in cr_devices['man']:
                        cr_devices['man'][c_manufacturer].append(c_dev)
                    else:
                        cr_devices['man'][c_manufacturer] = [c_dev]
                    
                    cr_devices['dev'][c_dev] = {
                        "name":         c_dev,
                        "title":        '',
                        "projects":     ["android_device_"+c_manufacturer+"_"+c_dev, "device_"+c_manufacturer+"_"+c_dev],
                        "manufacturer": c_manufacturer,
                        "alias":        '',
                        "branch":       'ics'
                        }
                    for p in cr_devices['dev'][c_dev]['projects']: cr_devices['projects'][p] = 1
                else:
                    cr_devices['-unknown-'][c_dev] = { "name": c_dev, "branch": 'ics' }
        
        # sort by key
        cr_devices['dev_sort'] = sorted(cr_devices['dev'])
        cr_devices['man_sort'] = sorted(cr_devices['man'])
        cr_devices['-unknown-_sort'] = sorted(cr_devices['-unknown-'])
        
        # build nav list
        for m in cr_devices['man_sort']:
            nl_dev = []
            for d in sorted(cr_devices['man'][m]):
                nl_dev.append(cr_devices['dev'][d])
            cr_devices['nav_list'].append({"name": m, "dev_list": nl_dev})
        nl_dev = []
        for d in cr_devices['-unknown-_sort']:
            nl_dev.append(cr_devices['-unknown-'][d])
        if nl_dev: cr_devices['nav_list'].append({"name": 'unknown', "dev_list": nl_dev})
        
        memcache.set('cr-devices', cr_devices, cache_cr_dev_timeout)
        return cr_devices
        
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
        cr_devices = CustomRomDevices().getDevices(force)
        self.response.out.write(json.dumps(cr_devices))


class CustomRomBuilds(webapp.RequestHandler):
    def getBuilds(self, device, force=False):
        builds = memcache.get('cr-builds', device)

        if force == False and builds is not None:
            return builds

        try:
            html = urlopen(build_url+device).read()
            html = re.sub(r"[\n\r\t]", r'', html)
            html = re.sub(build_list_regex, r'\1', html)
        except:
            return
        
        nightlies_branch = {}
        for branch in branches:
            nightlies_branch[branch] = []
        nightlies_branch['-unknown-'] = []
        type_filter = '((?:'+ (')|(?:'.join(types)) +'))'
        for r in re.finditer(build_regex, html):
            if custom_rom == 'cm':
                for b in re.finditer(type_filter+".*?((update-cm-(\d)|cm_ace_full)[^<>\/]+?.zip).*?(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(\s[A-Z]+)?)", r.group(1)):
                    #  1: "RC"
                    #  2: "update-cm-7.2.0-RC1-ace-signed.zip"
                    #  3: "update-cm-7"
                    #  4: "7"
                    #  5: "2012-03-14 14:19:01"
                    
                    if b:
                        if b.group(5):
                            utc_dt = parse_timestamp(b.group(5))
                            if b.group(4) == '9':
                                nightlies_branch['ics'].append([b.group(2), b.group(5), b.group(1), utc_dt])
                            elif b.group(4) == '7' or b.group(3) == 'cm_ace_full':
                                nightlies_branch['gingerbread'].append([b.group(2), b.group(5), b.group(1), utc_dt])
                            else:
                                nightlies_branch['-unknown-'].append([b.group(2), b.group(5), b.group(1), utc_dt])
                                
            elif custom_rom == 'aokp':
                for b in re.finditer("download-box.*?(aokp_[^<>\/]+?_"+ type_filter +"-(\d+).zip).*?(\d{4}-\d{1,2}-\d{1,2} \d{1,2}:\d{1,2}:\d{1,2}(?:\s[A-Z]+)?)", r.group(1)):
                    if b:
                        if b.group(4):
                            utc_dt =  parse_timestamp(b.group(4))
                            nightlies_branch['ics'].append([b.group(1), b.group(4), b.group(2), utc_dt])
            
        if custom_rom == 'aokp':
            for branch in nightlies_branch:
                nightlies_branch[branch] = sorted(nightlies_branch[branch], key=itemgetter(3), reverse=True)
        
        for branch in nightlies_branch:
            # clear cached merge for RSS feed
            cache_ns = device+"-"+branch
            memcache.delete('merge-builds', namespace=cache_ns)
        
        memcache_set('cr-builds', nightlies_branch, cache_build_timeout, namespace=device)
        return nightlies_branch
        
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
        builds = CustomRomBuilds().getBuilds(device, force)
        self.response.out.write(json.dumps(builds, default=json_datetime_handler))


class MainPage(webapp.RequestHandler):
    def get(self, device=None, branch=None):
        if device is None: device = qs_device(self)
        if branch is None: branch = qs_branch(self)
        
        device_config = CustomRomDevices().getDevices()
        manufacturer = ''
        dev_title = ''
        if device in device_config['dev']: 
            manufacturer = device_config['dev'][device]['manufacturer']
            dev_title    = device_config['dev'][device]['title']
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path,
            {"ga_tracking_id": ga_tracking_id, "custom_rom": custom_rom, "build_url": build_url, "gerrit_url": gerrit_url, "types": types,
             "url": self.request.host, "branch": branch, "device": device, "dev_title": dev_title, "manufacturer": manufacturer, "keywords": keywords,
             'devices': device_config, 'branches': branches, "changelog_server": changelog_server}))


class Ajax(webapp.RequestHandler):
    def filter(self, device, branch):
        filter_ns = device+'-'+branch
        filtered = memcache.get('filtered', filter_ns)
        
        if filtered is not None:
            logging.debug("------> DS: Filtered cache hit")
            return filtered

        logging.debug("######> DS: Build list of filtered changes for '%s'" % filter_ns)
        filtered = []
        common = Projects().list(branch, 'common')

        lc = LastChanges().get(branch)
        for c in lc:
            if (
                    c.project in common
                    or (re.search ("vendor_", c.project) and re.search(r'\b%s\b' % device, c.subject, re.IGNORECASE))
                    or (c.project == "vendor_aokp" and is_not_device_specific(c.subject))
                    or (device in device_specific.keys() and c.project in device_specific[device])
                    or (c.project == 'KANG' and re.search("^.*#dev:"+ device +"$", c.subject))
                ):
                c_time = parse_timestamp(c.last_updated)
                c_time_offset = c_time + timedelta(hours=gerrit_time_offset)
                filtered.append({"id": c.id, "branch": c.branch, "project": c.project,
                    "subject": c.subject, "last_updated_offset": c_time_offset, 
                    "last_updated": c.last_updated, "last_updated_utc": c_time})
        
        memcache_set('filtered', filtered, namespace=filter_ns)
        return filtered
    
    def get(self):
        branch = qs_branch(self)
        device = qs_device(self)
        
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(self.filter(device, branch), default=json_datetime_handler))


application = webapp.WSGIApplication([('/', MainPage),
                                         ('/changelog/', Ajax),
                                         ('/pull_reviews/', ReviewsCron),
                                         ('/get_builds/', CustomRomBuilds),
                                         ('/get_devices/', CustomRomDevices),
                                         ('/clear_db/', ClearDB),
                                         ('/load_project/', LoadProjects),
                                         ('/rm_duplicate/', RmDuplicate),
                                         ('/flush/', FlushCache),
                                         ('/flush-test/', FlushTest),
                                         ('/show_db/', ShowDb),
                                         ('/show_projects/', ShowProjects),
                                         ('/show_common_projects/', ShowCommonProjects),
                                         ('/changes_available/', ChangesAvailable),
                                         ('/changes_available_dev/', ChangesAvailableDevice),
                                         ('/new_kang/', NewKang),
                                         ('/remove_kang/', RemoveKang),
                                         ('/remove_kang-off/', Admin),
                                         ('/rename_kang/', RenameKang),
                                         ('/rename_kang-off/', Admin),
                                         ('/admin', Admin),
                                         ('/admin.html', Admin),
                                         ('/test', Test),
                                         ('/rss', RssFeed),
                                         ('/rss.xml', RssFeed),
                                         ('/rss/([^/#\?]+)(?:/([^/#\?]*))?', RssFeed),
                                         ('/([^/#\?]+)(?:/([^/#\?]*))?(?:mobiquo/mobiquo.php)?', MainPage),
                                         ],
                                     debug=True)


def main():
    run_wsgi_app(application)


if __name__ == "__main__":
    main()
