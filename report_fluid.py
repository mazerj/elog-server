# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os
import string
import types
import datetime, time

from elogapi import getdb

from app_tools import *

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
            (ok, rows) = db.q("""SELECT * """
                              """ FROM session WHERE """
                              """ date='%s' AND """
                              """ animal LIKE "%s" """ % (date, animal))
            if len(rows):
                tr = [datestr,]
                tr.append(ps('%s' % rows[0]['user']))
                tr.append(ps('%s' % rows[0]['weight']))
                tr.append(check(rows[0]['restricted']))
                tr.append(check(rows[0]['tested']))

                tr.append(check(rows[0]['health_stool']) + check(rows[0]['health_urine']) +
                          check(rows[0]['health_skin']) + check(rows[0]['health_pcv']))
                
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
                tr = ([datestr, glyph('flag')] + [' '] * 7)
            t.append(tr)
        env['data'][animal] = t
    env['header'] = ['date', 'user', 'wt (kg)', 'rstrct', 'test', \
                     'health<br>st/ur/sk/pcv', \
                     'fluid<br>(work+sup+fruit)', \
                     'fruit', 'other']
    env['date0'] = date0
                    
    return env
