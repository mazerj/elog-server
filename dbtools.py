#!/usr/bin/python
# -*- Mode: Python; tab-width: 4; py-indent-offset: 4; -*-

import sys, MySQLdb

try:
    import dbsettings
except ImportError:
    sys.stderr.write('Please create dbsettings.py from template\n')
    sys.exit(1)

class Database(object):
    def __init__(self, quiet=True):
        self.host = dbsettings.HOST
        self.port = dbsettings.PORT
        self.db = dbsettings.DB
        self.user = dbsettings.USER
        self.passwd = dbsettings.PASS
        self.quiet = quiet
        self.connect()

    def __del__(self):
        self.close()

    def connect(self):
        try:
            self.connection = MySQLdb.connect(host=self.host,
                                              port=self.port,
                                              user=self.user,
                                              passwd=self.passwd,
                                              db=self.db)
            self.cursor = self.connection.cursor()
        except MySQLdb.OperationalError as (errno, errstr):
            sys.stderr.write("Can't connect to: '%s' %s@%s:%d\n" % \
                             (self.db, self.user, self.host, self.port,))
            sys.stderr.write('Error: %s\n' % errstr)
            self.connection = None
            sys.exit(1)

    def flush(self):
        self.connection.commit()

    def close(self):
        if self.connection:
            self.flush()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def query(self, cmd, *args):
        try:
            if not self.quiet:
                sys.stderr.write('cmd: <%s>\n' % cmd)
            result = []
            self.cursor.execute(cmd, *args)
            fields = self.cursor.description
            for row in self.cursor.fetchall():
                dict = {}
                for fnum in range(len(fields)):
                    if row[fnum] is None:
                        # value is NULL, use empty string to represent..
                        dict[fields[fnum][0]] = ''
                    else:
                        dict[fields[fnum][0]] = row[fnum]
                result.append(dict)
            return result
        except MySQLdb.Error, e:
            (number, msg) = e.args
            sys.stderr.write('SQL ERROR #%d: <%s>\nQUERY=<%s>\n' %
                             (number, msg, cmd))
            return None

def getdb(**kwargs):
    """Open mysql database and return handle.

    This is for programs or tools that want to directly query or
    manipulate the database. You can pass keyword args to the
    Database constructor as follows:

    quiet (bool) - print debugging info to stderr
    host (str)   - hostname ('sql.mlab.yale.edu')
    db (str)     - database name ('mlabdata')
    user (str)   - database user ('mlab')
    passwd (str) - database password for specified ('mlab')

    Defaults will provide the same level of access you get running
    the elog program.
    """
    return Database(**kwargs)

def GetExper(animal):
    """Query database for most recent 'exper'."""
    db = getdb()
    try:
        # get the last non-training exper for this animal from the database
        # by using LIKE for animal, this should handle prefixing correctly..
        rows = db.query("""SELECT exper FROM exper"""
                        """ WHERE animal LIKE '%s%%'"""
                        """ AND exper not like '%%0000'"""
                        """ ORDER BY exper DESC LIMIT 1""" %
                        (animal,))
        if rows is None:
            return None
    finally:
        db.close()

    if len(rows) == 0:
        return None
    else:
        return rows[0]['exper']

def GetNextExper(animal):
    """Get next sequential exper id."""
    e = GetExper(animal)
    if e is None:
        nextno = 1
    else:
        nextno = int(e[-4:]) + 1
    return "%s%04d" % (animal, nextno)
    
