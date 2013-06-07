#!/usr/bin/python
# -*- coding: UTF-8 -*-

###############################################################################
# Copyright (C) 2009  Bull S. A. S.  -  All rights reserved
# Bull, Rue Jean Jaures, B.P.68, 78340, Les Clayes-sous-Bois
# This is not Free or Open Source software.
# Please contact Bull S. A. S. for details about its license.
###############################################################################
import unittest

import os, sys
import StringIO
import imp
import optparse
import re
import logging

from sequencer.commons import GenericDB, get_header
from shutil import copyfile

_logger = logging.getLogger()

_formatter = logging.Formatter('%(relativeCreated)s %(levelname)s %(funcName)s() - %(message)s')
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)

SRCDIR = u"./uni_tests"
BASEDIR = u"/tmp/testmmąöî"
TESTFILE = os.path.join(BASEDIR, u"testmmąöî.rs")

class LevelFilter(object):
    def __init__(self, level):
        self.__level = level

    def filter(self, logRecord):
        return logRecord.levelno <= self.__level

class Capturer():
    """
    Captures only the messages sent to output (lvl == 25, cf sequencer.tracer)
    by the sequencer, such as the graphs or known types table.
    """
    def __init__(self, logger):
        self.logger = logger
        self.capturer = StringIO.StringIO()
        handler = logging.StreamHandler(self.capturer)
        handler.setLevel(25)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        handler.addFilter(LevelFilter(25))
        self.logger.addHandler(handler)

    def getCaptured(self):
        return self.capturer.getvalue()

class BaseTest(unittest.TestCase):
    """Base Test Class"""
    def setUp(self):
        _logger.debug(get_header(" Start %s " % self.id(), "*", 120))


    def tearDown(self):
#        _logger.debug(get_header(" Stop %s " % self.id(), "*", 80))
        pass

class MinimalInitTest(BaseTest):

    def setUp(self):
        #import bin/sequencer as a module
        py_source_description = (".py", "U", imp.PY_SOURCE)
        module_filepath = "./bin/sequencer"
        module_name = os.path.basename(module_filepath)
        with open(module_filepath, "U") as module_file:
            seq_module = imp.load_module(
                    module_name, module_file, module_filepath, py_source_description)
        self.usage_parms = dict()
        self.usage_parms['base'] = ''
        self.usage_parms['dir'] = BASEDIR
        self.usage_parms['data'] = dict()
        self.parser = optparse.OptionParser()
        self.logger = seq_module._logger

        #init
        seq_module._update_usage(self.parser, self.usage_parms)
        self.db = self.usage_parms['db']
        self.config = self.usage_parms['config']
        self.usage_data_for = self.usage_parms['data']
        self.shortcuts = self.usage_parms['shortcuts']

        #os.system("ln ../bin/sequencer ./sequencer.py")
        #import sequencer.py
        #_update_usage(self.parser, self.usage_parms)
        
        #globalz = dict()
        #localz = dict()
        #execfile("./mytest", globalz, localz)
        #plop = localz['TestClass']()
        #plop.testfunc()
        #execfile("../bin/sequencer", globalz, localz)
        #localz['_update_usage'](self.parser, self.usage_parms)

    def tearDown(self):
        try:
            os.rmdir(BASEDIR)
            #remove binary file created by importing bin/sequencer as a module
            os.remove("./bin/sequencerc")
        except OSError:
            assert False

class FullInitTest(MinimalInitTest):

    def setUp(self):
        os.mkdir(BASEDIR)
        copyfile(SRCDIR+"/test_config", BASEDIR+"/config")
        copyfile(SRCDIR+"/test_rs", TESTFILE) 
        super(FullInitTest, self).setUp()
        
    def tearDown(self):        
        for afile in os.listdir(BASEDIR):
            filepath = os.path.join(BASEDIR, afile)
            try:
                os.remove(filepath)
            except OSError:
                assert False
        super(FullInitTest, self).tearDown()


