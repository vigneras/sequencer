# -*- coding: utf-8 -*-
###############################################################################
# Copyright (C) Bull S.A.S (2010, 2011)
# Contributor: Pierre Vignéras <pierre.vigneras@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################
"""
Test the SequencerDB API
"""
import io
import os
import sqlite3
import tempfile

from sequencer.dgm.db import SequencerSQLDB

from abstracttestdb import AbstractDGMDBTest
from tests.commons import SQLiteDB
from tests.dgm.tools import AssertDB


_DELETE_TMP_FILE = True

class TestDGMSQLDB(AbstractDGMDBTest, AssertDB):
    def setUp(self):
        AssertDB.setUp(self)
        self.connection = sqlite3.connect(':memory:')
        cursor = self.connection.cursor()
        # Enables foreign_keys support in sqlite
        cursor.execute("PRAGMA foreign_keys = ON")
        self.connection.commit()
        # See the assert at the beginning of this module:
        # sqlite3.paramstyle == 'qmark'
        # This means the module uses '?'  as the SQL parameter format.
        self.db = SequencerSQLDB(SQLiteDB('memory', self.connection))
        self.db.create_table()

    def tearDown(self):
        with io.StringIO() as out:
            self.db.raw_db.dump(out)
            print "Table is: \n" + out.getvalue()
        self.db.drop_table()
        self.connection.close()
        AssertDB.tearDown(self)

    """
    Test the db checking system
    """
    def test_none_ruleset_forbidden(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("INSERT INTO sequencer VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (None, "none_ruleset_forbidden",
                            None, None, None, None, None, None))
            self.fail("None ruleset is forbidden in the DB")
        except sqlite3.DatabaseError as de:
            print "Exception is: %s" % de

    def test_none_rulename_forbidden(self):
        cursor = self.connection.cursor()
        try:
            cursor.execute("INSERT INTO sequencer VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (self.__class__.__name__, None,
                            None, None, None, None, None, None))
            self.fail("None rule name is forbidden in the DB")
        except sqlite3.DatabaseError as de:
            print "Exception is: %s" % de

    def test_dump(self):
        tmpfile = tempfile.NamedTemporaryFile(suffix=".tmp",
                                              prefix=self.__class__.__name__ + "-",
                                              delete=_DELETE_TMP_FILE)
        name = tmpfile.name
        with  tmpfile:
            if not _DELETE_TMP_FILE:
                print "Dumping to %s" % name
            self.db.raw_db.dump(tmpfile)
            tmpfile.flush()
            stat = os.stat(name)
            self.assertTrue(stat.st_size > 0, stat.st_size)


    def test_update_ruleset_deps_multiple(self):
        """
        Override this test: it does not work with SQLDB and since we
        move to file based db, we no longer try to fix it.
        """
        pass
