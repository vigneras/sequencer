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
Test the DGM Model
"""
from sequencer.dgm.model import RuleSet, Component

import tests.dgm.tools as tools
from tests.commons import BaseGraph

class TestDGMModel_DepGraph(BaseGraph):
    """
    Test the DepGraph Maker.
    """
    def test_simple_nodeps_ta_tb_a_b(self):
        """
        RuleSet: #ta, #tb,
        Components: a#ta, b#tb
        Expecting: a#ta, b#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat"),
                                         Component("b#tb@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertTrue("Ra" in components["a#ta@cat"].actions)
        self.assertEquals("Action for a", components["a#ta@cat"].actions["Ra"])
        self.assertTrue("Rb" in components["b#tb@cat"].actions)
        self.assertEquals("Action for b", components["b#tb@cat"].actions["Rb"])
        self.assertNoEdgeBetween(depgraph.dag, "a#ta@cat", "b#tb@cat")

    def test_simple_deps_ta_tb_a_b_nodepsfinder(self):
        """
        RuleSet: #ta->#tb,
        Components: a#ta, b#tb
        Component a does not provide any depfinder, therefore, b#tb is
        not a dependency for a#ta
        Expecting: a#ta, b#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat"),
                                         Component("b#tb@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertNoEdgeBetween(depgraph.dag, "a#ta@cat", "b#tb@cat")


    def test_simple_deps_ta_tb_b_a_nodepsfinder(self):
        """
        RuleSet: #ta->#tb,
        Components: b#tb, a#ta (reverse than test_simple_deps_ta_tb_a_b_nodepsfinder)
        Expecting: a#ta, b#tb (order does not count)
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("b#tb@cat"),
                                         Component("a#ta@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertNoEdgeBetween(depgraph.dag, "a#ta@cat", "b#tb@cat")

    def test_simple_deps_ta_tb_a_b_withdepsfinder(self):
        """
        RuleSet: #ta->#tb,
        Components: a#ta, b#tb
        Component a does provide a depfinder that returns b#tb
        Expecting: a#ta -> b#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["b#tb@cat"]),
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat"),
                                         Component("b#tb@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "b#tb@cat")))

    def test_simple_deps_ta_tb_b_a_withdepsfinder(self):
        """
        RuleSet: #ta->#tb,
        Components: b#tb, a#ta (reverse)
        Component a does provide a depfinder that returns b#tb
        Expecting: a#ta -> b#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["b#tb@cat"]),
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("b#tb@cat"),
                                         Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "b#tb@cat")))

    def test_multiple_deps_ta_tb_a_withdepsfinder(self):
        """
        RuleSet: #ta->#tb,
        Components: a#ta
        Component a does provide a depfinder that returns b1#tb, b2#tb, c#tc
        Expecting: a#ta -> b1#tb, a#ta->b2#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["b1#tb@cat",
                                                                           "b2#tb@cat",
                                                                           "c#tc@cat"]),
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 4, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b1#tb@cat" in components)
        self.assertTrue("b2#tb@cat" in components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b1#tb@cat"))
        self.assertTrue(depgraph.dag.has_node("b2#tb@cat"))
        self.assertTrue(depgraph.dag.has_node("c#tc@cat"))
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "b1#tb@cat")))
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "b2#tb@cat")))
        # There are no rules for #tc, therefore, no dependency hold.
        self.assertFalse(depgraph.dag.has_edge(("a#ta@cat", "c#tc@cat")))

    def test_no_root_with_cycle_in_graph_rules(self):
        """
        There are no match in the given component list.
        RuleSet: #ta->#tb->#ta
        Components: c#tc
        Expecting: c#tc.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["foo#bar@cat"]),
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["foo#bar@cat"]),
                                    dependson=["Ra"]))

        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("c#tc@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1, "Map: %s" % components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertEquals(len(depgraph.dag.nodes()), 1)
        self.assertTrue(depgraph.dag.has_node("c#tc@cat"))

    def test_no_root_with_self_cycle_in_graph_rules(self):
        """
        There are no match in the given component list.
        RuleSet: #ta->#ta
        Components: c#tc
        Expecting: c#tc.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["foo#bar@cat"]),
                                    dependson=["Ra"]))

        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("c#tc@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1, "Map: %s" % components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertEquals(len(depgraph.dag.nodes()), 1)
        self.assertTrue(depgraph.dag.has_node("c#tc@cat"))

    def test_root_in_simple_cycle(self):
        """
        The root is in a simple cycle.
        RuleSet: #ta->#tb, #tb->#tc, #tc->#ta (triangle)
        Components: b#tb
        Expecting: b#tb
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"],
                                    dependson=["Rc"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rc",
                                    action="Action for c",
                                    dependson=["Ra"],
                                    types=["tc@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("b#tb@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1, "Map: %s" % components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))

    def test_simple_noroot(self):
        """
        There are no root in the given component list.
        RuleSet: #ta->#tb, #ta->#tc, #tb->#tc (triangle)
        Components: b#tb, a#ta (each depsfinder returns c#tc)
        Expecting: a#ta -> b#tb, a#ta -> c#tc
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["c#tc@cat"]),
                                    dependson=["Rb", "Rc"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["c#tc@cat"]),
                                    dependson=["Rc"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rc",
                                    action="Action for c",
                                    types=["tc@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("b#tb@cat"),
                                         Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 3, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertTrue(depgraph.dag.has_node("c#tc@cat"))
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "c#tc@cat")))
        self.assertTrue(depgraph.dag.has_edge(("b#tb@cat", "c#tc@cat")))

    def test_rule_applied_at_most_once(self):
        """
        Check that a given rule is applied at most once for a given component.
        RuleSet: #ta->#tc, #tb->#tc
        Components: a#ta, b#tb (each depsfinder returns c#tc)
        Expecting: c#tc contains a single action (applied once only).
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["c#tc@cat"]),
                                    dependson=["Rc"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["c#tc@cat"]),
                                    dependson=["Rc"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rc",
                                    action="Action for c",
                                    types=["tc@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("b#tb@cat"),
                                         Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 3, "Map: %s" % components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue("Rc" in components["c#tc@cat"].actions)
        self.assertEquals(components["c#tc@cat"].actions["Rc"], "Action for c")
        self.assertEquals(len(components["c#tc@cat"].actions), 1)
        self.assertEquals(len(depgraph.dag.node_attributes("c#tc@cat")), 1)

    def test_rule_applied_only_on_deps(self):
        """
        Check that a rule 'd' is applied on a component 'e' only if
        'e' is a parameter or if it is a dependency of a component 'c'
        which was applied a rule 'r' where 'r'.dependson includes 'd'.

        RuleSet: #ta->#tb, #tc
        Components: a#ta, c#tc (a#ta depsfinder returns foo#tc)
        Expecting: foo#tc should not contain any action.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["foo#tc@cat"]),
                                    dependson=["Rb"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["tb@cat"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rc",
                                    action="Action for c",
                                    types=["tc@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat"),
                                         Component("c#tc@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 3, "Map: %s" % components)
        self.assertTrue("foo#tc@cat" in components)
        self.assertTrue("c#tc@cat" in components)
        self.assertTrue("Rc" in components["c#tc@cat"].actions)
        self.assertEquals(components["c#tc@cat"].actions["Rc"], "Action for c")
        self.assertEquals(len(components["c#tc@cat"].actions), 1)
        self.assertEquals(len(depgraph.dag.node_attributes("c#tc@cat")), 1)
        self.assertEquals(len(components["foo#tc@cat"].actions), 0)
        self.assertEquals(len(depgraph.dag.node_attributes("foo#tc@cat")), 0)


    def test_only_root_rules_applied(self):
        """
        Check that a rule is applied on a parameter only if it is a
        potential root.

        RuleSet: #t(action1)->#t(action2)
        Components: a#t, b#t (a#t depsfinder returns b#t)
        Expecting: a#t contains only 1 action while b#t contains two actions.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Ra",
                                    action="Action for a",
                                    types=["t@cat"],
                                    filter="%name =~ a",
                                    depsfinder=tools.getMockDepsFinderCmd(["b#t@cat"]),
                                    dependson=["Rdep"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rb",
                                    action="Action for b",
                                    types=["t@cat"],
                                    filter="%name =~ b",
                                    dependson=["Rdep"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Rdep",
                                    action="Action for dep",
                                    types=["t@cat"]))

        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#t@cat"), Component("b#t@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2, "Map: %s" % components)
        self.assertTrue("a#t@cat" in components)
        self.assertTrue("b#t@cat" in components)
        self.assertEquals(len(components["a#t@cat"].actions), 1)
        self.assertTrue("Ra" in components["a#t@cat"].actions)
        self.assertEquals(len(components["b#t@cat"].actions), 2)
        self.assertTrue("Rb" in components["b#t@cat"].actions)
        self.assertTrue("Rdep" in components["b#t@cat"].actions)

        self.assertEquals(len(depgraph.dag.node_attributes("a#t@cat")), 1)
        self.assertEquals(len(depgraph.dag.node_attributes("b#t@cat")), 2)



    def test_multiple_actions_nodeps(self):
        """
        Check that a given component can contain multiple actions.
        RuleSet: #ta, #ta
        Components: a#ta
        Expecting: a#ta with 2 actions.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R1",
                                    action="Action for a",
                                    types=["ta@cat"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R2",
                                    action="Action for a",
                                    types=["ta@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("R1" in components["a#ta@cat"].actions)
        self.assertTrue("R2" in components["a#ta@cat"].actions)
        self.assertEquals(len(components["a#ta@cat"].actions), 2)
        self.assertEquals(len(depgraph.dag.node_attributes("a#ta@cat")), 2)

    def test_multiple_actions_cycle(self):
        """
        Check that a given component can contain multiple actions.
        RuleSet: R1:#ta, R2:#ta->R1
        Components: a#ta (R1 depsfinder returns itself: a#ta)
        Expecting: a#ta with 2 actions and a cycle.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R1",
                                    action="Action for a",
                                    types=["ta@cat"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R2",
                                    action="Action for a",
                                    types=["ta@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["a#ta@cat"]),
                                    dependson=["R1"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat")])
        components = depgraph.components_map

        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1, "Map: %s" % components)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("R1" in components["a#ta@cat"].actions)
        self.assertTrue("R2" in components["a#ta@cat"].actions)
        self.assertEquals(len(components["a#ta@cat"].actions), 2)
        self.assertEquals(len(depgraph.dag.node_attributes("a#ta@cat")), 2)
        self.assertTrue(depgraph.dag.has_edge(("a#ta@cat", "a#ta@cat")))


    def test_root_rules_for_a(self):
        """
        Check that the root rules for a single rule is the rule
        itself.
        """
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"])
        rules.add(r1)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)


    def test_root_rules_for_a_b(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["tb@cat"])
        rules.add(r1)
        rules.add(r2)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 2, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["tb@cat"], types)

    def test_root_rules_for_self_cycle(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R1"])
        rules.add(r1)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)


    def test_root_rules_for_a_b_cycle(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["tb@cat"],
                               dependson=["R1"])
        rules.add(r1)
        rules.add(r2)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 2, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["tb@cat"], types)


    def test_root_rules_for_a_a(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["ta@cat"])
        rules.add(r1)
        rules.add(r2)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)

    def test_root_rules_for_a_bc(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2", "R3"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["tb@cat"])
        r3 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R3",
                               action="A3",
                               types=["tc@cat"])
        rules.add(r1)
        rules.add(r2)
        rules.add(r3)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 3, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["tb@cat"], types)
        self.assertTrue(r3 in types["tc@cat"], types)

    def test_root_rules_for_a_ba(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2", "R3"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["tb@cat"])
        r3 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R3",
                               action="A3",
                               types=["ta@cat"])
        rules.add(r1)
        rules.add(r2)
        rules.add(r3)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 2, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["tb@cat"], types)

    def test_root_rules_for_a_b_a(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["tb@cat"],
                               dependson=["R3"])
        r3 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R3",
                               action="A3",
                               types=["ta@cat"])
        rules.add(r1)
        rules.add(r2)
        rules.add(r3)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 2, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["tb@cat"], types)

    def test_root_rules_for_a_aa(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2", "R3"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["ta@cat"])
        r3 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R3",
                               action="A3",
                               types=["ta@cat"])
        rules.add(r1)
        rules.add(r2)
        rules.add(r3)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)

    def test_root_rules_for_aa_a(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R3"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["ta@cat"],
                               dependson=["R3"])
        r3 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R3",
                               action="A3",
                               types=["ta@cat"])
        rules.add(r1)
        rules.add(r2)
        rules.add(r3)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["ta@cat"], types)

    def test_root_rules_for_a_a_cycle(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ta@cat"],
                               dependson=["R2"])
        r2 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R2",
                               action="A2",
                               types=["ta@cat"],
                               dependson=["R1"])
        rules.add(r1)
        rules.add(r2)
        ruleset = RuleSet(rules)
        types = ruleset.root_rules_for
        self.assertTrue(len(types) == 1, types)
        self.assertTrue(r1 in types["ta@cat"], types)
        self.assertTrue(r2 in types["ta@cat"], types)

    def test_root_rules_all_type_apply_to_any_component(self):
        rules = set()
        r1 = tools.create_rule(ruleset=self.__class__.__name__,
                               name="R1",
                               action="A1",
                               types=["ALL"])
        rules.add(r1)
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#ta@cat"),
                                         Component("b#tb@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("a#ta@cat" in components)
        self.assertTrue("b#tb@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#ta@cat"))
        self.assertTrue(depgraph.dag.has_node("b#tb@cat"))
        self.assertTrue("R1" in components["a#ta@cat"].actions)
        self.assertTrue("R1" in components["b#tb@cat"].actions)
        self.assertNoEdgeBetween(depgraph.dag, "a#ta@cat", "b#tb@cat")
