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
Test the SequencerDB API
"""
import random

import tests.dgm.tools as tools
from sequencer.commons import UnknownRuleSet

_DELETE_TMP_FILE = True

class AbstractDGMDBTest(object):
    """
    Basic test of the DB.
    """
    def test_dup_forbidden(self):
        rule1 = tools.create_rule(self.__class__.__name__, "DupForbidden")
        rule2 = tools.create_rule(self.__class__.__name__, "DupForbidden")
        self.assertEquals(rule1, rule2)
        self.db.add_rule(rule1)
        try:
            self.db.add_rule(rule2)
            self.fail("Duplicate rules are forbidden in the DB")
        except Exception as e:
            print "Exception is: %s" % e


    def test_get_empty_ruleset(self):
        self.assertRaises(ValueError, self.db.get_rules_for, None)
        self.assertRaises(UnknownRuleSet, self.db.get_rules_for, "foo")

    def test_add_remove_single(self):
        rule = tools.create_rule(self.__class__.__name__, "add_remove_single")
        self.db.add_rule(rule)
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1)
        self.assertRuleInMap(rule, rules_for)

        # Trailing comma is required for tuple
        remaining = self.db.remove_rules(rule.ruleset, (rule.name,))
        self.assertEquals(len(remaining), 0)
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 0, str(rules_for))

    def test_add_remove_multiple(self):
        rule1 = tools.create_rule("RS", "r1")
        rule2 = tools.create_rule("RS", "r2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        rules_map = self.db.get_rules_map()
        self.assertTrue(rules_map is not None)
        self.assertEquals(len(rules_map), 1)
        self.assertTrue("RS" in rules_map)
        self.assertEquals(len(rules_map['RS']), 2)
        self.assertRuleInMap(rule1, rules_map)
        self.assertRuleInMap(rule2, rules_map)

        # Trailing comma is required for tuple
        remaining = self.db.remove_rules(rule1.ruleset, (rule1.name, rule2.name))
        self.assertEquals(len(remaining), 0)
        rules_map = self.db.get_rules_map()
        self.assertTrue(rules_map is not None)
        self.assertEquals(len(rules_map), 0, str(rules_map))

    def test_unknown_remove(self):
        remaining = self.db.remove_rules(self.__class__.__name__,
                                         # Trailing comma is required for tuple
                                        ("unknown_remove",))
        self.assertEquals(len(remaining), 1)
        self.assertTrue("unknown_remove" in remaining)

    def test_multiple_removal(self):
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove1"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove2"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove3"))

        remaining = self.db.remove_rules(self.__class__.__name__,
                                        ("remove1", "remove2", "unknown"))
        self.assertEquals(len(remaining), 1)
        self.assertTrue("unknown" in remaining)
        rules = self.db.get_rules_for(self.__class__.__name__)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue("remove3" in rules)

    def test_remove_ref_deps_single(self):
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "r1"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "r2",
                                           dependson=set(['r1'])))

        remaining = self.db.remove_rules(self.__class__.__name__, ("r1",))
        self.assertEquals(len(remaining), 0)
        rules = self.db.get_rules_for(self.__class__.__name__)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue("r2" in rules)
        self.assertEquals(len(rules["r2"].dependson), 0)

    def test_remove_ref_deps_multiple(self):
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "r1"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "r2",
                                           dependson=set(['r1'])))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "r3",
                                           dependson=set(['r1', 'r2'])))

        remaining = self.db.remove_rules(self.__class__.__name__, ("r1",))
        self.assertEquals(len(remaining), 0)
        rules = self.db.get_rules_for(self.__class__.__name__)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 2)
        self.assertTrue("r2" in rules)
        self.assertTrue("r3" in rules)
        self.assertEquals(len(rules["r2"].dependson), 0)
        self.assertEquals(len(rules["r3"].dependson), 1)
        self.assertTrue("r2" in rules["r3"].dependson)


    def test_remove_whole_ruleset(self):
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove1"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove2"))
        self.db.add_rule(tools.create_rule(self.__class__.__name__, "remove3"))
        self.db.add_rule(tools.create_rule("other_ruleset", "a_rule"))

        remaining = self.db.remove_rules(self.__class__.__name__)
        self.assertEquals(len(remaining), 0)
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1)
        self.assertTrue(self.__class__.__name__ not in rules_for)
        self.assertEquals(len(rules_for["other_ruleset"]), 1)

    def test_update_normal_fields(self):
        rule = tools.create_rule(self.__class__.__name__, "update_normal")
        self.db.add_rule(rule)
        self.db.update_rule(rule.ruleset, rule.name,
                            [("types", "newtype@newcat"),
                             ("action", "NewAction"),
                             ("filter", "NewFilter")])
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1, str(rules_for))
        self.assertRuleInMap(tools.create_rule(self.__class__.__name__,
                                               "update_normal"),
                             rules_for)
        rule = rules_for[self.__class__.__name__]["update_normal"]
        types = rule.types
        self.assertEquals(len(types), 1)
        self.assertTrue('newtype@newcat' in types)
        self.assertEquals(rule.action, "NewAction")
        self.assertEquals(rule.filter, "NewFilter")

    def test_update_ruleset(self):
        rule = tools.create_rule(self.__class__.__name__, "update")
        self.db.add_rule(rule)
        self.db.update_rule(rule.ruleset, rule.name, [("ruleset", "NewRS")])
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1, str(rules_for))
        self.assertRuleInMap(tools.create_rule("NewRS", "update"),
                             rules_for)

    def test_update_rulename(self):
        rule = tools.create_rule(self.__class__.__name__, "update")
        self.db.add_rule(rule)
        self.db.update_rule(rule.ruleset, rule.name, [("name", "update_ok")])
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1, str(rules_for))
        self.assertRuleInMap(tools.create_rule(self.__class__.__name__,
                                               "update_ok"),
                             rules_for)

    def test_update_ruleset_and_rulename(self):
        rule = tools.create_rule(self.__class__.__name__, "update")
        self.db.add_rule(rule)
        self.db.update_rule(rule.ruleset, rule.name, [("ruleset", "NewRS"),
                                                      ("name", "update_ok")])
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1, str(rules_for))
        self.assertRuleInMap(tools.create_rule("NewRS", "update_ok"),
                             rules_for)

    def test_update_unknown(self):
        self.assertRaises(ValueError, self.db.update_rule,
                          self.__class__.__name__,
                          "update_unknown",
                          [("name", "should_not_happen")])
        rule = tools.create_rule(self.__class__.__name__, "update_unknown")
        self.db.add_rule(rule)
        self.assertRaises(ValueError, self.db.update_rule,
                          self.__class__.__name__,
                          "dummy",
                          [("name", "should_not_happen")])


    def test_update_name_deps_simple(self):
        self.db.add_rule(tools.create_rule("RS", "r1"))
        self.db.add_rule(tools.create_rule("RS", "r2", dependson=set(['r1'])))
        self.db.update_rule("RS", "r1", [("name", "foo")])
        rules = self.db.get_rules_for("RS")
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 2)
        self.assertEquals(len(rules["r2"].dependson), 1)
        self.assertTrue("foo" in rules["r2"].dependson)

    def test_update_name_deps_multiple(self):
        self.db.add_rule(tools.create_rule("RS", "r1"))
        self.db.add_rule(tools.create_rule("RS", "r2", dependson=set(['r1'])))
        self.db.add_rule(tools.create_rule("RS", "r3", dependson=set(['r1', "r2"])))
        self.db.update_rule("RS", "r1", [("name", "foo")])
        rules = self.db.get_rules_for("RS")
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 3)
        self.assertEquals(len(rules["r2"].dependson), 1)
        self.assertTrue("foo" in rules["r2"].dependson)
        self.assertEquals(len(rules["r3"].dependson), 2)
        self.assertTrue("r2" in rules["r3"].dependson)
        self.assertTrue("foo" in rules["r3"].dependson)

    def test_update_ruleset_deps_multiple(self):
        self.db.add_rule(tools.create_rule("RS", "r1"))
        self.db.add_rule(tools.create_rule("RS", "r2", dependson=set(['r1'])))
        self.db.add_rule(tools.create_rule("RS", "r3", dependson=set(['r1', "r2"])))
        self.db.update_rule("RS", "r1", [("ruleset", "newRS")])
        rules = self.db.get_rules_for("RS")
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 2)
        self.assertEquals(len(rules["r2"].dependson), 0)
        self.assertEquals(len(rules["r3"].dependson), 1)
        self.assertTrue("r2" in rules["r3"].dependson)
        rules = self.db.get_rules_for("newRS")
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue("r1" in rules)

    def test_in_out_single(self):
        rule = tools.create_rule(self.__class__.__name__, "InOutSingle")
        self.db.add_rule(rule)
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), 1)
        self.assertRuleInMap(rule, rules_for)

        rules = self.db.get_rules_for(rule.ruleset)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue(rule.name in rules)

    def test_in_out_many(self):
        n = random.randint(5, 10)
        i = n
        rules = set()
        while (i > 0):
            rules.add(tools.create_rule(self.__class__.__name__,
                                        "InOutMany-%d" % i))
            rules.add(tools.create_rule(self.__class__.__name__ +
                                        "-%d" % i, "InOutMany"))
            i -= 1
        self.db.add_rules(rules)
        rules_for = self.db.get_rules_map()
        self.assertTrue(rules_for is not None)
        self.assertEquals(len(rules_for), n + 1, "Map: %s" % rules_for)
        self.assertEquals(len(rules_for[self.__class__.__name__]), n)
        while (n > 0):
            self.assertEquals(len(rules_for[self.__class__.__name__ +
                                            "-%d" % n]), 1)
            n -= 1


    def test_in_out_n_types(self):
        types = set(['foo@cat', 'bar@cut'])
        rule = tools.create_rule(self.__class__.__name__, "InOutNTypes",
                                 types=types)
        self.db.add_rule(rule)
        rules = self.db.get_rules_for(rule.ruleset)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue(rule.name in rules)
        self.assertEquals(set(rules[rule.name].types.keys()), types)


    def test_in_out_n_dependson(self):
        dependson = set(['foo', 'bar'])
        rule = tools.create_rule(self.__class__.__name__, "InOutNDependsOn",
                                 dependson=dependson)
        self.db.add_rule(rule)
        rules = self.db.get_rules_for(rule.ruleset)
        self.assertTrue(rules is not None)
        self.assertEquals(len(rules), 1)
        self.assertTrue(rule.name in rules)
        self.assertEquals(rules[rule.name].dependson, dependson)


    def test_checksum_same(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (copy_ruleset_h, copy_h_for) = self.db.checksum(rule1.ruleset)
        self.assertEquals(orig_ruleset_h.hexdigest(), copy_ruleset_h.hexdigest())
        self.assertEquals(len(orig_h_for), 2)
        self.assertEquals(len(copy_h_for), 2)
        self.assertEquals(orig_h_for["R1"].hexdigest(),
                          copy_h_for["R1"].hexdigest())

    def test_checksum_onemore(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule3 = tools.create_rule(self.__class__.__name__, "R3")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        self.db.add_rule(rule3)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)
        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertEquals(len(other_h_for), 3)

    def test_checksum_differentname(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2bis = tools.create_rule(self.__class__.__name__, "R2bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2bis)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)
        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R2"].hexdigest(),
                             other_h_for["R2bis"].hexdigest())

    def test_checksum_different_types(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", types=["type@cat"])
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)
        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R2"].hexdigest(),
                             other_h_for["R2"].hexdigest())

        self.db.remove_rules(rule1.ruleset)
        rule1 = tools.create_rule(self.__class__.__name__, "R1", types=["type@cat", "ALL"])
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)
        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R1"].hexdigest(),
                             other_h_for["R1"].hexdigest())


    def test_checksum_different_filter(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1", filter="f1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2", filter="f2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", filter="f2Bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)

        self.assertEquals(orig_ruleset_h.hexdigest(),
                          other_ruleset_h.hexdigest())
        self.assertEquals(orig_h_for["R2"].hexdigest(),
                          other_h_for["R2"].hexdigest())


    def test_checksum_different_action(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1", action="A1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2", action="A2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", action="A2Bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)

        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R2"].hexdigest(),
                             other_h_for["R2"].hexdigest())



    def test_checksum_different_depsfinder(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1", depsfinder="D1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2", depsfinder="D2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", depsfinder="D2Bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)

        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R2"].hexdigest(),
                             other_h_for["R2"].hexdigest())


    def test_checksum_different_dependson(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1", dependson=["D1"])
        rule2 = tools.create_rule(self.__class__.__name__, "R2", dependson=["D2"])
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", dependson="D2Bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)

        self.assertNotEquals(orig_ruleset_h.hexdigest(),
                             other_ruleset_h.hexdigest())
        self.assertNotEquals(orig_h_for["R2"].hexdigest(),
                             other_h_for["R2"].hexdigest())


    def test_checksum_different_comments(self):
        rule1 = tools.create_rule(self.__class__.__name__, "R1", comments="C1")
        rule2 = tools.create_rule(self.__class__.__name__, "R2", comments="C2")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (orig_ruleset_h, orig_h_for) = self.db.checksum(rule1.ruleset)

        self.db.remove_rules(rule1.ruleset)
        rule2 = tools.create_rule(self.__class__.__name__, "R2", comments="C2Bis")
        self.db.add_rule(rule1)
        self.db.add_rule(rule2)
        (other_ruleset_h, other_h_for) = self.db.checksum(rule1.ruleset)

        self.assertEquals(orig_ruleset_h.hexdigest(),
                          other_ruleset_h.hexdigest())
        self.assertEquals(orig_h_for["R2"].hexdigest(),
                          other_h_for["R2"].hexdigest())






