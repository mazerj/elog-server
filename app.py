# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os, types, string
from flask import Flask, render_template, send_from_directory, url_for
import re, textwrap

#sys.path.append('%s/lib/elog' % os.path.dirname(os.path.dirname(sys.argv[0])))

sys.path.append(os.environ['ELOG_DIR'])
from elogapi import getdb


CHECKS = { 1:("""<span class="glyphicon glyphicon-check" """ \
                """aria-hidden="true"></span>"""),
          0:("""<span class="glyphicon glyphicon-unchecked" """
                """ aria-hidden="true"></span>""") }
MONTH_NAMES= ( '', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', \
               'jul', 'aug', 'sept', 'oct', 'nov', 'dec' )


def uniq(s): return list(set(s))

def baseenv(**env):
    db = getdb()
    return env

def getanimals():
    db = getdb()
    rows = db.query("""SELECT animal FROM session WHERE 1""")
    return sorted(list(set([row['animal'] for row in rows])))

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

    return render_template("exper.html", **env)


def expandnote(note):
    # this converts the note to a list of lines (0, 'linetext..) and
    # links (1, '/link/here') can can be parsed inside the jinja
    # template to generate buttons and text..
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
                    n.append((1, '&nbsp;'*10,))
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
    """returns list of links to matching sessions"""
    
    db = getdb()

    # look for matching exper
    rows = db.query("""SELECT * FROM exper WHERE """
                    """ exper LIKE '%%%s%%' ORDER BY date DESC""" % (pattern))
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]

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
                    """ CAST(date AS char) LIKE '%%%s%%' ORDER BY date DESC""" % (animal, date))
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]

    # last resort -- search NOTE fields in session, exper etc..
    rows = db.query("""SELECT * FROM session WHERE note LIKE '%%%s%%'""" % pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]
    
    rows = db.query("""SELECT * FROM exper WHERE note LIKE '%%%s%%'""" % pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]

    rows = db.query("""SELECT * FROM exper WHERE unit LIKE '%%%s%%'""" % pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]

    rows = db.query("""SELECT * FROM exper WHERE dfile LIKE '%%%s%%'""" % pattern)
    if rows:
        return ['/animals/%s/sessions/%s' % (x['animal'], x['date']) for x in rows]

    return []

def safeint(x):
    try:
        return int(round(x))
    except TypeError:
        return 'ND'


###########################################################################################
#  Actual server is implmemented starting here
###########################################################################################


app=Flask(__name__)

@app.route('/')
def index():
    env = baseenv()
    env['ANIMALS'] = getanimals()
    return render_template("index.html", **env)

@app.route('/animals/<id>')
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
def search():
    from flask import redirect, request, url_for
    db = getdb()

    links = findsessions(request.form['pattern'])
    if len(links) == 1:
        return redirect(links[0])
    elif len(links) >= 1:
        env = baseenv()
        return render_template("searchresult.html",
                               message="'%s': %d matches." % (request.form['pattern'], len(links),),
                               items=links, **env)
    else:
        env = baseenv()
        return render_template("searchresult.html",
                               message="'%s': no matches." % (request.form['pattern'],),
                               items=[], **env)
    
if __name__ == "__main__":
    import logging
    log = logging.getLogger('werkzeug')
    #log.setLevel(logging.ERROR)
	app.run(debug=True)
