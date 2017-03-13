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
Unit test of the ISE CLI ('sequencer [options] seqexec [options]')
"""
import os
import tempfile
from subprocess import Popen, PIPE

import lxml
from sequencer.ise.rc import ACTION_RC_OK, ACTION_RC_WARNING, ACTION_RC_KO
from sequencer.ise.parser import ISE, PAR, SEQ, ACTION

import tools


BASE_DIR = os.path.join(tools._ISE_TEST_DIR, '../..')
BASE_DIR = os.path.normpath(BASE_DIR)
BIN_DIR = os.path.join(BASE_DIR, 'bin')
LIB_DIR = os.path.join(BASE_DIR, 'lib')
BIN_PATH = os.path.expandvars("$PATH:%s" % BIN_DIR)
PYTHON_PATH = os.path.expandvars("$PYTHONPATH:%s" % LIB_DIR)

class TestCLIBasic(tools.AssertCLI):
    """Basic check of the ISE CLI"""

    def test_NoArgsUsage(self):
        (output, error) = Popen(["sequencer"],
                                stdout=PIPE,
                                stderr=PIPE,
                                env={'PATH':BIN_PATH,
                                     'PYTHONPATH':PYTHON_PATH}
                                ).communicate()
        self.check(r"^Usage: sequencer \[global_options\] <action> \[action_options\] <action parameters>.*$",
                   error)

    def test_NoExec(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        process = Popen(["sequencer", "seqexec", "--doexec=no",
                         "--report", "all"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertActionsInModel(output, ids=["a"])


    def test_GraphTo(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        tmpfile = tempfile.NamedTemporaryFile(suffix=".dot.xml",
                                              prefix=self.__class__.__name__ + "-",
                                              delete=True)
        filename = tmpfile.name
        process = Popen(["sequencer", "seqexec",
                         "--actionsgraphto=%s"%filename],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertTrue(os.path.exists(filename))
        self.assertTrue(os.stat(filename).st_size > 0)

    def test_ExecOk(self):
        doc = ISE(PAR(ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        process = Popen(["sequencer", "seqexec", "--report", "all"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertActionsInModel(output, ids=["a"])
        self.assertExecutedActions(output, ids=["a"])
        self.assertErrors(output, ids=[])
        self.assertUnexecutedActions(output, ids=[])
        self.assertEquals(process.returncode, ACTION_RC_OK)

    def test_ExecWarning(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="b"),
                      desc="test_ExecWarning"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        process = Popen(["sequencer", "seqexec", "--report", "all"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertActionsInModel(output, ids=["a", "b"])
        self.assertExecutedActions(output, ids=["a"])
        self.assertErrors(output, ids=["a"])
        self.assertUnexecutedActions(output, ids=["b"])
        self.assertEquals(process.returncode, ACTION_RC_WARNING)

    def test_ExecWarningForce(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_WARNING,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="b"),
                      desc="test_ExecWarning"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        process = Popen(["sequencer", "seqexec",
                         "--Force", "--report", "all"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertActionsInModel(output, ids=["a", "b"])
        self.assertExecutedActions(output, ids=["a", "b"])
        self.assertErrors(output, ids=[])
        self.assertUnexecutedActions(output, ids=[])
        self.assertEquals(process.returncode, ACTION_RC_WARNING)

    def test_ExecError(self):
        doc = ISE(SEQ(ACTION(tools.getMockActionCmd(ACTION_RC_KO,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="a"),
                      ACTION(tools.getMockActionCmd(ACTION_RC_OK,
                                                    "Message2StdOut",
                                                    "Message2StdErr"),
                             id="b"),
                      desc="test_ExecWarning"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        process = Popen(["sequencer", "seqexec", "--report", "all"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=PIPE,
                        env={'PATH':BIN_PATH,
                             'PYTHONPATH':PYTHON_PATH}
                        )
        (output, error) = process.communicate(xml)
        print "Output: %s\nError: %s" % (output, error)
        self.assertActionsInModel(output, ids=["a", "b"])
        self.assertExecutedActions(output, ids=["a"])
        self.assertErrors(output, ids=["a"])
        self.assertUnexecutedActions(output, ids=["b"])
        self.assertEquals(process.returncode, ACTION_RC_KO)

