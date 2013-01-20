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
Command Line Interface (CLI) of the DGM sequencer.

This command is the front end for the sequencer DGM stage.

It basically parse DGM options and arguments and then call the
sequencer DGM API.
"""
from __future__ import print_function

import logging
import operator
import optparse
import os
import sys

from ClusterShell.NodeSet import NodeSet
from sequencer.commons import confirm, UnknownRuleSet, smart_display, \
     HSEP, TRUNCATION_MAX_SIZE, REMOVE_UNSPECIFIED_COLUMNS, \
     write_graph_to, CyclesDetectedError, get_version, add_options_to, \
     replace_if_none, DuplicateRuleError
from sequencer.dgm.db import create_rule_from_strings_array
from sequencer.dgm.model import RuleSet, Component, NOT_FORCE_OP
from sequencer.ise import cli as ise_cli
from pygraph.readwrite.markup import write


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = logging.getLogger(__name__)

GRAPHRULES_ACTION_NAME = 'graphrules'
GRAPHRULES_DOC = "Display the rules graph related to the given ruleset."
KNOWNTYPES_ACTION_NAME = 'knowntypes'
KNOWNTYPES_DOC = "Display the types known by the given ruleset."
DEPMAKE_ACTION_NAME = 'depmake'
DEPMAKE_DOC = "Compute from the given ruleset the dependency" + \
    " graph of the given components."
DBCREATE_ACTION_NAME = 'dbcreate'
DBCREATE_DOC = "Create the sequencer table."
DBDROP_ACTION_NAME = 'dbdrop'
DBDROP_DOC = 'Remove the sequencer table'
DBADD_ACTION_NAME = 'dbadd'
DBADD_DOC = 'Add a rule'
DBREMOVE_ACTION_NAME = 'dbremove'
DBREMOVE_DOC = 'Remove a rule or a complete ruleset'
DBCOPY_ACTION_NAME = 'dbcopy'
DBCOPY_DOC = 'Copy a rule or a complete ruleset'
DBSHOW_ACTION_NAME = 'dbshow'
DBSHOW_DOC = 'Show rulesets'
DBUPDATE_ACTION_NAME = 'dbupdate'
DBUPDATE_DOC = 'Update a rule'
DBCHECKSUM_ACTION_NAME = 'dbchecksum'
DBCHECKSUM_DOC = "Display ruleset checksums"

GUESSER_MODULE_NAME = 'guesser.module.name'
GUESSER_PARAMS_NAME = 'guesser.factory.params'


def get_usage_data():
    """
    Return a mapping of
    {action_name: {'doc': action_doc, 'main': action_func}
    where 'action_func' is the function to call when the
    action_name has been given on the command line (thus, the main)
    """
    return {GRAPHRULES_ACTION_NAME: {'doc': GRAPHRULES_DOC,
                                     'main': graphrules},
            KNOWNTYPES_ACTION_NAME: {'doc': KNOWNTYPES_DOC,
                                     'main': knowntypes},
            DEPMAKE_ACTION_NAME: {'doc': DEPMAKE_DOC,
                                  'main': depmake},
            DBCREATE_ACTION_NAME: {'doc': DBCREATE_DOC,
                                   'main': dbcreate},
            DBDROP_ACTION_NAME: {'doc': DBDROP_DOC,
                                 'main': dbdrop},
            DBSHOW_ACTION_NAME: {'doc': DBSHOW_DOC,
                                 'main': dbshow},
            DBADD_ACTION_NAME: {'doc': DBADD_DOC,
                                'main': dbadd},
            DBREMOVE_ACTION_NAME: {'doc': DBREMOVE_DOC,
                                   'main': dbremove},
            DBUPDATE_ACTION_NAME: {'doc': DBUPDATE_DOC,
                                   'main': dbupdate},
            DBCOPY_ACTION_NAME: {'doc': DBCOPY_DOC,
                                 'main': dbcopy},
            DBCHECKSUM_ACTION_NAME: {'doc': DBCHECKSUM_DOC,
                                     'main': dbchecksum}
            }

# Warning: Unicode strings are required here (see smart_display())
RULES_HEADER = [u"ruleset", u"name", u"types", u"filter",
                u"action", u"depsfinder", u"dependson", u"comments"]
CHECKSUM_HEADER = [u"ruleset", u"name", u"checksum"]


def graphrules(db, config, args):
    """
    This action fetch the rules from the DB sequencer table and call
    the DGM stage for the computation of the related graph.
    This graph is then given to the user in the DOT format.
    """
    usage = "Usage: %prog [global_options] " + GRAPHRULES_ACTION_NAME + \
        " [action_options] ruleset"
    doc = GRAPHRULES_DOC + \
        " The graph is given in DOT format."
    parser = optparse.OptionParser(usage, description=doc)
    add_options_to(parser, ['--out'], config)
    (options, action_args) = parser.parse_args(args)
    if len(action_args) != 1:
        parser.error(GRAPHRULES_ACTION_NAME + ": ruleSet is missing.")

    req_ruleset = action_args[0]
    rules = db.get_rules_for(req_ruleset)
    ruleset = RuleSet(rules.values())
    write_graph_to(ruleset.get_rules_graph(), options.out)


def knowntypes(db, config, args):
    """
    This action fetch the rules from the DB sequencer table and call
    the DGM stage for the creation of the corresponding ruleset and to fetch
    the root rules mapping. The result is then displayed on the screen.
    """
    usage = "Usage: %prog [global_options] " + KNOWNTYPES_ACTION_NAME + \
        " [action_options] ruleset"
    doc = KNOWNTYPES_DOC + \
        " For each displayed types, the starting rules that will" + \
        " be applied on them for the" + \
        " computation of the dependency graph is also given."
    parser = optparse.OptionParser(usage, description=doc)
    (options, action_args) = parser.parse_args(args)
    if len(action_args) != 1:
        parser.error(KNOWNTYPES_ACTION_NAME + ": ruleSet is missing.")

    req_ruleset = action_args[0]
    rules = db.get_rules_for(req_ruleset)
    ruleset = RuleSet(rules.values())
    mapping = ruleset.root_rules_for
    tab_values = []
    # Sort according to category
    for type_ in sorted(mapping, key=lambda t: t[t.find('@') + 1]):
        for rule in mapping[type_]:
            line = [type_, rule.filter, rule.name, rule.action]
            tab_values.append(["NONE" if x is None else x for x in line])

    _LOGGER.output(smart_display([u"Type",
                                  u"Filter",
                                  u"Rule Name",
                                  u"Action"],
                                 tab_values, vsep=u" | "))


def parse_components_lists(lists):
    """
    Parse the given components lists.  We support components list of
    the form (copy/paste support from clubak -c output):

    foo[1,4]#type@cat/rule,bar#type@cat/rule

    It returns an array of components. The applied rule is removed
    from the original components list. In this example, the returned array
    will contain:

    ['foo[1,4]#type@cat', 'bar#type@cat']
    """
    components_list = set()
    for cl in lists:
        _LOGGER.debug("Parsing component: %s", cl)
        # cl is in the following form:
        # foo[1,4]#type@cat/rule,bar#type@cat/rule
        start = 0
        while(True):
            end = cl.find('/', start)
            # Normal component list of the following form:
            # foo[1,3]
            # comma separated list is not supported in this case
            if end == -1:
                components_list.add(cl[start:])
                break
            # We found a rulename i.e: cl contains a '/rulename'
            components_list.add(cl[start:end])
            # Find next component
            # foo#type@cat/rule,bar#type@cat/rule
            start = cl.find(',', end)
            if start == -1:
                break
            else:
                start += 1

    return components_list


def _parse_depmake_cmdline(config, args):
    """
    DGM Action Specific CLI Parser
    """

    usage = "Usage: %prog [global_options] " + DEPMAKE_ACTION_NAME + \
        " [action_options] ruleset components_list"
    doc = DEPMAKE_DOC + \
        " The output format is suitable for the 'seqmake' action."
    parser = optparse.OptionParser(usage, description=doc)
    parser.add_option('-F', '--Force',
                      metavar='RULE_LIST',
                      dest='force',
                      type='string',
                      help="Specify the force mode ('allowed'," + \
                          " 'always' or 'never')" + \
                          " that should be used for the execution of" + \
                          " each action related to the given comma" + \
                          " separated list of rule names. When prefixed" + \
                          " by " + NOT_FORCE_OP + ", " + \
                          " action execution will 'never' be" + \
                          " forced. Otherwise, it will 'always' be" + \
                          " forced. Action related to a rule that is " + \
                          " not specified in the list will see its" + \
                          " force mode set to 'allowed' meaning that" + \
                          " the decision is left to the Instruction " + \
                          " Sequence Executor (see '" + \
                          ise_cli.SEQEXEC_ACTION_NAME + "')")

    add_options_to(parser, ['--out', '--depgraphto', '--docache'], config)
    (options, action_args) = parser.parse_args(args)
    if len(action_args) < 2:
        parser.error(DEPMAKE_ACTION_NAME + \
                         ": ruleSet and/or components lists missing.")

    req_ruleset = action_args[0]
    lists = action_args[1:]
    components_lists = parse_components_lists(lists)
    return (options, req_ruleset, components_lists)


def get_component_set_from(config, components_lists):
    """
    Use the Guesser API to fetch the components set from the given
    components_lists
    """
    all_set = set()
    module_name = config.get(DEPMAKE_ACTION_NAME, GUESSER_MODULE_NAME)
    _LOGGER.debug("Guesser module name: %s" , module_name)
    module = __import__(module_name)
    # Go through sys.modules to find modules inside packages
    module = sys.modules[module_name]
    params = config.get(DEPMAKE_ACTION_NAME, GUESSER_PARAMS_NAME)
    params = replace_if_none(params)
    _LOGGER.debug("Guesser parameters: %s", params)
    guesser = module.get_guesser(params)
    _LOGGER.info("Using guesser: %s", guesser)
    for cl in components_lists:
        (components_for, unknown) = guesser.guess_type(cl)
        if len(unknown) != 0:
            _LOGGER.warning("%s: [Unknown components]", unknown)
        for table in components_for:
            for type_ in components_for[table]:
                components = NodeSet(components_for[table][type_])
                for component in components:
                    all_set.add(Component(component, type_, table))
    return all_set


def makedepgraph(config, rules, components_lists, options):
    """
    Return the dependency graph for the given pair ('req_ruleset',
    'components_lists').
    """
    ruleset = RuleSet(rules.values())
    all_set = get_component_set_from(config, components_lists)
    force_opt = options.force
    force_rule = force_opt.split(',') if force_opt is not None else []
    docache = True if getattr(options, 'docache', 'yes') == 'yes' else False
    _LOGGER.debug("Caching filter results (docache) is: %s", docache)
    depgraph = ruleset.get_depgraph(all_set, force_rule, docache)
    if _LOGGER.isEnabledFor(logging.DEBUG):
        _LOGGER.debug("Components set: %s",
                      NodeSet.fromlist([x.id for x in all_set]))
        _LOGGER.debug("Remaining: %s",
                      NodeSet.fromlist([str(x) for x in depgraph.remaining_components]))
        _LOGGER.debug("List: %s",
                      NodeSet.fromlist([str(x) for x in depgraph.components_map]))

    return depgraph


def depmake(db, config, args):
    """
    Parse the CLI arguments and invoke the 'makedepgraph' function.
    """
    (options, req_ruleset, components_lists) = _parse_depmake_cmdline(config,
                                                                      args)

    rules = db.get_rules_for(req_ruleset)
    dag = None
    depgraph = None
    # Provide the graphing capability even in the case of a
    # CycleDetectedError. Graph can be used to visualize such cycles.
    try:
        depgraph = makedepgraph(config, rules, components_lists, options)
        dag = depgraph.dag
    except CyclesDetectedError as cde:
        # A cycle leads to an error, since it prevents the normal
        # execution.
        _LOGGER.critical(str(cde))
        dag = cde.graph

    # Only execute when the depgraph is available (no cycle detected)
    if depgraph is not None:
        dst = options.out
        _LOGGER.debug("Writing to: %s", dst)

        output = write(depgraph.dag)
        if dst == '-':
            _LOGGER.output(output)
        else:
            print(output, file=open(dst, "w"))

    # The DOT graph is written afterwards for two reasons:
    #
    # 1. since the XML graph has already been written out, we can
    # modify the model for vizualisation (removing attributes, see
    # 'write_graph_to');
    #
    # 2. if an error occurs in next steps, it does not prevent the XML
    # graph from being used.
    if options.depgraphto is not None:
        write_graph_to(dag, options.depgraphto)

    return os.EX_OK if depgraph is not None else os.EX_DATAERR


def _display(rules, columns_max):
    """
    Display all given rules using smart_display().
    """
    tab_values = []

    for rule in  sorted(rules, key=operator.attrgetter('ruleset', 'name')):
        line = [rule.ruleset, rule.name, ','.join(rule.types),
                rule.filter, rule.action, rule.depsfinder,
                None if len(rule.dependson) == 0 \
                    else ','.join(sorted(rule.dependson)),
                rule.comments]
        tab_values.append(["NONE" if x is None else x for x in line])

    _LOGGER.output(smart_display(RULES_HEADER, tab_values,
                                 vsep=u' | ', columns_max=columns_max))


def dbcreate(db, config, args):
    """
    Create the sequencer table.
    """
    usage = "%prog [options] dbcreate"
    doc = DBCREATE_DOC
    parser = optparse.OptionParser(usage, description=doc)
    (options, dbcreate_args) = parser.parse_args(args)
    if len(dbcreate_args) != 0:
        parser.error(DBCREATE_ACTION_NAME + \
                         ": expected %d arguments, given %d" % \
                         (0, len(dbcreate_args)))
    db.create_table()


def dbdrop(db, config, args):
    """
    Drop the sequencer table.
    """
    usage = "%prog [options] dbdrop"
    doc = DBDROP_DOC
    parser = optparse.OptionParser(usage, description=doc)
    add_options_to(parser, ['--Enforce'], config)
    (options, dbdrop_args) = parser.parse_args(args)
    if len(dbdrop_args) != 0:
        parser.error(DBDROP_ACTION_NAME + \
                         ": expected %d arguments, given %d" % \
                         (0, len(dbdrop_args)))
    if not options.enforce:
        if not confirm("Confirm the full deletion of the sequencer table?",
                       False):
            _LOGGER.output("Canceled.")
            sys.exit(os.EX_OK)

    db.drop_table()


def dbshow(db, config, args):
    """
    Display the sequencer table.
    """
    usage = "%prog [options] dbshow [--columns=<column:max>,...] [ruleset]"
    doc = "Display the sequencer table (for the given " + \
        "ruleset if specified)."
    parser = optparse.OptionParser(usage, description=doc)
    parser.add_option("", "--columns", dest="columns_list",
                      action='store',
                      help="Use the given list of 'column:max' for" + \
                          " the display where 'column' is the column" + \
                          " label, and 'max' is the maximum number of" + \
                          " character that should be used in that" + \
                          "  column (0 means remove the column" + \
                          "  completely). Note: 'max' should" + \
                          "  be greater than %d" % TRUNCATION_MAX_SIZE + \
                          " if 'max' is not given at all, then only" + \
                          " specified columns are displayed")
    (options, show_args) = parser.parse_args(args)
    if len(show_args) > 1:
        parser.error(DBSHOW_ACTION_NAME + \
                         ": too many arguments %d, maximum is %d" % \
                         (len(show_args), 1))
    columns_max = dict()
    if options.columns_list is not None:
        columns_list = options.columns_list.split(',')
        for column_spec in columns_list:
            (column, sep, maxchar_s) = column_spec.partition(':')
            if column not in RULES_HEADER:
                parser.error(DBSHOW_ACTION_NAME + \
                                 ": unknown column: %s" % column)
            if len(maxchar_s) == 0:
                maxchar = REMOVE_UNSPECIFIED_COLUMNS
            else:
                try:
                    maxchar = int(maxchar_s)
                except ValueError:
                    parser.error(DBSHOW_ACTION_NAME + \
                                     ": invalid max value %s " % maxchar_s + \
                                     " for column %s." % column + \
                                     " Positive integer expected.")
                if 0 < maxchar < TRUNCATION_MAX_SIZE or maxchar < 0:
                    parser.error(DBSHOW_ACTION_NAME + \
                                     ": given max: %d" % maxchar + \
                                     " for column %s" % column + \
                                     " should be greater" + \
                                     " than %d" % TRUNCATION_MAX_SIZE)

            columns_max[column] = int(maxchar)

    _LOGGER.info("Reading from db: %s", db)
    if len(show_args) == 1:
        ruleset_name = show_args[0]
        ruleset = db.get_rules_for(ruleset_name)
        _display(ruleset.values(), columns_max)
    else:
        rules_map = db.get_rules_map()
        all_rules = []
        for ruleset_name in rules_map:
            all_rules.extend(rules_map[ruleset_name].values())
        _display(all_rules, columns_max)


def dbadd(db, config, args):
    """
    Add a rule into the sequencer table.
    """
    usage = "%prog [options] dbadd ruleset name types " + \
        "filter action depsfinder dependson comments"
    doc = """Add a rule into the sequencer table. Multiple 'types'
can be specified using the comma separator ','. Multiple dependencies
can be specified using the comma separator ','. Both action and
depsfinder should be a valid shell command line. Quote must be used to
prevent mis-interpretation by the running shell. Special 'NONE' and
'NULL' strings are interpreted as the special NULL db value. Note that
errors might be raised if DB constraints are not fulfilled. The DB
specific error message should tell what the problem is. If unclear,
have a look to the DB constraints."""
    parser = optparse.OptionParser(usage, description=doc)
    (options, add_args) = parser.parse_args(args)
    if len(add_args) != 8:
        parser.error(DBADD_ACTION_NAME + \
                         ": expected %d arguments, given %d" % \
                         (8, len(add_args)))

    add_args = [None if x == "NONE" or x == "NULL" else x for x in add_args]
    try:
        db.add_rule(create_rule_from_strings_array(add_args))
    except DuplicateRuleError as dre:
        _LOGGER.error(DBADD_ACTION_NAME + \
                     ": Rule %s.%s does already exists.",
                     dre.ruleset, dre.name)


def dbremove(db, config, args):
    """
    Remove a rule or a ruleset from the sequencer table.
    """
    usage = "%prog [options] dbremove [--nodeps] " + \
        "ruleset_name [rule_name...]"
    doc = """Remove all (given) rules from the sequencer table."""
    parser = optparse.OptionParser(usage, description=doc)
    add_options_to(parser, ['--Enforce', '--nodeps'], config)
    (options, remove_args) = parser.parse_args(args)
    if len(remove_args) < 1:
        parser.error(DBREMOVE_ACTION_NAME + \
                         ": expected at least %d arguments, given %d" % \
                         (1, len(remove_args)))
    ruleset = remove_args[0]
    rules = remove_args[1:] if len(remove_args) > 1 else None
    if not options.enforce:
        prompt = "Confirm the removal of %s ruleset %s?" % \
            (("rules %s from" % \
                  ", ".join(rules)) if rules is not None else "whole", \
                 ruleset)
        if not confirm(prompt, False):
            _LOGGER.output("Canceled.")
            sys.exit(os.EX_OK)
    remaining = db.remove_rules(ruleset, rules, options.nodeps)
    if remaining is not None and len(remaining) != 0:
        _LOGGER.error(DBREMOVE_ACTION_NAME + \
                      ": unable to remove following rules %s "
                      "from ruleset %s"
                      ", ".join(remaining), ruleset)


def dbupdate(db, config, args):
    """
    Update a rule of the sequencer table.
    """
    usage = "%prog [options] dbupdate [--nodeps] " + \
        "ruleset_name rule_name" + \
        " <column1>=<value1> <column2>=<value2>..."
    doc = "Update each columns <column1>, <column2>, ... " + \
    "of the given rule ('ruleset', 'name') with values " + \
        "<value1>, <value2>, ... respectively in the sequencer table."
    parser = optparse.OptionParser(usage, description=doc)
    add_options_to(parser, ['--nodeps'], config)
    (options, update_args) = parser.parse_args(args)
    if len(update_args) < 3:
        parser.error(DBUPDATE_ACTION_NAME + \
                         ": expected a minimum of %d arguments, given %d" % \
                         (3, len(update_args)))
    ruleset = update_args[0]
    rulename = update_args[1]
    update_set = set()
    for record in update_args[2:]:
        (col, sep, val) = record.partition("=")
        val = None if val == 'NONE' or val == 'NULL' else val
        update_set.add((col, val))
    if not db.update_rule(ruleset, rulename,
                          update_set, options.nodeps):
        _LOGGER.error(DBUPDATE_ACTION_NAME + \
                               ": unable to update specified rule (%s, %s)" % \
                               (ruleset, rulename))


def dbcopy(db, config, args):
    """
    Copy a rule or ruleset of the sequencer table.
    """
    usage = "%prog [options] dbcopy " + \
        "ruleset_src[:rule_src] ruleset_dst"
    doc = "Copy ruleset_src to ruleset_dst" + \
        " or copy rule_src from ruleset_src to ruleset_dest."
    parser = optparse.OptionParser(usage, description=doc)
    (options, copy_args) = parser.parse_args(args)
    if len(copy_args) < 2:
        parser.error(DBCOPY_ACTION_NAME + \
                         ": expected a minimum of %d arguments, given %d" % \
                         (2, len(copy_args)))
    (ruleset_src, sep, rule_src) = copy_args[0].partition(":")
    ruleset_dst = copy_args[1]

    src_set = db.get_rules_for(ruleset_src)
    dst_set = dict()
    try:
        dst_set = db.get_rules_for(ruleset_dst)
    except UnknownRuleSet:
        pass

    if rule_src is None and len(dst_set) != 0:
        _LOGGER.error(DBCOPY_ACTION_NAME + \
                               ": ruleset %s already exists!",
                      ruleset_dst)
        return
    if rule_src is not None and len(rule_src) != 0:
        if rule_src in dst_set:
            _LOGGER.error(DBCOPY_ACTION_NAME + \
                              ": rule %s " + \
                              " already exists in " + \
                              "ruleset %s!",
                          rule_src, ruleset_dst)
            return
        if rule_src not in src_set:
            _LOGGER.error(DBCOPY_ACTION_NAME + \
                              ": unknown rule %s in ruleset %s",
                          rule_src, ruleset_src)
            return
        rule_dst = src_set[rule_src]
        rule_dst.ruleset = ruleset_dst
        db.add_rules([rule_dst])
        return

    for rule in src_set.values():
        rule.ruleset = ruleset_dst
        dst_set[rule.name] = rule

    db.add_rules(dst_set.values())


def dbchecksum(db, config, args):
    """
    Display the checksums of rulesets and of each rule in that ruleset.
    """
    usage = "%prog [options] dbchecksum [ruleset]"
    doc = "Compute checksum for the specified ruleset " + \
    " (all if not specified)"
    parser = optparse.OptionParser(usage, description=doc)
    (options, action_args) = parser.parse_args(args)
    if len(action_args) > 1:
        parser.error(DBCHECKSUM_ACTION_NAME + \
                         ": too many arguments %d, maximum is %d" % \
                         (len(action_args), 1))
    tab_values = []
    if len(action_args) == 1:
        ruleset_name = action_args[0]
        (ruleset_h, h_for) = db.checksum(ruleset_name)
        for rulename in h_for:
            tab_values.append([ruleset_name,
                               rulename,
                               h_for[rulename].hexdigest()])
        tab_values.append([ruleset_name, HSEP, ruleset_h.hexdigest()])
    else:
        rules_map = db.get_rules_map()
        for ruleset_name in rules_map:
            (ruleset_h, h_for) = db.checksum(ruleset_name)
            for rulename in h_for:
                tab_values.append([ruleset_name,
                                   rulename,
                                   h_for[rulename].hexdigest()])
            tab_values.append([ruleset_name, HSEP, ruleset_h.hexdigest()])
    _LOGGER.output(smart_display(CHECKSUM_HEADER,
                                 tab_values,
                                 vsep=u' | '))
