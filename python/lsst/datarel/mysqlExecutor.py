# 
# LSST Data Management System
# Copyright 2008, 2009, 2010 LSST Corporation.
# 
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the LSST License Statement and 
# the GNU General Public License along with this program.  If not, 
# see <http://www.lsstcorp.org/LegalNotices/>.
#

from __future__ import with_statement
from contextlib import closing
import getpass
import MySQLdb as sql
import optparse
import os
import subprocess
import sys
from lsst.daf.persistence import DbAuth


class MysqlExecutor(object):
    def __init__(self, host, database, user, port=3306, password=None):
        self.host = host
        self.port = port
        self.user = user
        self.database = database
        if password == None:
            if self.host is not None and self.port is not None and \
                    DbAuth.available(self.host, str(self.port)):
                self.user = DbAuth.username(self.host, str(self.port))
                password = DbAuth.password(self.host, str(self.port))
            elif not os.path.exists(os.path.join(os.environ['HOME'], ".my.cnf")):
                password = getpass.getpass("%s's MySQL password: " % user)
        self.password = password
        self.mysqlCmd = ['mysql', '-vvv']
        if host is not None:
            self.mysqlCmd += ['-h', self.host]
        if port is not None:
            self.mysqlCmd += ['-P', str(self.port)]
        if user is not None:
            self.mysqlCmd += ['-u', self.user]
        if password is not None:
            self.mysqlCmd += ["-p='" + self.password + "'"]

    def createDb(self, database):
        if not isinstance(database, basestring):
            raise TypeError('database name is not a string')
        cmd = list(self.mysqlCmd)
        cmd += ['-e', 'CREATE DATABASE %s;' % database]
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()

    def execStmt(self, stmt):
        if not isinstance(stmt, basestring):
            raise TypeError('SQL statement is not a string')
        cmd = list(self.mysqlCmd)
        if self.database is not None:
            cmd += ['-D', self.database]
        cmd += ['-e', stmt]
        subprocess.check_call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()

    def execScript(self, script):
        if not isinstance(script, basestring):
            raise TypeError('Script file name is not a string')
        if not os.path.isfile(script):
            raise RuntimeError(
                'Script %s does not exist or is not a file' % script)
        with open(script, 'rb') as f:
            cmd = list(self.mysqlCmd)
            if self.database is not None:
                cmd += ['-D', self.database]
            subprocess.check_call(cmd, stdin=f,
                    stdout=sys.stdout, stderr=sys.stderr)
            sys.stdout.flush()
            sys.stderr.flush()

    def runQuery(self, query):
        if not isinstance(query, basestring):
            raise TypeError('Query is not a string')
        kw = dict()
        if self.host is not None:
            kw['host'] = self.host
        if self.port is not None:
            kw['port'] = self.port
        if self.user is not None:
            kw['user'] = self.user
        if self.database is not None:
            kw['db'] = self.database
        if self.password is not None:
            kw['passwd'] = self.password
        with closing(sql.connect(**kw)) as conn:
            with closing(conn.cursor()) as cursor:
                print query
                sys.stdout.flush()
                cursor.execute(query)
                return cursor.fetchall()


def addDbOptions(parser):
    if not isinstance(parser, optparse.OptionParser):
        raise TypeError('Expecting an optparse.OptionParser')
    defUser = (os.environ.has_key('USER') and os.environ['USER']) or None
    parser.add_option(
        "-u", "--user", dest="user", default=defUser,
        help="MySQL database user name (%default).")
    parser.add_option(
        "-H", "--host", dest="host", default="lsst10.ncsa.uiuc.edu",
        help="MySQL database server hostname (%default).")
    parser.add_option(
        "-P", "--port", dest="port", type="int", default=3306,
        help="MySQL database server port (%default).")
