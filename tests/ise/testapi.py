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
import io
import unittest

import lxml
from sequencer.ise.rc import ACTION_RC_KO, ACTION_RC_WARNING, \
    ACTION_RC_OK, ACTION_RC_UNEXECUTED
from sequencer.ise import api
from sequencer.ise.parser import ISE, SEQ, PAR, ACTION

from tests.ise import tools
from tests.ise.tools import AssertAPI


class TestISEAPIBasic(unittest.TestCase):
    """Basic check of the ISE API"""

    def _checkSimpleAction(self,
                           doc,
                           action_id,
                           expected_rc,
                           expected_std, expected_err):

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(expected_rc, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(1, len(actionsMap))
            self.assertTrue(action_id in actionsMap)
            action = actionsMap[action_id]
            self.assertEquals(action_id, action.id)
            self.assertEquals(expected_rc, action.rc)
            self.assertEquals(expected_std, action.stdout)
            self.assertEquals(expected_err, action.stderr)

    def test_EmptyAction(self):
        doc = ISE(SEQ(ACTION("", id="EmptyAction")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_OK, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(0, len(actionsMap))
            errorActionsMap = execution.error_actions
            self.assertEquals(1, len(errorActionsMap))
            self.assertTrue("EmptyAction" in errorActionsMap)
            action = errorActionsMap["EmptyAction"]
            self.assertEquals("EmptyAction", action.id)
            self.assertEquals(ACTION_RC_UNEXECUTED, action.rc)

    def test_SimpleSequenceActionOK(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleSequenceActionOK")))
        self._checkSimpleAction(doc,
                                "SimpleSequenceActionOK",
                                ACTION_RC_OK,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleSequenceActionKO(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleSequenceActionKO")))
        self._checkSimpleAction(doc,
                                "SimpleSequenceActionKO",
                                ACTION_RC_KO,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleSequenceActionWarning(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleSequenceActionWarning")))
        self._checkSimpleAction(doc,
                                "SimpleSequenceActionWarning",
                                ACTION_RC_WARNING,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleParallelActionOK(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleParallelActionOK")))
        self._checkSimpleAction(doc,
                                "SimpleParallelActionOK",
                                ACTION_RC_OK,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleParallelActionKO(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                              id="SimpleParallelActionKO")))
        self._checkSimpleAction(doc,
                                "SimpleParallelActionKO",
                                ACTION_RC_KO,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleParallelActionWarning(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleParallelActionWarning")))
        self._checkSimpleAction(doc,
                                "SimpleParallelActionWarning",
                                ACTION_RC_WARNING,
                                "Message2StdOut", "Message2StdErr")

    def test_SimpleRemote(self):
        """
        This test needs an SSH configuration that allows command to
        get executed on localhost without a password. Read ssh for
        details (or ClusterShell actually).
        """
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="SimpleRemote", remote="true",
                             component_set="localhost#compute")))
        self._checkSimpleAction(doc,
                                "SimpleRemote",
                                ACTION_RC_OK,
                                "localhost: Message2StdOut",
                                "localhost: Message2StdErr")

    def test_AggregatedRemote(self):
        """
        This test needs an SSH configuration that allows command to
        get executed on test1, test2, test3 without a password.


        You might consider writing into your ~/.ssh/config file the
        following to make it works:

        Host test1
              HostName localhost

        Host test2
              HostName localhost

        Host test3
              HostName localhost
        """
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="AggregatedRemote", remote="true",
                             component_set="test[1-3]#compute")))
        self._checkSimpleAction(doc,
                                "AggregatedRemote",
                                ACTION_RC_OK,
                                "test[1-3]: Message2StdOut",
                                "test[1-3]: Message2StdErr")

class TestISEAPIDep(AssertAPI):
    """
    Check dependency order between components is respected
    """

    def test_P_AA(self):

        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2", deps="1"),
                      desc="P_AA")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_OK, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(2, len(actionsMap))
            for i in range(1, 2):
                self.assertActionAttributes(actionsMap, str(i))

            a1 = actionsMap["1"]
            a2 = actionsMap["2"]
            self.assertTrue(a2.started_time > a1.ended_time)

class TestISEAPIErrorManagement(AssertAPI):
    """
    Check the management of errors during the execution of actions

    """

    def _test_SA_rc_A(self, rc):
        """ A sequence, where first action returns given rc -> next action
        should not be executed

        rc should be either WARNING or KO
        """

        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(rc,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      desc="SA_" + str(rc) + "_A")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            actionsMap = execution.executed_actions
            self.assertEquals(1, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("1" in execution.error_actions)
            action = actionsMap["1"]
            self.assertEquals(action.rc, rc)
            self.assertEquals(action.stdout, "A1.STD")
            self.assertEquals(action.stderr, "A1.ERR")


    def test_SA_KO_A(self):
        """ A sequence, where first action returns KO -> next action
        should not be executed

        """
        self._test_SA_rc_A(ACTION_RC_KO)

    def test_SA_W_A(self):
        """ A sequence, where first action returns WARNING -> next action
        should not be executed

        """

        self._test_SA_rc_A(ACTION_RC_WARNING)

    def _get_SA_W_A_Force_doc(self, force_attr):
        return ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                     "A1.STD", "A1.ERR"),
                              id="1",
                              force=force_attr),
                       ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                     "A2.STD", "A2.ERR"),
                              id="2"),
                       desc="SA_W_A_Force_" + force_attr)
                   )

    def _assert_SA_W_A_Force(self, doc, force_option, assert_dep_executed):
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader, force=force_option)
            actionsMap = execution.executed_actions
            self.assertTrue("1" in actionsMap)
            action = actionsMap["1"]
            self.assertEquals(action.rc, ACTION_RC_WARNING)
            self.assertEquals(action.stdout, "A1.STD")
            self.assertEquals(action.stderr, "A1.ERR")
            if assert_dep_executed:
                self.assertEquals(0, len(execution.error_actions))
                action = actionsMap["2"]
                self.assertEquals(action.rc, ACTION_RC_OK)
                self.assertEquals(action.stdout, "A2.STD")
                self.assertEquals(action.stderr, "A2.ERR")
            else:
                self.assertEquals(1, len(execution.error_actions))


    def test_SA_W_A_Force_Allowed(self):
        """ A sequence, where first action returns WARNING but with
        different force attribute and option -> next action *may not* be
        executed
        """

        doc = self._get_SA_W_A_Force_doc('allowed')
        self._assert_SA_W_A_Force(doc,
                                  False, # Option Force is false
                                  False) # Dep should not be executed

        self._assert_SA_W_A_Force(doc,
                                  True, # Option Force is true
                                  True) # Dep should not be executed

    def test_SA_W_A_Force_Always(self):
        doc = self._get_SA_W_A_Force_doc('always')
        self._assert_SA_W_A_Force(doc,
                                  False, # Option Force is false
                                  True) # Dep should be executed

        self._assert_SA_W_A_Force(doc,
                                  True, # Option Force is true
                                  True) # Dep should be executed

    def test_SA_W_A_Force_Never(self):
        doc = self._get_SA_W_A_Force_doc('never')
        self._assert_SA_W_A_Force(doc,
                                  False, # Option Force is false
                                  False) # Dep should not be executed

        self._assert_SA_W_A_Force(doc,
                                  True, # Option Force is true
                                  False) # Dep should not be executed



    def test_SAA_KO(self):
        """
        A sequence, where second action returns rc -> first action
        should have been executed

        rc should be KO or WARNING
        """

        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      desc="SAA_KO")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            actionsMap = execution.executed_actions
            self.assertEquals(2, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("2" in actionsMap)
            self.assertTrue("2" in execution.error_actions)
            action = actionsMap["1"]
            self.assertEquals(action.rc, ACTION_RC_OK)
            self.assertEquals(action.stdout, "A1.STD")
            self.assertEquals(action.stderr, "A1.ERR")
            action = actionsMap["2"]
            self.assertEquals(action.rc, ACTION_RC_KO)
            self.assertEquals(action.stdout, "A2.STD")
            self.assertEquals(action.stderr, "A2.ERR")

    def test_PA_KO_A(self):
        """
        A parallel, where first action returns KO -> next action
        should still be executed

        """

        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      desc="PA_KO_A")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            actionsMap = execution.executed_actions
            self.assertEquals(2, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("2" in actionsMap)
            self.assertTrue("1" in execution.error_actions)
            action = actionsMap["1"]
            self.assertEquals(action.rc, ACTION_RC_KO)
            self.assertEquals(action.stdout, "A1.STD")
            self.assertEquals(action.stderr, "A1.ERR")
            action = actionsMap["2"]
            self.assertEquals(action.rc, ACTION_RC_OK)
            self.assertEquals(action.stdout, "A2.STD")
            self.assertEquals(action.stderr, "A2.ERR")

    def test_PAA_KO(self):
        """
        A parallel, where second action returns KO -> first action
        should have been executed
        """

        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      desc="PAA_KO")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            actionsMap = execution.executed_actions
            self.assertEquals(2, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("2" in actionsMap)
            self.assertTrue("2" in execution.error_actions)
            action = actionsMap["1"]
            self.assertEquals(action.rc, ACTION_RC_OK)
            self.assertEquals(action.stdout, "A1.STD")
            self.assertEquals(action.stderr, "A1.ERR")
            action = actionsMap["2"]
            self.assertEquals(action.rc, ACTION_RC_KO)
            self.assertEquals(action.stdout, "A2.STD")
            self.assertEquals(action.stderr, "A2.ERR")


    def test_P_A_KO_A_Deps(self):
        """
        A parallel with two actions. The second action has an explicit
        dependency on the first one. The first one will fail.
        """

        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2", deps="1"),
                      desc="P_A_KO_A_Deps")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_KO, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(1, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("1" in execution.error_actions)
            a1 = actionsMap["1"]
            self.assertEquals(a1.rc, ACTION_RC_KO)
            self.assertEquals(a1.stdout, "A1.STD")
            self.assertEquals(a1.stderr, "A1.ERR")

    def test_P_A_Deps_A_KO(self):
        """
        A parallel with two actions. The first one has an explicit
        dependency on the last one. The last one will fail.

        This is not supported: any id referenced in a deps should be
        defined first in the document.

        """
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1", deps="2"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      desc="P_A_Deps_A_KO")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_KO, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(1, len(actionsMap))
            self.assertEquals(1, len(execution.error_actions))
            a1 = actionsMap["2"]
            self.assertEquals(a1.rc, ACTION_RC_KO)
            self.assertEquals(a1.stdout, "A2.STD")
            self.assertEquals(a1.stderr, "A2.ERR")

    def _test_P_A_rc_AA_Deps(self, rc):
        """
        A parallel with three actions. The last one has an explicit
        dependency on first ones. The first one will fail with rc
        (either WARNING or KO). Therefore, the second one should get
        executed, but not the third one.
        """
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(rc,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A3.STD", "A3.ERR"),
                             id="3", deps="1,2"),
                      desc="P_A_" + str(rc) + "_AA_Deps")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(rc, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(2, len(actionsMap), "actionsMap: %s" % actionsMap)
            self.assertEquals(1, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("2" in actionsMap)
            self.assertTrue("1" in execution.error_actions)
            a1 = actionsMap["1"]
            self.assertEquals(a1.rc, rc)
            self.assertEquals(a1.stdout, "A1.STD")
            self.assertEquals(a1.stderr, "A1.ERR")
            a2 = actionsMap["2"]
            self.assertEquals(a2.rc, ACTION_RC_OK)
            self.assertEquals(a2.stdout, "A2.STD")
            self.assertEquals(a2.stderr, "A2.ERR")

    def test_P_A_KO_AA_Deps(self):
        self._test_P_A_rc_AA_Deps(ACTION_RC_KO)

    def test_P_A_W_AA_Deps(self):
        self._test_P_A_rc_AA_Deps(ACTION_RC_WARNING)


    def test_P_A_W_AA_Deps_Force(self):
        """
        A parallel with three actions. The last one has an explicit
        dependency on first ones. The first one will fail with a
        WARNING but with force mode. Therefore, the second one should
        get executed, *and* also the third one.
        """
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A2.STD", "A2.ERR"),
                             id="2"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A3.STD", "A3.ERR"),
                             id="3", deps="1,2"),
                      desc="P_A_W_AA_Deps_Force")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader, force=True)
            self.assertEquals(ACTION_RC_WARNING, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(3, len(actionsMap), "actionsMap: %s" % actionsMap)
            self.assertEquals(0, len(execution.error_actions))
            self.assertTrue("1" in actionsMap)
            self.assertTrue("2" in actionsMap)
            self.assertTrue("3" in actionsMap)
            a1 = actionsMap["1"]
            self.assertEquals(a1.rc, ACTION_RC_WARNING)
            self.assertEquals(a1.stdout, "A1.STD")
            self.assertEquals(a1.stderr, "A1.ERR")
            a2 = actionsMap["2"]
            self.assertEquals(a2.rc, ACTION_RC_OK)
            self.assertEquals(a2.stdout, "A2.STD")
            self.assertEquals(a2.stderr, "A2.ERR")
            a3 = actionsMap["3"]
            self.assertEquals(a3.rc, ACTION_RC_OK)
            self.assertEquals(a3.stdout, "A3.STD")
            self.assertEquals(a3.stderr, "A3.ERR")

class TestISEAPITree(AssertAPI):
    """
    Check of the ISE API on simple Tree
    """

    def test_S_APA_OK(self):
        """ A sequence composed of an action, a parallel (with 2
        actions) and an action """

        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A2.STD", "A2.ERR"),
                                 id="2"),
                          ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A3.STD", "A3.ERR"),
                                 id="3")),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A4.STD", "A4.ERR"),
                                 id="4"),
                      desc="S_APA_OK")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_OK, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(4, len(actionsMap))
            self.assertEquals(0, len(execution.error_actions))

            for i in range(1, 5):
                self.assertActionAttributes(actionsMap, str(i))

            self._checkSAPAOrder(actionsMap)


    def _checkSAPAOrder(self, actionsMap):
        a1 = actionsMap["1"]
        a2 = actionsMap["2"]
        a3 = actionsMap["3"]
        a4 = actionsMap["4"]

        self.assertTrue(a2.started_time >= a1.ended_time)
        self.assertTrue(a3.started_time >= a1.ended_time)
        self.assertTrue(a4.started_time >= a2.ended_time)
        self.assertTrue(a4.started_time >= a3.ended_time)

    def test_P_ASA_OK(self):
        """
        A parallel composed of an action, a sequence (with 2
        actions) and an action
        """

        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "A1.STD", "A1.ERR"),
                             id="1"),
                      SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A2.STD", "A2.ERR"),
                                 id="2"),
                          ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A3.STD", "A3.ERR"),
                                 id="3")),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                        "A4.STD", "A4.ERR"),
                                 id="4"),
                      desc="P_ASA_OK")
                  )

        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            execution = api.execute(reader)
            self.assertEquals(ACTION_RC_OK, execution.rc)
            actionsMap = execution.executed_actions
            self.assertEquals(4, len(actionsMap))
            self.assertEquals(0, len(execution.error_actions))
            for i in range(1, 5):
                self.assertActionAttributes(actionsMap, str(i))

            self._checkPASAOrder(actionsMap)

    def _checkPASAOrder(self, actionsMap):
        a1 = actionsMap["1"]
        a2 = actionsMap["2"]
        a3 = actionsMap["3"]
        a4 = actionsMap["4"]

        self.assertTrue(a3.started_time > a2.ended_time)

