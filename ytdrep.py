# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

#
# Generate year-to-date reports as XLSX files for all animals on
# restriction during specified year. One tab per month/animal combo.
#

import sys, os, calendar
import xlsxwriter
from io import BytesIO

BOLD = None
CENTER = None

def ytd_rep_stream(db, year):
    """Generate excel file year-to-date summary for specified year.

    This is the only real externally visible function in this module!
    """

    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    BOLD = workbook.add_format({'bold': True,'align':'center','border':1})
    CENTER = workbook.add_format({'align':'center','border':1})
    npages = 0
    year = '%04d' % int(year)
    for m in range(1,13):
        npages += dump(db, workbook, '%s-%02d' % (year, m,))
    workbook.close()
    output.seek(0)
    return output


def emit(ws, s=None, fmt=None):
    try:
        xxxx = ws._rowno
    except:
        ws._rowno, ws._colno = 0, 0
            
    if s is not None:
        if fmt:
            ws.write(ws._rowno, ws._colno, s, fmt)
        else:
            ws.write(ws._rowno, ws._colno, s, CENTER)
        ws._colno = ws._colno + 1;
    else:
        ws._rowno = ws._rowno + 1;
        ws._colno = 0;

def s2i(s):
    """Convert string safely to int and back to string or - for ND"""
    try:
        return int(s)
    except:
        return ''
    
def s2f(s):
    """Convert string safely to float and back to string or - for ND"""
    try:
        return float(s)
    except:
        return ''
    
def s2yn(s):
    """Convert string safely to y/n flag or - for ND"""
    try:
        return 'NY'[int(s)]
    except:
        return ''
    
def s2num(s):
    """Convert string safely to number - 0.0 for ND"""
    try:
        return float(s)
    except:
        return 0.0

def s2wt(s):
    """Convert weight from log to string or - for ND -- 0kg is assumed ND"""
    s = s2num(s)
    if s == 0.0:
        return ''
    else:
        return s

def dump(db, workbook, monthstr):
    # what month are we dumping?
    year, month = map(int, monthstr.split('-'))
    start = '%04d-%02d-%02d' % (year, month, 1)
    stop = '%04d-%02d-%02d' % (year, month, 31)

    # first find all animals that were on restriction during that month
    rows = db.query("""SELECT * """
                    """ FROM session WHERE """
                    """ date >= '%s' AND date <= '%s' AND """
                    """ restricted > 0"""
                    """ ORDER BY date""" % (start, stop,))
    animals = list(set([r['animal'] for r in rows]))
    animals.sort()
    
    if len(animals) == 0:
        # no animals on restriction in the specified month
        return 0

    # exclude dummy animals -- this is a kludge..
    if 'tester' in animals:
        animals.remove('tester')
    if 'phred' in animals:
        animals.remove('phred')

    if len(animals) is 0:
        return

    for animal in animals:
        w = workbook.add_worksheet('%s-%s' % (monthstr, animal))

        # page title
        emit(w, '%s' % (animal,), BOLD)
        emit(w, '%s' % (monthstr,), BOLD)
        emit(w)
        
        # column headings
        emit(w, 'date', BOLD)
        emit(w, 'animal', BOLD)
        emit(w, 'user', BOLD)
        emit(w, 'wt', BOLD)
        emit(w, 'restict', BOLD)
        emit(w, 'test', BOLD)
        emit(w, 'stool', BOLD)
        emit(w, 'urine', BOLD)
        emit(w, 'skin', BOLD)
        emit(w, 'pcv', BOLD)
        emit(w, 'work ml', BOLD)
        emit(w, 'water ml', BOLD)
        emit(w, 'fruit ml', BOLD)
        emit(w, 'total ml', BOLD)
        emit(w)

        # step through each day in month and emit data for the current animal
        for day in range(1,calendar.monthrange(year,month)[1]+1):
            today = '%04d-%02d-%02d' % (year, month, day,)
            rows = db.query("""SELECT * """
                            """ FROM session WHERE """
                            """ date='%s' AND """
                            """ animal LIKE "%s" """ % (today, animal))
            
            emit(w, day)
            emit(w, r['animal'])
            if rows is not None and len(rows) > 0:
                r = rows[0]
                emit(w, r['user'])
                emit(w, s2wt(r['weight']))
                emit(w, s2yn(r['restricted']))
                emit(w, s2yn(r['tested']))
                emit(w, s2yn(r['health_stool']))
                emit(w, s2yn(r['health_urine']))
                emit(w, s2yn(r['health_skin']))
                emit(w, s2yn(r['health_pcv']))
                emit(w, s2i(r['water_work']))
                emit(w, s2i(r['water_sup']))
                emit(w, s2i(r['fruit_ml']))
                emit(w, s2num(r['water_work']) +
                         s2num(r['water_sup']) +
                         s2num(r['fruit_ml']))
            emit(w)
        emit(w)
        w.set_column('E:J', 4)
        return 1

