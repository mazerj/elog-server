# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os
import string
import types
import datetime, time
import numpy as np

from elogapi import getdb

CHECKS = { 1:("""<span class="glyphicon glyphicon-check" """ \
                  """aria-hidden="true"></span>"""),
                  0:("""<span class="glyphicon glyphicon-unchecked" """
                     """ aria-hidden="true"></span>""") }

def iget(rows, name):
    if isinstance(rows[0][name], types.StringType):
        return 0
    else:
        return rows[0][name]

def ps(s):
    """return string or '-'
    """
    if len(s): return s
    else: return '-'

def pc(s):                                # checked?
    """return checkmark or blank
    """
    if s: return CHECKS[1]
    else: return CHECKS[0]

def report(date0):
    db = getdb()
    
    env = {}
    # only do this for animals restricted during the specified month
    (ok, rows) = db.q("""SELECT animal """
                      """ FROM session WHERE """
                      """ MONTH('%s') = MONTH(date) AND """
                      """ YEAR('%s') = YEAR(date) AND """
                      """ restricted > 0""" % (date0, date0,))

    env['animals'] = sorted(list(set([r['animal'] for r in rows])))
    env['data'] = {}
    
    DAYS = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

    for animal in env['animals']:
        t = []
        for datenum in range(1,32):
            date = '%s%02d' % (date0[:-2], datenum)
            try:
                dow = time.strptime(date, '%Y-%m-%d').tm_wday
            except ValueError:
                break
            x = '%s %s' % (DAYS[dow], date)
            if dow in (5,6):
                datestr = """<font color='blue'>%s</font>""" % x
            else:
                datestr = x
            tr = [datestr,]
            (ok, rows) = db.q("""SELECT * """
                              """ FROM session WHERE """
                              """ date='%s' AND """
                              """ animal LIKE "%s" """ % (date, animal))
            if len(rows):
                tr.append(ps('%s' % rows[0]['user']))
                tr.append(ps('%s' % rows[0]['weight']))
                tr.append(pc(rows[0]['restricted']))
                tr.append(pc(rows[0]['tested']))
                tr.append(pc(rows[0]['health_stool']))
                tr.append(pc(rows[0]['health_urine']))
                tr.append(pc(rows[0]['health_skin']))
                tr.append(pc(rows[0]['health_pcv']))
                ww = iget(rows,'water_work')
                ws = iget(rows, 'water_sup')
                wf = iget(rows, 'fruit_ml')
                wt = ww + ws + wf
                tr.append('%s (%s+%s+%s)' % (wt, ww, ws, wf))
                tr.append(rows[0]['fruit'])
                l = rows[0]['note'].split('\n')[0]
                if len(l) and l[0] in '%#;%/!':
                    # if first line of note appears to be a "comment", put
                    # it in the other column..
                    tr.append(l[1:])
                else:
                    tr.append(' ')
            else:
                for n in range(11):
                    tr.append(' ')
            t.append(tr)
        env['data'][animal] = t
    env['header'] = ['date', 'user', 'kg', 'rest', 'test', \
                     'stool', 'urine', 'skin', 'pcv', 'fluid (w+s+f)', \
                     'fruit', 'other']
    env['date0'] = date0
                    
    return env
