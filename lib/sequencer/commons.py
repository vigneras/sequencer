# -*- coding: utf-8 -*-
"""
This module defines common stuff to all sequencer modules.
"""
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

from __future__ import print_function, division
from logging import getLogger
from pygraph.algorithms.accessibility import mutual_accessibility
from pygraph.algorithms.searching import depth_first_search
from pygraph.readwrite.dot import write
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import InvalidGraphType
from pygraph.classes.graph import graph
from pygraph.classes.hypergraph import hypergraph
from operator import itemgetter
from ConfigParser import RawConfigParser
import cStringIO
import math
import os
import pwd
import random
import re
import sys
import time


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]

# Should be after the get_version() function definition! See below
# __version__ = get_version()

_LOGGER = getLogger(__name__)
_PACKAGE_NAME = __name__.split('.')[0]


def get_package_name():
    """
    Return the distribution package name (RPM, DEB, whatever
    the final format is)
    """
    return _PACKAGE_NAME


_SEQUENCER_META_FILE = ".metainfo"
_SEQUENCER_VERSION_PREFIX = get_package_name() + ".version"
_SEQUENCER_LASTCOMMIT_PREFIX = get_package_name() + ".lastcommit"
_MISSING_VERSION_MSG = "?.?.?"
_MISSING_LASTCOMMIT_MSG = "? ? ? ?"

# Used by smartdisplay
FILL_EMPTY_ENTRY = '!#$_'
TRUNCATION_REF = "..{%s}"
TRUNCATION_MAX_SIZE = len(TRUNCATION_REF)
REMOVE_UNSPECIFIED_COLUMNS = -1

# Use by replace_if_none
NONE_VALUE = unicode(None)


def convert_uni_graph_to_str(G):
    """
    Returns a graph filled with str values only.
    Inspired by pygraph.readwrite.markup.write
    """
    if (type(G) == graph):
        gr = graph()
    elif (type(G) == digraph ):
        gr = digraph()
    elif (type(G) == hypergraph ):
        return write_hypergraph(G)
    else:
        raise InvalidGraphType

    for each_node in G.nodes():
        strnode = to_str_from_unicode(each_node, should_be_uni=True)
        gr.add_node(strnode)

        for each_attr in G.node_attributes(each_node):
            strattr0 = to_str_from_unicode(each_attr[0], should_be_uni=True)
            strattr1 = to_str_from_unicode(each_attr[1], should_be_uni=True)
            gr.add_node_attribute(strnode, (strattr0, strattr1))

    for edge_from, edge_to in G.edges():
        strfrom = to_str_from_unicode(edge_from, should_be_uni=True)
        strto = to_str_from_unicode(edge_to, should_be_uni=True)
        strlabel = to_str_from_unicode(
                        G.edge_label((edge_from, edge_to)),
                        should_be_uni=True)
        strweight = to_str_from_unicode(
                        G.edge_weight((edge_from, edge_to)), 
                        should_be_uni=True)
        gr.add_edge((strfrom, strto))
        gr.set_edge_label((strfrom, strto), strlabel)
        gr.set_edge_weight((strfrom, strto), strweight)
        for attr_name, attr_val in G.edge_attributes((edge_from, edge_to)):
            stra_name = to_str_from_unicode(attr_name, should_be_uni=True)
            stra_val = to_str_from_unicode(attr_val, should_be_uni=True)
            gr.add_edge_attribute((edge_from, edge_to), (stra_name, stra_val))

    return gr


# Overriding of the write() function of RawConfigParser is necessary because 
# it does not handle non-ascii characters
# TODO it would be FAR FAR better to write a wrapper: would  convert a parser
# that contains unicode data to a parser that contains str
class UnicodeConfigParser(RawConfigParser):
    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for (key, value) in self._defaults.items():
                fp.write("%s = %s\n" % (key, str(value).replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section.encode('utf-8'))
            for (key, value) in self._sections[section].items():
                if key == "__name__":
                    continue
                if (value is not None) or (self._optcre == self.OPTCRE):
                    #the following line replaces:
                    #key = " = ".join((key, str(value).replace('\n', '\n\t')))
                    key = u" = ".join((key, value.replace(u'\n', u'\n\t')))
                fp.write("%s\n" % (key.encode('utf-8')))
            fp.write("\n")


def to_unicode(value, encoding='utf-8'):
    """
    Returns a unicode object made from the value of the given string.
    """
    if isinstance(value, unicode):
        return value
    elif isinstance(value, basestring):
        try:
            value = unicode(value, encoding)
        except (UnicodeDecodeError):
            value = value.decode('utf-8', 'replace')
    return value


def to_str_from_unicode(value, encoding='utf-8', should_be_uni=True):
    """
    Returns a string encoded from the given unicode object
    """
    if isinstance(value, unicode):
        value = value.encode(encoding)
        if not should_be_uni:
            _LOGGER.warning("%s: is unicode-typed, should be a string" % value)
    elif isinstance(value, basestring):
        if should_be_uni:
            _LOGGER.warning("%s: is a string, should be unicode-typed" % value)
        pass
    return value


def replace_if_none(value):
    """
    Replace the given value by NONE_VALUE if it is considered none or empty
    """
    return None if value is not None and (value == NONE_VALUE or len(value) == 0) \
        else value


def replace_if_none_by_uni(value):
    """
    Replace the given value by unicode "None" if it is considered none or empty
    """
    return NONE_VALUE if value is None or (value == NONE_VALUE or len(value) == 0) \
        else value


def get_basedir(base=None):
    """
    Returns the base directory for the fetching of rules and
    configuration files.
    This directory is based on the command name itself.
    """
    cmd = to_unicode(os.path.basename(sys.argv[0]))
    cmdfile = to_unicode(os.path.abspath(sys.argv[0]))
    # Do not follow symbolic links
    stat = os.lstat(cmdfile)
    if stat.st_uid == 0:
        owner = u'root'
        confdir = os.path.join(u'/etc', cmd)
    else:
        owner_data = pwd.getpwuid(stat.st_uid)
        owner = to_unicode(owner_data[0])
        confdir = to_unicode(os.path.join(owner_data[5], '.'+cmd))
    _LOGGER.debug("Owner is %s; confdir starts at %s",  owner, confdir)
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
                   delta.days * 24 * 3600) * 10 ** 6)) / 10 ** 6


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

    # raw_input does not handle unicode
    if isinstance(prompt, unicode):
        prompt = prompt.encode('utf-8')

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
            delay = (2 ** i * 50 * random.randint(1, 100) + 1000) / 100000.0
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


# Code below taken from http://code.activestate.com/recipes/267662/ (r7)
# and modified to our own needs.
def indent(rows,
           hasHeader=False, headerChar='-',
           delim=' | ',
           justify_functions=None,
           separateRows=False,
           prefix='', postfix='',
           max_widths=None,
           filler_char='_'):
    """Indents a table by column.
       - rows: A sequence of sequences of items, one sequence per row.
       - hasHeader: True if the first row consists of the columns' names.
       - headerChar: Character to be used for the row separator line
         (if hasHeader==True or separateRows==True).
       - delim: The column delimiter.
       - justify_functions: Determines how are data justified in each column.
         Valid values are function of the form f(str,width)->str such as 
         str.ljust, str.center and str.rjust. Default is str.ljust.
       - separateRows: True if rows are to be separated by a line
         of 'headerChar's.
       - prefix: A string prepended to each printed row.
       - postfix: A string appended to each printed row.
       - max_widths: Determines the maximum width for each column.
         Words are wrapped to the specified maximum width if greater than 0.
         Wrapping is not done at all when max_width is set to None.
         This is the default.
       - filler_char: a row entry that is FILL_EMPTY_ENTRY will be filled by
         the specified filler character up to the maximum width for
         the related column. 
    """
    if justify_functions is None:
        justify_functions = [unicode.ljust] * len(rows[0])
    _LOGGER.debug("Justify: %s", justify_functions)
    if max_widths is None:
        max_widths = [0] * len(rows[0])
    _LOGGER.debug("max_widths: %s", max_widths)

    def i2str(item, maxwidth):
        """Trasform the given row item into a final string."""
        if item is FILL_EMPTY_ENTRY:
            return filler_char * maxwidth
        return item

    # closure for breaking logical rows to physical, using wrapfunc
    def rowWrapper(row):
        newRows = [wrap_onspace_strict(item, width).split('\n') for (item, width) in zip(row, max_widths)]
        _LOGGER.debug("NewRows: %s", newRows)
        if len(newRows) <= 1:
            return newRows
        return [[substr or '' for substr in item] for item in map(None, *newRows)]

    # break each logical row into one or more physical ones
    logicalRows = [rowWrapper(row) for row in rows]
    _LOGGER.debug("logicalRows: %s", logicalRows)
    # Fetch the list of physical rows
    physicalRows = logicalRows[0]
    for lrow in logicalRows[1:]:
        physicalRows += lrow
    _LOGGER.debug("physicalRows: %s", physicalRows)
    # columns of physical rows
    if len(physicalRows) == 0:
        return ''
    columns = map(None, *physicalRows)
    _LOGGER.debug("columns: %s", columns)
    # get the maximum of each column by the string length of its items
    maxWidths = [max([len(item) for item in column]) for column in columns]
    _LOGGER.debug("MaxWidths: %s", maxWidths)
    rowSeparator = headerChar * (len(prefix) + len(postfix) + sum(maxWidths) + \
                                 len(delim) * (len(maxWidths) - 1))
    output = cStringIO.StringIO()
    if separateRows:
        print(rowSeparator, file=output)
    # for physicalRows in logicalRows:
    for row in physicalRows:
        _LOGGER.debug("row: %s", row)
        line = [justify(i2str(item, width),
                        width) for (item,
                                    justify,
                                    width) in zip(row,
                                                  justify_functions,
                                                  maxWidths)]

        line_uni = [to_unicode(elt) for elt in line]
        line_uni = prefix + delim.join(line_uni) + postfix
        line_uni = to_str_from_unicode(line_uni)

        print(line_uni,
              file=output)
        if separateRows or hasHeader:
            print(rowSeparator, file=output)
            hasHeader = False
    return output.getvalue()


# written by Mike Brown
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/148061
def wrap_onspace(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line[line.rfind('\n') + 1:])
                         + len(word.split('\n', 1)[0]
                              ) >= width)],
                   word),
                  text.split(' ')
                 )


def wrap_onspace_strict(text, width):
    """Similar to wrap_onspace, but enforces the width constraint:
       words longer than width are split."""
    if text is None:
        text = str(None)
    if width == 0:
        return text
    wordRegex = re.compile(r'\S{' + str(width) + r',}')
    return wrap_onspace(wordRegex.sub(lambda m: wrap_always(m.group(), width), text), width)


def wrap_always(text, width):
    """A simple word-wrap function that wraps text on exactly width characters.
       It doesn't split the text in words."""
    return '\n'.join([ text[width * i:width * (i + 1)] \
                       for i in xrange(int(math.ceil(1.*len(text) / width))) ])


def smart_display(header, data,
                  hsep=u'=', vsep=u' | ',
                  justify=None,
                  columns_max=None,
                  filler_char=u'-'):
    """
    Display an array so each columns are well aligned.

    - header: the list of column header that should be displayed

    - data: a list of lines that should be displayed. A line is a
      list of strings. If one element in the line is the FILL_EMPTY_ENTRY
      constant, the 'filler_char' string will fill up the corresponding column.

    - hsep: the horizontal separator (just after the header)
    - vsep: the vertical separator (between columns)

    - justify: a list of alignement justifiers, one for each column.
      Values in the list should be a function f(s,w)->s such as 
      str.rjust, str.ljust and str.center. Default is str.ljust.

    - columns_max: a {column_header: max} dictionnary that should be used
      for the display of the related column. If max is 0, it means
      that the column will not be displayed at all. If max is greater
      than 0, then max characters will be used for the display of the column.
      When a string is greater than the 'max', it is wrapped.
      When max=REMOVE_UNSPECIFIED_COLUMNS, then
      only header from columns_max will be displayed.

      *Warning*: Unicode strings are required.
    """

    assert header is not None
    assert data is not None
    assert hsep is not None
    assert vsep is not None
    assert len(header) > 0
    if justify is not None:
        assert len(justify) == len(header)
    else:
        justify = ['left'] * len(header)
    if columns_max is None:
        columns_max = dict()

    def remove_columns(header, columns_max, data):
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
                for line in data:
                    del line[i]
            else:
                # Next column is j+1 only if a removal has not been made.
                i += 1

    remove_columns(header, columns_max, data)
    col_nb = len(header)
    line_nb = len(data)
    max_widths = []
    for h in header:
        max_widths.append(columns_max.get(h, 0))

    return indent([header] + data, hasHeader=True,
                  headerChar=hsep, delim=vsep,
                  separateRows=False,
                  max_widths=max_widths,
                  filler_char=filler_char)


def output_graph(graph, root=None):
    """
    Returns a tuplet containing:
    - the result of the depth_first_search() function starting at 'root'
      (is a tuplet)
    - a dot format output of the given graph (display it using graphviz
      dotty command)
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
    strgraph = convert_uni_graph_to_str(graph)
    nodes = strgraph.nodes()
    for node in nodes:
        # Attributes (also called label in pygraph) on nodes may be
        # actions (in the case of depgraph). They may contain symbols
        # (such as quote, double quote, colon, ...) that might confuse
        # the DOT graph format. So we remove all of them directly
        # since escaping seems a bit tricky for now.
        attributes = strgraph.node_attributes(node)
        for attribute in attributes:
            attributes.remove(attribute)

    dot = output_graph(strgraph)[1]
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
        self.ruleset = ruleset


class NoSuchRuleError(SequencerError):
    """
    Raised when a given rule does no exist in a given ruleset.
    """
    def __init__(self, ruleset, name):
        SequencerError.__init__(self, "Ruleset %s does not "
                                "contain rule %s" % (ruleset, name))
        self.ruleset = ruleset
        self.name = name


class DuplicateRuleError(SequencerError):
    """
    Raised when a added rule is already in the db.
    """
    def __init__(self, ruleset, name):
        SequencerError.__init__(self,
                                " Rule: %s.%s does "
                                "already exists." % (ruleset, name))
        self.ruleset = ruleset
        self.name = name


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
