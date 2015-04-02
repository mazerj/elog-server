# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

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

def safeint(x):
    try:
        return int(round(x))
    except TypeError:
        return 'ND'

def uniq(s): return list(set(s))

