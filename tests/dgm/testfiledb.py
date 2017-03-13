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
import tempfile

from sequencer.dgm.db import SequencerFileDB
from tests.dgm.abstracttestdb import AbstractDGMDBTest
from tests.dgm.tools import AssertDB

_DELETE_TMP_FILE = True

class TestDGMFileDB(AbstractDGMDBTest, AssertDB):
    def setUp(self):
        AssertDB.setUp(self)
        self.basedir = tempfile.mkdtemp(suffix='tmp', prefix='testfiledb')
        self.db = SequencerFileDB(self.basedir)
        self.db.create_table()

    def tearDown(self):
#        self.db.drop_table()
        AssertDB.tearDown(self)

