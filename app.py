# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os, types, string
import re, textwrap

from flask import *
from functools import wraps

#sys.path.append('%s/lib/elog' % os.path.dirname(os.path.dirname(sys.argv[0])))

sys.path.append(os.environ['ELOG_DIR'])
from elogapi import getdb

LOG=True
SSL=True

CHECKS = { 1:("""<span class="glyphicon glyphicon-check" """ \
                """aria-hidden="true"></span>"""),
          0:("""<span class="glyphicon glyphicon-unchecked" """
                """ aria-hidden="true"></span>""") }
MONTH_NAMES= ( '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', \
               'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec' )

USERS = { 'admin':'f00lish0one',
          'public':'boring99',
          'mazer':'the-0ne' }

# Useful helper functions

def uniq(s): return list(set(s))

def safeint(x):
    try:
        return int(round(x))
    except TypeError:
        return 'ND'

def today(n=0):
    import datetime
    return (datetime.datetime.now() -
            datetime.timedelta(days=n)).strftime("%Y-%m-%d")

def baseenv(**env):
    return env

def getanimals():
    db = getdb()
    print db
    rows = db.query("""SELECT animal FROM session WHERE 1""")
    return sorted(list(set([row['animal'] for row in rows])))

def expandnote(note):
    """
    Converts a 'note' into a list of tokens of the form:
      (0, 'linetext..) or (1, '/link/here')
    can can be easily parsed inside a jinja template. This will
    recursively expand 'notes' inside notes to handle links to
    expers and attachments etc..
    """

    def expandattachment(id):
        env = baseenv(ANIMAL=id)
        db = getdb()
        row = db.query("""SELECT * FROM attachment WHERE"""
                       """ attachmentID=%s""" % (id,))[0]
        row['date'] = '%s' % row['date']
        env.update(row)

        for k in env.keys():
            if type(env[k]) is types.StringType and len(env[k]) == 0:
                env[k] = 'ND'

        env['note'] = expandnote(env['note'])
        return render_template("attachment.html", **env)

    def expandexper(id):
        env = baseenv(ANIMAL=id)
        db = getdb()
        row = db.query("""SELECT * FROM exper WHERE exper='%s'""" % (id,))[0]
        row['date'] = '%s' % row['date']
        env.update(row)

        for k in env.keys():
            if type(env[k]) is types.StringType and len(env[k]) == 0:
                env[k] = 'ND'

        env['note'] = expandnote(env['note'])

        rows = db.query("""SELECT * FROM unit WHERE """\
                        """exper='%s'""" % (env['exper'],))
        env['units'] = rows
        for u in env['units']:
            u['note'] = expandnote(u['note'])

        rows = db.query("""SELECT * FROM dfile WHERE """\
                        """exper='%s'""" % (env['exper'],))
        env['dfiles'] = rows
        for d in env['dfiles']:
            d['note'] = expandnote(d['note'])
            d['crap'] = CHECKS[d['crap']]
        for k in d.keys():
            if type(d[k]) is types.StringType and len(d[k]) == 0:
                d[k] = 'ND'
            

        return render_template("exper.html", **env)
    
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
        pattern = today(-1)

    print pattern

    # look for matching exper
    rows = db.query("""SELECT * FROM exper WHERE """
                    """ exper LIKE '%%%s%%' ORDER BY date DESC""" % (pattern))
    if rows:
        return ['/animals/%s/sessions/%s' % \
                (x['animal'], x['date']) for x in rows]

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
        return ['/animals/%s/sessions/%s' % \
                (x['animal'], x['date']) for x in rows]

    # last resort -- search NOTE fields in session, exper etc..
    rows = db.query("""SELECT * FROM session WHERE note LIKE '%%%s%%'""" % \
                    pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) \
                for x in rows]
    
    rows = db.query("""SELECT * FROM exper WHERE note LIKE '%%%s%%'""" % \
                    pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) \
                for x in rows]

    rows = db.query("""SELECT * FROM exper WHERE unit LIKE '%%%s%%'""" % \
                    pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) \
                for x in rows]

    rows = db.query("""SELECT * FROM exper WHERE dfile LIKE '%%%s%%'""" % \
                    pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) \
                for x in rows]

    return []

def check_auth(username, password):
    """
    This function is called to check if a username / password combination
    is valid.
    """
    if username in USERS and USERS[username] == password:
        session['username'] = username
        return True
    else:
        return False

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(("""Could not verify your access level for that URL.\n"""
                     """You have to login with proper credentials"""),
                    401, {'WWW-Authenticate':'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


########################################################################
#  Actual server is implmemented starting here
########################################################################


app=Flask(__name__)

@app.route('/')
@requires_auth
def index():
    env = baseenv()
    env['ANIMALS'] = getanimals()
    return render_template("index.html", **env)

@app.route('/about')
def about():
    env = baseenv()
    env['db'] = getdb()
    env['session'] = session
    return render_template("about.html", **env)

@app.route('/animals/<id>')
@requires_auth
def animals(id):
    env = baseenv(ANIMAL=id)
    db = getdb()
    rows = db.query("""SELECT date FROM session WHERE animal='%s'""" % id)

    env['toc'] = {}
    env['years'] = sorted(uniq([r['date'].year for r in rows]))[::-1]
    for y in env['years']:
        yl = []
        for m in range(1,13):
            rows = db.query("""SELECT date FROM session WHERE """
                            """ animal='%s' AND """
                            """ YEAR(date)=%d and MONTH(date)=%d """ % \
                            (id, y, m))
            ml = []
            for r in rows:
                ml.append('/animals/%s/sessions/%s' % (id, r['date']))
            yl.append(ml)
        env['toc'][y] = yl
    env['MONTHS'] = MONTH_NAMES
    return render_template("animals_toc.html", **env)

@app.route('/animals/<id>/sessions/<date>')
@requires_auth
def sessions(id, date):
    env = baseenv(ANIMAL=id)
    db = getdb()
    # should be exactly one row:
    row = db.query("""SELECT * FROM session WHERE """
                   """ animal='%s' and date='%s'""" % (id, date))[0]
    row['date'] = '%s' % row['date']
    env.update(row)
    for k in env.keys():
        if type(env[k]) is types.StringType and len(env[k]) == 0:
            env[k] = 'ND'

    env['restricted'] = CHECKS[env['restricted']]
    env['tested'] = CHECKS[env['tested']]

    env['dtb'] = safeint(env['dtb'])
    env['dtb_ml'] = safeint(env['dtb_ml'])
    env['xdtb'] = safeint(env['xdtb'])
    env['xdtb_ml'] = safeint(env['xdtb_ml'])

    env['health_stool'] = CHECKS[env['health_stool']]
    env['health_skin'] = CHECKS[env['health_skin']]
    env['health_urine'] = CHECKS[env['health_urine']]
    env['health_pcv'] = CHECKS[env['health_pcv']]

    env['note'] = expandnote(env['note'])

    return render_template("session.html", **env)

@app.route('/assets/<path>')
def assets(path):
    try:
        return send_from_directory('assets', path)
    except Exception, e:
        return str(e)

@app.route('/fonts/<path>')
def fonts(path):
    try:
        return send_from_directory('fonts', path)
    except Exception, e:
        return str(e)


@app.route('/search', methods=['POST'])
@requires_auth
def search():
    from flask import redirect, request, url_for
    db = getdb()

    links = findsessions(request.form['pattern'])
    
    if len(links) == 1:
        return redirect(links[0])
    elif len(links) >= 1:
        env = baseenv()
        return render_template("searchresult.html",
                               message="'%s': %d matches." % \
                               (request.form['pattern'], len(links),),
                               items=links, **env)
    else:
        env = baseenv()
        return render_template("searchresult.html",
                               message="'%s': no matches." % \
                               (request.form['pattern'],),
                               items=[], **env)

@app.route('/report/fluids/<int:year>-<int:month>')
def fluids_specific(year, month):
    from report_fluid import report
    env = report('%04d-%02d-01' % (year, month))
    return render_template("report_fluid.html", **env)

@app.route('/report/pick')
def pick():
    db = getdb()

    rows = db.query("""SELECT date FROM session WHERE 1""")
    l = sorted(uniq(['/report/fluids/%s' % d[:7] \
                     for d in ['%s' % r['date'] for r in rows]]))[::-1]
    env = baseenv()
    return render_template("searchresult.html",
                           message="Monthly logs for ...",
                           items=l, **env)

app.secret_key = "aslLKJLjkasdf90u8s(&*(&assdfslkjfasLKJdf8"

if __name__ == "__main__":
    if not LOG:
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

    if SSL:
        if 0:
            from OpenSSL import SSL
            context = SSL.Context(SSL.SSLv23_METHOD)
            context.use_privatekey_file('server.key')
            context.use_certificate_file('server.crt')
            app.run(debug=True, ssl_context=context)
        else:
            app.run(debug=True, ssl_context=('server.crt', 'server.key'))
    else:
        app.run(debug=True)
