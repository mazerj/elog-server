# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, os, types, string
import re, textwrap, datetime

sys.path.append(os.environ['ELOG_DIR'])
from elogapi import getdb

from app_tools import *

db = getdb()
rows = db.query("""SELECT animal FROM session WHERE 1""")
animals = sorted(list(set([row['animal'] for row in rows])))

for a in animals:
    d = { 'animal':a, 'user':'mazer', 'date':today() }
    db.query("""INSERT INTO animal (%s) VALUES %s""" % \
             (string.join(d.keys(), ','), tuple([d[k] for k in d.keys()]),))
    print a
