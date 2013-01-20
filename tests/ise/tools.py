# -*- coding: utf-8 -*-
###############################################################################
# Copyright (C) Bull S.A.S (2010, 2011)
# Contributor: Pierre Vignéras <pierre.vigneras@bull.net>
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
import os
import re

from sequencer.ise.rc import ACTION_RC_OK
from sequencer.ise import model
from sequencer.ise.parser import ACTION
from tests.commons import BaseTest


_ISE_TEST_DIR = os.path.dirname(__file__)
_MOCK_ACTION_SCRIPT_NAME = u"MockAction.py"

def getMockActionFullPath():
    return os.path.join(_ISE_TEST_DIR, _MOCK_ACTION_SCRIPT_NAME)

def getMockActionCmd(rc, msg_std, msg_err):
    return "python " + getMockActionFullPath() + " " + str(rc) \
        + " " + msg_std + " " + msg_err

def getActionXML(cmd="dummyCMD", id="dummyID",
                 component_set="dummyCS", desc="dummyDESC"):

    return ACTION(cmd, id=id, component_set=component_set, desc=desc)

class AssertModel(BaseTest):

    def assertActionsNb(self, model, nb):
        actions = model.actions
        self.assertNotEquals(actions, None)
        self.assertEquals(len(actions), nb)

    def assertContainer(self, container, nb=0):
        self.assertNotEquals(container, None)
        self.assertTrue(isinstance(container, model.InstructionsContainer),
                        "Found: " + str(container))
        if nb > 0:
            self.assertEquals(len(container.instructions), nb)
        return container.instructions

    def assertSequence(self, seq, nb=0):
        instructions = self.assertContainer(seq, nb)
        self.assertTrue(isinstance(seq, model.Sequence), "Found: " + str(seq))
        return instructions

    def assertParallel(self, par, nb=0):
        instructions = self.assertContainer(par, nb)
        self.assertTrue(isinstance(par, model.Parallel), "Found: " + str(par))
        return instructions

    def assertContainsAction(self, actions, id_):
        for action in actions:
            if action.id == id_:
                return action
        self.fail("Action %s not found in %s" % (id_, actions))

    def assertAction(self, action,
                     id=None,
                     cmd=None,
                     deps=None,
                     remote=None,
                     cs=None,
                     desc=None,
                     force=None):
        self.assertNotEquals(action, None)
        self.assertTrue(isinstance(action, model.Action), "Found: " + str(action))
        if id is not None:
            self.assertEquals(action.id, id)
        if cmd is not None:
            self.assertEquals(action.command, cmd)
        if deps is not None:
            self.assertEquals(action.deps, deps)
        if remote is not None:
            self.assertEquals(action.remote, remote)
        if cs is not None:
            self.assertEquals(action.component_set, cs)
        if desc is not None:
            self.assertEquals(action.description, desc)
        if force is not None:
            self.assertEquals(action.force, force)

class AssertAPI(BaseTest):
    def assertActionAttributes(self, actionsMap, key):
        self.assertTrue(key in actionsMap)
        action = actionsMap[key]
        self.assertEquals(action.rc, ACTION_RC_OK)
        self.assertEquals(action.stdout, "A" + key + ".STD")
        self.assertEquals(action.stderr, "A" + key + ".ERR")

class AssertCLI(BaseTest):
    def check(self, pattern, string):
        match = re.search(pattern, string, re.MULTILINE)
        self.assertTrue(match, "Can't find %s in string: %s" % (pattern, string))
        return match

    def _get_actions_list_from_header(self, header, output):
        header_match = self.check(header, output)
        # The actions list follow the header and ends with the empty string
        tmp = output[header_match.end() + 1:]
        list_match = re.search("^\s*$", tmp, re.MULTILINE)
        return tmp[:list_match.start()]


    def assertActionsInModel(self, output, ids=[]):
        header = r"^Actions in Model: %d\tLegend:.*" % len(ids)
        actions_list = self._get_actions_list_from_header(header, output)
        for id_ in ids:
            self.check(r"^\s+%s \| \s+.*\s+|\s+localhost\s*" % id_, actions_list)

    def assertExecutedActions(self, output, ids=[]):
        header = r"^Executed Actions: %d \(\d+\.\d+ %%\)\tLegend:.*" % len(ids)
        actions_list = self._get_actions_list_from_header(header, output)
        for id_ in ids:
            self.check(r"^\s+%s |\s+\d+:\d+:\d+\.\d+ |\s+.*" % id_, actions_list)

    def assertErrors(self, output, ids=[]):
        header = r"^Errors: %d \(\d+\.\d+ %%\)\tLegend:.*" % len(ids)
        actions_list = self._get_actions_list_from_header(header, output)
        for id_ in ids:
            self.check((r"^\s+%s |\s+\d+ |\s+.*$") % id_, actions_list)

    def assertUnexecutedActions(self, output, ids=[]):
        header = r"^Unexecuted Actions: %d \(\d+\.\d+ %%\)\tLegend:.*" % len(ids)
        actions_list = self._get_actions_list_from_header(header, output)
        for id_ in ids:
            self.check(r"^\s+%s |\s+\d+.*" % id_, actions_list)
