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
Command Line Interface (CLI) of the sequencer Chain feature.

This command is a shortcut for the following:

sequencer depmake <arguments> | \
sequencer seqmake <options>   | \
sequencer seqexec <options>

It does the same thing without the creation of XML file at eath stages
(wherever possible).
"""
import optparse
import os
import time
from logging import getLogger

from sequencer.commons import write_graph_to, CyclesDetectedError, \
     get_version, add_options_to
from sequencer.dgm import cli as dgm_cli
from sequencer.ise import cli as ise_cli
from sequencer.ism import cli as ism_cli


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)

CHAIN_ACTION_NAME = 'chain'
CHAIN_DOC = "Chain 'depmake', 'seqmake' and 'seqexec' actions."

def get_usage_data():
    """
    Return a mapping of
    {action_name: {'doc': action_doc, 'chain': action_func}
    where 'action_func' is the function to call when the
    action_name has been given on the command line (thus, the chain)
    """
    return {CHAIN_ACTION_NAME: {'doc': CHAIN_DOC, 'main': chain}}


def _parse(config, args):
    """
    Chaining Implementation
    """
    usage = "Usage: %prog [global_options] ['chain'] <ruleset> " + \
        "[action_options] components_list"
    chain_doc = CHAIN_DOC + \
        " That is: make the dependency graph for the given ruleset and" + \
        " components_list," + \
        " compute an instructions sequence and execute it." + \
        " Note that the action name 'chain' is optional." + \
        " Giving the ruleset name directly is a shortcut."

    parser = optparse.OptionParser(usage, description=chain_doc)
    parser.add_option("-F", "--Force",
                      metavar='RULE_LIST',
                      dest='force',
                      type='string',
                      help="Specify the comma-separated list of rules" + \
                          " for which" + \
                          " related action should be forced.")

    add_options_to(parser, ['--depgraphto', '--actionsgraphto', '--progress',
                            '--doexec', '--report', '--dostats',
                            '--fanout', '--algo', '--docache'],
                   config)
    (options, action_args) = parser.parse_args(args)
    if len(action_args) < 2:
        parser.error(CHAIN_ACTION_NAME + ": wrong number of arguments.")

    return (options, action_args)

def chain(db, config, chain_args):
    """
    Execute the chainer CLI
    """
    (options, action_args) = _parse(config, chain_args)
    req_ruleset = action_args[0]
    components_lists = dgm_cli.parse_components_lists(action_args[1:])

    rules = db.get_rules_for(req_ruleset)
    depdag = None
    seqdag = None
    depgraph = None
    execution = None
    # Provide the graphing capability even in the case of a
    # CycleDetectedError. Graph can be used to visualize such cycles.
    try:
        depmake_start = time.time()
        depgraph = dgm_cli.makedepgraph(config,
                                        rules,
                                        components_lists,
                                        options)
        depmake_stop = time.time()
        depdag = depgraph.dag
    except CyclesDetectedError as cde:
        # Output an error here since we can't continue
        _LOGGER.critical(str(cde))
        depdag = cde.graph

    # A cycle has not been detected, we can continue.
    if depgraph is not None:
        seqmake_start = time.time()
        (ise_model, xml_result, error) = ism_cli.makesequence(depgraph.dag,
                                                              options.algo)
        seqmake_stop = time.time()
        if ise_model is None:
            assert error is not None
            _LOGGER.critical(str(error))
            seqdag = error.graph
        else:
            seqdag = ise_model.dag
            seqexec_start = time.time()
            execution = ise_cli.execute(ise_model, options)
            seqexec_stop = time.time()

            ise_cli.report(options.report, ise_model, execution)
            if getattr(options, 'dostats', 'no') == 'yes':
                stats = ise_cli.get_header(" STATS ",
                                           "=",
                                           ise_cli.REPORT_HEADER_SIZE)
                _LOGGER.output(stats)
                lines = ise_cli.report_stats(execution,
                                             ('DepMake',
                                              depmake_start, depmake_stop),
                                             ('SeqMake',
                                              seqmake_start, seqmake_stop),
                                             ('SeqExec',
                                              seqexec_start, seqexec_stop))
                for line in lines:
                    _LOGGER.output(line)


    # The DOT format graphs are written out at the end for various reasons:
    #
    # - graph models are modified by the 'write_graph_to' function.
    #
    # - the time required to make that graph should not be taken into
    # account (since it can be produced without execution using
    # --doexec option)
    #
    # - if an error occurs in next steps it does not prevent the
    # execution of anything useful
    if options.depgraphto is not None:
        write_graph_to(depdag, options.depgraphto)


    if options.actionsgraphto is not None and seqdag is not None:
        write_graph_to(seqdag, options.actionsgraphto)

    return execution.rc if execution is not None else os.EX_DATAERR
