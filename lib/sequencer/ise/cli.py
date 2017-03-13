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
Command Line Interface (CLI) of the ISE sequencer.

This command is the front end for the sequencer ISE stage.

It basically parse ISE options and arguments and then call the
sequencer ISE API.
"""
from __future__ import division

import optparse
import os, sys
import time
from datetime import datetime as dt, timedelta
from logging import getLogger

from ClusterShell.NodeSet import NodeSet
from sequencer.commons import write_graph_to, get_header, \
    smart_display, FILL_EMPTY_ENTRY, CyclesDetectedError, td_to_seconds, get_version, \
    add_options_to, to_unicode
from sequencer.ise import api, model, parser


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)

REPORT_TYPES = ['all', 'none', 'model', 'exec', 'error', 'unexec']
REPORT_HEADER_SIZE = 80

SEQEXEC_ACTION_NAME = 'seqexec'
SEQEXEC_DOC = """Execute the given instructions sequence."""

_ID_LEN = 16
_COMPSET_LEN = 20
_DESC_LEN = 40
_TIME_LEN = 15
_DURATION_LEN = 23
_RC_LEN = 3
_DEPS_NB_LEN = 6
_PERCENT_LEN = 7
_TIME_FORMAT = "%H:%M:%S.%f"

_ISE_MODEL_FORMAT = "%*.*s %*.*s %*.*s %s"
_ISE_EXEC_FORMAT = "%*.*s  %*.*s  %*.*s  %*.*s  %*.*s %*.*s %s"
_ISE_ERROR_FORMAT = "%*.*s %*.*s %*.*s %*.*s %s"
_ISE_UNEXEC_FORMAT = "%*.*s %*.*s %*.*s %*.*s %s"

def get_usage_data():
    """
    Return a mapping of
    {action_name: {'doc': action_doc, 'main': action_func}
    where 'action_func' is the function to call when the
    action_name has been given on the command line (thus, the main)
    """
    return {SEQEXEC_ACTION_NAME: {'doc': SEQEXEC_DOC, 'main': seqexec}}

def _parse(basedir, config, args):
    """
    ISE Action Specific CLI Parser
    """

    usage = "Usage: %prog [global_options] " + SEQEXEC_ACTION_NAME + \
        " [action_options]"

    doc = SEQEXEC_DOC + \
        " The input can be the output of the 'seqmake' action."
    cmd = os.path.basename(sys.argv[0])
    progname=to_unicode(cmd).encode('ascii', 'replace')
    opt_parser = optparse.OptionParser(usage, description=doc, prog=progname)
    opt_parser.add_option("-F", "--Force",
                          dest="force",
                          action='store_true',
                          default=False,
                          # If you want to read the default from a
                          # config file, you need a way to override
                          # it. Therefore, 'store_true' above is not a
                          # good action.  You should provide either a
                          # --Force=no or a --no-Force option.

                          # default=config.getboolean(SEQEXEC_ACTION_NAME, "Force"),
                          help="Do not stop the execution of an action when" + \
                              " one of its dependencies exits" + \
                              " with a WARNING error code.")
    add_options_to(opt_parser, ['--file', '--actionsgraphto', '--progress',
                            '--doexec', '--report', '--dostats', '--fanout'],
                   config)


    (ise_options, action_args) = opt_parser.parse_args(args)
    if len(action_args) != 0:
        opt_parser.error(SEQEXEC_ACTION_NAME + \
                             ": wrong number of arguments.")

    return (ise_options, action_args)


def _report_model(a_model):
    """
    Display the 'model' type of report
    """
    header = [u"Id", u"[@]Component Set", u"Deps", u"Description"]
    actions = a_model.actions.values()
    actions_nb = len(actions)
    _LOGGER.output("Actions in Model: %d\tLegend: @=remote, Deps=Dependencies",
                   actions_nb)
    tab_values = []
    deps_total_nb = 0
    # Sort by len() first then alphabetically so:
    # b1, b2, b20, c1, c2, c10, c100 appears in that order
    sorted_list = sorted(actions, key=lambda action: len(action.id))
    for action in sorted(sorted_list, key=lambda action: action.id):
        nodeset = NodeSet()
        deps = action.all_deps()
        deps_total_nb += len(deps)
        for dep in deps:
            if len(dep) != 0:
                nodeset.add(dep)
        tab_values.append([action.id,
                           ("@" if action.remote else "")+action.component_set,
                           str(nodeset),
                           action.description])
    tab_values.append([FILL_EMPTY_ENTRY] * len(header))
    try:
        average_deps = float(deps_total_nb) / actions_nb
    except ZeroDivisionError:
        average_deps = 0
    tab_values.append(["Average #Deps:", "-",
                       "%2.1f" % average_deps,
                       "-"])
    _LOGGER.output(smart_display(header,
                                 tab_values, vsep=u" | ",
                                 justify=[str.center, str.center, str.ljust, str.center]))

def _compute_seq_total_time(execution):
    """
    Compute the total sequential time of the given execution (i.e. the
    sum of each execution action duration)
    """
    seq_duration = timedelta()
    for executed_action in execution.executed_actions.values():
        start  = dt.fromtimestamp(executed_action.started_time)
        end = dt.fromtimestamp(executed_action.ended_time)
        duration = end - start
        seq_duration = seq_duration + duration

    return seq_duration

def _compute_optimal_time(execution):
    """
    Compute the optimal time that can be reached with the given
    execution.
    """
    actions = execution.executed_actions
    dag = execution.model.dag
    def _compute_optimal_time_rec(root):
        """
        Recursive function
        """
        result = 0.0
        try:
            max_dep = 0
            for dep in dag.neighbors(root):
                max_dep = max(max_dep, _compute_optimal_time_rec(dep))

            if root in actions:
                result = max_dep + \
                    (actions[root].ended_time - actions[root].started_time)
            else:
                result = max_dep
            return result
        finally:
            _LOGGER.debug("Optimal time for %s: %s", root, result)

    result = 0
    for node in dag.nodes():
        if len(dag.incidents(node)) == 0:
            result = max(result, _compute_optimal_time_rec(node))

    return result

def _report_exec(execution):
    """
    Display the 'exec' type of report
    """
    header = [u"Id", u"Submitted Time",
              u"Started Time", u"Ended Time", u"Duration",
              u"RC", u"[@]Component Set"]
    executed_actions = execution.executed_actions.values()
    executed_actions_nb = len(executed_actions)
    model_actions_nb = len(execution.model.actions)
    try:
        percentage = (float(executed_actions_nb) / model_actions_nb) * 100
    except ZeroDivisionError:
        percentage = 0.0
    _LOGGER.output("\nExecuted Actions: %d (%2.1f %%)\tLegend:" + \
                       " @=remote, RC=Returned Code",
                   executed_actions_nb, percentage)
    tab_values = []
    # Initialise with worst case so they will get replace by first
    # occurence
    if executed_actions_nb > 0:
        first_started = min(executed_actions,
                            key=lambda execaction: \
                                execaction.started_time).started_time
        last_started = max(executed_actions,
                           key=lambda execaction: \
                               execaction.started_time).started_time
        first_ended = min(executed_actions,
                          key=lambda execaction: \
                              execaction.ended_time).ended_time
        last_ended =  max(executed_actions,
                          key=lambda execaction: \
                              execaction.ended_time).ended_time
    for execaction in sorted(executed_actions,
                                  key=lambda execaction: \
                                      execaction.submitted_time):

        submit = dt.fromtimestamp(execaction.submitted_time)
        start  = dt.fromtimestamp(execaction.started_time)
        end = dt.fromtimestamp(execaction.ended_time)
        duration = end - start
        submitted_time = submit.strftime(_TIME_FORMAT)
        started_time = start.strftime(_TIME_FORMAT)
        ended_time = end.strftime(_TIME_FORMAT)
        cs_label = ("@" if execaction.remote else "") + execaction.component_set

        tab_values.append([execaction.id,  submitted_time,
                           started_time, ended_time, str(duration),
                           str(execaction.rc), cs_label])
    try:
        seq_total_time = _compute_seq_total_time(execution)
        average_duration = seq_total_time // executed_actions_nb
        tab_values.append([FILL_EMPTY_ENTRY] * len(header))
        tab_values.append(["First:", "-",
                           str(dt.fromtimestamp(first_started)\
                                   .strftime(_TIME_FORMAT)),
                           str(dt.fromtimestamp(first_ended)\
                                   .strftime(_TIME_FORMAT)),
                           "-", "-", "-"])
        tab_values.append(["Last:", "-",
                           str(dt.fromtimestamp(last_started)\
                                   .strftime(_TIME_FORMAT)),
                           str(dt.fromtimestamp(last_ended)\
                                   .strftime(_TIME_FORMAT)),
                           "-", "-", "-"])
        tab_values.append(["Average:", "-", "-", "-",
                           str(average_duration),
                           "-", "-"])
    except ZeroDivisionError:
        average_duration = 0
    output = smart_display(header,
                           tab_values, vsep=u' | ',
                           justify=[str.center, str.center,
                                       str.center, str.center, str.center,
                                       str.center, str.ljust])
    _LOGGER.output(output)

def _report_error(execution):
    """
    Display the 'error' type of report
    """
    actions_nb = len(execution.model.actions)
    error_actions = execution.error_actions.values()
    error_actions_nb = len(error_actions)
    try:
        percentage = (float(error_actions_nb) / actions_nb) * 100
    except ZeroDivisionError:
        percentage = 0.0

    _LOGGER.output("\nErrors: %d (%2.1f %%)\tLegend: " + \
                   "rDeps=reverse dependencies, RC=returned code",
                   error_actions_nb, percentage)
    tab_values = []
    # Sort by len() first then alphabetically so:
    # b1, b2, b20, c1, c2, c10, c100 appears in that order
    sorted_list = sorted(error_actions,
                         key=lambda error_action: len(error_action.id))
    for error_action in sorted(sorted_list,
                               key=lambda error_action: error_action.id):
        rdeps = error_action.next()
        rdeps_nb = len(rdeps)
        percentage = (float(rdeps_nb) / actions_nb) * 100
        nodeset = NodeSet()
        for rdep in error_action.next():
            if len(rdep) != 0:
                nodeset.add(rdep)
        tab_values.append([error_action.id, str(error_action.rc),
                           str(rdeps_nb), u"%2.1f" % percentage, str(nodeset)])
    output = smart_display([u"Id", u"RC",
                            u"#rDeps", u"%rDeps",
                            u"rDeps"],
                           tab_values, vsep=u" | ",
                           justify=[str.center, str.center,
                                    str.center, str.center,
                                    str.ljust])
    _LOGGER.output(output)

def _report_unexec_line(id_, deps_nb, mdeps_nb, mdeps_percent, mdeps):
    """
    Display a single line of the 'unexec' type of report
    """
    _LOGGER.output(_ISE_UNEXEC_FORMAT % (_ID_LEN, _ID_LEN, id_,
                                         _DEPS_NB_LEN, _DEPS_NB_LEN, deps_nb,
                                         _DEPS_NB_LEN, _DEPS_NB_LEN, mdeps_nb,
                                         _PERCENT_LEN, _PERCENT_LEN,
                                         mdeps_percent,
                                         mdeps))

def _report_unexec(a_model, execution):
    """
    Display the 'unexec' type of report
    """
    all_actions_set = set(a_model.actions.keys())
    all_actions_set_nb = len(all_actions_set)
    executed_actions_set = set(execution.executed_actions.keys())
    unexecuted_actions_set = all_actions_set.difference(executed_actions_set)
    unexecuted_actions_nb = len(unexecuted_actions_set)
    try:
        percentage = (float(unexecuted_actions_nb) / all_actions_set_nb) * 100
    except ZeroDivisionError:
        percentage = 0.0
    _LOGGER.output("\nUnexecuted Actions: %d (%2.1f %%)\t" + \
                       "Legend: mDeps=missings (error or unexecuted)" + \
                       " dependencies",
                   unexecuted_actions_nb, percentage)
    tab_values = []
    # Sort by len() first then alphabetically so:
    # b1, b2, b20, c1, c2, c10, c100 appears in that order
    sorted_list = sorted(unexecuted_actions_set, key = len)
    for id_ in sorted(sorted_list):
        action = a_model.actions[id_]
        all_deps = action.all_deps()
        all_deps_nb = len(all_deps)
        unexec = set(all_deps) - set(execution.executed_actions.keys())
        error = set(all_deps) & set(execution.error_actions.keys())
        missings = unexec.union(error)
        nodeset = NodeSet()
        missing_nb = len(missings)
        for missing in missings:
            if len(missing) != 0:
                nodeset.add(missing)
        try:
            percentage = ((float(missing_nb) / all_deps_nb) * 100)
        except ZeroDivisionError:
            percentage = 0.0
        tab_values.append([id_, str(len(all_deps)),
                           str(missing_nb),
                           u"%2.1f" % percentage,
                           str(nodeset)])
    output = smart_display([u"Id", u"#Deps",
                            u"#mDeps", u"%mDeps",
                            u"mDeps"],
                           tab_values, vsep=u" | ",
                           justify=[str.center, str.center,
                                    str.center, str.center,
                                    str.ljust])
    _LOGGER.output(output)

def _diplay_stats_duration(type_, duration, percent):
    """
    Return a string representing a duration in the stats report.
    """
    return "%s Duration: %s (%2.1f %%)" % (type_, duration, percent)

def report_stats(execution, prep_info, model_info, exec_info):
    """
    Return a list of strings representing statistics on the given
    execution.

    - 'execution' is the execution for which stats should be produced.
    - '*_info' are 3-tuplet (label, start, stop) where 'start' and
      'stop' are time values and 'label' is a string.

    prep label is (normally) one of: 'DepMake', 'Parsing'
    model label is (normally) one of: 'SeqMake', 'Modeling'
    exec label is (normally) one of: 'SeqExec', 'Execution'
    """
    strings = []
    (prep_label, prep_start, prep_stop) = prep_info
    (model_label, model_start, model_stop) = model_info
    (exec_label, exec_start, exec_stop) = exec_info
    overall_time = dt.fromtimestamp(exec_stop) - dt.fromtimestamp(prep_start)
    overall_raw = td_to_seconds(overall_time)

    duration = dt.fromtimestamp(prep_stop) - dt.fromtimestamp(prep_start)
    percent = (td_to_seconds(duration) /  overall_raw) * 100
    strings.append(_diplay_stats_duration(prep_label, duration, percent))

    duration = dt.fromtimestamp(model_stop) - dt.fromtimestamp(model_start)
    percent = (td_to_seconds(duration) /  overall_raw) * 100
    strings.append(_diplay_stats_duration(model_label, duration, percent))

    duration = dt.fromtimestamp(exec_stop) - dt.fromtimestamp(exec_start)
    percent = (td_to_seconds(duration) / overall_raw) * 100
    strings.append(_diplay_stats_duration(exec_label, duration, percent))

    seq_time = _compute_seq_total_time(execution)
    speedup = td_to_seconds(seq_time) / td_to_seconds(overall_time)
    optimal_time = _compute_optimal_time(execution)
    try:
        overhead = td_to_seconds(overall_time) / optimal_time
    except ZeroDivisionError:
        overhead = 0


    strings.extend(["Sequential Duration: %s" % seq_time,
                    "Overall Duration: %s" % overall_time,
                    "Sequential/Overall: %.2f" % speedup,
                    "Optimal Time: %s" % timedelta(seconds=optimal_time),
                    "Optimal Fanout: %d" % execution.best_fanout,
                    "Overall/Optimal: %.2f" % overhead,
                    "Overall Returned Code: %s" % execution.rc])
    return strings


def execute(the_model, options):
    """
    Execute the sequence of instructions represented by the given
    model using the given options.

    Options should have the following attributes:
    - force
    - doexec
    - progress
    """
    doexec = True if getattr(options, 'doexec', 'yes') == 'yes' else False
    return api.execute_model(the_model,
                             options.force,
                             doexec,
                             options.progress,
                             options.fanout)


def report(report_type, the_model, execution):
    """
    Output a report of the given type, for the given model and execution.
    """
    assert report_type in REPORT_TYPES
    if report_type != 'none':
        _LOGGER.output(get_header(" REPORTS ", "=", REPORT_HEADER_SIZE))
        if report_type == 'all' or report_type == 'model':
            _report_model(the_model)
        if report_type == 'all' or report_type == 'exec':
            _report_exec(execution)
        if report_type == 'all' or report_type == 'error':
            _report_error(execution)
        if report_type == 'all' or report_type == 'unexec':
            _report_unexec(the_model, execution)


def seqexec(db, config, args):
    """
    Parse the CLI arguments and invoke the 'seqexec' function.
    """
    (options, action_args) = _parse(db.basedir, config, args)

    _LOGGER.debug("Reading from: %s", options.src)
    src = options.src
    if src == '-':
        src = sys.stdin

    parser_start = time.time()
    the_parser = parser.ISEParser(src)
    parser_stop = time.time()

    # Provide the graphing capability even in the case of a
    # CycleDetectedError. Graph can be used to visualize such cycles.
    the_model = None
    dag = None
    try:
        model_start = time.time()
        the_model = model.Model(the_parser.root)
        dag = the_model.dag
        model_stop = time.time()
    except CyclesDetectedError as cde:
        # A cycle leads to an error, since it prevents the normal
        # execution.
        _LOGGER.critical(str(cde))
        dag = cde.graph

    if the_model is not None:
        exec_start = time.time()
        execution = execute(the_model, options)
        exec_stop = time.time()

        report(options.report, the_model, execution)

        if getattr(options, 'dostats', 'no') == 'yes':
            _LOGGER.output(get_header(" STATS ", "=", REPORT_HEADER_SIZE))
            for line in report_stats(execution,
                                     ('Parsing', parser_start, parser_stop),
                                     ('Modelling', model_start, model_stop),
                                     ('Execution', exec_start, exec_stop)):
                _LOGGER.output(line)




    # The DOT format graph is written out at the end for various reasons:
    #
    # - the graph model is modified by the 'write_graph_to' function.
    #
    # - the time required to make that graph should not be taken into
    # account (since it can be produced without execution using
    # --doexec option)
    #
    # - if an error occurs in next steps it does not prevent the
    # execution of anything useful
    if options.actionsgraphto is not None:
        write_graph_to(dag, options.actionsgraphto)

    return execution.rc if the_model is not None else os.EX_DATAERR


