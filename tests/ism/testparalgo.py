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
"""
Test the ISM Algorithm
"""
from sequencer.ism.algo import order_par_only
from pygraph.classes.digraph import digraph

from tests.ism.abstracttest import AbstractISMAlgo
from tests.ism.tools import add_action
from tests.ise.tools import AssertModel

import random

class TestISMParAlgo(AbstractISMAlgo, AssertModel):
    """
    Test of ISM par algorithm
    """
    order = staticmethod(order_par_only)

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
        par = instructions.pop()
        actions = self.assertParallel(par, nb=2)
        self.assertAction(actions[0], id="a#ta/Rule", cs="a#ta", cmd="Cmd",
                          deps=set(['b#tb/Rule']))
        self.assertAction(actions[1], id="b#tb/Rule", cs="b#tb", cmd="Cmd")

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
        par = instructions.pop()
        seqs = self.assertParallel(par, 2)
        seqa = self.assertSequence(seqs[0], na)
        for i in range(0, na):
            self.assertAction(seqa[i], id="a#ta/Rule"+str(i),
                              cs="a#ta", cmd="Cmd"+str(i))
        seqb = self.assertSequence(seqs[1], nb)
        for i in range(0, nb):
            self.assertAction(seqb[i], id="b#tb/Rule"+str(i),
                              cs="b#tb", cmd="Cmd"+str(i))

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
        seqs = self.assertParallel(par, 2)
        seqa = self.assertSequence(seqs[0], na)
        for i in range(0, na):
            self.assertAction(seqa[i], id="a#ta/Rule"+str(i),
                              cs="a#ta", cmd="Cmd"+str(i))

        seqb = self.assertSequence(seqs[1], nb)

        for i in range(0, nb):
            self.assertAction(seqb[i], id="b#tb/Rule"+str(i),
                              cs="b#tb", cmd="Cmd"+str(i))


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
        par = instructions.pop()
        actions = self.assertParallel(par, nb=3)
        self.assertContainsAction(actions, "a#ta/Rule")
        self.assertContainsAction(actions, "b#tb/Rule")
        self.assertContainsAction(actions, "c#tc/Rule")

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
        par = instructions.pop()
        actions = self.assertParallel(par, nb=3)
        a = self.assertContainsAction(actions, "a#ta/Rule")
        b = self.assertContainsAction(actions, "b#tb/Rule")
        c = self.assertContainsAction(actions, "c#tc/Rule")
        self.assertAction(a, id="a#ta/Rule", deps=set(['c#tc/Rule']))
        self.assertAction(b, id="b#tb/Rule", deps=set(['c#tc/Rule']))
        self.assertAction(c, id="c#tc/Rule", deps=set())

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
        par = instructions.pop()
        actions = self.assertParallel(par, nb=4)
        a = self.assertContainsAction(actions, "a#ta/Rule")
        b = self.assertContainsAction(actions, "b#tb/Rule")
        c = self.assertContainsAction(actions, "c#tc/Rule")
        d = self.assertContainsAction(actions, "d#td/Rule")
        self.assertAction(a, id="a#ta/Rule", deps=set(['b#tb/Rule', 'd#td/Rule']))
        self.assertAction(b, id="b#tb/Rule", deps=set())
        self.assertAction(c, id="c#tc/Rule", deps=set(['b#tb/Rule', 'd#td/Rule']))
        self.assertAction(d, id="d#td/Rule", deps=set())


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
        par = instructions.pop()
        actions = self.assertParallel(par, nb=6)

        a = self.assertContainsAction(actions, "a#ta/Rule")
        b = self.assertContainsAction(actions, "b#tb/Rule")
        c = self.assertContainsAction(actions, "c#tc/Rule")
        d = self.assertContainsAction(actions, "d#td/Rule")
        e = self.assertContainsAction(actions, "e#te/Rule")
        f = self.assertContainsAction(actions, "f#tf/Rule")

        self.assertAction(a, "a#ta/Rule", deps=set(['b#tb/Rule', 'c#tc/Rule']))
        self.assertAction(b, "b#tb/Rule", deps=set())
        self.assertAction(c, "c#tc/Rule", deps=set(['e#te/Rule']))
        self.assertAction(d, "d#td/Rule", deps=set(['e#te/Rule', 'f#tf/Rule']))
        self.assertAction(e, "e#te/Rule", deps=set())
        self.assertAction(f, "f#tf/Rule", deps=set(['b#tb/Rule']))


