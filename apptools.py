# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import numpy as np

def glyph(name):
    return """<span class="glyphicon glyphicon-%s" aria-hidden="true"></span> """ % name

def check(bool):
    if bool:
        return glyph('check')
    else:
        return glyph('unchecked')

def today(n=0):
    import datetime
    return (datetime.datetime.now() -
            datetime.timedelta(days=n)).strftime("%Y-%m-%d")

def safeint(x, default=0):
    try:
        return int(round(x))
    except TypeError:
        return default

def safefloat(x, default=0.0):
    try:
        return float(x)
    except (TypeError, ValueError):
        return default

def str2num(s, fn=int, default=0):
    try:
        return fn(s)
    except:
        return default
    
def uniq(s): return list(set(s))

def smooth(x, y, k=5):
    if len(x) > k:
        k = (2 * k) + 1
        ny = np.convolve(y, np.ones(k)/k, mode='same')
        return x,ny
    else:
        return x,y

