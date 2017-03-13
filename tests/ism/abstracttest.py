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
Test the ISM Algorithm
"""
from sequencer.commons import CyclesDetectedError
from sequencer.ism.algo import REMOTE_CHAR
from pygraph.classes.digraph import digraph

from tests.ism.tools import add_action

import random

class AbstractISMAlgo(object):
    """
    Common tests for all ISM Algorithm
    """

    def test_empty_depgraph(self):
        depgraph = digraph()
        (ise_model, xml, error) = self.order(depgraph)
        self.assertTrue(len(ise_model.actions) == 0)

    def test_node_noaction(self):
        depgraph = digraph()
        depgraph.add_node("a#ta")
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 0)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 0)

    def test_a_nop(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        depgraph.add_node("nop#t")
        depgraph.add_edge(('a#ta', 'nop#t'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 1)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        a = instructions[0]
        self.assertAction(a, id="a#ta/Rule1", cs="a#ta", cmd="cmd1")

    def test_many2nop(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        add_action(depgraph, "b#tb", [("Rule2", "cmd2")])
        depgraph.add_node("nop#t")
        depgraph.add_edge(('a#ta', 'nop#t'))
        depgraph.add_edge(('b#tb', 'nop#t'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 2)
        self.assertTrue("a#ta/Rule1" in ise_model.actions)
        self.assertTrue("b#tb/Rule2" in ise_model.actions)

    def test_nop_a(self):
        depgraph = digraph()
        depgraph.add_node("nop#t")
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        depgraph.add_edge(('nop#t', 'a#ta'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 1)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        a = instructions[0]
        self.assertAction(a, id="a#ta/Rule1", cs="a#ta", cmd="cmd1")

    def test_nop2many(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        add_action(depgraph, "b#tb", [("Rule2", "cmd2")])
        depgraph.add_node("nop#t")
        depgraph.add_edge(('nop#t', 'a#ta'))
        depgraph.add_edge(('nop#t', 'b#tb'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 2)
        self.assertTrue("a#ta/Rule1" in ise_model.actions)
        self.assertTrue("b#tb/Rule2" in ise_model.actions)

    def _pathExist(self, depgraph, src, dst):
        """
        Returns true if a path exists in the given depgraph between nodes
        src and dst.
        """
        neighbors = depgraph.neighbors(src)
        if neighbors is None or len(neighbors) == 0:
            return False
        if dst in neighbors:
            return True
        for child in neighbors:
            if self._pathExist(depgraph, child, dst):
                return True
        return False

    def test_a_nop_b(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        add_action(depgraph, "b#tb", [("Rule2", "cmd2")])
        depgraph.add_node("nop#t")
        depgraph.add_edge(('a#ta', 'nop#t'))
        depgraph.add_edge(('nop#t', 'b#tb'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        print("Tranformed Graph: %s" % ise_model.dag.nodes())
        self.assertActionsNb(ise_model, 2)
        self.assertTrue("a#ta/Rule1" in ise_model.actions)
        self.assertTrue("b#tb/Rule2" in ise_model.actions)
        self.assertTrue(self._pathExist(ise_model.dag, 'a#ta/Rule1', 'b#tb/Rule2'))

    def test_many2nop2many(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        add_action(depgraph, "b#tb", [("Rule2", "cmd2")])
        depgraph.add_node("nop#t")
        add_action(depgraph, "c#tc", [("Rule3", "cmd3")])
        add_action(depgraph, "d#td", [("Rule4", "cmd4")])
        depgraph.add_edge(('a#ta', 'nop#t'))
        depgraph.add_edge(('b#tb', 'nop#t'))
        depgraph.add_edge(('nop#t', 'c#tc'))
        depgraph.add_edge(('nop#t', 'd#td'))
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        print("Tranformed Graph: %s" % ise_model.dag.nodes())
        self.assertActionsNb(ise_model, 4)
        self.assertTrue("a#ta/Rule1" in ise_model.actions)
        self.assertTrue("b#tb/Rule2" in ise_model.actions)
        self.assertTrue("c#tc/Rule3" in ise_model.actions)
        self.assertTrue("d#td/Rule4" in ise_model.actions)
        self.assertTrue(self._pathExist(ise_model.dag, 'a#ta/Rule1', 'c#tc/Rule3'))
        self.assertTrue(self._pathExist(ise_model.dag, 'a#ta/Rule1', 'd#td/Rule4'))
        self.assertTrue(self._pathExist(ise_model.dag, 'b#tb/Rule2', 'c#tc/Rule3'))
        self.assertTrue(self._pathExist(ise_model.dag, 'b#tb/Rule2', 'd#td/Rule4'))

    def test_single_one_action(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", "cmd1")])
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 1)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        a = instructions[0]
        self.assertAction(a, id="a#ta/Rule1", cs="a#ta", cmd="cmd1")

    def test_single_n_actions(self):
        depgraph = digraph()
        n = random.randint(5, 10)
        actions = []
        for i in range(0, n):
            actions.append(("Rule"+str(i), "Cmd"+str(i)))

        add_action(depgraph, "a#ta", actions)
        print("Graph: %s" % depgraph)
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, n)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        container = instructions.pop()
        actions = self.assertContainer(container, nb=n)
        for i in range(0, n):
            a = actions[i]
            self.assertAction(a, id="a#ta/Rule"+str(i),
                              cs="a#ta", cmd="Cmd"+str(i))

    def test_remote_action(self):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1", REMOTE_CHAR+"cmd1")])
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 1)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        a = instructions[0]
        self.assertAction(a, id="a#ta/Rule1", cs="a#ta",
                          cmd="cmd1", remote=True)

    def _test_action_force(self, force_mode):
        depgraph = digraph()
        add_action(depgraph, "a#ta", [("Rule1?force=" + force_mode, "cmd1")])
        print("Graph: %s" % depgraph.nodes())
        (ise_model, xml, error) = self.order(depgraph)
        self.assertActionsNb(ise_model, 1)
        instructions = ise_model.instructions
        self.assertNotEquals(instructions, None)
        self.assertEquals(len(instructions), 1)
        a = instructions[0]
        self.assertAction(a, id="a#ta/Rule1", cs="a#ta", cmd="cmd1",
                          force=force_mode)

    def test_action_force(self):
        self._test_action_force('always')
        self._test_action_force('never')
        self._test_action_force('allowed')

    def test_none_graph_forbidden(self):
        try:
            self.order(None)
            self.fail("Giving None as the graph should raise an exception!")
        except ValueError:
            pass

    def test_selfcycle_forbidden(self):
        graph = digraph()
        graph.add_node("a")
        graph.add_node("b")
        graph.add_edge(("a", "a"))
        try:
            self.order(graph)
            self.fail("Self cycles in the graph should be detected!")
        except CyclesDetectedError:
            pass

    def test_cycle_forbidden(self):
        graph = digraph()
        graph.add_node("a")
        graph.add_node("b")

        graph.add_edge(("a", "b"))
        graph.add_edge(("b", "a"))
        try:
            self.order(graph)
            self.fail("Cycles in the graph should be detected!")
        except CyclesDetectedError:
            pass

