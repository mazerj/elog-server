# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os, types, string
import re, textwrap, datetime

from flask import *
from functools import wraps

#sys.path.append('%s/lib/elog' % os.path.dirname(os.path.dirname(sys.argv[0])))

sys.path.append(os.environ['ELOG_DIR'])
from elogapi import getdb

from app_tools import *

HTTPS=True
LOGGING=True
HOST='0.0.0.0'
#HOST='127.0.0.1'
PORT=5000
LOCAL='192.168.1.1'

try:
    USERS = {}
    USERS_RW = {}
    for l in open('userdata', 'r').readlines():
        l = l[:-1].split(':')
        if len(l) == 3:
            USERS[l[0]] = l[1]
            USERS_RW[l[0]] = (l[2].lower() == 'rw')
except:
    sys.stderr.write("""bad/missing 'userdata' file.\n""")
    sys.exit(1)

# Useful helper functions

def writeaccess():
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
    rows = db.query("""SELECT animal FROM animal WHERE 1""")
    return sorted(list(set([row['animal'] for row in rows])))

def expandattachment(id):
    env = baseenv()
    db = getdb()
    row = db.query("""SELECT * FROM attachment WHERE"""
                   """ attachmentID=%s""" % (id,))[0]
    row['date'] = '%s' % row['date']
    env.update(row)

    for k in env.keys():
        if type(env[k]) is types.StringType and len(env[k]) == 0:
            env[k] = 'N/A'

    env['note'] = expandnote(env['note'])
    return render_template("attachment.html", **env)

def expandexper(exper):
    env = baseenv()
    db = getdb()
    row = db.query("""SELECT * FROM exper WHERE exper='%s'""" % (exper,))[0]
    row['date'] = '%s' % row['date']
    env.update(row)

    for k in env.keys():
        if type(env[k]) is types.StringType and len(env[k]) == 0:
            env[k] = 'N/A'

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
            d['crap'] = check(d['crap'])
        for k in d.keys():
            if type(d[k]) is types.StringType and len(d[k]) == 0:
                d[k] = 'N/A'


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
            env[k] = 'N/A'

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
    note = re.sub('<elog:attach=(.*)>',     '< ELOG /attachments/\\1 >', note)

    n = []
    links = re.findall('< ELOG /.* >', note)
    links.append(None)
    
    k0 = 0
    for l in links:
        if l:
            k = note.find(l)
            frags = note[k0:k].split('\n')
        else:
            frags = note[k0:].split('\n')
        for j in frags:
            lines = textwrap.wrap(j, 80)
            for lno in range(len(lines)):
                if lno > 0:
                    n.append((1, '.. '+'&nbsp;'*8,))
                n.append((0, lines[lno],))
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

    if pattern.lower() == '=today':
        pattern = today(0)
    elif pattern.lower() == '=yesterday':
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

    rows = db.query("""SELECT * FROM exper WHERE unit LIKE '%%%s%%'""" % \
                    pattern)
    if rows:
        return [(x['animal'], x['date']) for x in rows]

    rows = db.query("""SELECT * FROM exper WHERE dfile LIKE '%%%s%%'""" % \
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


def islocalconnection(addr):
    # If LOCAL is not None, then anything not matching the
    # local definition is non-local. If LOCAL is none, then
    # everything is non-local!
    if LOCAL:
        return not request.remote_addr.startswith(LOCAL)
    else:
        return False

def check_auth(username, password):
    """
    This function is called to check if a username / password combination
    is valid.
    """

    if islocalconnection(request.remote_addr):
        # local source (not through firewall), don't require password,
        # just password..
        if username:
            session['username'] = username
            return True
        else:
            return False
    else:
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

    if islocalconnection(request.remote_addr):
        msg = "Username required"
    else:
        msg = "Username and password required"

    return Response(("""Could not verify your access level for that URL.\n"""
                     """You have to login with proper credentials"""),
                        401, {'WWW-Authenticate':
                              'Basic realm="%s"' % msg})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


def Error(msg):
    return render_template("message.html", header="Error", message=msg)
    


########################################################################
#  Actual server is implmemented starting here
########################################################################


app = Flask(__name__)

@app.route('/')
@requires_auth
def index():
    env = baseenv()
    env['ANIMALS'] = getanimals()
    return render_template("index.html", **env)

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
                ml.append('/animals/%s/sessions/%s' % (animal, r['date']))
            yl.append(ml[::-1])
        env['toc'][y] = yl
    env['MONTHS'] = [datetime.date(2014,n+1,1).strftime('%B') \
                     for n in range(12)]
    return render_template("sessionlist.html", **env)

@app.route('/animals/new')
@requires_auth
def animal_new():
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
    env['action'] = '/animals/%s/set' % (animal,)
    return render_template("edit_animal.html", **env)

@app.route('/animals/<animal>/delete')
@requires_auth
def animal_delete(animal):
    db = getdb()
    rows = db.query("""SELECT * FROM animal WHERE animal='%s'""" % animal)
    if rows is None or len(rows) > 1:
        return Error("""Can't delete %s""" % animal)
    else:
        db.query("""DELETE FROM animal WHERE animal='%s'""" % animal)

    print 'deleted -- redirecting'
    return redirect("/")


@app.route('/animals/<animal>/set', methods=['POST'])
@requires_auth
def animal_set(animal):
    db = getdb()
    form = getform()

    if 'save' in form or 'done' in form:
        db.query("""UPDATE animal SET animal='%s', date='%s', user='%s', idno='%s', note='%s'"""
                 """ WHERE animal='%s'""" % (form['animal'], form['date'],
                                             form['user'], form['idno'], form['note'],
                                             animal))
        if not 'done' in form:
            return ('', 204)
    return redirect(form['_back'])

@app.route('/animals/<animal>/sessions/<date>/new')
@requires_auth
def session_new(animal, date):
    print 'session_new:', animal, date
    animal = animal.encode()
    date = date.encode()
    
    db = getdb(quiet=False)
    rows = db.query("""SELECT date FROM session WHERE """
                    """ animal='%s' AND date='%s' """ % (animal, date))
    if len(rows):
        return Error("%s/%s exists." % (animal, date))

                               

    # get most recent session for this animal
    rows = db.query("""SELECT * FROM session WHERE """
                    """ animal='%s' ORDER BY date DESC LIMIT 1""" % (animal,))
    
    r = { 'computer':'http',
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
    
@app.route('/animals/<animal>/sessions/new', methods=['POST'])
@requires_auth
def session_new_today(animal):
    print '\n\nXXX', animal, '\n'
    animal = animal.encode()
    form = getform()
    if len(form['date']) < 10:
        date = today()
    else:
        date = form['date']
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
    return send_from_directory('assets', 'favicon.ico')

@app.route('/assets/<path>')
@requires_auth
def assets(path):
    return send_from_directory('assets', path)

@app.route('/fonts/<path>')
@requires_auth
def fonts(path):
    return send_from_directory('fonts', path)

@app.route('/search', methods=['POST'])
@requires_auth
def search():
    from flask import redirect, request, url_for
    db = getdb()

    form = getform()
    links = findsessionlinks(form['pattern'])
    
    if len(links) == 1:
        return redirect(links[0])
    elif len(links) > 30:
        # show max of 30 sessions at a time
        env = baseenv()
        return render_template("searchresult.html",
                               message="'%s': %d matches." % \
                               (form['pattern'], len(links),),
                               items=links, **env)
    elif len(links) > 0:
        env = baseenv()
        env['sessions'] = expandsessions(form['pattern'])
        return render_template("sessions.html", **env)
    else:
        return Error("%s: no matches." % form['pattern'])

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
    l = sorted(uniq(['/report/fluids/%s' % d[:7] \
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
        env['action'] = '/expers/%s/set' % (exper,)
        return render_template("edit_exper.html", **env)
    else:
        return Error("%s: no matches." % exper)

@app.route('/expers/<exper>/set', methods=['POST'])
@requires_auth
def exper_set(exper):
    form = getform()
    db = getdb()
    note = form['note']
    if 'save' in form or 'done' in form:
        db.query("""UPDATE exper SET note='%s' WHERE exper='%s' """ % (note, exper))
        if not 'done' in form:
            return ('', 204)
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
        env['action'] = '/expers/%s/units/%s/set' % (exper, unit,)
        return render_template("edit_unit.html", **env)
    else:
        return Error("%s/%s: no matches." % (exper, unit,))

@app.route('/expers/<exper>/units/<unit>/set', methods=['POST'])
@requires_auth
def exper_units_set(exper, unit):
    db = getdb()
    r = getform()
 
    r['depth'] = str2num(r['depth'])
    r['qual'] = str2num(r['qual'], float)
    r['rfx'] = str2num(r['rfx'], float)
    r['rfy'] = str2num(r['rfy'], float)
    r['rfr'] = str2num(r['rfr'], float)
    r['latency'] = str2num(r['latency'], float)

    if 'save' in r or 'done' in r:
        db.query("""UPDATE unit SET """
                 """   note='%(note)s', """
                 """   wellloc='%(wellloc)s', """
                 """   note='%(area)s', """
                 """   hemi='%(hemi)s', """
                 """   depth=%(depth)d, """
                 """   qual=%(qual)f, """
                 """   ori='%(ori)s', """
                 """   color='%(color)s', """
                 """   rfx=%(rfx)f, """
                 """   rfy=%(rfy)f, """
                 """   rfr=%(rfr)f, """
                 """   latency=%(latency)f """
                 """ WHERE exper='%(exper)s' AND unit='%(unit)s' """ % r)
        if not 'done' in r:
            return ('', 204)
    return redirect(r['_back'])

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
        env['action'] = '/animals/%s/sessions/%s/set' % \
          (animal, date)
        return render_template("edit_session.html", **env)
    else:
        return Error("%s/%s: no matches." % (animal, date,))

@app.route('/animals/<animal>/sessions/<date>/set', methods=['POST'])
@requires_auth
def session_set(animal, date):
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
            return ('', 204)
    return redirect(r['_back'])

@app.route('/test')
@requires_auth
def test():
    return render_template("test.html")

@app.route('/dbtest')
@requires_auth
def dbtest():
    db = getdb()
    r = db.query("""select * from session limit 1""")
    return '%s' % columntypes(db)

if __name__ == "__main__":
    db = getdb(quiet=True)
    if not LOGGING:
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
    if HTTPS:
        app.secret_key = 'aslLKJLjkasdf90u8s(&*(&assdfslkjfasLKJdf8'
        app.run(debug=True, host=HOST, port=PORT,
                ssl_context=('server.crt', 'server.key'))
    else:
        app.run(debug=True, host=HOST)
