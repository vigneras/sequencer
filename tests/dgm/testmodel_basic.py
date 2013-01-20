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
Test the DGM Model
"""
from sequencer.dgm.errors import UnknownDepError
from sequencer.dgm.model import RuleSet, Component, ALL, NONE, AllFilter, NoneFilter, ReFilter, ScriptFilter, FullType

import tests.dgm.tools as tools
from tests.commons import BaseTest


class TestDGMModel_TypeBasic(BaseTest):
    """
    Basic test of DGM Rule Type
    """

    def test_type_all(self):
        type_ = FullType("ALL")
        self.assertTrue(type_.match(Component("foo#bar@cat")))

    def test_type_all_cat(self):
        type_ = FullType("bar@ALL")
        self.assertTrue(type_.match(Component("foo#bar@cat")))
        self.assertTrue(type_.match(Component("fuu#bar@another")))
        self.assertFalse(type_.match(Component("foo#baz@cat")))

    def test_type_all_type(self):
        type_ = FullType("ALL@cat")
        self.assertTrue(type_.match(Component("foo#bar@cat")))
        self.assertTrue(type_.match(Component("foo#baz@cat")))
        self.assertFalse(type_.match(Component("fuu#bar@another")))

    def test_type_normal(self):
        type_ = FullType("bar@cat")
        self.assertTrue(type_.match(Component("foo#bar@cat")))
        self.assertFalse(type_.match(Component("foo#baz@cat")))
        self.assertFalse(type_.match(Component("foo#bar@caz")))
        self.assertFalse(type_.match(Component("foo#baz@caz")))



class TestDGMModel_FilterBasic(BaseTest):
    """
    Basic test of DGM Rule Filter
    """

    def test_filter_all(self):
        filter_ = AllFilter()
        self.assertTrue(filter_.filter(Component("foo#bar@cat")))

    def test_filter_none(self):
        filter_ = NoneFilter()
        self.assertFalse(filter_.filter(Component("foo#bar@cat")))

    def test_filter_re(self):
        rule = tools.create_rule("RS", "RN", action="Unused")
        filter_= ReFilter(rule, '%id', '=~', 'foo.*')
        self.assertTrue(filter_.filter(Component("foo#bar@cat")))
        self.assertFalse(filter_.filter(Component("bar#foo@cat")))

        filter_= ReFilter(rule, '%id', '!~', 'foo.*')
        self.assertFalse(filter_.filter(Component("foo#bar@cat")))
        self.assertTrue(filter_.filter(Component("bar#foo@cat")))

    def test_filter_script(self):
        # WARNING: space is important for bash!
        rule = tools.create_rule("RS", "RN",
                                 action="Unused",
                                 filter="bash -c '[[ %id =~ ^foo.* ]]'")

        filter_= ScriptFilter(rule)
        self.assertTrue(filter_.filter(Component("foo#bar@cat")))
        self.assertFalse(filter_.filter(Component("bar#foo@cat")))



class TestDGMModel_RuleBasic(BaseTest):
    """
    Basic test of DGM Rule Model
    """

    def test_rule_fields(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_fields",
                                 ["type@cat"],
                                 "Filter",
                                 "Action",
                                 "DepsFinder",
                                 ["DependsOn"],
                                 "Comments")
        self.assertEquals(rule.ruleset, self.__class__.__name__)
        self.assertEquals(rule.name, "rule_fields")
        self.assertEquals(set(rule.types.keys()), set(["type@cat"]))
        self.assertEquals(rule.filter, "Filter")
        self.assertEquals(rule.action, "Action")
        self.assertEquals(rule.depsfinder, "DepsFinder")
        self.assertEquals(rule.dependson, set(["DependsOn"]))
        self.assertEquals(rule.comments, "Comments")

    def test_rule_none_fields(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_fields",
                                 [ALL],
                                 NONE,
                                 NONE,
                                 NONE,
                                 NONE,
                                 NONE)
        self.assertEquals(rule.ruleset, self.__class__.__name__)
        self.assertEquals(rule.name, "rule_fields")
        self.assertEquals(set(rule.types.keys()), set([ALL]))
        self.assertEquals(rule.filter, NONE)
        self.assertEquals(rule.action, NONE)
        self.assertEquals(rule.depsfinder, NONE)
        self.assertEquals(rule.dependson, set())
        self.assertEquals(rule.comments, NONE)

    def test_rule_fields_multiple_types_and_depsfinders(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_fields_multiple_types_and_depsfinders",
                                 ["t1@cat", "t2@cat"],
                                 "Filter",
                                 "Action",
                                 "DepsFinder",
                                 ["r1", "r2"],
                                 "Comments")
        self.assertEquals(rule.ruleset, self.__class__.__name__)
        self.assertEquals(rule.name, "rule_fields_multiple_types_and_depsfinders")
        self.assertEquals(set(rule.types.keys()), set(["t1@cat", "t2@cat"]))
        self.assertEquals(rule.filter, "Filter")
        self.assertEquals(rule.action, "Action")
        self.assertEquals(rule.depsfinder, "DepsFinder")
        self.assertEquals(rule.dependson, set(["r1", "r2"]))
        self.assertEquals(rule.comments, "Comments")

    def test_rule_fields_starik(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_fields_starik",
                                 [ALL],
                                 "Filter",
                                 "Action",
                                 "DepsFinder",
                                 ["r1"],
                                 "Comments")
        self.assertEquals(rule.ruleset, self.__class__.__name__)
        self.assertEquals(rule.name, "rule_fields_starik")
        self.assertEquals(set(rule.types.keys()), set([ALL]))
        self.assertEquals(rule.filter, "Filter")
        self.assertEquals(rule.action, "Action")
        self.assertEquals(rule.depsfinder, "DepsFinder")
        self.assertEquals(rule.dependson, set(["r1"]))
        self.assertEquals(rule.comments, "Comments")

    def test_rule_fields_starik_multiple(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_fields_starik_multiple",
                                 [ALL, "t@cat"],
                                 "Filter",
                                 "Action",
                                 "DepsFinder",
                                 ["r1"],
                                 "Comments")
        self.assertEquals(rule.ruleset, self.__class__.__name__)
        self.assertEquals(rule.name, "rule_fields_starik_multiple")
        self.assertEquals(set(rule.types.keys()), set([ALL, "t@cat"]))
        self.assertEquals(rule.filter, "Filter")
        self.assertEquals(rule.action, "Action")
        self.assertEquals(rule.depsfinder, "DepsFinder")
        self.assertEquals(rule.dependson, set(["r1"]))
        self.assertEquals(rule.comments, "Comments")

    def test_rule_pass_filter_none(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_pass_none_filter",
                                 filter=NONE)
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))

    def test_rule_pass_filter_all(self):
        rule = tools.create_rule(self.__class__.__name__,
                                 "rule_pass_all_filter",
                                 filter=ALL)
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))

    def test_rule_pass_filter_bash(self):
        patternl = "%id-%name-%type-%category-%ruleset-%rulename"
        patternr = "foo#bar@cat-foo-bar-cat-RS-RN"

        rule = tools.create_rule("RS",
                                 "RN",
                                 filter="bash -c '[[ %s =~ %s ]]'" % \
                                     (patternl, patternr))
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))
        self.assertFalse(rule.pass_filter(Component("bar#foo@cat")))

    def test_rule_pass_filter_re_id(self):
        rule = tools.create_rule("RS", "RN", filter="%id =~ foo#bar@cat")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))
        self.assertFalse(rule.pass_filter(Component("bar#foo@cat")))

        rule = tools.create_rule("RS", "RN", filter="%id !~ foo#bar@cat")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))
        self.assertTrue(rule.pass_filter(Component("bar#foo@cat")))

    def test_rule_pass_filter_re_name(self):
        rule = tools.create_rule("RS", "RN", filter="%name =~ foo")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))
        self.assertFalse(rule.pass_filter(Component("bar#foo@cat")))

        rule = tools.create_rule("RS", "RN", filter="%name !~ foo")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))
        self.assertTrue(rule.pass_filter(Component("bar#foo@cat")))

    def test_rule_pass_filter_re_type(self):
        rule = tools.create_rule("RS", "RN", filter="%type =~ bar")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))
        self.assertFalse(rule.pass_filter(Component("bar#foo@cat")))

        rule = tools.create_rule("RS", "RN", filter="%type !~ bar")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))
        self.assertTrue(rule.pass_filter(Component("bar#foo@cat")))

    def test_rule_pass_filter_re_category(self):
        rule = tools.create_rule("RS", "RN", filter="%category =~ cat")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))
        self.assertFalse(rule.pass_filter(Component("bar#foo@baz")))

        rule = tools.create_rule("RS", "RN", filter="%category !~ cat")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))
        self.assertTrue(rule.pass_filter(Component("bar#foo@baz")))

    def test_rule_pass_filter_re_rulename(self):
        rule = tools.create_rule("RS", "RN", filter="%rulename =~ RN")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))

        rule = tools.create_rule("RS", "RN", filter="%rulename !~ RN")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))

    def test_rule_pass_filter_re_ruleset(self):
        rule = tools.create_rule("RS", "RN", filter="%ruleset =~ RS")
        self.assertTrue(rule.pass_filter(Component("foo#bar@cat")))

        rule = tools.create_rule("RS", "RN", filter="%ruleset !~ RS")
        self.assertFalse(rule.pass_filter(Component("foo#bar@cat")))


    def test_rule_match_type(self):
        rule = tools.create_rule("RS", "RN", types=["bar@cat"])
        self.assertTrue(rule.match_type(Component("foo#bar@cat")))
        self.assertFalse(rule.match_type(Component("bar#foo@cat")))

    def test_rule_match_type_multiple(self):
        rule = tools.create_rule("RS", "RN", types=["bar@cat", "baz@cat"])
        self.assertTrue(rule.match_type(Component("foo#bar@cat")))
        self.assertTrue(rule.match_type(Component("foo#baz@cat")))
        self.assertFalse(rule.match_type(Component("bar#foo@cat")))

        rule = tools.create_rule("RS", "RN", types=["bar@cat1", "baz@cat2"])
        self.assertTrue(rule.match_type(Component("foo#bar@cat1")))
        self.assertTrue(rule.match_type(Component("foo#baz@cat2")))
        self.assertFalse(rule.match_type(Component("foo#bar@cat2")))
        self.assertFalse(rule.match_type(Component("foo#baz@cat1")))

    def test_rule_match_type_starik(self):
        rule = tools.create_rule("RS", "RN", types=[ALL])
        self.assertTrue(rule.match_type(Component("foo#bar@cat")))
        self.assertTrue(rule.match_type(Component("foo#baz@cat")))
        self.assertTrue(rule.match_type(Component("bar#foo@cat")))

    def test_rule_match_type_starik_multiple(self):
        rule = tools.create_rule("RS", "RN", types=[ALL, "foo@cat"])
        self.assertTrue(rule.match_type(Component("foo#bar@cat")))
        self.assertTrue(rule.match_type(Component("foo#baz@cat")))
        self.assertTrue(rule.match_type(Component("bar#foo@cat")))


class TestDGMModel_RuleError(BaseTest):
    """
    Check errors on Rule Model
    """

    def test_none_ruleset_forbidden(self):
        try:
            tools.create_rule(None, "none_ruleset_forbidden")
            self.fail("Setting ruleset to None should raise an exception!")
        except ValueError:
            pass

    def test_none_rulename_forbidden(self):
        try:
            tools.create_rule(self.__class__.__name__,
                              None)
            self.fail("Setting rule name to None should raise an exception!")
        except ValueError:
            pass


    def test_none_types_forbidden(self):
        try:
            tools.create_rule(self.__class__.__name__,
                              "none_types_forbidden",
                              types=None)
            self.fail("Setting types to None should raise an exception!")
        except ValueError:
            pass

    def test_empty_types_forbidden(self):
        try:
            tools.create_rule(self.__class__.__name__,
                              "EmptyTypesForbidden",
                              types=set())
            self.fail("Setting an empty set should raise an exception!")
        except ValueError:
            pass

    def test_empty_filter_forbidden(self):
        try:
            tools.create_rule(self.__class__.__name__,
                              "EmptyFilterForbidden",
                              filter="")
            self.fail("Setting an empty filter should raise an exception!")
        except ValueError:
            pass

    def test_empty_depsfinder_forbidden(self):
        try:
            tools.create_rule(self.__class__.__name__,
                              "EmptyDepsFinderForbidden",
                              depsfinder="")
            self.fail("Setting an empty depsfinder should raise an exception!")
        except ValueError:
            pass


class TestDGMModel_RuleSetBasic(BaseTest):
    """
    Basic test of RuleSet Model
    """

    def test_ruleset_field_empty(self):
        ruleset = RuleSet(set())
        self.assertTrue(ruleset.name is None)
        self.assertEquals(ruleset.rules, set())
        graph = ruleset.get_rules_graph()
        self.assertTrue(graph is not None)
        self.assertEquals(len(graph.edges()), 0)
        self.assertEquals(len(graph.nodes()), 0)


    def test_ruleset_field_single(self):
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_field_single"))
        ruleset = RuleSet(rules)
        self.assertEquals(ruleset.name, self.__class__.__name__)
        self.assertEquals(ruleset.rules, rules)
        graph = ruleset.get_rules_graph()
        self.assertTrue(graph is not None)
        self.assertEquals(len(graph.edges()), 0)
        self.assertEquals(len(graph.nodes()), 1)
        self.assertTrue(graph.has_node("ruleset_field_single"))


    def test_ruleset_field_multiple(self):
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_field_multiple"))
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_field_multiple2"))
        ruleset = RuleSet(rules)
        self.assertEquals(ruleset.name, self.__class__.__name__)
        self.assertEquals(ruleset.rules, rules)
        graph = ruleset.get_rules_graph()
        self.assertTrue(graph is not None)
        self.assertEquals(len(graph.edges()), 0)
        self.assertEquals(len(graph.nodes()), 2)
        self.assertTrue(graph.has_node("ruleset_field_multiple"))
        self.assertTrue(graph.has_node("ruleset_field_multiple2"))

    def test_ruleset_dependencies(self):
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_dependencies"))
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_dependencies2",
                                    dependson=["ruleset_dependencies"]))
        ruleset = RuleSet(rules)
        self.assertEquals(ruleset.name, self.__class__.__name__)
        self.assertEquals(ruleset.rules, rules)
        graph = ruleset.get_rules_graph()
        self.assertTrue(graph is not None)
        self.assertEquals(len(graph.edges()), 1)
        self.assertTrue(graph.has_edge(("ruleset_dependencies2",
                                        "ruleset_dependencies")))

class TestDGMModel_RuleSetError(BaseTest):
    """
    Test Error Checking of RuleSet Model
    """
    def test_ruleset_different(self):
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "ruleset_different"))
        rules.add(tools.create_rule(self.__class__.__name__ + "-2",
                                    "ruleset_different"))
        try:
            RuleSet(rules)
            self.fail("Creating a RuleSet with different " + \
                          "ruleset should raise an exception")
        except ValueError:
            pass

    def test_baddep(self):
        rule = tools.create_rule(self.__class__.__name__,
                                    "baddep", dependson="Unknown")
        rules = set()
        rules.add(rule)
        try:
            RuleSet(rules)
            self.fail("Unknown Dependency should be raised: %s" % rule)
        except UnknownDepError as ude:
            print "Exception is: %s" % ude

    def test_baddep2(self):
        rule1 = tools.create_rule(self.__class__.__name__, "BadDep2-1")
        rule2 = tools.create_rule(self.__class__.__name__, "BadDep2-2", dependson="Unknown")
        rules = set([rule1, rule2])
        try:
            RuleSet(rules)
            self.fail("Unknown Dependency should be raised: %s" % rule2)
        except UnknownDepError as ude:
            print "Exception is: %s" % ude

    def test_cycles_self(self):
        """Self cycles are allowed in the graph rules"""
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "nocycles_self",
                                    dependson=["nocycles_self"]))
        # This should not raise an exception
        RuleSet(rules)

    def test_cycles_simple(self):
        """Cycles are allowed in the graph rules"""
        rules = set()
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "nocycles_simple1",
                                    dependson=["nocycles_simple2"]))
        rules.add(tools.create_rule(self.__class__.__name__,
                                    "nocycles_simple2",
                                    dependson=["nocycles_simple1"]))
        # This should not raise an exception
        RuleSet(rules)


class TestDGMModel_ComponentBasic(BaseTest):
    """
    Basic Test of Component Model
    """
    def test_notype_forbidden(self):
        try:
            Component("dummy")
            self.fail("Creating a Component with no type " + \
                          " should raise an exception")
        except ValueError:
            pass

        try:
            Component("dummy", None)
            self.fail("Creating a Component with no type " + \
                          " should raise an exception")
        except ValueError:
            pass

    def test_nocategory_forbidden(self):
        try:
            Component("dummy#type")
            self.fail("Creating a Component with no category " + \
                          " should raise an exception")
        except ValueError:
            pass

        try:
            Component("dummy", "type", None)
            self.fail("Creating a Component with no category " + \
                          " should raise an exception")
        except ValueError:
            pass

    def test_equals(self):
        component1 = Component("foo#type@cat")
        component2 = Component("foo#type@cat")
        self.assertEquals(component1, component2)
        component1 = Component("foo", "type", "cat")
        component2 = Component("foo", "type", "cat")
        self.assertEquals(component1, component2)
        component1 = Component("foo#type@cat")
        component2 = Component("foo", "type", "cat")
        self.assertEquals(component1, component2)

    def test_different(self):
        component1 = Component("foo#type1@cat")
        component2 = Component("foo#type2@cat")
        self.assertNotEquals(component1, component2)
        component1 = Component("foo", "type1", "cat")
        component2 = Component("foo", "type2", "cat")
        self.assertNotEquals(component1, component2)
        component1 = Component("foo", "type1", "cat")
        component2 = Component("foo#type2@cat")
        self.assertNotEquals(component1, component2)
        component1 = Component("foo", "type", "cat1")
        component2 = Component("foo", "type", "cat2")
        self.assertNotEquals(component1, component2)
        component1 = Component("foo#type@cat1")
        component2 = Component("foo#type@cat2")
        self.assertNotEquals(component1, component2)

    def test_type_complex(self):
        component = Component("foo#something#anotherthing#thetype@foo@bar@cat")
        self.assertEquals(component.name, "foo#something#anotherthing")
        self.assertEquals(component.type, "thetype@foo@bar")
        self.assertEquals(component.category, "cat")


