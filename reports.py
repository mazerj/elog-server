# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os
import string
import types
import datetime, time

from dbtools import getdb
from apptools import *

import numpy as np

from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.io import gridplot
from bokeh.models.formatters import DatetimeTickFormatter
import pandas as pd
import bokeh.palettes
TOOLS = "hover,crosshair,pan,wheel_zoom,box_zoom,reset"

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
					   """<span class="glyphicon glyphicon-eye-open"></span></a> %s""") % (animal, date, datestr)
			
			rows = db.query("""SELECT * """
							""" FROM session WHERE """
							""" date='%s' AND """
							""" animal LIKE "%s" """ % (date, animal))
			
			if rows is None or len(rows) == 0:
				link = (""" <a class="btn-sm btn-danger hidden-print pull-right" """
					"""href="/animals/%s/sessions/%s/new">%s</a>""") % \
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

    Returns date and data info seperately with dates as pandas Timestamps
	"""
	db = getdb()
	
	rs = db.query("""SELECT * FROM session WHERE """
				  """  animal='%s' """
				  """  ORDER BY date """ % (animal,))

    dates = np.array([pd.Timestamp('%s'%r['date']) for r in rs])
	
	m = np.zeros((len(rs), 4))
    dlist = []
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

		dlist.append(dates[n])
		m[n, 0] = dtb
		m[n, 1] = dtb_ml
		m[n, 2] = xdtb
		m[n, 3] = xdtb_ml
	return dlist, m

def tt(start=None, label=None):
    import time
    if start:
        print "%s: %fms" % (label, 1000*(time.time() - start),)
    else:
        return time.time()
	
def fluid_report(animal):
	db = getdb()

	rows = db.query("""SELECT date,water_sup,water_work,fruit_ml,weight """
					""" FROM session """
					""" WHERE animal='%s' AND """
					""" date > DATE_SUB(NOW(), INTERVAL 90 DAY) """
					""" ORDER BY date """ % animal)
	md, m = dtbhist(animal)

    cpal = bokeh.palettes.Set2[3]

	plots = []
    if len(rows) > 0:
		p = figure(title="%s: last 90d - ml" % animal, \
					   plot_width=500, plot_height=300,
					   x_axis_type='datetime', tools=TOOLS)
		p.yaxis.axis_label = 'Fluid Intake (ml)'
		p.xaxis.axis_label = 'Date'

		x = np.array([pd.Timestamp('%s'%r['date']) for r in rows])
		wt = np.array([safefloat(r['weight']) for r in rows])
        wt[wt == 0] = np.nan
		ytotal = np.array([safefloat(r['water_work']) +
						   safefloat(r['water_sup']) +
						   safefloat(r['fruit_ml']) for r in rows])
		ywork = np.array([safefloat(r['water_work']) for r in rows])

		p.circle(x[np.nonzero(ytotal)], ytotal[np.nonzero(ytotal)], \
					 color=cpal[0])
		p.triangle(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)], \
					   color=cpal[1])
        
        mx,my,mc = [],[],[]
		for n in range(len(x)):
			if ywork[n] > 0:
                mx.append(np.take(x,[n, n]))
                my.append(np.array([ywork[n], ytotal[n]]))
                mc.append(cpal[0])
                
                mx.append(np.take(x, [n, n]))
                my.append(np.array([ywork[n], 0]))
                mc.append(cpal[1])

			else:
                mx.append(np.take(x, [n, n]))
                my.append(np.array([0, ytotal[n]]))
                mc.append(cpal[0])
        p.multi_line(mx, my, color=mc)

		dtbx = []
		dtby = []
		for n in range(m.shape[0]):
			if md[n] > x[0]:
				dtbx.append(md[n])
				dtby.append(m[n,3])
		p.circle(np.array(dtbx), np.array(dtby), color=cpal[2], legend='dtb')
				
		sx, sy = smooth(x[np.nonzero(ytotal)], ytotal[np.nonzero(ytotal)])
		p.line(np.array(sx), np.array(sy), line_color=cpal[0], line_width=3, legend='total')
		sx, sy = smooth(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)]);
		p.line(np.array(sx), np.array(sy), line_color=cpal[1], line_width=3, legend='work')

        p.ygrid.band_fill_alpha = 0.25
        p.ygrid.band_fill_color = cpal[-1]        
        p.legend.location = 'top_left'
		plots.append(p)

		wt = np.array([safefloat(r['weight']) for r in rows])
        wt[wt == 0] = np.nan
		ytotal = ytotal / wt
		ywork = ywork / wt

		p = figure(title="%s: last 90d - ml/kg" % animal, \
					   plot_width=500, plot_height=300, \
					   x_axis_type='datetime', tools=TOOLS)
		p.yaxis.axis_label = 'Fluid Intake (mg/kg)'
		p.xaxis.axis_label = 'Date'
					   
		p.circle(x[np.nonzero(ytotal)], ytotal[np.nonzero(ytotal)], color=cpal[0])
		p.triangle(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)], color=cpal[1])
        mx,my,mc = [],[],[]
		for n in range(len(x)):
			if ywork[n] > 0:
				mx.append(np.array((x[n], x[n])))
                my.append(np.array((ywork[n], ytotal[n])))
                mc.append(cpal[0])
                
				mx.append(np.array((x[n], x[n])))
                my.append(np.array((ywork[n], 0)))
                mc.append(cpal[1])
			else:
				mx.append(np.array((x[n], x[n])))
                my.append(np.array((0, ytotal[n])))
                mc.append(cpal[0])
        p.multi_line(mx, my, color=mc)

		sx, sy = smooth(x[np.nonzero(ytotal)], ytotal[np.nonzero(ytotal)])
		p.line(np.array(sx), np.array(sy), line_color=cpal[0], line_width=3, legend='total')
		sx, sy = smooth(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)]);
		p.line(np.array(sx), np.array(sy), line_color=cpal[1], line_width=3, legend='work')

        p.ygrid.band_fill_alpha = 0.25
        p.ygrid.band_fill_color = cpal[-1]
        p.legend.location = 'top_left'
		plots.append(p)

	rows = db.query("""SELECT * FROM session WHERE """
					""" animal='%s' ORDER BY date""" % animal)

	if len(rows) > 0:
		x = np.array([pd.Timestamp('%s'%r['date']) for r in rows])
		ytotal = np.array([safefloat(r['water_work']) +
						   safefloat(r['water_sup']) +
						   safefloat(r['fruit_ml']) for r in rows])
		ywork = np.array([safefloat(r['water_work']) for r in rows])

		p = figure(title="%s: all data" % animal, \
					   plot_width=500, plot_height=300, \
					   x_axis_type='datetime', tools=TOOLS)
		p.yaxis.axis_label = 'Fluid Intake (ml)'
		p.xaxis.axis_label = 'Date'

		p.line(md, m[:,3], line_color=cpal[2], line_width=3, legend='dtb')
        
		sx, sy = smooth(x, ytotal)
        p.triangle(x, ytotal, color=cpal[0])
		p.line(x, ytotal, line_color=cpal[0], line_width=3, legend='total')

		sx, sy = smooth(x[np.nonzero(ywork)], ywork[np.nonzero(ywork)])
		if len(sx) == len(sy):
			p.line(sx, sy, line_color=cpal[1], line_width=3, legend='work')
		else:
			p.line(x, ywork, line_color=cpal[1], line_width=3, legend='work')
            
        p.ygrid.band_fill_alpha = 0.25
        p.ygrid.band_fill_color = cpal[-1]
        p.legend.location = 'top_left'
        plots.append(p)
        plots.append(None)

	html = file_html(gridplot(plots, ncols=2), CDN, "%s fluids" % animal)
    
	return html

def weight_report(animal):
    db = getdb()

	rows = db.query("""SELECT date,weight,thweight FROM session WHERE """
					""" animal='%s' AND """
					""" weight > 0 AND """
					""" date > DATE_SUB(NOW(), INTERVAL 90 DAY) ORDER BY date""" % animal)

    cpal = bokeh.palettes.Set2[3]
    plots = []
	if len(rows) > 0:
        
		x = np.array([pd.Timestamp('%s'%r['date']) for r in rows])
		y = np.array([r['weight'] for r in rows])
        y[y == 0] = np.nan
		t = np.array([safefloat(r['thweight'],0.0) for r in rows])

		p = figure(title="%s: last 90d" % animal, \
					   plot_width=500, plot_height=300,
					   x_axis_type='datetime', tools=TOOLS)
		#p.yaxis.axis_label('Weight (kg)')
		#p.xaxis.axis_label('Date')
        
		p.line(x, y, line_color=cpal[1], line_width=3, legend='weight')
        p.circle(x, y, color=cpal[1])
		p.line(x[np.nonzero(t)], t[np.nonzero(t)], line_color=cpal[0], line_width=3, legend='thresh')
        
        p.legend.location = 'bottom_left'
        p.ygrid.band_fill_alpha = 0.25
        p.ygrid.band_fill_color = cpal[-1]

        plots.append(p)

	rows = db.query("""SELECT date,weight,thweight FROM session WHERE """
					""" animal='%s' AND """
					""" weight > 0 ORDER BY date""" % animal)
	
	if len(rows) > 0:
		x = np.array([pd.Timestamp('%s'%r['date']) for r in rows])
		y = np.array([r['weight'] for r in rows])
        y[y == 0] = np.nan
		t = np.array([safefloat(r['thweight'],0.0) for r in rows])

		p = figure(title="%s: all data" % animal, \
					   plot_width=500, plot_height=300,
					   x_axis_type='datetime', tools=TOOLS)
		#p.yaxis.axis_label('Weight (kg)')
		#p.xaxis.axis_label('Date')

		sx, sy = smooth(x, y)
		if len(sx) == len(sy):
			p.line(sx, sy, line_color=cpal[1], line_width=3, legend='weight', line_dash='dotted')
        else:
            p.line(x, y, line_color=cpal[1], line_width=3, legend='weight')
		p.circle(x, y, color=cpal[1])
		p.line(x[np.nonzero(t)], t[np.nonzero(t)], line_color=cpal[0], line_width=3, legend='thresh')
        
        p.legend.location = 'bottom_left'
        p.ygrid.band_fill_alpha = 0.25
        p.ygrid.band_fill_color = cpal[-1]

        plots.append(p)
		
	html = file_html(gridplot(plots, ncols=1), CDN, "%s fluids" % animal)
    
	return html
