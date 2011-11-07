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
This module defines logging stuff to all sequencer modules.
"""
import logging
import sys, types
from logging import Handler, Formatter, DEBUG, INFO, WARNING, ERROR, CRITICAL
from logging.handlers import TimedRotatingFileHandler, MemoryHandler

import sequencer


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]


# Use by the logging framework
OUTPUT_LOG_LEVEL = 25 # Between INFO=20 and WARNING=30
_LOGGER_CLASS = logging.getLoggerClass()

class SequencerLogger(_LOGGER_CLASS):
    """
    Provides an output() method.
    """
    def __init__(self, name):
        logging.Logger.__init__(self, name)

    def output(self, msg, *args, **kwargs):
        """
        Displays the given message at the OUTPUT_LOG_LEVEL
        """
        self.log(OUTPUT_LOG_LEVEL, msg, *args, **kwargs)

logging.setLoggerClass(SequencerLogger)
logging.addLevelName(OUTPUT_LOG_LEVEL, 'OUTPUT')

class SmartFormatter(Formatter):
    """
    Multiplexer Formatter Implementation. Instance of this class uses
    a specific formatter for each level.
    """
    def __init__(self, formatter_for_level=dict(), default=Formatter()):
        """
        Use the given formatter_for_level map of {level: formatter} to
        format messages. If for a given level, a formatter does not exist in
        the formatter_for_level dictionary, the default formatter specified
        by 'default' is used instead.
        """
        Formatter.__init__(self)
        self.formatter_for_level = formatter_for_level
        self.default = default

    def format(self, record):
        """
        Format the given record using the formatter given by this
        record level.
        """
        formatter = self.formatter_for_level.get(record.levelno, self.default)
        return formatter.format(record)

class StandardUnixHandler(Handler):
    """
    This handler writes a given record to the standard output if the
    record level is strictly less than 'error_level'. Otherwise, the
    record is written to the standard error.
    """
    def __init__(self, level=logging.NOTSET, error_level=logging.WARNING):
        """
        Records with a level strictly less that error_level are
        written to standard output. Standard error is used otherwise.
        """
        Handler.__init__(self, level)
        self.error_level = error_level

    def _get_stream_for_(self, record):
        """
        Return the stream (standard error or standard output according
        to the given record level)
        """
        return sys.stderr if record.levelno >= self.error_level else sys.stdout

    def emit(self, record):
        """
        This peace of code is largely taken from StreamHandler code.
        The main difference is the call to '_get_stream_for()' at the very
        beginning.
        """
        try:
            msg = self.format(record)
            # Here is the difference: get the stream related to record
            # level
            stream = self._get_stream_for_(record)
            fs = "%s\n"
            if not hasattr(types, "UnicodeType"): #if no unicode support...
                stream.write(fs % msg)
            else:
                try:
                    if (isinstance(msg, unicode) and
                        getattr(stream, 'encoding', None)):
                        fs = fs.decode(stream.encoding)
                        try:
                            stream.write(fs % msg)
                        except UnicodeEncodeError:
                            #Printing to terminals sometimes fails. For example,
                            #with an encoding of 'cp1251', the above write will
                            #work if written to a stream opened or wrapped by
                            #the codecs module, but fail when writing to a
                            #terminal even when the codepage is set to cp1251.
                            #An extra encoding step seems to be needed.
                            stream.write((fs % msg).encode(stream.encoding))
                    else:
                        stream.write(fs % msg)
                except UnicodeError:
                    stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)



def init_trace(options):
    """
    Initialize the sequencer specific way of logging.
    The sequencer defines two handler:
    - one that fills a log file (provided by options.log)
    - one that writes to stdout/stderr according to the log level
    """

    # Use the module name instead of a hardwired string in case the module
    # name change (e.g: from sequencer to sequencer when it will become
    # open-source.
    root_logger = logging.getLogger(sequencer.__name__)
    # By default, filelog_level is infinity: we do not log unless
    # specified
    file_handler = None
    try:
        log_args = getattr(options, 'log')
        (log_file, sep, level) = log_args.partition(':')
        # create file handler which logs messages. Rotate every
        # monday, keep 4 such files (hence 4 weeks)
        file_handler = TimedRotatingFileHandler(log_file, 'W0', backupCount=4)
        if len(level) > 0:
            file_handler.setLevel(logging.getLevelName(level))
        else:
            # By default, we log all messages to the log file.
            file_handler.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        sformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        formatter = Formatter(sformat)
        file_handler.setFormatter(formatter)
        # add the handlers to the logger
        root_logger.addHandler(MemoryHandler(8192,
                                             file_handler.level,
                                             file_handler))
    except AttributeError:
        pass

    # Console level default to OUTPUT (normal stdout)
    console_level = OUTPUT_LOG_LEVEL
    # create console handler with a higher log level
    console_handler = StandardUnixHandler()
    # DEBUG is considered more important
    # If all three options are seen on the command line,
    # DEBUG will be used.
    if getattr(options, 'quiet'):
        console_level = logging.WARNING
    if getattr(options, 'verbose'):
        console_level = logging.INFO
    if getattr(options, 'debug'):
        console_level = logging.DEBUG

    console_handler.setLevel(console_level)
    sformat = '%(levelname)s %(funcName)s() - %(message)s'
    lvl_func_msg_formatter = Formatter(sformat)
    msg_formatter = Formatter('%(message)s')
    lvl_msg_formatter = Formatter('%(levelname)s - %(message)s')
    # The console handler provides the following:
    # OUTPUT messages are displayed without any extra
    # WARNING, ERROR and CRITICAL messages should display the level
    # INFO also displays the level but not the function since it can
    # be used by non-developper
    formatter_for_level = {DEBUG: lvl_func_msg_formatter,
                           INFO: lvl_msg_formatter,
                           OUTPUT_LOG_LEVEL: msg_formatter,
                           WARNING: lvl_msg_formatter,
                           ERROR: lvl_msg_formatter,
                           CRITICAL: lvl_msg_formatter}
    formatter = SmartFormatter(default=lvl_func_msg_formatter,
                               formatter_for_level=formatter_for_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(MemoryHandler(8192,
                                         console_handler.level,
                                         console_handler))
    # Set root logger level to the minimum instead of NOTSET so for
    # debug and info levels, one can use logger.isEnabledFor(level)
    # method for performance purpose.
    min_level = min(sys.maxint if file_handler is None else file_handler.level,
                    console_handler.level)
    root_logger.setLevel(min_level)
    logging.getLogger('').setLevel(logging.NOTSET)






