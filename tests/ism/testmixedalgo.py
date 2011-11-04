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
Test the ISM Algorithm
"""
from clmsequencer.ism.algo import order_mixed
from pygraph.classes.digraph import digraph

from tests.ism.abstracttest import AbstractISMAlgo
from tests.ism.tools import add_action
from tests.ise.tools import AssertModel

import random

class TestISMMixedAlgo(AbstractISMAlgo, AssertModel):
    """
    Test of ISM mixed algorithm
    """
    def setUp(self):
        self.order = order_mixed

    def test_seq_a_b_single_action(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        depgraph.add_edge(("a#ta", "b#tb"))
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, nb=2)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        self.assertNotEquals(seq, None)
        actions = self.assertSequence(seq, nb=2)
        self.assertAction(actions[0], id="b#tb/Rule", cs="b#tb", cmd="Cmd")
        self.assertAction(actions[1], id="a#ta/Rule", cs="a#ta", cmd="Cmd")

    def test_seq_a_b_n_actions(self):
        depgraph = digraph()
        na = random.randint(5, 10)
        actions = []
        for i in range(0, na):
            actions.append(("Rule"+str(i), "Cmd"+str(i)))

        add_action(depgraph, "a#ta", actions)

        nb = random.randint(5, 10)
        actions = []
        for i in range(0, nb):
            actions.append(("Rule"+str(i), "Cmd"+str(i)))

        add_action(depgraph, "b#tb", actions)
        depgraph.add_edge(("a#ta", "b#tb"))

        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, na+nb)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        self.assertNotEquals(seq, None)
        seqs = self.assertSequence(seq, nb=2)
        seqb = seqs[0]
        actions_b = self.assertSequence(seqb, nb=nb)
        for i in range(0, nb):
            self.assertAction(actions_b[i], id="b#tb/Rule"+str(i), cs="b#tb", cmd="Cmd"+str(i))

        seqa = seqs[1]
        actions_a = self.assertSequence(seqa, nb=na)
        for i in range(0, na):
            self.assertAction(actions_a[i], id="a#ta/Rule"+str(i), cs="a#ta", cmd="Cmd"+str(i))

    def test_par_a_b_single_action(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, nb=2)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        par = instructions.pop()
        self.assertNotEquals(par, None)
        actions = self.assertParallel(par, nb=2)
        self.assertAction(actions[0], id="a#ta/Rule", cs="a#ta", cmd="Cmd")
        self.assertAction(actions[1], id="b#tb/Rule", cs="b#tb", cmd="Cmd")

    def test_par_a_b_n_actions(self):
        depgraph = digraph()
        na = random.randint(5, 10)
        actions = []
        for i in range(0, na):
            actions.append(("Rule"+str(i), "Cmd"+str(i)))

        add_action(depgraph, "a#ta", actions)

        nb = random.randint(5, 10)
        actions = []
        for i in range(0, nb):
            actions.append(("Rule"+str(i), "Cmd"+str(i)))

        add_action(depgraph, "b#tb", actions)
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, na+nb)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        par = instructions.pop()
        self.assertNotEquals(par, None)
        seqs = self.assertParallel(par, nb=2)
        seqa = seqs[0]
        actions_a = self.assertSequence(seqa, nb=na)
        for i in range(0, na):
            self.assertAction(actions_a[i], id="a#ta/Rule"+str(i), cs="a#ta", cmd="Cmd"+str(i))

        seqb = seqs[1]
        actions_b = self.assertSequence(seqb, nb=nb)
        for i in range(0, nb):
            self.assertAction(actions_b[i], id="b#tb/Rule"+str(i), cs="b#tb", cmd="Cmd"+str(i))

    def test_a_dep_b_c(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        add_action(depgraph, "c#tc")
        depgraph.add_edge(("a#ta", "b#tb"))
        depgraph.add_edge(("a#ta", "c#tc"))
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 3)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        self.assertNotEquals(seq, None)
        instructions = self.assertSequence(seq, nb=2)
        par = instructions[0]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "b#tb/Rule")
        self.assertContainsAction(actions, "c#tc/Rule")
        action = instructions[1]
        self.assertAction(action, id="a#ta/Rule", cs="a#ta")

    def test_a_b_dep_c(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        add_action(depgraph, "c#tc")
        depgraph.add_edge(("a#ta", "c#tc"))
        depgraph.add_edge(("b#tb", "c#tc"))
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 3)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        instructions = self.assertSequence(seq, nb=2)
        action = instructions[0]
        self.assertAction(action, id="c#tc/Rule")
        par = instructions[1]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "a#ta/Rule")
        self.assertContainsAction(actions, "b#tb/Rule")

    def test_a_b_c_d_square(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        add_action(depgraph, "c#tc")
        add_action(depgraph, "d#td")
        depgraph.add_edge(("a#ta", "b#tb"))
        depgraph.add_edge(("a#ta", "d#td"))
        depgraph.add_edge(("c#tc", "b#tb"))
        depgraph.add_edge(("c#tc", "d#td"))
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 4)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        instructions = self.assertSequence(seq, nb=2)
        par = instructions[0]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "b#tb/Rule")
        self.assertContainsAction(actions, "d#td/Rule")
        par = instructions[1]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "a#ta/Rule")
        self.assertContainsAction(actions, "c#tc/Rule")

    def test_complex_case_a_b_c_f_e_d_diamond(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta")
        add_action(depgraph, "b#tb")
        add_action(depgraph, "c#tc")
        add_action(depgraph, "d#td")
        add_action(depgraph, "e#te")
        add_action(depgraph, "f#tf")


        depgraph.add_edge(("a#ta", "b#tb"))
        depgraph.add_edge(("a#ta", "c#tc"))

        depgraph.add_edge(("d#td", "e#te"))
        depgraph.add_edge(("d#td", "f#tf"))

        depgraph.add_edge(("f#tf", "b#tb"))
        depgraph.add_edge(("c#tc", "e#te"))

        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 6)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        seq = instructions.pop()
        instructions = self.assertSequence(seq, nb=3)
        par = instructions[0]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "b#tb/Rule")
        self.assertContainsAction(actions, "e#te/Rule")
        par = instructions[1]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "f#tf/Rule")
        self.assertContainsAction(actions, "c#tc/Rule")
        par = instructions[2]
        actions = self.assertParallel(par, nb=2)
        self.assertContainsAction(actions, "a#ta/Rule")
        self.assertContainsAction(actions, "d#td/Rule")

