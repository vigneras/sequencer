# -*- coding: utf-8 -*-
###############################################################################
# Copyright (C) Bull S.A.S (2010, 2011)
# Contributor: Pierre Vignéras <pierre.vigneras@bull.net>
from __future__ import print_function, division
from logging import getLogger
from operator import itemgetter
from pygraph.algorithms.accessibility import mutual_accessibility
from pygraph.algorithms.searching import depth_first_search
from pygraph.readwrite.dot import write
import os
import pwd
import random
import sys
import time

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
This module defines common stuff to all sequencer modules.
"""




__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]

# Should be after the get_version() function definition! See below
# __version__ = get_version()

_LOGGER = getLogger(__name__)
_PACKAGE_NAME = __name__.split('.')[0]

def get_package_name():
    """
    Return the distribution package name (RPM, DEB, whatever the final format is)
    """
    return _PACKAGE_NAME


_SEQUENCER_META_FILE = ".metainfo"
_SEQUENCER_VERSION_PREFIX = get_package_name() + ".version"
_SEQUENCER_LASTCOMMIT_PREFIX = get_package_name() + ".lastcommit"
_MISSING_VERSION_MSG = "?.?.?"
_MISSING_LASTCOMMIT_MSG = "? ? ? ?"

# Used by smartdisplay
HSEP = None
TRUNCATION_REF = "..{%s}"
TRUNCATION_MAX_SIZE = len(TRUNCATION_REF)
REMOVE_UNSPECIFIED_COLUMNS = -1

# Use by replace_if_none
NONE_VALUE = str(None)
def replace_if_none(value):
    """
    Replace the given value by NONE_VALUE if it is considered none or empty
    """
    return None if value is not None and (value == NONE_VALUE or len(value) == 0) \
        else value

def get_basedir(base=None):
    """
    Returns the base directory for the fetching of rules and
    configuration files.
    This directory is based on the command name itself.
    """
    cmd = os.path.basename(sys.argv[0])
    cmdfile = os.path.abspath(sys.argv[0])
    # Do not follow symbolic links
    stat = os.lstat(cmdfile)
    if stat.st_uid == 0:
        owner = 'root'
        confdir = os.path.join('/etc', cmd)
    else:
        owner_data = pwd.getpwuid(stat.st_uid)
        owner = owner_data[0]
        confdir = os.path.join(owner_data[5], '.'+cmd)
    _LOGGER.debug("Owner is %s; confdir starts at %s", (owner, confdir))
    if base is None:
        return confdir
    return os.path.join(confdir, base)

def add_options_to(parser, options, config):
    """
    Add given options to the given parser using given configuration
    file.
    """
    for long_opt in options:
        parms = get_option_for(long_opt, config)
        parser.add_option(*parms[0], **parms[1])

def get_option_for(opt_name, config):
    """Returns a pair [opt_tuple, opt_dict] where 'opt_tuple'
    represents short and long options and 'opt_dict' represents other
    parameters required by OptionParser.add_option() method. An example of
    usage is:

    parms = get_option_for('--dir', config)
    opt_parser.add_option(*parms[0], **parms[1])
    """

    if opt_name == '--Enforce':
        return [['-E', opt_name],
                {'dest':'enforce',
                 'action':'store_true',
                 'default':False,
                 'help':'Do not ask for a confirmation. ' + \
                     'Default is %default.'
                 }
                ]
    if opt_name == '--out':
        return [['-o', opt_name],
                {'metavar':'FILE',
                 'dest':'out',
                 'type':'string',
                 'default':'-',
                 'help':'Use the given output FILE instead of stdout.'
                 }
                ]
    if opt_name == '--depgraphto':
        return [[opt_name],
                {'metavar':"FILE",
                 'dest':'depgraphto',
                 'type':'string',
                 'help':"Write the dependency graph in DOT format" + \
                     " to the given FILE. " + \
                     " Use Graphviz dotty command for visualisation."
                 }
                ]
    if opt_name == '--file':
        return [['-f', opt_name],
                {'metavar':'FILE',
                 'dest':'src',
                 'type':'string',
                 'default':'-',
                 'help':'Use the given input FILE instead of stdin.'
                 }
                ]
    # Prevent circular dependencies
    import sequencer.ism.cli as ism_cli
    if opt_name == '--algo':
        return [[opt_name],
                {'dest':'algo',
                 'type':'choice',
                 'action':'store',
                 'choices':ism_cli.ALGO_TYPES.keys(),
                 'default':config.get(ism_cli.SEQMAKE_ACTION_NAME, "algo"),
                 'help':'Use the given algorithm. Can be one of: ' + \
                     ', '.join(ism_cli.ALGO_TYPES.keys()) + \
                     '. Default: %default'}
            ]
    if opt_name == '--actionsgraphto':
        return [[opt_name],
                {'metavar':'FILE',
                 'dest':'actionsgraphto',
                 'type':'string',
                 'help':'Write the actions dependency graph' + \
                     ' in DOT format' + \
                     ' to the given FILE. ' + \
                     ' Use Graphviz dotty command for' + \
                     ' visualisation.'}
                ]
    # Prevent circular dependencies
    import sequencer.ise.cli as ise_cli
    if opt_name == '--progress':
        return [[opt_name],
                {'metavar':'n',
                 'dest':'progress',
                 'type':'float',
                 'default':config.getfloat(ise_cli.SEQEXEC_ACTION_NAME,
                                           "progress"),
                 'help':'Display a progress report every ' + \
                     'n seconds (roughly). If n=0, do not display any ' + \
                     'progress. Default: %default'
                 }
                ]
    if opt_name == '--doexec':
        return [[opt_name],
                {'dest':'doexec',
                 'metavar': '[yes|no]',
                 'type':'choice',
                 'action':'store',
                 'choices':['yes', 'no'],
                 'default':config.get(ise_cli.SEQEXEC_ACTION_NAME,
                                      "doexec"),
                 'help':"If 'no', *do not* execute anything." + \
                 " This is often used with '--report model'" + \
                 " and/or  '--actionsgraphto' options in order to " + \
                 "\"see\" what will be done before the actual execution." + \
                 " Default: %default"}
                ]
    if opt_name == '--report':
        return [[opt_name],
                {'dest':'report',
                 'type':'choice',
                 'metavar':'type',
                 'action':'store',
                 'choices':ise_cli.REPORT_TYPES,
                 'default':config.get(ise_cli.SEQEXEC_ACTION_NAME,
                                      "report"),
                 'help':'Display a report.' + \
                     ' Can be one of: ' + \
                     ', '.join(ise_cli.REPORT_TYPES) + \
                     '. Default: %default'
                 }
                ]
    if opt_name == '--dostats':
        return [[opt_name],
                {'dest':'dostats',
                 'metavar': '[yes|no]',
                 'type':'choice',
                 'action':'store',
                 'choices':['yes', 'no'],
                 'default':config.get(ise_cli.SEQEXEC_ACTION_NAME,
                                      "dostats"),
                 'help':"If 'yes', display statistics. Default: %default."
                 }
                ]

    if opt_name == '--fanout':
        return [[opt_name],
                {'metavar':'n',
                 'dest':'fanout',
                 'type':'int',
                 'default':config.getint(ise_cli.SEQEXEC_ACTION_NAME,
                                         "fanout"),
                 'help':'Launch a maximum of n actions in parallel.' + \
                     ' Default: %default'
                 }
                ]
    if opt_name == '--nodeps':
        return [[opt_name],
                {'dest':'nodeps',
                 'action':'store_true',
                 'default':False,
                 'help':'Do not update references from ' + \
                     'other rules in the same ruleset.'
                 }
                ]
    # Prevent circular dependencies
    import sequencer.dgm.cli as dgm_cli
    if opt_name == '--docache':
        return [[opt_name],
                {'dest':'docache',
                 'metavar': '[yes|no]',
                 'type':'choice',
                 'action':'store',
                 'choices':['yes', 'no'],
                 'default':config.get(dgm_cli.DEPMAKE_ACTION_NAME,
                                      "docache"),
                 'help':'Use a cache for filtering decision. Default: %default'
                 }]
    raise ValueError("Unknown option: %s" % opt_name)

def td_to_seconds(delta):
    """
    Return the number of seconds of a time duration.
    """
    return float((delta.microseconds +
                  (delta.seconds +
                   delta.days * 24 * 3600) * 10**6)) / 10**6

def _get_metainfo():
    """
    Return meta information from the meta file. This file is normally
    written by the packaging process.
    """
    currentdir = os.path.dirname(__file__)
    meta_file_name = os.path.join(currentdir, _SEQUENCER_META_FILE)
    meta = dict()
    try:
        with open(meta_file_name, "r") as meta_file:
            for line in meta_file:
                if not line.startswith('#'):
                    (key, sep, value) = line.partition(' = ')
                    if len(value) > 0:
                        meta[key] = value.strip()
    except IOError as ioe:
        _LOGGER.error("Can't open meta file %s: %s ", meta_file_name, ioe)
    return meta

def get_version():
    """
    Returns the version of the sequencer software. The actual version
    is registered into the _SEQUENCER_META_FILE. The content of this
    file should be generated during the packaging phase.
    """
    meta = _get_metainfo()
    return meta.get(_SEQUENCER_VERSION_PREFIX, _MISSING_VERSION_MSG)

__version__ = get_version()

def get_lastcommit():
    """
    Returns the last commit id. The actual commit id
    is registered into the _SEQUENCER_META_FILE. The content of this
    file should be generated during the packaging phase.
    """
    meta = _get_metainfo()
    return meta.get(_SEQUENCER_LASTCOMMIT_PREFIX, _MISSING_LASTCOMMIT_MSG)


def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True


    This code was taken directly from:
    http://code.activestate.com/recipes/541096-prompt-the-user-for-confirmation/
    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s [%s]|%s: ' % (prompt, 'y', 'n')
    else:
        prompt = '%s [%s]|%s: ' % (prompt, 'n', 'y')

    while True:
        ans = raw_input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('please enter y or n.')
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False


def get_db_connection(host, database, user, password, retry=8):
    """
    If a specific port is required, provide it inside the host name, as in:
    localhost:3124

    Return a generic connection where:
      - 'connection': is a connection to the db.
      - 'param_char' is the string used to represent parameter in the
    specific implementation of the Python DB API.
    """
    assert None not in (host, database, user, password)
    i = 0
    import pgdb
    while True:
        try:
            connection = pgdb.connect(host=host,
                                      database=database,
                                      user=user,
                                      password=password)
            break
        except pgdb.InternalError as pgi:
            if i == retry:
                _LOGGER.error("Connection to db %s" % database + \
                                       " failed after %d retries." % retry + \
                                       " Exiting." + \
                                       " Failure message: " + str(pgi).strip())
                sys.exit(os.EX_TEMPFAIL)

            # The next formula gives the following result:
            # i    min    middle    max
            # 0    0,0105    0,0350    0,0600
            # 1    0,0110    0,0600    0,1100
            # 2    0,0120    0,1100    0,2100
            # 3    0,0140    0,2100    0,4100
            # 4    0,0180    0,4100    0,8100
            # 5    0,0260    0,8100    1,6100
            # 6    0,0420    1,6100    3,2100
            # 7    0,0740    3,2100    6,4100
            # 8    0,1380    6,4100    12,8100
            # 9    0,2660    12,8100    25,6100

            # Expressed in seconds
            delay = (2**i * 50 * random.randint(1, 100) + 1000)/100000.0
            i = i + 1
            _LOGGER.debug("Connection to db %s failed." % database + \
                          " Next retry #%d in %s s" % (i, delay))
            time.sleep(delay)
    assert pgdb.paramstyle == 'pyformat'
    return PostgresDB(database, connection)

class GenericDB(object):
    """
    Instance of this class are independent of the underlying DB
    implementation. Any DB-API 2.0 compliant object should work. This
    allows SQL statements to be performed on various DB such as postgresql
    (the actual target) or sqlite (used for unit tests).

    Note however, that the paramstyle differs between database. For
    example, sqlite uses 'qmark' whereas pgdb uses
    'format'. Therefore, the exact string should be passed to
    guarantee database independence.
    """
    def __init__(self, name, connection, param_char='?'):
        self.name = name
        self.connection = connection
        self.param_char = param_char

    def sql_match_exp(self, column, regexp):
        """
        Return the actual db implementation dependent expression for
        regexp matching.
        """
        raise NotImplementedError("Abstract class: should be " + \
                                      "implemented in subclasses")

    def execute(self, sql, values=None, fetch=False):
        """
        Execute the given sql statement with the given values.
        If 'fetch' is True returns a tuple (rowcount, result).
        """
        result = None
        sql = sql.replace('?', self.param_char)
        _LOGGER.debug("Executing query: %s with %s", sql, values)
        cursor = self.connection.cursor()
        if values is not None:
            cursor.execute(sql, values)
        else:
            cursor.execute(sql)
        rowcount = cursor.rowcount
        if fetch:
            result = cursor.fetchall()
            _LOGGER.debug("Returned: %s", result)
        self.connection.commit()
        return (rowcount, result)

    def dump(self, out):
        """
        Dump the DB to the given file.
        """
        for line in self.connection.iterdump():
            out.write(u'%s\n' % line)

    def close(self):
        """
        Close the connection.
        """
        self.connection.close()

    def get_name(self):
        """
        Return this database name.
        """
        return self.name

class PostgresDB(GenericDB):
    """
    Postgres implementation of the GenericDB.
    """
    def __init__(self, name, connection):
        # The module uses '%s' as the SQL parameter format.
        GenericDB.__init__(self, name, connection, '%s')

    def sql_match_exp(self, column, regexp):
        return column + " ~ " + regexp


def substitute(value_for, string):
    """
    For each key in value_for, substitue the related value in the given string.
    """
    if string is None:
        return None
    result = string
    for key in value_for:
        result = result.replace(key, value_for[key])
    return result

def make_list_from_sql_result(sql_result, column_name):
    """
    Returns a list made from each element of the given column_name in
    the given sql_result.
    """
    result = []
    for i in sql_result:
        result.append(i[column_name])

    return result


def get_header(title, symbol, size):
    """
    Display a header of the given size, filled with the given symbol
    with the title in the center
    """
    title_len = len(title)
    symbol_nb = (size - title_len) // 2
    return (symbol * symbol_nb) + title + (symbol * symbol_nb)

def get_nodes_from(component_set):
    """
    Get the list of nodes specified in the given component set
    """
    index = component_set.find('#')
    if (index == -1):
        return component_set
    return component_set[0:index]

def smart_display(header, tab_values, hsep=u"-", vsep=u" ",
                  left_align=None, columns_max=dict()):
    """
    Display an array so each columns are well aligned.

    header: the list of column header that should be displayed

    tab_values: a list of lines that should be displayed. A line is a
    list of strings. If one element in the line is the HSEP constant, the
    'hsep' string will fill the corresponding column.

    hsep: the horizontal separator (just after the header)
    vsep: the vertical separator (between columns)

    left_align: a list of boolean representing left alignement when true.

    columns_max: a {column_header: max} dictionnary that should be used
    for the display of the related column. If max is 0, it means
    that the column will not be displayed at all. If max is greater
    than 0, then max characters will be used for the display of the column.
    When a string is greater than the 'max', it is truncated and a legend is
    produced at the end of the table. When max=REMOVE_UNSPECIFIED_COLUMNS, then
    only header from columns_max will be displayed.

    *Warning*: Unicode strings are required.
    """

    if left_align is not None:
        assert len(left_align) == len(header)

    def truncate(s, maxchar, legends, nextref):
        """
        Return a tuple (trunc_s, nextref) where trunc_s is
        the string 's' truncated if its length is larger than
        maxchar, and the string 's' unmodified otherwise.
        If truncation occurs, the given legends dictionnary is updated
        and nextref is incremented (and returned in the tuple)
        """
        result = s
        if s is not None and len(s) > maxchar:
            trunc_maxchar = maxchar - TRUNCATION_MAX_SIZE
            assert trunc_maxchar >= 0, "Can't represent string %s " % s + \
                " with the provided maximum" + \
                " characters %d" % maxchar
            ref = nextref
            if s in legends:
                ref = legends[s]
            else:
                legends[s] = ref
                nextref = ref + 1
            result = s[0:trunc_maxchar] + TRUNCATION_REF % ref
        return (result, nextref)

    def remove_columns(header, columns_max, tab_values):
        """
        Remove columns with a maximum character number set to 0 and
        columns that are not present in columns_max if one element in
        columns_max maps to REMOVE_UNSPECIFIED_COLUMNS
        """
        # We use a copy because we modify the list during the iteration
        given_header = header[:]
        # If we found a columns_max set to REMOVE_UNSPECIFIED_COLUMNS
        # we scan the header table and we set unspecified column_max
        # to 0 so they will be removed in the next step
        for cmax in columns_max.copy():
            if columns_max[cmax] == REMOVE_UNSPECIFIED_COLUMNS:
                for head in given_header:
                    if head not in columns_max:
                        columns_max[head] = 0

        for cmax in columns_max.copy():
            if columns_max[cmax] == REMOVE_UNSPECIFIED_COLUMNS:
                del columns_max[cmax]

        i = 0
        for head in given_header:
            if head in columns_max and columns_max[head] == 0:
                del header[i]
                for line in tab_values:
                    del line[i]
            else:
                # Next column is j+1 only if a removal has not been made.
                i += 1

    def compute_max_map(header, tab_values, columns_max):
        """
        Return a list of maximum number of character for each column.
        """
        col = 0
        max_map = [0] * col_nb
        while col < col_nb:
            head = header[col]
            max_map[col] = columns_max.get(head, len(header[col]))
            line = 0
            while line < line_nb:
                string = tab_values[line][col]
                if string is not HSEP:
                    max_map[col] = columns_max.get(head,
                                                   max(max_map[col],
                                                       len(string)))
                line += 1
            col += 1
        return max_map

    def align(left_align, data, col):
        """
        Return the given data for the given col aligned
        """
        if left_align is not None and left_align[col]:
            return u"%-*.*s" % data
        else:
            return u"%*.*s" % data

    legends = dict()
    nextref = 0
    remove_columns(header, columns_max, tab_values)
    col_nb = len(header)
    line_nb = len(tab_values)
    max_map = compute_max_map(header, tab_values, columns_max)
    lines = []
    col = 0
    line_len = 0
    # Write the header
    while col < col_nb:
        (head, nextref) = truncate(header[col], max_map[col], legends, nextref)
        lines.append(align(left_align, (max_map[col], max_map[col], head), col))
        lines.append(vsep)
        line_len += (max_map[col] + len(vsep))
        col += 1
    # Write the separator
    lines.append('\n' + (hsep * line_len) + '\n')
    line = 0
    # Write each line
    while line < line_nb:
        col = 0
        while col < col_nb:
            (string, nextref) = truncate(tab_values[line][col],
                                         max_map[col], legends, nextref)
            if string is HSEP:
                string = hsep * max_map[col]
            data = (max_map[col], max_map[col], string)
            lines.append(align(left_align, data, col))
            lines.append(vsep)
            col += 1
        line += 1
        lines.append(u'\n')
    if len(legends) > 0:
        lines.append(u'\nLegend:\n')
        for (string, ref) in sorted(legends.items(), key=itemgetter(1)):
            if string is not None:
                lines.append(str(ref) + ': ' + string + '\n')

    return "".join(lines)

def output_graph(graph, root=None):
    """
    Returns a tuplet containing:
    - the result of the depth_first_search() function starting at 'root' (is is a tuplet)
    - a dot format output of the given graph (display it using graphviz dotty command)
    """

    dfs = depth_first_search(graph, root)
    dot = write(graph)
    return [dfs, dot]


def remove_leaves(graph, leaves):
    """
    Remove the given leaves form the given graph, including any edges
    that are incidents to them.
    """
    _LOGGER.debug("Removing %s from %s", leaves, graph)
    for node in leaves:
        incidents = graph.incidents(node)
        for parent in incidents:
            graph.del_edge((parent, node))
        graph.del_node(node)

def write_graph_to(graph, file_name):
    """
    Write the given graph to the given file_name. If 'file_name' ==
    '-', prints to stdout (using logger.output())
    """
    nodes = graph.nodes()
    for node in nodes:
        # Attributes (also called label in pygraph) on nodes may be
        # actions (in the case of depgraph). They may contain symbols
        # (such as quote, double quote, colon, ...) that might confuse
        # the DOT graph format. So we remove all of them directly
        # since escaping seems a bit tricky for now.
        attributes = graph.node_attributes(node)
        for attribute in attributes:
            attributes.remove(attribute)

    dot = output_graph(graph)[1]
    if file_name == '-':
        _LOGGER.output(dot)
    else:
        a_file = open(file_name, "w")
        print(dot, file=a_file)
        _LOGGER.debug("Graph written to %s", file_name)

class SequencerError(Exception):
    """
    Base Class for all Sequencer Exception
    """
    pass

class UnknownRuleSet(SequencerError):
    """
    Raised when a given ruleset is unknown from the sequencer.
    """
    def __init__(self, ruleset):
        SequencerError.__init__(self, "Unknown ruleset: %s" % ruleset)

class InternalError(SequencerError):
    """
    Thrown when an error has been detected in the sequencer itself.

    When this happened, it usually means that a bug has been found.
    In this case, please contact Bull support.
    """
    pass

class CyclesDetectedError(SequencerError):
    """
    Thrown when a cycle has been detected in the given graph.
    """
    def __init__(self, cycle, graph):
        self.cycle = cycle
        self.graph = graph
        msg = "At least one cycle has been detected: " + str(cycle)
        SequencerError.__init__(self, msg)

    def get_all_cycles(self):
        """
        Currently, this just return the result of the call to
        mutual_accessibility which actually returns the set of
        strongly connected components in the graph. From that result,
        it should be possible to get the actual cycles.

        But this is not implemented yet.
        """
        return mutual_accessibility(self.graph)


class SQLError(Exception):
    """
    Thrown when an SQL error is detected.
    """
    pass


