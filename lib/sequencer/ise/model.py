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
ISE Model implementation
"""
from __future__ import print_function

import uuid
from logging import getLogger

from sequencer.commons import InternalError, CyclesDetectedError, get_version
from sequencer.ise import parser
from sequencer.ise.errors import BadDepError, UnknownDepsError
from pygraph.algorithms.cycles import find_cycle
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import AdditionError


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)

def _get_element_from_xml(element, dag):
    """
    Return the model element from the given dag.
    """
    if element.tag == parser.NS_SEQ_TAG:
        return Sequence(element, dag)
    elif element.tag == parser.NS_PAR_TAG:
        return Parallel(element, dag)
    elif element.tag == parser.NS_ACTION_TAG:
        return Action(element, dag)
    else:
        raise InternalError("Unknown element: " + str(element))

def _add_all_edges(src_set, dest_set, graph):
    """
    Create edges from all src_set element to each element in dest_set in the given graph.
    """
    for src in src_set:
        for dst in dest_set:
            _add_edge(src, dst, graph)

def _add_edge(src, dst, graph):
    """
    Add src -> dst edge in the given graph. Add corresponding nodes if required.
    """
    if not graph.has_node(src):
        graph.add_node(src)
    if not graph.has_node(dst):
        graph.add_node(dst)
    _LOGGER.debug("Creating: %s -> %s", src, dst)
    try:
        graph.add_edge([src, dst])
    except AdditionError as addition_error:
        # This (probably) means that the edge already exists.
        # Display the error to get sure it is what we expect anyway.
        _LOGGER.error(str(addition_error))
        raise BadDepError([src, dst])

class Model(object):
    """
    The ISE model. An XML tree is parsed and transformed into such a model.
    """
    def __init__(self, root):
        self.instructions = []
        self.actions = {}
        self.deps = set()
        self.dag = digraph()
        for element in list(root):
            tree = _get_element_from_xml(element, self.dag)
            self.instructions.append(tree)
            self.actions.update(tree.actions)
            self.deps.update(tree.deps)
        self.check_deps()
        self.check_cycles()

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def check_deps(self):
        """
        We didn't find a good way to express in the XSD the constraint
        that deps should refer to valid id. Therefore, we implement
        the check here, in the model.

        Raise an UnknownDepError if some explicit dependencies refer to unknown ids
        """
        ids = self.actions.keys()
        unknown_deps = self.deps.difference(ids)
        if len(unknown_deps) != 0:
            raise UnknownDepsError(unknown_deps)

    def check_cycles(self):
        """
        Raise a CyclesDetectedError if a cycle is detected.
        """
        cycles = find_cycle(self.dag)
        if cycles:
            raise CyclesDetectedError(cycles, self.dag)

class InstructionBase(object):
    """
    Base class for any instruction: action, seq or par
    List of fields:
    description - the description string as given in the XML element.
    actions - the set of actions (a singleton for action, a set for par and seq)
    deps - the set of explicit dependencies
    starting_set - ids that represents this instruction start
    ending_set - ids that represents this instruction end
    """
    def __init__(self, element):
        self.description = element.get(parser.DESC_ATTR, parser.DEFAULT_DESC)
        self.actions = {}
        self.deps = set()

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

class InstructionsContainer(InstructionBase):
    """Base class for container type instructions: seq or par"""
    def __init__(self, element, dag):
        InstructionBase.__init__(self, element)
        self.instructions = []
        for item in list(element):
            instruction = _get_element_from_xml(item, dag)
            self.instructions.append(instruction)
            self.actions.update(instruction.actions)
            self.deps.update(instruction.deps)



class Sequence(InstructionsContainer):
    """
    This class represents a sequence in the ISE model.
    """
    def __init__(self, element, dag):
        InstructionsContainer.__init__(self, element, dag)
        if self.instructions:
            # Starts from first instructions of first block
            self.starting_set = self.instructions[0].starting_set
            # Ends at last instructions of last block
            self.ending_set = self.instructions[-1].ending_set
        # The graph edges are only updated within a sequence
        self._update_graph_edges(dag)
        _LOGGER.debug("New object: %s", self)

    def __str__(self):
        return "SEQ(%s)" % ", ".join([str(x) for x in self.instructions])

    def _update_graph_edges(self, dag):
        """
        Update the graph edges for the given sequence
        """
        # This is the only type that creates edges in the graph
        dep = None
        for i in self.instructions:
            _LOGGER.debug("%s: starting_set=%s, ending_set=%s",
                          i, i.starting_set, i.ending_set)

            # First element does not have any dependencies in a sequence
            if (dep is not None):
                # Current element has an implicit (seq) dependency:
                # all its starting actions should wait until
                # dependency ending actions has completed.
                _add_all_edges(i.starting_set, dep.ending_set, dag)

            dep = i

class Parallel(InstructionsContainer):
    """
    This class represents a Parallel in the ISE model.
    """
    def __init__(self, element, dag):
        InstructionsContainer.__init__(self, element, dag)
        self.starting_set = set()
        self.ending_set = set()
        for i in self.instructions:
            # Starts from startingSet of all blocks
            self.starting_set.update(i.starting_set)
            # Ends at endingSet of all blocks
            self.ending_set.update(i.ending_set)
        _LOGGER.debug("New object: %s", self)

    def __str__(self):
        return "PAR(%s)" % ", ".join([str(x) for x in self.instructions])


class Action(InstructionBase):
    """
    This class represents an Action in the ISE model.
    """
    def __init__(self, element, dag):
        InstructionBase.__init__(self, element)
        self.attributes = element.attrib
        self.id = self.attributes.get(parser.ID_ATTR,
                                      str(uuid.uuid4()))
        if element.text is None:
            _LOGGER.warning("Action command is None for: %s" + \
                                " This will raise an exception" + \
                                " on execution!",  self.id)
        self.command = element.text
        # Update the graph
        self.dag = dag
        if not dag.has_node(self.id):
            dag.add_node(self.id)

        self.actions[self.id] = self
        # We start when this action starts.
        self.starting_set = set([self.id])
        # We end when this action ends.
        self.ending_set = set([self.id])

        self.component_set = self.attributes.get(parser.COMPONENT_SET_ATTR,
                                                 parser.DEFAULT_COMPONENT_SET)
        self.remote = self.attributes.get(parser.REMOTE_ATTR,
                                          "false").lower() in ['true', '1',
                                                               't', 'y',
                                                               'yes']
        self.force = self.attributes.get(parser.FORCE_ATTR,
                                         parser.DEFAULT_FORCE)
        # Handle explicit dependencies
        deps_string = self.attributes.get(parser.DEPS_ATTR)
        if deps_string:
            for string in deps_string.split(','):
                dep = string.strip()
                self.deps.add(dep)
                _add_edge(self.id, dep, dag)

        _LOGGER.debug("New object: %s", self)

    def __str__(self):
        return "ACTION(%s)" % self.id


    def next(self):
        """
        Return the set of action ids that depends on this action.
        """
        return self.dag.incidents(self.id)

    def all_deps(self):
        """
        Return the set of action ids, this action depends on
        (implicitely or explicitely)
        """
        return self.dag.neighbors(self.id)
