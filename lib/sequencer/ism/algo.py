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
ISM Algorithm implementation

Implements the actual algorithm that transforms a graph (usually
computed by the DGM) into a sequence for execution.

The result is a tuple (ise_model, xml) where xml is the XML that
has been generated for the creation of the ise_model.

Graph should be a dag. Its nodes should have the following attributes:
- rule.name -> rule.action: the action to execute.
"""
from __future__ import print_function

import logging

import clmsequencer.ise.model as ise_model
from clmsequencer.commons import SequencerError, CyclesDetectedError, \
     get_version, remove_leaves
from clmsequencer.ise.parser import ACTION, SEQ, PAR, ISE, \
    NS_SEQ_TAG, DEPS_ATTR
from clmsequencer.ise.rc import FORCE_ALLOWED
from lxml import etree as ET
from pygraph.algorithms.critical import transitive_edges
from pygraph.algorithms.cycles import find_cycle
from pygraph.algorithms.sorting import topological_sorting


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = logging.getLogger(__name__)

REMOTE_CHAR = '@'

def _check_valid(graph):
    """
    Check that the given graph is valid. This function does not return
    anything. It raise an exception however if the graph is considered
    invalid.
    """
    if graph is None:
        raise ValueError("The given graph is None!")

    if not graph.DIRECTED:
        raise ValueError("The given graph is not a directed graph!")

    cycle = find_cycle(graph)
    if len(cycle) != 0:
        _LOGGER.error("A cycle has been detected")
        raise CyclesDetectedError(cycle, graph)


def _remove_useless_deps(graph):
    """
    Remove useless dependencies such as: A->B->C, A->C. In such a
    case, A->C is useless. Such edge will be removed in the given graph.
    """
    useless_edges = transitive_edges(graph)
    for edge in set(useless_edges):
        _LOGGER.info("Removing useless dependency: %s", edge)
        graph.del_edge(edge)

def _remove_useless_nodes(graph):
    """
    Remove useless nodes i.e. nodes with no attributes are nodes with
    no actions and can therefore be removed.
    """
    for node in graph.nodes():
        attributes = graph.node_attributes(node)
        if len(attributes) == 0:
            _LOGGER.info("Removing useless node (no action): %s", node)
            parents = frozenset(graph.incidents(node))
            children = frozenset(graph.neighbors(node))
            for parent in parents:
                _LOGGER.debug("Removing edge: %s -> %s", parent, node)
                graph.del_edge((parent, node))
                for child in children:
                    if graph.has_edge((node, child)):
                        _LOGGER.debug("Removing edge: %s -> %s", node, child)
                        graph.del_edge((node, child))
                    _LOGGER.debug("Adding edge: %s -> %s", parent, child)
                    graph.add_edge((parent, child))
            graph.del_node(node)

def _prepare(graph, options=None):
    """
    Perform various preparation on the given graph according to given
    options.
    """
    _check_valid(graph)
    _remove_useless_deps(graph)
    _remove_useless_nodes(graph)

def _get_cmd_remote_from(cmd):
    """
    From the command attribute, remove remote prefix
    and return a tuplet (cmd, remote)
    Note: the command may contain other prefix if any.
    Note: remote is an XML boolean value hence, a string "true" or "false"
    """
    # Command might be of the following forms: cmd, +cmd, @cmd, @+cmd, +@cmd
    if cmd[0] == REMOTE_CHAR:
        remote = "true"
        cmd = cmd[1:]
    elif cmd[1] == REMOTE_CHAR:
        remote = "true"
        cmd = cmd[0] + cmd[2:]
    else:
        remote = "false"

    return (cmd, remote)

def _get_info_from(node, attribute):
    """
    return a tuple (id, {param: value, ..}) for the given graph node
    and attributes.
    """
    param_char = attribute[0].rfind('?')
    params = dict()
    if param_char == -1:
        rulename = attribute[0]
    else:
        rulename = attribute[0][0:param_char]
        paramstring = attribute[0][param_char + 1:]
        for keyval in paramstring.split('&'):
            (key, sep, val) = keyval.partition('=')
            params[key] = val

    return (node + "/" + rulename, params)

def _create_actions_from(node, graph, create_deps=False):
    """
    Create an XML action from the given node in the given graph.  if
    'create_deps' is True, dependencies are expressed explicitely
    (using the 'deps' action XML attribute)
    """
    actions = []
    attributes = graph.node_attributes(node)
    for attribute in attributes:
        # attribute is of the following form:
        # <attribute attr="rulename?param=value" value="@echo oberon105"/>
        (cmd, remote) = _get_cmd_remote_from(attribute[1])
        (id_, params) = _get_info_from(node, attribute)
        component_set = node
        if create_deps:
            deps = []
            for dep in graph.neighbors(node):
                dep_attributes = graph.node_attributes(dep)
                for dep_attribute in dep_attributes:
                    deps.append(_get_info_from(dep, dep_attribute)[0])
            action = ACTION(cmd,
                            id=id_,
                            component_set=component_set,
                            deps=",".join(deps),
                            remote=remote,
                            force=params.get('force', FORCE_ALLOWED))
        else:
            action = ACTION(cmd,
                            id=id_,
                            component_set=component_set,
                            remote=remote,
                            force=params.get('force', FORCE_ALLOWED))
        actions.append(action)


    if len(actions) == 0:
        _LOGGER.info("No action found for: %s --> removed", node)

    return actions


def _make_instruction_from(node_action_set):
    """
    Return the instruction for the given set of actions.  The result
    is either a SEQ when the set contains more than one action, the action
    itself if the set contains only one action, or None if the set is
    empty.
    """
    assert node_action_set is not None

    nb = len(node_action_set)
    if nb == 0:
        return None

    if nb == 1:
        return node_action_set[0]

    assert len(node_action_set) > 1, "%r" % node_action_set
    return SEQ(*node_action_set)

def _create_final_xml_from(actions, ise_structure):
    """
    Create the final XML document from the given set of actions.  The
    given ise_structure is either a SEQ or a PAR. It is used only if
    len(actions) > 1

    This method returns a tuple (ise_model, xml_document,
    error).  if ise_model is None, error is the exception
    that has been raised.
    """
    if len(actions) > 1:
        # Several actions should be enclosed by either a SEQ or a PAR
        # ISE structure.
        xml_result = ISE(ise_structure(*actions))
    elif len(actions) == 1:
        # We only have a single action, no need to include it in a PAR
        # or a SEQ.
        xml_result = ISE(actions[0])
    else:
        # No action at all, make an empty document, PAR or SEQ is not
        # required either.
        _LOGGER.warning("No actions found at all!")
        xml_result = ISE()

    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug("XML result is: %s",
                      ET.tostring(xml_result, pretty_print=True))

    # Gives the XML to the model so various check can be performed!
    model = None
    error = None
    # Do not prevent cycle detections from writing the XML result to a
    # file. This can be used for debugging purpose!
    try:
        model = ise_model.Model(xml_result)
    except SequencerError as se:
        error = se

    return (model, xml_result, error)

def order_seq_only(graph):
    """
    A topological sort is performed on the graph. All actions are
    enclosed into a Sequence ISE structure.
    """
    _prepare(graph)
    nodes = topological_sorting(graph.reverse())
    actions = []
    for node in nodes:
        actions.extend(_create_actions_from(node, graph, create_deps=False))

    return _create_final_xml_from(actions, SEQ)


def order_par_only(graph):
    """
    All instructions are executed within a Parallel ISE
    structure. Dependencies are specified using explicit dependencies
    (the deps ISE Action XML attribute).
    """
    _prepare(graph)
    instructions = []
    for node in graph.nodes():
        node_action_set = _create_actions_from(node, graph, create_deps=True)
        i = _make_instruction_from(node_action_set)
        if (i is not None):
            instructions.append(i)

    return _create_final_xml_from(instructions, PAR)



def _make_deps_leaf(node, node_action_set):
    """
    Return the instruction for a leaf.
    """
    _LOGGER.debug("Node %s is a leaf", node)
    return _make_instruction_from(node_action_set)

def _optimal_xml_block_for_root(graph, root, xml_cache):
    """
    Return the optimal XML block for the given root node.
    Note: the given 'root' *must* be a root in the graph!

    xml_cache maps a node with its already computed xml block

    For a given (non-computed) node, the XML is created using the
    following schema:

    Create a PAR that includes each node.deps.
    Create a SEQ between the node and the created PAR.
    return the SEQ as the XML block.

    Things to take care of:
    Multiple actions -> SEQ
    No deps -> NO PAR, NO SEQ, just an ACTION
    Single Dep -> SEQ only
    Mutlipte Deps -> SEQ(PAR(deps), node)

    When a dep is already in the cache, an explicit dependency should
    be made instead of an implicit SEQ.
    """

    def _make_explicit_deps(node_action_set, dep):
        """
        Update each action of the given set so they include given dep
        in their explicit dependencies. The new set is returned.
        """
        deps = []
        dep_attributes = graph.node_attributes(dep)
        for dep_attribute in dep_attributes:
            deps.append(_get_info_from(dep, dep_attribute)[0])
        for action in node_action_set:
            new_deps = ",".join(deps)
            current_deps = action.get(DEPS_ATTR)
            if (current_deps is None):
                current_deps = new_deps
            else:
                current_deps = current_deps + "," + new_deps
            action.set(DEPS_ATTR, current_deps)
        return node_action_set


    def _make_deps_single(node, node_action_set, dep):
        """
        Return the instruction for a node in the graph with a single
        dependency.
        """
        # Only one child: make a SEQ with it directly
        xml_block = _xml_block_for(graph, dep)
        if (xml_block is None):
            # Child XML block has already been computed
            # Make an explicit dependency
            _LOGGER.debug("Making %s an explicit dependency of %s", dep, node)
            node_action_set = _make_explicit_deps(node_action_set, dep)
            return _make_instruction_from(node_action_set)

        # A child does exist.
        if (xml_block.tag == NS_SEQ_TAG):
            _LOGGER.debug("Making %s an implicit dependency of %s (merging)",
                          dep, node)
            # It is already a sequence, we should merge with it
            for action in node_action_set:
                xml_block.append(action)
            return xml_block

        # Make an implicit dependency
        _LOGGER.debug("Making %s an implicit dependency of %s", dep, node)
        return SEQ(xml_block, _make_instruction_from(node_action_set))

    def _make_deps_several(node, node_action_set, deps):
        """
        Return the instruction for a node in the graph with several
        dependencies.
        """
        par_dep = []
        for dep in deps:
            xml_block = _xml_block_for(graph, dep)
            if (xml_block is None):
                # This dep XML block has already been computed
                # Make an explicit dependendy
                _LOGGER.debug("Making %s an explicit dependency of %s", dep, node)
                node_action_set = _make_explicit_deps(node_action_set, dep)
            else:
                # Add dep to the PAR group of implicit dependency
                _LOGGER.debug("Making %s an implicit dependency of %s", dep, node)
                par_dep.append(xml_block)

        if (len(par_dep) == 0):
            # No PAR has been computed, therefore the SEQ is also useless
            return _make_instruction_from(node_action_set)
        elif (len(par_dep) == 1):
            # PAR is useless, but not the SEQ!
            if (par_dep[0].tag == NS_SEQ_TAG):
                # Dep is already a SEQ, merge with it
                for action in node_action_set:
                    par_dep[0].append(action)
                return par_dep[0]
            # Add the SEQ
            return SEQ(par_dep[0], _make_instruction_from(node_action_set))

        return SEQ(PAR(*par_dep), _make_instruction_from(node_action_set))


    def _make_deps(node, node_action_set, deps):
        """
        Return the instruction for the given node with the given
        action set and dependencies.
        """
        if (len(deps) == 0):
            return _make_deps_leaf(node, node_action_set)

        if (len(deps) == 1):
            return _make_deps_single(node, node_action_set, deps[0])

        # Several dependencies
        assert len(deps) > 1

        return _make_deps_several(node, node_action_set, deps)


    # Internal recursive function
    def _xml_block_for(graph, node):
        """
        Return the XML block or None if the given node has already
        been processed
        """
        _LOGGER.info("Treating %s", node)
        if (node in xml_cache):
            _LOGGER.debug("Given node %s is already in cache.", node)
            return None
        # Start creating the XML for the given node
        # Dependencies will be updated afterwards when required
        node_action_set = _create_actions_from(node,
                                               graph,
                                               create_deps=False)
        deps = graph.neighbors(node)
        instruction = _make_deps(node, node_action_set, deps)
        xml_cache[node] = instruction
        return instruction

    return _xml_block_for(graph, root)

def order_optimal(graph):
    """
    The optimal solution does the following:

    1. Starts from root nodes
    2. for each such root node, create the optimal xml block
    3. make a PAR block with those roots node

    """
    _prepare(graph)
    nodes = graph.nodes()
    xml_cache = dict()
    roots = []
    for node in nodes:
        # Starts from root nodes
        if (len(graph.incidents(node)) == 0):
            instruction = _optimal_xml_block_for_root(graph, node, xml_cache)
            if (instruction is not None):
                roots.append(instruction)

    # roots elements cat be started in parallel
    return _create_final_xml_from(roots, PAR)

def order_mixed(graph):
    """
    This algorithm does the following: it starts from
    leaves. Add them into a Parallel ISE structure. It removes
    leaves. And starts again. Each such parallel structure is enclosed into
    a Sequential ISE structure. That's it.

    This algorithm is correct: it ensure that dependencies will get
    executed first, efficient, most independent instructions will get
    executed in parallel but *not* optimal!

    However this algorithm have one major problems: it layers set of
    independent instructions one after the other making artificial dependencies
    between all instructions of layer n-1 to layer n. Therefore, if a single
    action returns an error at layer n, all instructions at layer n-1 will not
    be executed. This is the major problem.

    As a side effect, each action at layer n-1 will have s(n)
    dependencies on each action at layer n (action set at layer n is of
    size s(n)). Therefore the number of edges in the final graph is in
    Sum(s(i-1)*s(i)) for all i in [1, n] where n is the last action set
    with no dependencies.

    For clusters with thousands of nodes, this can lead to a very huge
    number of edges (count several gigabytes of memory for their internal
    representations)!

    E.g: a->b, a->c, d->b, it returns seq(par(b,c),par(a,d)). And therefore
    d will have to wait the end of both b and c while only b is
    required.
    """
    _prepare(graph)

    nodes = graph.nodes()
    par_list = []
    while len(nodes) > 0:
        instructions = []
        leaves = []
        for node in nodes:
            _LOGGER.debug("Node: %s", node)
            if len(graph.neighbors(node)) == 0:
                leaves.append(node)
                node_action_set = _create_actions_from(node,
                                                       graph,
                                                       create_deps=False)
                i = _make_instruction_from(node_action_set)
                if (i is not None):
                    instructions.append(i)

        if len(instructions) > 1:
            par_list.append(PAR(*instructions))
        elif len(instructions) == 1:
            par_list.append(instructions[0])
        else:
            _LOGGER.debug("No instructions found in nodes: %s", nodes)
        remove_leaves(graph, leaves)
        nodes = graph.nodes()

    return _create_final_xml_from(par_list, SEQ)

