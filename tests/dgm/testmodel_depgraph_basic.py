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
from sequencer.dgm.model import RuleSet, Component, ALL, NONE

import tests.dgm.tools as tools
from tests.commons import BaseGraph
from sequencer.dgm.cli import NOT_FORCE_OP


class TestDGMModel_DepGraphBasic(BaseGraph):
    """
    Test the DepGraph Maker.
    """
    def test_empty_ruleset(self):
        ruleset = RuleSet(set())
        depgraph = ruleset.get_depgraph([Component("unknown#unknown@cat")])
        self.assertTrue(depgraph is not None)

    def test_unknown_component(self):
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="test_unknown_component",
                                    types=["known@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("foo#unknown@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1)
        self.assertTrue("foo#unknown@cat" in components)
        self.assertEquals(len(components["foo#unknown@cat"].actions), 0)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("foo#unknown@cat"))

    def test_known_component(self):
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R",
                                    action="The Action",
                                    types=["known@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("foo#known@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1)
        self.assertTrue("foo#known@cat" in components)
        self.assertTrue("R" in components["foo#known@cat"].actions)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("foo#known@cat"))

    def test_substitution_in_action(self):
        rules = set()
        pattern = "%id-%name-%type-%category-%ruleset-%rulename"
        rules.add(tools.create_rule(ruleset="RS",
                                    name="RN",
                                    action= pattern,
                                    types=["known@cat"]))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("foo#known@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 1)
        self.assertTrue("foo#known@cat" in components)
        self.assertTrue("RN" in components["foo#known@cat"].actions)
        self.assertEquals("foo#known@cat-foo-known-cat-RS-RN",
                          components["foo#known@cat"].actions["RN"])
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("foo#known@cat"))
        attributes = depgraph.dag.node_attributes("foo#known@cat")
        self.assertEquals(len(attributes), 1)
        rule, action = attributes[0]
        self.assertEquals(rule, "RN")
        self.assertEquals(action, "foo#known@cat-foo-known-cat-RS-RN")

    def test_substitution_in_depsfinder(self):
        rules = set()
        pattern = "%id-%name-%type-%category-%ruleset-%rulename"
        rules.add(tools.create_rule(ruleset="RS",
                                    name="RN",
                                    action="Action",
                                    depsfinder=tools.getMockDepsFinderCmd([pattern]),
                                    types=["known@cat"],
                                    dependson=["Dummy"]))
        rules.add(tools.create_rule(ruleset="RS",
                                    name="Dummy"))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("foo#known@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("foo#known@cat" in components)
        self.assertTrue("foo#known@cat-foo-known-cat-RS-RN" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("foo#known@cat"))
        self.assertTrue(depgraph.dag.has_node("foo#known@cat-foo-known-cat-RS-RN"))

    def test_filtered_none_components_requested(self):
        """
        When filtered out components are requested, rules are not applied, but the
        components remains in the depgraph.
        RuleSet: #root (filter = NONE) -> #deps
        Components: a#root, b#deps
        Component a provides a depfinder that returns c#deps but it is filtered out
        Expecting: a#root, b#deps (a#root has no action)
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R-root",
                                    action="Root Action",
                                    types=["root@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["c#deps@cat"]),
                                    dependson=["R-deps"],
                                    filter=NONE))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R-deps",
                                    action="Deps Action",
                                    types=["deps@cat"]))

        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#root@cat"),
                                         Component("b#deps@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue("a#root@cat" in components)
        self.assertTrue("b#deps@cat" in components)
        self.assertTrue("c#deps@cat" not in components)
        self.assertTrue("R-root" not in components["a#root@cat"].actions)
        self.assertTrue("R-deps" in components["b#deps@cat"].actions)
        self.assertTrue(depgraph.dag.has_node("a#root@cat"))
        self.assertTrue(depgraph.dag.has_node("b#deps@cat"))
        self.assertFalse(depgraph.dag.has_node("c#deps@cat"))


    def test_filtered_none_components_deps(self):
        """
        Check that dependencies are not in the graph when they are filtered out.
        RuleSet: #root -> #deps (filter = NONE)
        Components: a#root
        Component a provides a depfinder that returns b#deps
        Expecting: a#root, b#deps (b#deps has no action, it has been filtered out)
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R-root",
                                    action="Root Action",
                                    types=["root@cat"],
                                    depsfinder=tools.getMockDepsFinderCmd(["b#deps@cat"]),
                                    dependson=["R-Deps"]))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R-Deps",
                                    action="Deps Action",
                                    types=["deps@cat"],
                                    filter=NONE))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#root@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue("a#root@cat" in components)
        self.assertTrue("R-root" in components["a#root@cat"].actions)
        self.assertEquals("Root Action", components["a#root@cat"].actions["R-root"])
        self.assertTrue("b#deps@cat" in components)
        self.assertTrue(depgraph.dag.has_node("a#root@cat"))
        self.assertTrue(depgraph.dag.has_node("b#deps@cat"))
        self.assertTrue("Deps Action" not in components["b#deps@cat"].actions)

    def test_filtered_all_components(self):
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="test_filtered_all_components",
                                    types=["any@cat"],
                                    filter=ALL))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("in#any@cat"),
                                         Component("out#any@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue("in#any@cat" in components)
        self.assertTrue("out#any@cat" in components)
        self.assertTrue(depgraph.dag.has_node("in#any@cat"))
        self.assertTrue(depgraph.dag.has_node("out#any@cat"))

    def test_filtered_components(self):
        """
        Check that filter other than NONE and ALL works as expected.
        RuleSet: #root (filter = in.*)
        Components: in#root in_foo#root out#root
        Expecting: in#root, in_foo#root out#root
        (out#root has no action, it has been filtered out)
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R",
                                    types=["root@cat"],
                                    action="Root Action",
                                    # WARNING: space is important here!!
                                    filter="%name =~ in.*"))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("in#root@cat"),
                                         Component("in_foo#root@cat"),
                                         Component("out#root@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 3)
        self.assertTrue("in#root@cat" in components)
        self.assertTrue("in_foo#root@cat" in components)
        self.assertTrue("out#root@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("in#root@cat"))
        self.assertTrue(depgraph.dag.has_node("in_foo#root@cat"))
        self.assertTrue(depgraph.dag.has_node("out#root@cat"))
        self.assertTrue("R" in components["in#root@cat"].actions)
        self.assertEquals("Root Action", components["in#root@cat"].actions["R"])
        self.assertTrue("R" in components["in_foo#root@cat"].actions)
        self.assertEquals("Root Action", components["in_foo#root@cat"].actions["R"])
        self.assertTrue("Root Action" not in components["out#root@cat"].actions)

    def test_a_nop_b(self):
        """
        Check that action NONE are understood correctly.
        RuleSet: #root, #dep (filter = ALL),
        a#root -> b#dep (a.action=NONE)
        Expecting: a#root -> b#dep
        But a#root has no attribute in the xml graph.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Root",
                                    types=["root@cat"],
                                    action=NONE,
                                    depsfinder=tools.getMockDepsFinderCmd(["b#dep@cat"]),
                                    dependson=['Dep']))
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="Dep",
                                    types=["dep@cat"],
                                    action="Dep Action"))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("a#root@cat")])
        components = depgraph.components_map
        self.assertTrue(components is not None)
        self.assertEquals(len(components), 2)
        self.assertTrue("a#root@cat" in components)
        self.assertTrue("b#dep@cat" in components)
        self.assertTrue(depgraph.dag is not None)
        self.assertTrue(depgraph.dag.has_node("a#root@cat"))
        self.assertTrue(depgraph.dag.has_node("b#dep@cat"))
        self.assertFalse("Root" in components["a#root@cat"].actions, components)
        self.assertTrue("Dep" in components["b#dep@cat"].actions)
        attributes = depgraph.dag.node_attributes("a#root@cat")
        self.assertEquals(len(attributes), 0)
        attributes = depgraph.dag.node_attributes("b#dep@cat")
        self.assertEquals(len(attributes), 1)



    def test_force_options(self):
        """
        Check that force flag is generated correctly.
        """
        rules = set()
        rules.add(tools.create_rule(ruleset=self.__class__.__name__,
                                    name="R",
                                    types=["force@cat"],
                                    action="Test Action"))
        ruleset = RuleSet(rules)
        depgraph = ruleset.get_depgraph([Component("in#force@cat")], force_rule=['R'])
        components = depgraph.components_map
        attributes = depgraph.dag.node_attributes("in#force@cat")
        self.assertEquals('R?force=always', attributes[0][0])
        self.assertTrue("R?force=always" in components["in#force@cat"].actions)
        self.assertEquals("Test Action", components["in#force@cat"].actions["R?force=always"])

        depgraph = ruleset.get_depgraph([Component("in#force@cat")],
                                        force_rule=[NOT_FORCE_OP + 'R'])
        components = depgraph.components_map
        attributes = depgraph.dag.node_attributes("in#force@cat")
        self.assertEquals('R?force=never', attributes[0][0])
        self.assertTrue("R?force=never" in components["in#force@cat"].actions)
        self.assertEquals("Test Action", components["in#force@cat"].actions["R?force=never"])


