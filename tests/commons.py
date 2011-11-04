# -*- coding: utf-8 -*-
###############################################################################
# Copyright (C) Bull S.A.S (2010, 2011)
# Contributor: Pierre Vignéras <pierre.vigneras@bull.net>

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
###############################################################################
import unittest

import sys
from clmsequencer.commons import get_tracer, get_header, GenericDB
import re
import logging

_logger = logging.getLogger()

_formatter = logging.Formatter('%(relativeCreated)s %(levelname)s %(funcName)s() - %(message)s')
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)

class BaseTest(unittest.TestCase):
    """Base Test Class for all clmsequencer"""
    def setUp(self):
        _logger.debug(get_header(" Start %s " % self.id(), "*", 120))


    def tearDown(self):
#        _logger.debug(get_header(" Stop %s " % self.id(), "*", 80))
        pass

class BaseGraph(BaseTest):
    def assertNoEdgeBetween(self, graph, a, b):
        self.assertFalse(graph.has_edge((a, b)) or graph.has_edge((b,a)))


class SQLiteDB(GenericDB):
    def __init__(self, name, connection):
        GenericDB.__init__(self, name, connection, '?')
        self.connection.create_function("REGEXP", 2, self.regexp)

    @staticmethod
    def regexp(expr, item):
        reg = re.compile(expr)
        result = reg.search(item) is not None
        return result

    def sql_match_exp(self, column, re):
        return "%s REGEXP '%s'" % (column, re)


