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
"""
Various Tools for the DB DGM API
"""
import os
import sqlite3

from sequencer.dgm.model import Rule, ALL

from tests.commons import BaseTest


assert sqlite3.paramstyle == 'qmark'

_DGM_TEST_DIR = os.path.dirname(__file__)
_MOCK_DEPSFINDER_SCRIPT_NAME = u"MockDepsFinder.py"

def getMockDepsFinderFullPath():
    return os.path.join(_DGM_TEST_DIR, _MOCK_DEPSFINDER_SCRIPT_NAME)

def getMockDepsFinderCmd(deps):
    return "python " + getMockDepsFinderFullPath() + " " + " ".join(deps)

def create_rule(ruleset,
                name,
                # Trailing comma is required!
                types=("unset@unset",),
                filter=ALL,
                action=None,
                depsfinder=None,
                dependson=set(),
                comments=""):

    return Rule(ruleset,
                name,
                types,
                filter,
                action,
                depsfinder,
                dependson,
                comments)

class AssertDB(BaseTest):
    def assertRuleInMap(self, rule, map_):
        self.assertTrue(rule.ruleset in map_,
                        "RS: %s, map_: %s" % (rule, map_))
        self.assertTrue(rule.name in map_[rule.ruleset],
                        "%s is not in %s" % (rule, map_[rule.ruleset]))

