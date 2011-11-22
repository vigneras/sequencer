#!/usr/bin/env python
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
Get name#type@category for each given components@list given.

Such a module MUST define a get_guesser(param) function (see below).
This function will be called by the sequencer (DGM and chain stages)
to get the type and the category of given components.

If a component in the given list already has the form:
name#type@category it will be returned as is. Otherwise, this guesser
implementation just returns exotic@alien for each component given
meaning that neither type nor category is known.

Note however that nodeset are supported:

For example, for: bullx[2-3] bullx14#compute@node the following
strings will be returned:

bullx2#exotic@alien
bullx3#exotic@alien
bullx14#compute@node
"""
from ClusterShell.NodeSet import NodeSet

__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]

def get_guesser(param):
    """
    Returns a guesser related to the given parameter.
    """
    return Guesser(param)

class Guesser(object):
    """
    Basic Guesser implementation.
    """
    def __init__(self, param):
        """
        Use the class method get_guesser() instead.
        """
        pass

    def guess_type(self, components_list):
        """
        For the given list of components, return a tuple (result,
        unknown) where result is a map of dictionnary

        {category: {type: NodeSet}}

        and unknown are elements of the given components_list that
        should be considered unknown.

        This implementation will always return an empty unknown set.
        """
        (raw_names, sep, category) = components_list.partition('@')
        if len(category) == 0:
            category = 'alien'
        (names, sep, requested_type) = raw_names.partition('#')
        if len(requested_type) == 0:
            requested_type = 'exotic'
        return self.fetch(NodeSet(names), category, requested_type)

    def fetch(self, nodeset, category, type):
        """
        For the given nodeset and category, return a tuple (result,
        unknown) where result is a map of dictionnary

        {category: {type : NodeSet}}

        and unknown are elements of the given nodeset that were not
        found.
        This implementation will always return an empty unknown set.
        """
        result = {}
        result[category] = { type : nodeset }
        requested_set = NodeSet()
        return (result, requested_set)




