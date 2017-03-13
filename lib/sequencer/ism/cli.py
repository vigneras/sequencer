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
Command Line Interface (CLI) of the ISM sequencer.

This command is the front end for the sequencer ISM stage.

It basically parse a DGM output file (a python graph) and produces an
ISE XML input file.
"""
from __future__ import print_function

import optparse
import codecs
import sys
from logging import getLogger
from os import EX_OK, path

from sequencer.commons import get_version, add_options_to
from sequencer.ism.algo import order_mixed, \
    order_seq_only, order_par_only, order_optimal
from lxml import etree as ET
from pygraph.readwrite.markup import read


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)


SEQMAKE_ACTION_NAME = 'seqmake'
SEQMAKE_DOC = "Compute an instructions sequence from the given dependency " + \
    "graph."

def get_usage_data():
    """
    Return a mapping of
    {action_name: {'doc': action_doc, 'main': action_func}
    where 'action_func' is the function to call when the
    action_name has been given on the command line (thus, the main)
    """
    return {SEQMAKE_ACTION_NAME: {'doc': SEQMAKE_DOC, 'main': seqmake}}

ALGO_TYPES = {
    'mixed':order_mixed,
    'seq': order_seq_only,
    'par': order_par_only,
    'optimal': order_optimal,
    }

def _parse(config, ism_args):
    """
    ISM Action Specific CLI Parser
    """

    usage = "Usage: %prog [global_options] " + SEQMAKE_ACTION_NAME + \
        " [action_options]"

    doc = SEQMAKE_DOC + \
        " The input can be the output of the 'depmake' action." + \
        " The output can be used as an input of the 'seqexec' action."
    cmd = path.basename(sys.argv[0])
    progname=to_unicode(cmd).encode('ascii', 'replace')
    opt_parser = optparse.OptionParser(usage, description=doc, prog=progname)
    add_options_to(opt_parser, ['--file', '--out', '--algo'], config)
    (ism_options, action_args) = opt_parser.parse_args(ism_args)
    if len(action_args) != 0:
        opt_parser.error(SEQMAKE_ACTION_NAME + \
                             ": wrong number of arguments.")

    return (ism_options, action_args)

def makesequence(depgraph, algo_type):
    """
    Make the sequence for the given dependency graph using the given
    algorithm type.
    """
    algo = ALGO_TYPES[algo_type]
    return algo(depgraph)

def seqmake(db, config, ism_args):
    """
    Parse the CLI arguments and invoke the 'seqmake' function.
    """
    (ism_options, action_args) = _parse(config, ism_args)

    _LOGGER.debug("Reading from: %s", ism_options.src)
    src = ism_options.src
    if src == '-':
        src = sys.stdin
    else:
        src = open(src, "r")

    xml = src.read()
    depgraph = read(xml)

    (ise_model, xml_result, error) = makesequence(depgraph, ism_options.algo)
    if error is not None:
        # Issue a warning here (and not error) since the only thing
        # really required is the availability of the xml_result
        _LOGGER.warning(str(error))

    dst = ism_options.out
    _LOGGER.debug("Writing to: %s", dst)

    output = ET.tostring(xml_result, pretty_print=True, encoding="UTF-8")
    if dst == '-':
        _LOGGER.output(output)
    else:
        print(output, file=open(dst, "w"))

    return EX_OK
