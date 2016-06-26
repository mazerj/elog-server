# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os
import string
import types
import datetime, time

from dbtools import getdb
from apptools import *

import matplotlib as mpl
mpl.use('Agg')						  # prevent Tk loading..
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import matplotlib.dates as mdates
import json


def iget(rows, name):
    if isinstance(rows[0][name], types.StringType):
        return 0
    else:
        return rows[0][name]

def ps(s):
    """return string or '-'
    """
    if len(s):
        try:
            x = float(s)
        except ValueError:
            return s
        if x == 0:
            return '-'
        else:
            return s
    else:
        return '-'

def monthly_report(startdate):
    db = getdb()
    
    env = {}
    # only do this for animals restricted during the specified month
    rows = db.query("""SELECT animal """
                    """ FROM session WHERE """
                    """ MONTH('%s') = MONTH(date) AND """
                    """ YEAR('%s') = YEAR(date) AND """
                    """ restricted > 0""" % (startdate, startdate,))

    env['animals'] = sorted(list(set([r['animal'] for r in rows])))
    env['data'] = {}
    
    DAYS = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')

    for animal in env['animals']:
        t = []
        for datenum in range(1,32):
            date = '%s%02d' % (startdate[:-2], datenum)
            try:
                dow = time.strptime(date, '%Y-%m-%d').tm_wday
            except ValueError:
                break
            x = '%s %s' % (DAYS[dow], date)
            if dow in (5,6):
                datestr = """<font color='blue'>%s</font>""" % x
            else:
                datestr = x
            datestr = ("""<a class="hidden-print btn-sm btn-primary" """
                       """href="/animals/%s/sessions/%s"> """
                       """<span class="glyphicon glyphicon-chevron-right"></span></a> %s""") % (animal, date, datestr)
            
            rows = db.query("""SELECT * """
                            """ FROM session WHERE """
                            """ date='%s' AND """
                            """ animal LIKE "%s" """ % (date, animal))
            
            if rows is None or len(rows) == 0:
                link = """ <a class="btn-sm btn-danger hidden-print pull-right" href="/animals/%s/sessions/%s/new">%s</a>""" % \
                  (animal, date, glyph('flag'))
                datestr = datestr + link

            if len(rows):
                tr = [datestr,]
                tr.append(ps('%s' % rows[0]['user']))
                tr.append(ps('%s' % rows[0]['weight']))
                tr.append(check(rows[0]['restricted']))
                tr.append(check(rows[0]['tested']))

                tr.append(check(rows[0]['health_stool']) +
                          check(rows[0]['health_urine']) +
                          check(rows[0]['health_skin']) +
                          check(rows[0]['health_pcv']))

                if rows[0]['restricted']:
                    ww = iget(rows,'water_work')
                    ws = iget(rows, 'water_sup')
                    wf = iget(rows, 'fruit_ml')
                    wt = ww + ws + wf
                    tr.append('%s (%s+%s+%s)' % (wt, ww, ws, wf))
                else:
                    tr.append('ad lib')
                tr.append(rows[0]['fruit'])
                l = rows[0]['note'].split('\n')[0]
                if len(l) and l[0] in '%#;%/!':
                    # if first line of note appears to be a "comment", put
                    # it in the other column..
                    tr.append(l[1:])
                else:
                    tr.append(' ')
            else:
                tr = ([datestr,] + [' '] * 8)
            t.append(tr)
        env['data'][animal] = t
    env['header'] = ['date', 'user', 'wt (kg)', 'rstrct', 'test', \
                     'health<br>(St/Ur/Sk/PCV)', \
                     'fluid<br>(work+sup+fruit)', \
                     'fruit', 'other']
    env['startdate'] = startdate

    return env

def dtbhist(animal, INTERVAL=7):
    """Generate matrix of DTB data for this animal.

    DTB is calculated by taking the last 7d of data and calculating
    the AVERAGE +- 2*STD:
        (working volume) / (weight)
    over the sampling interval. The 'regular' DTB is then clipped at
    10ml/kg (dtb10ml); this doesn't apply when animals are under VCS
    close monitor (mlab), so the raw DTB clipped to zero is also
    computed (dtb00ml) and plotted.
    """
    db = getdb()
    
    rs = db.query("""SELECT * FROM session WHERE """
                  """  animal='%s' """
                  """  ORDER BY date """ % (animal,))

    dates = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) \
                      for r in rs])
    
    m = np.zeros((len(rs), 5))
    for n in range(0, len(rs)):
        v = []
        for k in range(n-1, 0, -1):
            r = rs[k]
            if r['water_work'] and r['weight'] and \
              r['tested'] and r['restricted']:
                v.append(r['water_work']/r['weight'])
            if len(v) >= INTERVAL:
                break
        v = np.array(v)
        dtb = max(10.0, np.mean(v) - (2 * np.std(v)))
        if rs[n]['weight']:
            dtb_ml = round(dtb * rs[n]['weight'])
        else:
            dtb_ml = np.nan
        xdtb = max(0.0, np.mean(v) - (2 * np.std(v)))
        if rs[n]['weight']:
            xdtb_ml = round(xdtb * rs[n]['weight'])
        else:
            xdtb_ml = np.nan

        m[n, 0] = dates[n]
        m[n, 1] = dtb
        m[n, 2] = dtb_ml
        m[n, 3] = xdtb
        m[n, 4] = xdtb_ml
    return m
	
def fluid_report(animal):
	plots = []
	
	db = getdb()

	rows = db.query("""SELECT date,water_sup,water_work,fruit_ml """
					""" FROM session """
					""" WHERE animal='%s' AND """
					""" date > DATE_SUB(NOW(), INTERVAL 90 DAY) """
                    """ ORDER BY date """ % animal)
    m = dtbhist(animal)
    
	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date']) \
                      for r in rows])
		ytotal = np.array([safefloat(r['water_work']) +
                           safefloat(r['water_sup']) +
                           safefloat(r['fruit_ml']) for r in rows])
		ywork = np.array([safefloat(r['water_work']) for r in rows])
		plt.clf()

        # jitter points
        sx, sy = smooth(x, ytotal)
		plt.plot(x+.2, ytotal, 'rv')
        plt.plot(sx+.2, sy, 'r-', label='total')
        
        sx, sy = smooth(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)])
		plt.plot(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)], 'bo')
        if len(sx) == len(sy):
            # if lengths aren't the same, there's not enough to smooth
            plt.plot(sx, sy, 'b-', label='work')
        else:
            plt.plot(x, ywork, 'b-', label='work')

        plt.plot(m[np.greater(m[:,0], x[0]), 0],
                 m[np.greater(m[:,0], x[0]), 2], 'g-', label='dtb10ml')

        plt.plot(m[np.greater(m[:,0], x[0]), 0],
                 m[np.greater(m[:,0], x[0]), 4], 'g:', label='dtb00ml')

        
		plt.legend(loc='upper left')
		plt.gca().xaxis_date()
		plt.title('%s: last 90d' % animal)
		plt.ylabel('Fluid Intake (ml)')
		plots.append(('dummy%d'%len(plots),
                      json.dumps(mpld3.fig_to_dict(plt.gcf()))))
		
	rows = db.query("""SELECT * FROM session WHERE """
					""" animal='%s' ORDER BY date""" % animal)

	if len(rows) > 0:
		x = np.array([mdates.strpdate2num('%Y-%m-%d')('%s'%r['date'])
                      for r in rows])
		ytotal = np.array([safefloat(r['water_work']) +
                           safefloat(r['water_sup']) +
                           safefloat(r['fruit_ml']) for r in rows])
		ywork = np.array([safefloat(r['water_work']) for r in rows])

		plt.clf()

        # jitter points
        sx, sy = smooth(x, ytotal)
		plt.plot(x+.2, ytotal, 'rv')
        plt.plot(sx+.2, sy, 'r-', label='total')

        sx, sy = smooth(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)])
        plt.plot(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)], 'bo')
        if len(sx) == len(sy):
            plt.plot(sx, sy-1.0, 'b-', label='work')
        else
            plt.plot(x, ywork, 'b-', label='work')

        plt.plot(m[:,0], m[:,2], 'g-', label='dtb10ml')
        plt.plot(m[:,0], m[:,4], 'g-', label='dtb00ml')
        
		plt.legend(loc='upper left')
		plt.gca().xaxis_date()
		plt.title('%s: all data' % animal)
		plt.ylabel('Fluid Intake (ml)')
		plots.append(('dummy%d'%len(plots),
                      json.dumps(mpld3.fig_to_dict(plt.gcf()))))

    return plots

def weight_report(animal):
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
        sx, sy = smooth(x, y)
        if len(sx) == len(sy):
            plt.plot_date(sx, sy, 'b-')
        else:
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
        sx, sy = smooth(x, y)
        if len(sx) == len(sy):
            plt.plot_date(x, y, 'b-')
        else:
            plt.plot_date(x, y, 'b-')
        
		plt.title('%s: all data' % animal);
		plt.ylabel('Weight (kg)')
		plots.append(('dummy%d'%len(plots), json.dumps(mpld3.fig_to_dict(plt.gcf()))))
		
    return plots
