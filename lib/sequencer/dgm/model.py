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
DGM Model implementation
"""
from __future__ import print_function

from logging import getLogger, DEBUG, INFO
import os
import re
import shlex
import subprocess
from io import StringIO

from ClusterShell.NodeSet import NodeSet
from sequencer.commons import CyclesDetectedError, substitute, get_version,\
                                to_unicode, to_str_from_unicode
from sequencer.dgm.errors import UnknownDepError
from sequencer.ise.rc import FORCE_ALWAYS, FORCE_NEVER
from pygraph.algorithms.cycles import find_cycle
from pygraph.classes.digraph import digraph


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)

NONE = None
ALL = 'ALL'
FILTER_RE_OP = ['=~', '!~']
NOT_FORCE_OP = '^'

def _get_var_map(id_, name, type_, category, ruleset, rulename, help):
    """
    Returns the variable substitution mapping.
    """
    return {'%id': id_,
            '%name': name,
            '%type': type_,
            '%category': category,
            '%ruleset': ruleset,
            '%rulename': rulename,
            '%help': help
            }

VARS = _get_var_map(None, None, None, None, None, None, None).keys()

class FullType(object):
    """
    Implementation of a type of the form: type@category

    ALL is supported for both type and category.  When ALL alone is
    provided for a given type, it is equivalent to ALL@ALL and
    therefore, it matches anything.
    """

    def __init__(self, dbtype):
        (self.type, sep, self.category) = dbtype.rpartition('@')
        if len(self.type) == 0:
            if dbtype == ALL:
                self.type = ALL
                self.category = ALL
            else:
                raise ValueError("Can't find category separator '@' " + \
                                     "in given type: %s!" % dbtype)

    def match(self, component):
        """
        Returns true if the given component matches this type.
        """
        return (self.type == ALL or component.type == self.type) and \
            (self.category == ALL or component.category == self.category)

    def __str__(self):
        return self.type + '@' + self.category

    def __eq__(self, other):
        return self.type == other.type and self.category == other.category

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return self.type.__hash__() + self.category.__hash__()


def _is_all_filter(filter_):
    """
    Return true if the given filter is the special 'ALL' filter
    """
    return filter_ == ALL


def _is_none_filter(filter_):
    """
    Return true if the given filter is the special 'NONE' filter
    """
    return filter_ is NONE


class AbstractFilter(object):
    """
    Defines an abstract filter.
    """
    def filter(self, component):
        """
        Return true if the given component passes this filter, False
        otherwise.
        """
        raise NotImplementedError("Subclasses should implement this method")

class AllFilter(AbstractFilter):
    """
    This implementation always returns True.
    """
    def filter(self, component):
        return True

class NoneFilter(AbstractFilter):
    """
    This implementation always returns False.
    """
    def filter(self, component):
        return False

class CacheFilter(AbstractFilter):
    def __init__(self):
        AbstractFilter.__init__(self)
        self._cache = dict()
        self.docache = True

    def filter(self, component):
        """
        Perform caching before calling _filter_impl() if self.docache
        is True. Therefore, subclasses should redefined _filter_impl() instead
        of this method.
        """
        if self.docache:
            if component.id in self._cache:
                result = self._cache[component.id]
                if _LOGGER.isEnabledFor(DEBUG):
                    _LOGGER.debug("Component %s found in cache, returning %s",
                                  component.id, result)
            else:
                result = self._filter_impl(component)
                self._cache[component.id] = result
                if _LOGGER.isEnabledFor(DEBUG):
                    _LOGGER.debug("Component %s not found in cache, storing %s",
                                  component.id, result)
            return result
        return self._filter_impl(component)

    def _filter_impl(self, component):
        """
        Subclasses should implement this function
        """
        raise NotImplementedError("Subclasses should implement this method")

class ReFilter(CacheFilter):
    """
    This class implements a filter of the following forms:

    %var =~ pattern

    or

    %var !~ pattern

    where pattern is a regular expression.
    """
    def __init__(self, rule, var, eq, pattern):
        CacheFilter.__init__(self)
        self.rule = rule
        self.var = var
        self.eq = eq
        self.pattern = pattern

    def _filter_impl(self, component):
        var_map = _get_var_map(component.id,
                               component.name,
                               component.type,
                               component.category,
                               self.rule.ruleset,
                               self.rule.name,
                               self.rule.help)
        var_value = substitute(var_map, self.var)
        match = re.match(self.pattern, var_value)
        return (match and self.eq == '=~') or (not match and self.eq == '!~')

class ScriptFilter(CacheFilter):
    """
    This class implements a script filter.
    """
    def __init__(self, rule):
        CacheFilter.__init__(self)
        self.rule = rule

    def _filter_impl(self, component):
        var_map = _get_var_map(component.id,
                               component.name,
                               component.type,
                               component.category,
                               self.rule.ruleset,
                               self.rule.name,
                               self.rule.help)

        cmd_string = substitute(var_map, self.rule.filter)
        cmd = shlex.split(to_str_from_unicode(cmd_string, should_be_uni=True))
        _LOGGER.debug("%s: calling filter cmd: %s", self.rule.name, cmd)
        try:
            popen = subprocess.Popen(cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     bufsize=-1) # Use system default
        except OSError as ose:
            _LOGGER.error("%s: can't call filter '%s': %s",
                          self.rule.name, cmd_string, ose)
            return False

        (msg_std, msg_err) = popen.communicate()
        msg_std = msg_std.strip()
        msg_err = msg_err.strip()
        _LOGGER.debug("%s: output of filter command %s on component %s: %s",
                      self.rule.name, cmd_string, component, msg_std)
        if len(msg_err) != 0:
            _LOGGER.warning("%s: error when applying filter command " + \
                                "%s to component %s: %s",
                            self.rule.name, cmd_string,
                            component, msg_err)
        _LOGGER.debug("%s: filter command: %s RC: %d",
                      self.rule.name,
                      cmd_string,
                      popen.returncode)

        return popen.returncode == os.EX_OK


def _find_match(rules, components):
    """
    Returns a mapping {component.id: (rule, ..., )} representing rules
    that should be applied to each component
    """
    result = {}
    for component in components:
        for rule in rules:
            if rule.match_type(component):
                if rule.pass_filter(component):
                    #test_unicode("%s" % component, False, 'FIND_MATCH')
                    _LOGGER.debug("Component %s has been" + \
                                  " filtered in by rule %s ",
                                  component, rule)
                    ruleset = result.get(component.id, set())
                    ruleset.add(rule)
                    result[component.id] = ruleset
                else:
                    _LOGGER.info("Component %s has been" + \
                                 " filtered out by rule %s ",
                                 component, rule)
    return result

def _update_graph_with_node(graph, node):
    """
    Update the given graph with the given node name
    """
    if not graph.has_node(node):
        graph.add_node(node)

def _update_graph_with_edge(graph, edge):
    """
    Update the given graph with the given edge name
    """
    if not graph.has_edge(edge):
        graph.add_edge(edge)


class Rule(object):
    """
    This class represents a single rule.
    The following parameters have the following constraints:
    None value will raise an exception for the following fields:
      ruleset, name, types
    Empty value will raise an exception for the following fields:
      types, filter, depsfinder
    """

    def __init__(self,
                 ruleset,
                 name,
                 types,
                 filter_,
                 action,
                 depsfinder,
                 dependson,
                 comments, 
                 help):

        if (ruleset is None or \
                name is None or \
                types is None):
            raise ValueError("None is an invalid value for: " + \
                                 " ruleset, name, types")

        if len(types) == 0 or \
                (filter_ is not None and len(filter_) == 0) or \
                (depsfinder is not None and len(depsfinder) == 0):
            raise ValueError("Empty content is invalid for: " + \
                                 " types, filter and depfinders")

        self.ruleset = ruleset
        self.name = name
        self.types = dict()
        for type_ in types:
            self.types[type_] = FullType(type_)
        self.filter = filter_
        self._filter_impl = self._get_filter_impl_from(filter_)
        self.action = action
        self.depsfinder = depsfinder
        # if None convert to an empty set to prevent special case treatment.
        self.dependson = set() if dependson is None else set(dependson)
        self.comments = comments
        self.help = help

    def __eq__(self, other):
        return self.ruleset == other.ruleset and self.name == self.name

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def __hash__(self):
        return self.ruleset.__hash__() + self.name.__hash__()

    def match_type(self, component):
        """
        Returns True if component matches this rule. False otherwise.
        """
        for type_ in self.types:
            if self.types[type_].match(component):
                return True
        return False

    def _get_filter_impl_from(self, filter_):
        """
        Returns a filter object related to the given filter_.
        """
        if _is_all_filter(filter_):
            return AllFilter()
        if _is_none_filter(filter_):
            return NoneFilter()
        for var in VARS:
            # The filter starts with a known variable: it is a regexp
            # We try to look after a string that looks like:
            # %id =~ a pattern
            match = re.match("("+ var + ")\s*([!=]~)\s*(\S*)", filter_)
            if match:
                _LOGGER.debug("Regexp filter for variable: %s", var)
                eq = match.group(2)
                if eq not in FILTER_RE_OP:
                    raise ValueError(("Invalid filter operator - %s! " + \
                                          "Expecting one of %s ") % \
                                         (eq, FILTER_RE_OP))
                return ReFilter(self, var, eq, match.group(3))
        return ScriptFilter(self)

    def set_filter_caching_policy(self, docache):
        """
        Specifies filter caching policy
        """
        self._filter_impl.docache = docache


    def pass_filter(self, component):
        """
        Return true if the given component passes this rule
        filter. False otherwise.
        """
        return self._filter_impl.filter(component)

class RuleSet(object):
    """
    Represents a set of rules in the dependency table.
    """
    def __init__(self, rules):
        # Field name and rules_for are really initialized in the
        # _make_graph() method
        self.rules = set(rules)
        self.rules_for = dict()
        self.name = None
        self.dag = digraph()
        self._make_graph()
        self._check_deps()
        self.root_rules_for = self._compute_root_rules_mapping()
        if self.name is not None:
            _LOGGER.debug("root_rules mapping for %s is: %s",
                          self.name, ", ".join(self.root_rules_for))
        # Cycles are allowed in the graph rules. Example are:
        # TALIM -> TALIM and
        # TALIM -> ETH Switch -> TALIM
        #self._check_cycles()

    def _make_graph(self):
        """
        Make the rules graph. The field 'dag' is updated.
        """
        for rule in self.rules:
            self.rules_for[rule.name] = rule
            # The first rule of the given rules set gives this RuleSet name
            if self.name is None:
                self.name = rule.ruleset
            elif rule.ruleset != self.name:
                raise ValueError(("Rule (%s, %s) does not belong " + \
                                      "to ruleset %s") % (rule.ruleset,
                                                          rule.name,
                                                          self.name))

            _update_graph_with_node(self.dag, rule.name)
            for dep_rule in rule.dependson:
                _update_graph_with_node(self.dag, dep_rule)
                self.dag.add_edge((rule.name, dep_rule))

    def _check_deps(self):
        """
        Check that each dependencies specified by each rule in the
        ruleset are valid.
        """
        for rule in self.rules:
            for dep_rule in rule.dependson:
                if dep_rule not in self.rules_for:
                    raise UnknownDepError(rule, dep_rule)

    def _check_cycles(self):
        """
        Raise a CyclesDetectedError if a cycle is detected.
        """
        cycles = find_cycle(self.dag)
        if cycles:
            raise CyclesDetectedError(cycles, self.dag)

    def get_rules_graph(self):
        """
        Return the rules graph.
        """
        return self.dag

    def get_depgraph(self, components, force_rule=list(), docache=True):
        """
        Return a DepGraph instance representing the components
        dependency graph.
        """
        depgraph = DepGraph(self, components, force_rule, docache)
        return depgraph

    def _compute_root_rules_mapping(self, types=None):
        """
        Compute the root rules mapping, i.e. the set of rules that
        will be applied to a component given on the command line
        (the initial set).

        The result is a mapping {fulltype : [rule1, rule2, ..., ruleN]}
        """
        if types is None:
            types = dict()
        roots = set()

        def _update_types(rules):
            """
            Update the result types for the given set of rules.
            """
            for rule in rules:
                for type_ in rule.types:
                    # Check wether other root rules are available
                    # for type_ or if the current rule is not a
                    # real root rule (another parent rule already
                    # matched)
                    if type_ in types and not types[type_].issubset(rules):
                        _LOGGER.debug("Type %s is already mapped" + \
                                      " skipping rule %s",
                                      type_, rule.name)
                    else:
                        _LOGGER.debug("Adding rule %s to type %s",
                                      rule.name, type_)
                        rules = types.setdefault(type_, set())
                        rules.add(rule)

        # Finding roots in the graph
        for rule in self.rules:
            if len(self.dag.incidents(rule.name)) == 0:
                roots.add(rule)

        if len(roots) == 0:
            if len(self.rules) == 0:
                return types
            _LOGGER.debug("Cycle found: any rule is a potential root")
            _update_types(self.rules)
            return types
        # We do have roots
        _update_types(roots)
        # Remove roots, and start again
        new_ruleset = RuleSet(self.rules - roots)
        return new_ruleset._compute_root_rules_mapping(types)

    def _find_roots(self, components):
        """
        Return a mapping {component.id: (rule1, ...)} where
        rule1,... are roots rules to apply to the component.

        Roots here does not mean absolute 'roots' in the sense that
        for the famous example:
        nfs1#node cd0#colddoor

        nfs1#node may start first while it might have been expected
        that cd0#colddoor will instead (since #R1:#colddoor->R2:#node).
        The depgraph making does not requires absolute 'roots' to be
        started first.

        The main problem arises however with rule dependencies on same type
        such as: R1:#mngt->R2:#mngt. In this specific case, we must start
        from R1 for a component of type #mngt, not from R2. This is what
        this method actually returns.
        """
        if _LOGGER.isEnabledFor(DEBUG):
            _LOGGER.debug("Looking at potential roots in components: %s",
                          ",".join([str(x) for x in components]))

        roots = set()
        for component in components:
            for fulltype in self.root_rules_for:
                if FullType(fulltype).match(component):
                    roots.update(self.root_rules_for[fulltype])

        return _find_match(roots, components)

class Component(object):
    """
    A component is defined from a string of the form: name#type@cat
    Both name and type are mandatory.
    """

    def __init__(self, *args):
        if len(args) == 1:
            self.id = args[0]
            (name, sep, type_cat) = self.id.rpartition("#")
            (type_, sep, category) = type_cat.rpartition("@")
            if len(name) == 0 or len(type_) == 0:
                raise ValueError("Type and category are mandatory " + \
                                 "arguments " + \
                                 "in component definition. " + \
                                 "Use name#type@category. " + \
                                 "Got: %s" % args)
            self.name = name
            self.type = type_
            self.category = category
        elif len(args) == 3:
            self.name = args[0]
            if args[1] is None or len(args[1]) == 0 or \
                    args[2] is None or len(args[2]) == 0:
                raise ValueError("Type and category are mandatory " + \
                                 "arguments " + \
                                 "in component definition. " + \
                                 "Use name#type@category. " + \
                                 "Got: %s" % set(args))
            self.type = args[1]
            self.category = args[2]
            self.id = self.name + '#' + self.type + "@" + self.category

        else:
            raise ValueError("Wrong number of arguments: %d. Expecting: %d" %\
                                 (len(args), 3))

        self.fulltype = FullType(self.type + '@' + self.category)
        self.actions = {}

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        #print("STR")
        return "%s" % (self.id)
        #return "%s" % to_str_from_unicode(self.id, should_be_uni=True)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


class DepGraph(object):
    """
    Represents a component dependency graph.  Public fields are:

    'ruleset': the ruleset from which this instance has been created.

    'dag': the pygraph instance representing the dependency graph.

    'components_map': a mapping 'id': Component instance of all
    components in the dependency graph
    """
    def __init__(self, ruleset, requested_components,
                 force_rule=list(), docache=True):
        self.remaining_components = requested_components
        self.ruleset = ruleset
        self.dag = digraph()
        self.components_map = dict()
        self.force_for_rule = dict()
        # Set each filter 'docache'' to their specified value
        for rule in self.ruleset.rules_for.values():
            rule.set_filter_caching_policy(docache)
        for rulename in force_rule:
            mode = FORCE_ALWAYS
            if rulename[0] == NOT_FORCE_OP:
                rulename = rulename[1:]
                mode = FORCE_NEVER
            if rulename not in self.ruleset.rules_for:
                raise ValueError("Unknown rule: %s" % rulename + \
                                     " in ruleset: %s" % self.ruleset.name + \
                                     " for force option: %s" % force_rule)
            self.force_for_rule[rulename] = mode

        # Last instruction that computes the actual dependency graph
        self._compute()


    def _compute(self):
        """
        Compute the dependency graph.
        """
        # Each components requested becomes nodes in the dependency
        # graph.
        for component in self.remaining_components:
            self.dag.add_node(component.id)
            self.components_map[component.id] = component

        # For each requested nodes
        while (len(self.remaining_components) != 0):
            # We find roots (component from which rules can start
            # being applied)
            roots = self.ruleset._find_roots(self.remaining_components)
            if roots is None or len(roots) == 0:
                _LOGGER.debug("No roots found. Stopping.")
                break
            _LOGGER.debug("Roots found: %s", ",".join(roots))
            for component_id in roots:
                component = self.components_map[component_id]
                self.remaining_components.remove(component)
                # Apply each rule applicable to a given root
                for rule in roots[component_id]:
                    self._apply(rule, component)

    def _apply(self, rule, component):
        """
        Application of a rule to a component
        """
        # Find out if the rule has already been applied to the given
        # component

        attributes = self.dag.node_attributes(component.id)
        for (rulename, action) in attributes:
            last_rule_char = rulename.rfind('?')
            if last_rule_char != -1:
                rulename = rulename[0:last_rule_char]
            if rulename == rule.name:
                _LOGGER.debug("Rule %s already applied to %s." + \
                              " Application skipped",
                              rule.name, component)
                return

        # Fetch all dependencies of the component first!
        rules_for = self._get_deps(component, rule)
        for id_ in rules_for:
            # For each dependency, create an edge from the current
            # component to the dependency
            edge = (component.id, id_)
            _update_graph_with_edge(self.dag, edge)
            edge_label = []
            for dep_rule in rules_for[id_]:
                # For each rule applicable to the dependency, applies
                # it.
                self._apply(dep_rule, self.components_map[id_])
                edge_label.append(dep_rule.name)
            self.dag.set_edge_label(edge, ", ".join(edge_label))

        # All dependencies have been treated, update the component.
        self._update_from(rule, component)

    def _update_from(self, rule, component):
        """
        Update the component with its action. Substitution of
        variables is done.
        """
        # Substitute variable names by their value in the action
        # string first.

        var_map = _get_var_map(component.id,
                               component.name,
                               component.type,
                               component.category,
                               self.ruleset.name,
                               rule.name,
                               rule.help)

        action = substitute(var_map, rule.action)
        _LOGGER.info("%s.action(%s): %s", rule.name, component.id, action)
        key = rule.name
        force = self.force_for_rule.get(rule.name)
        if force is not None:
            key += '?force=' + force
        if action is not None:
            self.dag.add_node_attribute(component.id, (key, action))
            component.actions[key] = action

    def _get_deps(self, component, rule):
        """
        Find dependencies of a given component. This implies calling
        the rule.depsfinder script. Substitution of variables is done.
        Returns None if the given rule has already been applied on
        the given component.
        """
        result = dict()
        depsfinder = rule.depsfinder
        if rule.dependson is None or len(rule.dependson) == 0 or \
                depsfinder is None or len(depsfinder) == 0:
            _LOGGER.debug("No 'DepsFinder' or 'DependsOn' specified" + \
                              " in rule %s for component %s. Skipping.",
                          rule, component)
            return result
        var_map = _get_var_map(component.id,
                               component.name,
                               component.type,
                               component.category,
                               self.ruleset.name,
                               rule.name,
                               rule.help)
        cmd = substitute(var_map, depsfinder)
        _LOGGER.debug("Calling depsfinder for component %s: %s", component, cmd)
        popen_args = shlex.split(to_str_from_unicode(cmd, should_be_uni=True))
        try:
            popen = subprocess.Popen(popen_args,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     bufsize=-1) # Use system default
        except OSError as ose:
            _LOGGER.error("Can't call depsfinder '%s': %s", cmd, ose)
            return result

        (msg_std, msg_err) = popen.communicate()
        msg_std = msg_std.strip()
        msg_err = msg_err.strip()
        if len(msg_err) != 0:
            _LOGGER.warning("Depsfinder error when " + \
                                "applying rule %s to component %s: %s",
                            rule, component, msg_err)
        deps = set()
        with StringIO(to_unicode(msg_std)) as reader:
            for dep in reader:
                dep_id = dep.strip()
                if len(dep_id) == 0:
                    continue
                dependency = self.components_map.get(dep_id)
                if dependency is None:
                    _LOGGER.debug("Creating dep for component %s with id: %r",
                                  component, dep_id)
                    dependency = Component(dep_id)
                    self.components_map[dep_id] = dependency

                deps.add(dependency)
                _update_graph_with_node(self.dag, dep_id)

        if _LOGGER.isEnabledFor(INFO):
            _LOGGER.info("%s.depsfinder(%s): %s",
                         rule.name, component.id,
                         NodeSet.fromlist([str(x.id) for x in deps]))
        # Find match only on rule.dependson
        return _find_match([self.ruleset.rules_for[x] for x in rule.dependson],
                           deps)

