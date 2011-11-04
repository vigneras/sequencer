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
from __future__ import print_function

import tempfile

import lxml.etree
from clmsequencer.commons import CyclesDetectedError, output_graph
from clmsequencer.ise.errors import UnknownDepsError, BadDepError
from clmsequencer.ise import model
from clmsequencer.ise.parser import ISE,SEQ,PAR,ACTION

from tests.ise.tools import AssertModel


class TestISEModelBasic(AssertModel):
    """Test Basic ISE Models."""

    def _check_empty(self, doc, model_type, expected_desc):

        print(lxml.etree.tostring(doc, pretty_print=True))
        empty_model = model.Model(doc)
        print(empty_model.actions)
        print(empty_model.deps)
        self.assertActionsNb(empty_model, 0)
        self.assertEquals(len(empty_model.deps), 0)
        instructions = empty_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        instruction = instructions.pop()
        self.assertTrue(isinstance(instruction, model_type))
        self.assertEquals(expected_desc, instruction.description)
        instructions = instruction.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 0)


    def test_EmptySequence(self):

        # Create an empty sequence
        doc = ISE(SEQ(desc="SeqDesc"))
        self._check_empty(doc, model.Sequence, "SeqDesc")

    def test_EmptyParallel(self):

        # Create an empty parallel
        doc = ISE(PAR(desc="ParDesc"))
        self._check_empty(doc, model.Parallel, "ParDesc")

    def _check4Simple(self, doc, modelType,
                      expectedDesc,
                      expectedActionCMD,
                      expectedActionId,
                      expectedActionCS,
                      expectedActionDesc):

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 1)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        instruction = instructions.pop()
        self.assertTrue(isinstance(instruction, modelType))
        self.assertEquals(expectedDesc, instruction.description)
        instructions = instruction.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        action = instructions.pop()
        self.assertTrue(isinstance(action, model.Action))
        self.assertAction(action,
                          id=expectedActionId,
                          cmd=expectedActionCMD,
                          cs=expectedActionCS,
                          desc=expectedActionDesc)

    def test_SimpleSequence(self):

        doc = ISE(SEQ(ACTION("ActionCMD",
                             id="ActionID",
                             component_set="ActionCS",
                             desc="ActionDesc"),
                      desc="SeqDesc"))
        self._check4Simple(doc,
                           model.Sequence,
                           "SeqDesc",
                           "ActionCMD",
                           "ActionID",
                           "ActionCS",
                           "ActionDesc")

    def test_SimpleParallel(self):

        # Create a parallel with one action
        doc = ISE(PAR(ACTION("ActionCMD",
                             id="ActionID",
                             component_set="ActionCS",
                             desc="ActionDesc"),
                      desc="ParDesc"))
        self._check4Simple(doc,
                           model.Parallel,
                           "ParDesc",
                           "ActionCMD",
                           "ActionID",
                           "ActionCS",
                           "ActionDesc")

    def test_RemoteFlagInAction(self):
        # We choose a PAR here, it may be changed to a SEQ. It should
        # not matter since SEQ and PAR models are already checked by
        # previous tests.
        doc = ISE(PAR(ACTION("Action1",
                             id="id1",
                             remote="false"),
                      ACTION("Action2",
                             id="id2",
                             remote="true")))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 2)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        instruction = instructions.pop()
        self.assertTrue(isinstance(instruction, model.InstructionsContainer))
        instructions = instruction.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 2)
        action = instructions[0]
        self.assertAction(action, id="id1", remote=False)
        action = instructions[1]
        self.assertAction(action, id="id2", remote=True)

    def test_ForceFlagInAction(self):
        doc = ISE(ACTION("Action1",
                         id="id1",
                         force="allowed"),
                  ACTION("Action2",
                         id="id2",
                         force="never"),
                  ACTION("Action3",
                         id="id3",
                         force="always"),
                  ACTION("Action4",
                         id="id4"))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 4)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 4)
        action = instructions[0]
        self.assertAction(action, id="id1", force='allowed')
        action = instructions[1]
        self.assertAction(action, id="id2", force='never')
        action = instructions[2]
        self.assertAction(action, id="id3", force='always')
        action = instructions[3]
        self.assertAction(action, id="id4", force='allowed')

class TestISEModelDep(AssertModel):
    """Test  ISE Models with Explicit Dependencies."""

    def _checkCycleDetection(self, doc, expectedCycles):
        print(lxml.etree.tostring(doc, pretty_print=True))
        try:
            aModel = model.Model(doc)
            # This is not normal! It should fail!
            # Get the graph for debugging purpose
            graph = aModel.dag
            deleteTmpFile = False
            self.fail("CyclesDetectedError not raised! I was expecting cycles: " +
                      str(expectedCycles))
        except CyclesDetectedError as error:
            graph = error.graph
            # If debugging is required, just change this to True
            deleteTmpFile = True
            print("Detected cycle: " + str(error.cycle))
            print("Cycles expected: " + str(expectedCycles))
            scc = error.get_all_cycles()
            print("SCC: " + str(scc))
#           self.assertEquals(expectedCycles, scc.values())
        finally:
            dfs, dot = output_graph(graph)
            print("Corresponding depth-first search is: " + str(dfs))
            file = tempfile.NamedTemporaryFile(suffix=".dot",
                                               prefix=self.__class__.__name__ + "-",
                                               delete=deleteTmpFile)
            print("DOT File is: " + file.name +
                  ". Use Graphviz dotty command for its visualisation.")
            print(dot, file=file)

    def test_uselessDep(self):
        """
        Check for explicit dependency that is already an implicit one
        """
        doc = ISE(SEQ(ACTION("Action1", id="id1"),
                      ACTION("Action2", id="id2", deps="id1")))
        print(lxml.etree.tostring(doc, pretty_print=True))
        try:
            model.Model(doc)
            self.fail("BadDepError not raised! I was expecting dep: (id2, id1)")
        except BadDepError as error:
            self.assertEquals(['id2', 'id1'], error.bad_dep,
                            "Bad Dep is: %s" % error.bad_dep)


    def test_unknownDeps(self):
        doc = ISE(PAR(ACTION("Action1", id="id1"),
                      ACTION("Action2", id="id2", deps="id1, id3, id4")))
        print(lxml.etree.tostring(doc, pretty_print=True))
        try:
            model.Model(doc)
            self.fail("UnknownDepsError not raised! I was expecting dep: id3, id4")
        except UnknownDepsError as error:
            self.assertTrue("id3" in error.unknown_deps)
            self.assertTrue("id4" in error.unknown_deps)

    def test_selfDepError(self):

        doc = ISE(SEQ(ACTION("Action1", id="id1", deps="id1")))
        self._checkCycleDetection(doc, [['id1', 'id1']])

    def test_simpleCycleError(self):

        doc = ISE(SEQ(ACTION("Action1", id="id1", deps="id2"),
                      ACTION("Action2", id="id2")))
        self._checkCycleDetection(doc, [['id1','id2']])

    def test_SimpleDepAction(self):

        doc = ISE(ACTION("Action1", id="id1"),
                  ACTION("Action2", id="id2"),
                  ACTION("Action3", id="id3", deps="id1, id2"))
        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 3)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 3)
        a = instructions[0]
        self.assertAction(a, id="id1")
        a = instructions[1]
        self.assertAction(a, id="id2")
        a = instructions[2]
        self.assertAction(a, id="id3", deps=set(['id1', 'id2']))

    def test_MultipleCyclesDetectionSimpleSequence(self):
        doc = ISE(SEQ(ACTION("Action1", id="id1", deps="id2"),
                      ACTION("Action2", id="id2", deps="id3"),
                      ACTION("Action2", id="id3")))
        self._checkCycleDetection(doc, [['id1','id2'], ['id2', 'id3']])

    def test_ComplexDepPar(self):
        doc = ISE(PAR(SEQ(PAR(ACTION("Action3", id="id3"),
                              ACTION("Action4", id="id4", deps="id5")),
                          ACTION("Action1", id="id1")),
                      SEQ(PAR(ACTION("Action5", id="id5"),
                              ACTION("Action6", id="id6", deps="id3")),
                          ACTION("Action2", id="id2"))))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 6)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        par = instructions.pop()
        seqs = self.assertParallel(par, nb=2)
        self.assertNotEquals(seqs, None)
        self.assertEquals(len(seqs), 2)

        # First branch
        seq = seqs[0]
        instructions = self.assertSequence(seq, 2)
        par = instructions[0]
        actions = self.assertParallel(par, 2)
        self.assertAction(actions[0], id="id3", cmd="Action3")
        self.assertAction(actions[1], id="id4", cmd="Action4")
        action = instructions[1]
        self.assertAction(action, id="id1", cmd="Action1")

        # Second branch
        seq = seqs[1]
        instructions = self.assertSequence(seq, 2)
        par = instructions[0]
        actions = self.assertParallel(par, 2)
        self.assertAction(actions[0], id="id5", cmd="Action5")
        self.assertAction(actions[1], id="id6", cmd="Action6")
        action = instructions[1]
        self.assertAction(action, id="id2", cmd="Action2")

    def test_CyclesInComplexDepPar(self):
        doc = ISE(PAR(SEQ(PAR(ACTION("Action3", id="id3"),
                              ACTION("Action4", id="id4", deps="id5, id1")),
                          ACTION("Action1", id="id1")),
                      SEQ(PAR(ACTION("Action5", id="id5"),
                              ACTION("Action6", id="id6", deps="id3, id2")),
                          ACTION("Action2", id="id2"))))

        self._checkCycleDetection(doc, [['id4','id1'], ['id6', 'id2']])


    def test_ComplexDepSeq(self):
        doc = ISE(SEQ(PAR(SEQ(ACTION("Action3", id="id3"),
                              ACTION("Action4", id="id4", deps="id1")),
                          ACTION("Action1", id="id1")),
                      PAR(SEQ(ACTION("Action5", id="id5"),
                              ACTION("Action6", id="id6", deps="id3")),
                          ACTION("Action2", id="id2"))))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 6)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        pars = self.assertSequence(seq, nb=2)
        self.assertNotEquals(pars, None)
        self.assertEquals(len(pars), 2)

        # First branch
        par = pars[0]
        instructions = self.assertParallel(par, 2)
        seq = instructions[0]
        actions = self.assertSequence(seq, 2)
        self.assertAction(actions[0], id="id3", cmd="Action3")
        self.assertAction(actions[1], id="id4", cmd="Action4")
        action = instructions[1]
        self.assertAction(action, id="id1", cmd="Action1")

        # Second branch
        par = pars[1]
        instructions = self.assertParallel(par, 2)
        seq = instructions[0]
        actions = self.assertSequence(seq, 2)
        self.assertAction(actions[0], id="id5", cmd="Action5")
        self.assertAction(actions[1], id="id6", cmd="Action6")
        action = instructions[1]
        self.assertAction(action, id="id2", cmd="Action2")


    def test_CyclesInComplexDepSeq(self):
        doc = ISE(SEQ(PAR(SEQ(ACTION("Action3", id="id3"),
                              ACTION("Action4", id="id4", deps="id5, id1")),
                          ACTION("Action1", id="id1")),
                      PAR(SEQ(ACTION("Action5", id="id5"),
                              ACTION("Action6", id="id6", deps="id3, id2")),
                          ACTION("Action2", id="id2"))))

        self._checkCycleDetection(doc, [['id4','id5'], ['id6', 'id2']])


class TestISEModelTree(AssertModel):
    """Test ISE Models with a tree architecture."""

    def test_S_APA(self):
        """ A sequence composed of an action, a parallel (with 2
        actions) and an action """

        doc = ISE(SEQ(
                ACTION("Action1"),
                PAR(ACTION("Action2"), ACTION("Action3")),
                ACTION("Action4")))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 4)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        instructions = self.assertSequence(seq, 3)
        self.assertAction(instructions[0], cmd="Action1")
        par = instructions[1]
        actions = self.assertParallel(par, 2)
        self.assertAction(instructions[2], cmd="Action4")
        self.assertAction(actions[0], cmd="Action2")
        self.assertAction(actions[1], cmd="Action3")

    def test_P_ASA(self):
        """ A parallel composed of an action, a sequence (with 2
        actions) and an action """

        doc = ISE(PAR(
                ACTION("Action1"),
                SEQ(ACTION("Action2"), ACTION("Action3")),
                ACTION("Action4")))

        print(lxml.etree.tostring(doc, pretty_print=True))
        a_model = model.Model(doc)
        self.assertActionsNb(a_model, 4)
        instructions = a_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        par = instructions.pop()
        instructions = self.assertParallel(par, 3)
        self.assertAction(instructions[0], cmd="Action1")
        actions = self.assertSequence(instructions[1], 2)
        self.assertAction(instructions[2], cmd="Action4")
        self.assertAction(actions[0], cmd="Action2")
        self.assertAction(actions[1], cmd="Action3")



