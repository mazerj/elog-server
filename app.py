# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os, types, string
import re, textwrap, datetime
import distutils.spawn

from flask import *
from functools import wraps

import matplotlib as mpl
mpl.use('Agg')						  # prevent Tk loading..
import matplotlib.pyplot as plt
import mpld3
import numpy as np

# run elog with -dir option to find install dir
try:
    elogpath = os.popen('elog -dir 2>/dev/null').read()[:-1]
except:
    elogpath = ''
    
if elogpath is None:
	sys.stderr.write("Can't find elog executable/path\n")
	sys.exit(1)
else:
    elogpath = elogpath + '/lib/elog'
	sys.path.append(elogpath)
	from elogapi import getdb, GetExper, GetNextExper
	sys.stderr.write("loaded elogapi from %s\n" % elogpath)

from app_tools import *

LOGGING = True
HOST    = '0.0.0.0'
PORT    = 5000

try:
	import pam
except ImportError:
    pam = None
	try:
		USERS = {}
		USERS_RW = {}
		for l in open('userdata', 'r').readlines():
			l = l[:-1].split(':')
			if len(l) == 3:
				USERS[l[0]] = l[1]
				USERS_RW[l[0]] = (l[2].lower() == 'rw')
	except:
		sys.stderr.write("Bad or missing 'userdata' file.\n")
		sys.exit(1)

def writeaccess():
	if pam:
        if session['username'] == 'elogger':
            # 'elogger' user is special -- read only access..
            return False
        else:
            return True
	else:
		try:
			return USERS_RW[session['username']]
		except KeyError:
			# if you're not in the userdata file, you get readonly access
			return False

def baseenv(**env):
	env['RW'] = writeaccess()
	return env

def getanimals():
	db = getdb()
	rows = db.query("""SELECT animal FROM animal WHERE 1 ORDER BY animal""")
	return [row['animal'] for row in rows]

def safenote(s):
	# convert note to markdown format link
	return s
	#return re.sub('<elog:(.*)=(.*)>', '[elog:\\1=\\2](DO NOT CHANGE)', s)

def unsafenote(s):
	# markdown format 'speical' link back to elog link
	return s.replace('\r\n', '\n').replace("'", "\\'")
	#return re.sub('\[elog:(.*)=(.*)\]\(DO NOT CHANGE\)', '<elog:\\1=\\2>', s)

def expandattachment(id):
	env = baseenv()
	db = getdb()
	rows = db.query("""SELECT * FROM attachment WHERE"""
					""" attachmentID=%s""" % (id,))
	if len(rows) > 0:
		rows[0]['date'] = '%s' % rows[0]['date']
		env.update(rows[0])

		for k in env.keys():
			if type(env[k]) is types.StringType and len(env[k]) == 0:
				env[k] = ''

		env['note'] = expandnote(env['note'])
		return render_template("attachment.html", **env)
	else:
		return red("[WARNING: bad attachment link to #%s]\n" % id)

def expandexper(exper):
	env = baseenv()
	db = getdb()
	row = db.query("""SELECT * FROM exper WHERE exper='%s'""" % (exper,))[0]
	row['date'] = '%s' % row['date']
	env.update(row)

	for k in env.keys():
		if type(env[k]) is types.StringType and len(env[k]) == 0:
			env[k] = ''

	env['note'] = expandnote(env['note'])

	rows = db.query("""SELECT * FROM unit WHERE """\
					"""exper='%s'""" % (env['exper'],))
	env['units'] = rows
	if rows:
		for u in env['units']:
			u['note'] = expandnote(u['note'])

	rows = db.query("""SELECT * FROM dfile WHERE """\
					"""exper='%s'""" % (env['exper'],))
	env['dfiles'] = rows
	if rows:
		for d in env['dfiles']:
			d['note'] = expandnote(d['note'])
			d['dfileID'] = '%s' % d['dfileID']
		for k in d.keys():
			if type(d[k]) is types.StringType and len(d[k]) == 0:
				d[k] = ''


	return render_template("exper.html", **env)

def expandsession(animal, date):
	env = baseenv(ANIMAL=animal)
	db = getdb()
	# should be exactly one row:
	row = db.query("""SELECT * FROM session WHERE """
				   """ animal='%s' and date='%s'""" % (animal, date))[0]
	row['date'] = '%s' % row['date']
	env.update(row)
	for k in env.keys():
		if type(env[k]) is types.StringType and len(env[k]) == 0:
			env[k] = ''

	env['restricted'] = check(env['restricted'])
	env['tested'] = check(env['tested'])

	env['dtb'] = safeint(env['dtb'])
	env['dtb_ml'] = safeint(env['dtb_ml'])
	env['xdtb'] = safeint(env['xdtb'])
	env['xdtb_ml'] = safeint(env['xdtb_ml'])

	env['health_stool'] = check(env['health_stool'])
	env['health_skin'] = check(env['health_skin'])
	env['health_urine'] = check(env['health_urine'])
	env['health_pcv'] = check(env['health_pcv'])

	env['totalfluid'] = safeint(env['water_work']) + \
	  safeint(env['water_sup']) + safeint(env['fruit_ml'])

	env['note'] = expandnote(env['note'])

	return render_template("session.html", **env)
	
def expandnote(note):
	"""
	Converts a 'note' into a list of tokens of the form:
	  (0, 'linetext..) or (1, '/link/here')
	can can be easily parsed inside a jinja template. This will
	recursively expand 'notes' inside notes to handle links to
	expers and attachments etc..
	"""

	note = re.sub('<elog:exper=(.*)/(.*)>', '< ELOG /expers/\\2 >', note)
	note = re.sub('<elog:attach=(.*)>',		'< ELOG /attachments/\\1 >', note)

	n = []
	links = re.findall('< ELOG /.* >', note)
	links.append(None)
	
	k0 = 0
	for l in links:
		if l:
			k = note.find(l)
			txt = note[k0:k]
		else:
			txt = note[k0:]
        if len(txt) > 0:
            n.append((0, txt))
		if l:
			ltype = l.split(' ')[2].split('/')[1]
			lid = l.split(' ')[2].split('/')[2]
			if ltype == 'expers':
				n.append((1, expandexper(lid),))
			elif ltype == 'attachments':
				n.append((1, expandattachment(lid),))
			k0 = k + len(l)
	return n

def findsessions(pattern):
	"""
	Search function that tried to find sessions that match the pattern. The
	pattern could be the session animal/date combination, an exper id or
	simply a string that occurs inside on of the 'note' fields. Not a full
	search, but good enough to get most things
	"""
	
	db = getdb()

	if pattern.lower() == ':today':
		pattern = today(0)
	elif pattern.lower().startswith(':yesterday'):
		pattern = today(1)

	# look for matching exper
	rows = db.query("""SELECT * FROM exper WHERE """
					""" exper LIKE '%%%s%%' ORDER BY date DESC""" % (pattern))
	if rows:
		return [(x['animal'], x['date']) for x in rows]

	# look for matching session
	x = re.match('(.*)[/ ](.*)', pattern)
	if x is None or len(x.groups()) < 2:
		animal = '%'
		date = pattern
	else:
		animal = x.group(1)
		date = x.group(2)
	rows = db.query("""SELECT * FROM session WHERE """
					""" animal LIKE '%s' AND """
					""" CAST(date AS char) LIKE '%%%s%%' """
					""" ORDER BY date DESC""" % (animal, date))
	if rows:
		return [(x['animal'], x['date']) for x in rows]

	# last resort -- search NOTE fields in session, exper etc..
	rows = db.query("""SELECT * FROM session WHERE note LIKE '%%%s%%'""" % \
					pattern)
	if rows:
		return [(x['animal'], x['date']) for x in rows]
	
	rows = db.query("""SELECT * FROM exper WHERE note LIKE '%%%s%%'""" % \
					pattern)
	if rows:
		return [(x['animal'], x['date']) for x in rows]

	rows = db.query("""SELECT * FROM unit WHERE note LIKE '%%%s%%'""" % \
					pattern)
	if rows:
		return [(x['animal'], x['date']) for x in rows]

	rows = db.query("""SELECT * FROM dfile WHERE note LIKE '%%%s%%'""" % \
					pattern)
	if rows:
		return [(x['animal'], x['date']) for x in rows]

	return []

def findsessionlinks(pattern):
	l = findsessions(pattern)
	return ['/animals/%s/sessions/%s' % x for x in l]

def expandsessions(pattern):
	sessions = []
	for animal, date in findsessions(pattern):
		sessions.append(expandsession(animal, date))
	return sessions

def columntypes(db):
	# almost introspection...
	import MySQLdb.constants.FIELD_TYPE
	
	field_type = {}
	for f in dir(MySQLdb.constants.FIELD_TYPE):
		n = getattr(MySQLdb.constants.FIELD_TYPE, f)
		if type(n) is types.IntType:
			field_type[n] = f
	x = {}
	for d in db.cursor.description:
		x[d[0]] = field_type[d[1]]
	return x


def check_auth(username, password):
	"""
	This function is called to check if a username / password combination
	is valid. If PAM is available, then it will validate against the system
	login (validated users are always given RW access). Otherwise, the
	'userdata' file fille be read. At least one has to be available..
	"""
	if pam:
        if pam.pam().authenticate(username, password):
			session['username'] = username
			return True
		else:
			return False

    if username in USERS and USERS[username] == password:
        session['username'] = username
        return True
    else:
        app.logger.info('invalid login attempt from %s.' % \
                        (request.remote_addr))
        session['username'] = 'none'
        return False

def authenticate():
	"""Sends a 401 response that enables basic auth"""
	
	return Response(render_template("logout.html"),
					401, {'WWW-Authenticate':'Basic realm="elog"'})

def requires_auth(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		auth = request.authorization
		if not auth or not check_auth(auth.username, auth.password):
			return authenticate()
		return f(*args, **kwargs)
	return decorated


def Error(msg, goto=[]):
	return render_template("message.html", header="Error",
                           message=msg, goto=goto)

def Message(msg):
	return render_template("message.html", header="Message",
                           message=msg)

def Reload():
	return ('', 204)

def confirm(message, target):
    return render_template("confirm.html",
                           message=message,
                           ok=target, cancel=request.referrer)


########################################################################
#  Actual server is implmemented starting here
########################################################################

app = Flask(__name__)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'GET':
		return render_template("login.html")
	form = getform()
	if check_auth(form['username'], form['password']):
		return redirect('/')
	else:
		return Reload()

@app.route('/')
@requires_auth
def index():
	env = baseenv()
	env['ANIMALS'] = getanimals()
	return render_template("index.html", **env)

@app.route('/logout')
def logout():
	return (render_template("logout.html"), 401)

@app.route('/about')
@requires_auth
def about():
	env = baseenv()
	env['db'] = getdb()
	env['session'] = session
	return render_template("about.html", **env)

@app.route('/animals/<animal>')
@requires_auth
def animals(animal):
	animal = animal.encode()
	env = baseenv(ANIMAL=animal)
	db = getdb()
	rows = db.query("""SELECT date FROM session WHERE animal='%s'""" % animal)

    tod = today()
	env['toc'] = {}
	env['years'] = sorted(uniq([r['date'].year for r in rows]))[::-1]
	for y in env['years']:
		yl = []
		for m in range(1,13):
			rows = db.query("""SELECT date FROM session WHERE """
							""" animal='%s' AND """
							""" YEAR(date)=%d and MONTH(date)=%d""" % \
							(animal, y, m))
			ml = []
			for r in rows:
                label = '%s' % r['date']
                if label.startswith(tod):
                    label = blue(label)
				ml.append((label,
                           '/animals/%s/sessions/%s' % (animal, r['date'])))
			yl.append(ml[::-1])
		env['toc'][y] = yl
	env['MONTHS'] = [datetime.date(2014,n+1,1).strftime('%B') \
					 for n in range(12)]
	return render_template("sessionlist.html", **env)

@app.route('/animals/new')
@requires_auth
def animal_new():
	if not writeaccess():
		return Error("No write access!")
    
	db = getdb()
	r = { 'animal':'CHANGE-ME', 'date':today(), 'user':session['username'] }
	db.query("""INSERT INTO animal (%s) VALUES %s""" % \
			 (string.join(r.keys(), ','), tuple([r[k] for k in r.keys()]),))
	return redirect("/animals/%s/edit" % (r['animal'],))

@app.route('/animals/<animal>/edit')
@requires_auth
def animal_edit(animal):
	db = getdb()
	x = db.query("""SELECT * FROM animal WHERE animal='%s'""" % animal)
	if x is None:
		return Error("Can't edit %s" % (animal,))
	env = baseenv(ANIMAL=animal)
	env['row'] = x[0]
	env['row']['note'] = safenote(env['row']['note'])
	env['action'] = '/animals/%s/set' % (animal,)
	return render_template("edit_animal.html", **env)

# NOTE: THIS DELETES ENTRY IN ANIMAL TABLE, BUT NOT THE
# ACTUAL DATA!!!

@app.route('/animals/<animal>/delete')
@requires_auth
def animal_delete(animal):
    return confirm('Are you sure you want to delete animal %s?' % (animal),
                   request.path + 'C')

@app.route('/animals/<animal>/deleteC')
@requires_auth
def animal_deleteC(animal):
	db = getdb()
	rows = db.query("""SELECT * FROM animal WHERE animal='%s'""" % animal)
	if rows is None or len(rows) > 1:
		return Error("""Can't delete %s""" % animal)
	else:
		db.query("""DELETE FROM animal WHERE animal='%s'""" % animal)
    return redirect("/")

@app.route('/animals/<animal>/set', methods=['POST'])
@requires_auth
def animal_set(animal):
	if not writeaccess():
		return Error("No write access!")
    
	db = getdb()
	form = getform()

	if 'save' in form or 'done' in form:
		form['note'] = unsafenote(form['note'])
		db.query("""UPDATE animal SET """
				 """ animal='%s', date='%s', """
				 """ user='%s', idno='%s', dob='%s', """
				 """ note='%s' """
				 """ WHERE animal='%s'""" % \
				 (form['animal'], form['date'],
				  form['user'], form['idno'], form['dob'],
				  form['note'], animal))
		if not 'done' in form:
			return Reload()
	return redirect(form['_back'])

# this actually creates new or jumps to existing..
@app.route('/animals/<animal>/sessions/<date>/new')
@requires_auth
def session_new(animal, date):
	if not writeaccess():
		return Error("No write access!")

    animal = animal.encode()
	date = date.encode()
	
	db = getdb()
	rows = db.query("""SELECT date FROM session WHERE """
					""" animal='%s' AND date='%s' """ % (animal, date))
	if len(rows) == 0:
		# get most recent session for this animal
		rows = db.query("""SELECT * FROM session WHERE """
						""" animal='%s' ORDER BY date DESC LIMIT 1""" % (animal,))

		r = { 'computer':'web',
			  'animal':animal, 'date':date, 'user':session['username'] }
		if len(rows):
			# propagate these values from last entry..
			r['restricted'] = int(rows[0]['restricted'])
			r['tested'] = int(rows[0]['tested'])
			r['thweight'] = safefloat(rows[0]['thweight'])
			r['food'] = safeint(rows[0]['food'], 20)
			r['health_stool'] = safeint(rows[0]['health_stool'])
			r['health_skin'] = safeint(rows[0]['health_skin'])
			r['health_urine'] = safeint(rows[0]['health_urine'])
			r['health_pcv'] = safeint(rows[0]['health_pcv'])

		x = db.query("""INSERT INTO session (%s) VALUES %s""" % \
					 (string.join(r.keys(), ','), tuple([r[k] for k in r.keys()]),))
		if x is None:
			return Error("Can't insert %s/%s" % (animal, date))
	
	return redirect("/animals/%s/sessions/%s" % (animal, date))


def getform(r=None):
	"""Get copy of POST request data coverting unicode to str along the way."""
	if r is None:
		r = request.form.copy()
	for k in r.keys():
		if type(r[k]) is types.UnicodeType:
			r[k] = r[k].encode()
	return r
	
@app.route('/animals/<animal>/sessions/today')

def session_today(animal):
	db = getdb()
	animal = animal.encode()

	t = today()
	rows = db.query("""SELECT date FROM session WHERE date='%s' AND animal='%s'""" % (t, animal))
	if rows is not None and len(rows) > 0:
		return redirect('/animals/%s/sessions/%s' % (animal, t,))
	else:
		return session_new(animal, t)

@app.route('/animals/<animal>/sessions/new', methods=['POST'])
@requires_auth
def session_new_today(animal):
	animal = animal.encode()
	form = getform()
	# jquery-ui returns MM/DD/YYYY, conert to YYYY-MM-DD...
	date = form['date']
	date = string.join([date.split('/')[n] for n in [2,0,1]], '-')
	return session_new(animal, date)

@app.route('/animals/<animal>/sessions/<date>')
@requires_auth
def sessions(animal, date):
	env = baseenv(ANIMAL=animal)
	env['sessions'] = [expandsession(animal, date)]
	return render_template("sessions.html", **env)

@app.route('/favicon.ico')
@requires_auth
def favicon():
	return send_from_directory('static', 'favicon.ico')

@app.route('/assets/<path>')
@requires_auth
def assets(path):
	return send_from_directory('static', path)

@app.route('/fonts/<path>')
@requires_auth
def fonts(path):
	return send_from_directory('fonts', path)

@app.route('/search/<pattern>')
@requires_auth
def globalsearch(pattern):
	db = getdb()

	links = findsessionlinks(pattern)
	
	if len(links) == 1:
		return redirect(links[0])
	elif len(links) > 30:
		# show max of 30 sessions at a time
		env = baseenv()
		return render_template("searchresult.html",
							   message="'%s': %d matches." % \
							   (pattern, len(links),),
							   items=links, **env)
	elif len(links) > 0:
		env = baseenv()
		env['sessions'] = expandsessions(pattern)
		return render_template("sessions.html", **env)
	else:
		return Error("%s: no matches." % pattern)

@app.route('/search', methods=['POST'])
@requires_auth
def search():
	form = getform()
    return globalsearch(form['pattern'])

@app.route('/report/fluids/<int:year>-<int:month>')
@requires_auth
def fluids_specific(year, month):
	from report_fluid import report
	env = report('%04d-%02d-01' % (year, month))
	return render_template("report_fluid.html", **env)

@app.route('/report/pick')
@requires_auth
def pick():
	db = getdb()

	rows = db.query("""SELECT date FROM session WHERE 1""")
	l = sorted(uniq(['/report/fluids/%s' % d[:7]
					 for d in ['%s' % r['date'] for r in rows]]))[::-1]
    env = baseenv()
	return render_template("searchresult.html",
						   message="Select month",
						   items=l, **env)

@app.route('/expers/<exper>/edit')
@requires_auth
def exper_edit(exper):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	rows = db.query("""SELECT * FROM exper WHERE exper='%s'""" % (exper,))
	if rows:
		env = baseenv()
		env['row'] = rows[0]
		env['row']['note'] = safenote(env['row']['note'])
		env['action'] = '/expers/%s/set' % (exper,)
		return render_template("edit_exper.html", **env)
	else:
		return Error("%s: no matches." % exper)

@app.route('/expers/<exper>/set', methods=['POST'])
@requires_auth
def exper_set(exper):
	if not writeaccess():
		return Error("No write access!")
	form = getform()
	db = getdb()
	note = form['note']
	if 'save' in form or 'done' in form:
		note = unsafenote(note)
		db.query("""UPDATE exper SET note='%s' """
				 """ WHERE exper='%s' """ % (note, exper))
		if not 'done' in form:
			return Reload()
	return redirect(form['_back'])


@app.route('/expers/<exper>/units/<unit>/edit')
@requires_auth
def exper_unit_edit(exper, unit):
	if not writeaccess():
		return Error("No write access!")
	
	db = getdb()
	rows = db.query("""SELECT * FROM unit WHERE exper='%s' """
					""" AND unit='%s' """ % (exper, unit))
	if rows:
		env = baseenv()
		env['row'] = rows[0]
		env['row']['note'] = safenote(env['row']['note'])
		env['action'] = '/expers/%s/units/%s/set' % (exper, unit,)
		return render_template("edit_unit.html", **env)
	else:
		return Error("%s/%s: no matches." % (exper, unit,))

@app.route('/expers/<exper>/units/<unit>/set', methods=['POST'])
@requires_auth
def exper_units_set(exper, unit):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	r = getform()

	r['orig_unit'] = unit
	r['depth'] = str2num(r['depth'])
	r['qual'] = str2num(r['qual'], float)
	r['rfx'] = str2num(r['rfx'], float)
	r['rfy'] = str2num(r['rfy'], float)
	r['rfr'] = str2num(r['rfr'], float)
	r['latency'] = str2num(r['latency'], float)

	if 'save' in r or 'done' in r:
		r['note'] = unsafenote(r['note'])
		r['orig_unit'] = r['orig_unit'].encode()

		db.query("""UPDATE unit SET """
				 """   unit='%(unit)s', """
				 """   note='%(note)s', """
				 """   wellloc='%(wellloc)s', """
				 """   area='%(area)s', """
				 """   hemi='%(hemi)s', """
				 """   depth=%(depth)d, """
				 """   qual=%(qual)f, """
				 """   ori='%(ori)s', """
				 """   color='%(color)s', """
				 """   rfx=%(rfx)f, """
				 """   rfy=%(rfy)f, """
				 """   rfr=%(rfr)f, """
				 """   latency=%(latency)f """
				 """ WHERE exper='%(exper)s' AND unit='%(orig_unit)s' """ % r)

		if not 'done' in r:
			return Reload()
	return redirect(r['_back'])

@app.route('/paste', methods=['POST'])
@requires_auth
def paste():
	if not writeaccess():
		return Error("No write access!")
    
	db = getdb()
	imtype, imdata = request.form['idata'].split(',')
	#imtype = imtype.split('/')[1].split(';')[0]
	
	db.query("""INSERT INTO attachment"""
				""" (srcID, type,user,date,title,note,data)"""
				""" VALUES (0, '%s','%s','%s','%s','%s', '%s')""" % \
				(imtype, session['username'], today(),
				 'no title', 'no note', imdata,))
	rows = db.query("""SELECT attachmentID FROM attachment"""
					""" ORDER BY attachmentID DESC LIMIT 1""")
	id = rows[0]['attachmentID']

	return redirect('/attachments/%s/edit' % id)


@app.route('/attachments/showlist')
@requires_auth
def attachments_showlist():
	return redirect('/attachments/showlist/1')

@app.route('/attachments/showlist/<page>')
@requires_auth
def attachments_showlist_bypage(page):
    PERPAGE = 12
	env = baseenv()
	db = getdb()
    page = int(page)

    rows = db.query("""SELECT date FROM attachment """)
    n = len(rows)
    page = max(1, min(page, int(n/PERPAGE)+1))
    offset = min(max(0, ((page-1) * 10)), n)

    rows = db.query("""SELECT * FROM attachment """
					""" ORDER BY attachmentID DESC LIMIT %d,%d""" %
                    (offset, PERPAGE))
	env['page'] = max(1,page)
	env['pages'] = 1+int(round(n/PERPAGE))
	env['rows'] = rows
	return render_template("attachmentlist.html", **env)
	
@app.route('/attachments/<id>/edit')
@requires_auth
def attachments_edit(id):
	if not writeaccess():
		return Error("No write access!")
	
	db = getdb()
	rows = db.query("""SELECT * FROM attachment WHERE """
					""" attachmentID=%s""" % (id,))
	if rows:
		env = baseenv()
		env['row'] = rows[0]
		env['row']['note'] = safenote(env['row']['note'])
		env['action'] = '/attachments/%s/set' % (id,)
		return render_template("edit_attachment.html", **env)
	else:
		return Error("%s: no matches." % (id,))

def attachment_countlinks(id):
    ln = '<elog:attach=%s>' % id
    
	db = getdb()
    n = 0
    for t in ('session', 'exper', 'unit', 'dfile', 'animal'):
        rows = db.query("""SELECT note FROM %s WHERE """
                        """ note LIKE '%%%s%%'""" % (t, ln))
        n = n + len(rows)
    return n

@app.route('/attachments/<id>/delete')
@requires_auth
def attachments_delete(id):
    return confirm('Are you sure you want to delete attachment %s?' % (id),
                   request.path + 'C')

@app.route('/attachments/<id>/deleteC')
@requires_auth
def attachments_deleteC(id):
	if not writeaccess():
		return Error("No write access!")

    n = attachment_countlinks(id)
    if n > 0:
        return Error("""One or more links in notes.\n""",
                     ("Search for them?",
                      "/search/attach=%s" % id))
    else:
        db = getdb()
        rows = db.query("""DELETE FROM attachment WHERE """
                        """ attachmentID=%s""" % (id,))
        return Message("""Deleted attachment.""")
    
@app.route('/attachments/<id>/set', methods=['POST'])
@requires_auth
def attachment_set(id):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	r = getform()

	if 'save' in r or 'done' in r:
		r['note'] = unsafenote(r['note'])
		db.query("""UPDATE attachment SET """
				 """   note='%s', title='%s' """
				 """ WHERE attachmentID=%s """ %
				 (r['note'],r['title'],r['attachmentID']))
		if not 'done' in r:
			return Reload()
	return redirect(r['_back'])

@app.route('/dfile/<id>/edit')
@requires_auth
def dfile_edit(id):
	if not writeaccess():
		return Error("No write access!")
	
	db = getdb()
	rows = db.query("""SELECT * FROM dfile WHERE """
					""" dfileID=%s""" % (id,))
	if rows:
		env = baseenv()
		env['row'] = rows[0]
		env['row']['note'] = safenote(env['row']['note'])
		env['action'] = '/dfile/%s/set' % (id,)
		return render_template("edit_dfile.html", **env)
	else:
		return Error("%s: no matches." % (id,))

@app.route('/dfile/<id>/set', methods=['POST'])
@requires_auth
def dfile_set(id):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	r = getform()

	r['crap'] = str2num('crap' in r)
	
	if 'save' in r or 'done' in r:
		r['note'] = unsafenote(r['note'])
		db.query("""UPDATE dfile SET """
				 """   note='%s', crap=%s """
				 """ WHERE dfileID=%s """ %
				 (r['note'],r['crap'],id,))
		if not 'done' in r:
			return Reload()
	return redirect(r['_back'])

@app.route('/animals/<animal>/sessions/<date>/newexper')
@requires_auth
def exper_new(animal, date):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	exper = GetNextExper(animal)
	db.query("""INSERT INTO exper SET """
			 """  animal='%s', date='%s', exper='%s',"""
			 """  note=''""" % (animal, date, exper))
	link = "\n<elog:exper=%s/%s>\n" % (date, exper)

	rows = db.query("""SELECT note FROM session WHERE animal='%s' AND""" \
					""" date='%s'""" % (animal, date,))
	note = rows[0]['note'] + link
	rows = db.query("""UPDATE session SET note='%s' WHERE """\
					"""	 animal='%s' AND date='%s'""" % (note, animal, date,))
	return redirect('/expers/%s/edit' % (exper,))

@app.route('/expers/<exper>/newunit')
@requires_auth
def unit_new(exper):
	if not writeaccess():
		return Error("No write access!")
	# start with set as TTL, let user change
	db = getdb()
	r = db.query("""SELECT * FROM exper WHERE exper='%s'""" % exper)[0]
	u = 'TTL'
	k = 0
	while 1:
		rows = db.query("""SELECT unit FROM unit WHERE """
						"""	 unit='%s' and exper='%s'""" % (u, exper))
		if len(rows) == 0:
			break
		u = 'sig%02d' % k
		k = k + 1
			
	db.query("""INSERT INTO unit SET """
			 """  unit='%s', """
			 """  experID=%d, """
			 """  exper='%s', """
			 """  animal='%s', """
			 """  date='%s' """ % (u, r['experID'], exper, r['animal'], r['date']))
	return redirect('/expers/%s/units/%s/edit' % (exper, u))

@app.route('/expers/<exper>/units/<unit>/delete')
@requires_auth
def unit_delete(exper, unit):
    # stage2: ask for confirmation
    return confirm('Are you sure you want to delete unit %s:%s?' % (exper,unit),
                   request.path + 'C')

@app.route('/expers/<exper>/units/<unit>/deleteC')
@requires_auth
def unit_deleteC(exper, unit):
    # stage2: actually delete..
	db = getdb()
	r = db.query("""SELECT animal,date FROM exper WHERE exper='%s'""" % (exper))[0]
	db.query("""DELETE FROM unit WHERE """
			 """  exper='%s' AND unit='%s' """ % (exper, unit))
	return redirect('/animals/%s/sessions/%s' % (r['animal'], r['date']))


@app.route('/animals/<animal>/sessions/<date>/edit')
@requires_auth
def session_edit(animal, date):
	if not writeaccess():
		return Error("No write access!")
	
	db = getdb()
	rows = db.query("""SELECT * FROM session WHERE animal='%s' AND""" \
					""" date='%s'""" % (animal, date,))
	if rows:
		env = baseenv()
		env['row'] = rows[0]
		env['row']['note'] = safenote(env['row']['note'])
		env['action'] = '/animals/%s/sessions/%s/set' % (animal, date)
		return render_template("edit_session.html", **env)
	else:
		return Error("%s/%s: no matches." % (animal, date,))

@app.route('/animals/<animal>/sessions/<date>/set', methods=['POST'])
@requires_auth
def session_set(animal, date):
	if not writeaccess():
		return Error("No write access!")
	db = getdb()
	r = getform()

	r['restricted'] = str2num('restricted' in r)
	r['tested'] = str2num('tested' in r)
	r['health_stool'] = str2num('health_stool' in r)
	r['health_urine'] = str2num('health_urine' in r)
	r['health_skin'] = str2num('health_skin' in r)
	r['health_pcv'] = str2num('health_pcv' in r)
	r['water_work'] = str2num(r['water_work'])
	r['water_sup'] = str2num(r['water_sup'])
	r['fruit_ml'] = str2num(r['fruit_ml'])
	r['food'] = str2num(r['food'])
	r['weight'] = str2num(r['weight'], float)

	r['note'] = unsafenote(r['note'])

	if 'save' in r or 'done' in r:
		db.query("""UPDATE session SET """
				 """   note='%(note)s', """
				 """   restricted=%(restricted)d, """
				 """   tested=%(tested)d, """
				 """   health_stool=%(health_stool)d, """
				 """   health_skin=%(health_skin)d, """
				 """   health_urine=%(health_urine)d, """
				 """   health_pcv=%(health_pcv)d, """
				 """   water_work=%(water_work)d, """
				 """   water_sup=%(water_sup)d, """
				 """   fruit_ml=%(fruit_ml)d, """
				 """   food=%(food)d, """
				 """   weight=%(weight)f """
				 """ WHERE animal='%(animal)s' """
				 """ AND date='%(date)s'""" % r)
		if not 'done' in r:
			return Reload()
	return redirect(r['_back'])

def smooth(x, y, k=1):
    k = (2 * k) + 1
    ny = np.convolve(y, np.ones(k)/k, mode='valid')
    n = (len(y) - len(ny)) / 2
    return x[n:-n],ny

@app.route('/animals/<animal>/weight/plot')
@requires_auth
def plot_weight(animal):
	import matplotlib.dates as mdates

	db = getdb()

	plots = []
	
	rows = db.query("""SELECT date,weight,thweight FROM session WHERE """
					""" animal='%s' AND """
					""" weight > 0 AND """
					""" date > DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY date""" % animal)
    
	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) for r in rows])
		y = np.array([r['weight'] for r in rows])
		t = np.array([safefloat(r['thweight'],0.0) for r in rows])
		plt.clf()
		plt.plot_date(x[np.nonzero(t)], t[np.nonzero(t)], 'ro')
		plt.plot_date(x, y, 'bo')
        x, y = smooth(x, y)
        plt.plot_date(x, y, 'b-')
        
		plt.title('%s: last 90d' % animal);
		plt.ylabel('Weight (kg)')
		plots.append(('dummy%d'%len(plots), json.dumps(mpld3.fig_to_dict(plt.gcf()))))

	rows = db.query("""SELECT date,weight,thweight FROM session WHERE """
					""" animal='%s' AND """
					""" weight > 0 ORDER BY date""" % animal)
	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) for r in rows])
		y = np.array([r['weight'] for r in rows])
		t = np.array([safefloat(r['thweight'],0.0) for r in rows])
		plt.clf()
		plt.plot_date(x[np.nonzero(t)], t[np.nonzero(t)], 'ro')
		plt.plot_date(x, y, 'bo')
        x, y = smooth(x, y)
        plt.plot_date(x, y, 'b-')
        
		plt.title('%s: all data' % animal);
		plt.ylabel('Weight (kg)')
		plots.append(('dummy%d'%len(plots), json.dumps(mpld3.fig_to_dict(plt.gcf()))))
		
	
	return render_template("plotview.html",
						   title='%s weight history' % animal,
						   plots=plots)

	
@app.route('/animals/<animal>/fluid/plot')
@requires_auth
def plot_fluid(animal):
	import matplotlib.dates as mdates

	plots = []
	
	db = getdb()

	rows = db.query("""SELECT date,water_sup,water_work,fruit_ml """
					""" FROM session """
					""" WHERE animal='%s' AND """
					""" date > DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY date """ % animal)
	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) for r in rows])
		y1 = np.array([safefloat(r['water_work']) +
			  safefloat(r['water_sup']) +
			  safefloat(r['fruit_ml']) for r in rows])
		y2 = np.array([safefloat(r['water_work']) for r in rows])
		plt.clf()
        sx, sy = smooth(x, y1)
		plt.plot(x, y1, 'ro', label='total')
        plt.plot(sx, sy, 'r-')
        sx, sy = smooth(x, y2)
		plt.plot(x, y2, 'bo', label='work')
        plt.plot(sx, sy, 'b-')
		plt.legend()			  #<- bug wrap around...
		plt.gca().xaxis_date()
		plt.title('%s: last 90d' % animal)
		plt.ylabel('Fluid Intake (ml)')
		plots.append(('dummy%d'%len(plots),
                      json.dumps(mpld3.fig_to_dict(plt.gcf()))))
		
	rows = db.query("""SELECT * FROM session WHERE """
					""" animal='%s' ORDER BY date""" % animal)

	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) for r in rows])
		y1 = np.array([safefloat(r['water_work']) +
                       safefloat(r['water_sup']) +
                       safefloat(r['fruit_ml']) for r in rows])
		y2 = np.array([safefloat(r['water_work']) for r in rows])
		plt.clf()
        sx, sy = smooth(x, y1)
		plt.plot(x, y1, 'ro', label='total')
        plt.plot(sx, sy, 'r-')

        sx, sy = smooth(x, y2)
		plt.plot(x, y2-1.0, 'bo', label='work')
        plt.plot(sx, sy-1.0, 'r-')
        
		plt.legend()			  #<- bug wrap around...
		plt.gca().xaxis_date()
		plt.title('%s: all data' % animal)
		plt.ylabel('Fluid Intake (ml)')
		plots.append(('dummy%d'%len(plots),
                      json.dumps(mpld3.fig_to_dict(plt.gcf()))))

	
	return render_template("plotview.html",
						   title='%s fluid history' % animal,
						   plots=plots)

# some useful filters

@app.template_filter('red')
def red(s):
	return """<font color="red">%s</font>""" % s

@app.template_filter('blue')
def blue(s):
	return """<font color="blue">%s</font>""" % s

@app.template_filter('glyph')
def insert_glyph(name):
	return """
	<span class="glyphicon glyphicon-%s" aria-hidden="true"></span>
	""" % name

if __name__ == "__main__":
	try:
		getanimals()
	except TypeError:
		sys.stderr.write('run fix-animals to update database\n')
		sys.exit(1)

	if not LOGGING:
		import logging
		log = logging.getLogger('werkzeug')
		log.setLevel(logging.ERROR)
		
	app.secret_key = 'aslLKJLjkasdf90u8s(&*(&assdfslkjfasLKJdf8'
	app.run(debug=True, host=HOST, port=PORT,
			ssl_context=('server.crt', 'server.key'))
