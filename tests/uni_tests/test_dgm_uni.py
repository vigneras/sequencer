#!/usr/bin/python
# -*- coding: UTF-8 -*-

import ConfigParser
import os, sys
import codecs
import logging

from commons import MinimalInitTest, FullInitTest, Capturer, BASEDIR, \
                    TESTFILE, SRCDIR
from sequencer.commons import to_unicode
from sequencer.dgm import cli as dgm_cli


def fetch_and_check(rsfile, section, option, value):
    """
    Checks in the file 'rsfile' if the given option in the given section is 
    equal to 'value'.
    """
    cp = ConfigParser.SafeConfigParser()
    try:
        with codecs.open(rsfile, 'r', encoding='utf-8') as f:
            cp.readfp(f)
    except IOError:
        return "OMGBBQ"
    if cp.has_section(section) and cp.has_option(section, option):
        return value == cp.get(section, option)
    else: 
        return False

def compare_to_ref(funcName, result):
    """
    For a unit test 'funcName', returns the expected value of a test result,
    stored in the file test_ref_values. The char '*' is used to preserve spaces
    at the end and at the beginning of a line.
    """
    cp = ConfigParser.SafeConfigParser()
    try:
        with codecs.open(SRCDIR+"/test_ref_values", 'r', encoding='utf-8') as f:
            cp.readfp(f)
    except IOError:
        return "OMGBBQ"
    if cp.has_section(funcName) and cp.has_option(funcName, result):
        val = cp.get(funcName, result).replace('\\n', '\n')
        val = val.replace('*', '')
        return val
    else: 
        return "ALBATROS!"

class DGMUnicodeTest(MinimalInitTest):

    def test_dbcreate(self):
        dgm_cli.dbcreate(self.db, self.config, [])
        assert os.path.exists(BASEDIR)

class DGMUnicodeFullTest(FullInitTest):

    def test_dbdrop(self):
        os.remove(BASEDIR+"/config")
        dgm_cli.dbdrop(self.db, self.config, ["-E"])
        assert os.path.exists(BASEDIR) == False
        # required for tearDown
        os.mkdir(BASEDIR)

    def test_dbadd_create_ruleset(self):
        uniargs = [u"mmąöî666", u"mmąöî", u"fake@mmąöî", u"mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs)
        filepath = os.path.join(BASEDIR, u"mmąöî666.rs")
        assert os.path.exists(filepath)
        with open(filepath) as f1:
            with open(TESTFILE) as f2:
                assert f1.read() == f2.read()

    def test_dbadd_nocreate(self):
        uniargs = [u"testmmąöî", u"mmąöîname", u"fake@mmąöîtype", \
                    u"mmąöîfilter", u"mmąöîaction", u"mmąöîdeps", \
                    u"mmąöîdepends", u"mmąöîcomments", u"mmąöîhelp"]
        dgm_cli.dbadd(self.db, self.config, uniargs)
        assert os.path.exists(TESTFILE)
        assert fetch_and_check(TESTFILE, u"mmąöîname", "types", u"fake@mmąöîtype")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "filter", u"mmąöîfilter")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "action", u"mmąöîaction")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "depsfinder", u"mmąöîdeps")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "dependson", u"mmąöîdepends")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "comments", u"mmąöîcomments")
        assert fetch_and_check(TESTFILE, u"mmąöîname", "help", u"mmąöîhelp")

    def test_dbremove_rule(self):
        with open(TESTFILE) as f1:
            assert f1.read() != ""
        uniargs = [u"-E", u"testmmąöî", u"mmąöî"]
        dgm_cli.dbremove(self.db, self.config, uniargs)
        assert os.path.exists(TESTFILE)
        with open(TESTFILE) as f1:
            assert f1.read() == ""

    def test_dbremove_ruleset(self):
        uniargs_add = [u"testmmąöî", u"mmąöî2", u"fake@mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)
        uniargs = [u"-E", u"testmmąöî"]
        dgm_cli.dbremove(self.db, self.config, uniargs)
        assert os.path.exists(TESTFILE) #it's not a bug, it's a feature...
        with open(TESTFILE) as f1:
            assert f1.read() == ""

    def test_dbupdate(self):
        uniargs = [u"testmmąöî", u"mmąöî", u"help=updatemmąöî", \
                    u"comments=updatemmąöî"]
        dgm_cli.dbupdate(self.db, self.config, uniargs)
        assert fetch_and_check(TESTFILE, u"mmąöî", "help", u"updatemmąöî")
        assert fetch_and_check(TESTFILE, u"mmąöî", "comments", u"updatemmąöî")

    def test_dbupdate_deps(self):
        # Add a rule that depends on the one in the test file (mmąöî)
        uniargs_add = [u"testmmąöî", u"mmąöî2", u"fake@mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)

        # Update the name of the first one and update references
        uniargs = [u"testmmąöî", u"mmąöî", u"name=updatemmąöî"]
        dgm_cli.dbupdate(self.db, self.config, uniargs)
        assert not fetch_and_check(TESTFILE, u"mmąöî", "help", u"mmąöî")
        assert fetch_and_check(TESTFILE, u"updatemmąöî", "help", u"mmąöî")
        assert fetch_and_check(TESTFILE, u"mmąöî2", "dependson", u"updatemmąöî")

    def test_dbupdate_nodeps(self):
        # Add a rule that depends on the one in the test file (mmąöî)
        uniargs_add = [u"testmmąöî", u"mmąöî2", u"fake@mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)

        # Update the name of the first one and don't update references
        uniargs = [u"--nodeps", u"testmmąöî", u"mmąöî", u"name=updatemmąöî"]
        dgm_cli.dbupdate(self.db, self.config, uniargs)
        # TODO is this a bug? cf dgm.model:312. The tests should be:
        #assert not fetch_and_check(TESTFILE, u"mmąöî", "help", u"mmąöî")
        #assert fetch_and_check(TESTFILE, u"updatemmąöî", "help", u"mmąöî")
        #assert fetch_and_check(TESTFILE, u"mmąöî2", "dependson", u"mmąöî")
        assert fetch_and_check(TESTFILE, u"mmąöî", "help", u"mmąöî")
        assert fetch_and_check(TESTFILE, u"mmąöî2", "dependson", u"mmąöî")


    def test_dbupdate_change_ruleset_name(self):
        uniargs = [u"testmmąöî", u"mmąöî", u"ruleset=updatemmąöî", \
                    u"comments=updatemmąöî"]
        dgm_cli.dbupdate(self.db, self.config, uniargs)
        filepath = os.path.join(BASEDIR, u"updatemmąöî.rs")
        assert os.path.exists(filepath)
        assert fetch_and_check(filepath, u"mmąöî", "comments", u"updatemmąöî")
        assert not fetch_and_check(TESTFILE, u"mmąöî", "comments", \
                    u"updatemmąöî")

    def test_dbcopy_rule_create(self):
        uniargs = [u"testmmąöî:mmąöî", u"mmąöî666"]
        dgm_cli.dbcopy(self.db, self.config, uniargs)
        filepath = os.path.join(BASEDIR, u"mmąöî666.rs")
        assert os.path.exists(filepath)
        with open(filepath) as f1:
            with open(TESTFILE) as f2:
                assert f1.read() == f2.read()

    def test_dbcopy_rule_nocreate(self):
        # Create a second rs
        uniargs_add = [u"mmąöî666", u"mmąöî", u"fake@mmąöî", u"mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)
        # Empty second rs
        uniargs_rem = [u"-E", u"mmąöî666"]
        dgm_cli.dbremove(self.db, self.config, uniargs_rem)
        filepath = os.path.join(BASEDIR, u"mmąöî666.rs")
        # Test if still here and empty
        assert os.path.exists(filepath)
        with open(filepath) as f1:
             assert f1.read() == ""
        # Copy from test to second rs 
        uniargs = [u"testmmąöî:mmąöî", u"mmąöî666"]
        dgm_cli.dbcopy(self.db, self.config, uniargs)
        with open(filepath) as f1:
            with open(TESTFILE) as f2:
                assert f1.read() == f2.read()

    def test_dbcopy_ruleset_create(self):
        uniargs = [u"testmmąöî", u"mmąöî666"]
        dgm_cli.dbcopy(self.db, self.config, uniargs)
        filepath = os.path.join(BASEDIR, u"mmąöî666.rs")
        assert os.path.exists(filepath)
        with open(filepath) as f1:
            with open(TESTFILE) as f2:
                assert f1.read() == f2.read()

    def test_dbcopy_ruleset_nocreate(self):
        # Create a second rs
        uniargs_add = [u"mmąöî666", u"mmąöî", u"fake@mmąöî", u"mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)
        # Empty second rs
        uniargs_rem = [u"-E", u"mmąöî666"]
        dgm_cli.dbremove(self.db, self.config, uniargs_rem)
        filepath = os.path.join(BASEDIR, u"mmąöî666.rs")
        # Test if still here and empty
        assert os.path.exists(filepath)
        with open(filepath) as f1:
             assert f1.read() == ""
        # Copy from test to second rs 
        uniargs = [u"testmmąöî", u"mmąöî666"]
        dgm_cli.dbcopy(self.db, self.config, uniargs)
        with open(filepath) as f1:
            with open(TESTFILE) as f2:
                assert f1.read() == f2.read()

    def test_dbchecksum(self):
        #TODO catch stdout
        pass

    def test_graphrules_nofile(self):
        uniargs = [u"testmmąöî"]
        # The graph is sent to output using logger.output()
        capturer = Capturer(self.logger)
        dgm_cli.graphrules(self.db, self.config, uniargs)
        data = capturer.getCaptured().decode('utf-8')

        val = compare_to_ref("test_graphrules_nofile", "graph")
        assert data == val

    def test_graphrules_nofile_2rules(self):
        # Add a rule that depends on the one in the test file (mmąöî)
        uniargs_add = [u"testmmąöî", u"mmąöî2", u"fake@mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)

        uniargs = [u"testmmąöî"]
        # The graph is sent to output using logger.output()
        capturer = Capturer(self.logger)
        dgm_cli.graphrules(self.db, self.config, uniargs)
        data = capturer.getCaptured().decode('utf-8')

        val = compare_to_ref("test_graphrules_nofile_2rules", "graph")
        assert data == val

    def test_graphrules_file(self):
        pathgraph = os.path.join(BASEDIR, u"mmąöîgraph")
        uniargs = [u"--out="+pathgraph, u"testmmąöî"]
        dgm_cli.graphrules(self.db, self.config, uniargs)
        assert os.path.exists(pathgraph)
        with open(pathgraph) as f1:
            f1r = f1.read().decode('utf-8')
            val = compare_to_ref("test_graphrules_file", "graph")
            assert val == f1r

    def test_graphrules_file_2rules(self):
        # Add a rule that depends on the one in the test file (mmąöî)
        uniargs_add = [u"testmmąöî", u"mmąöî2", u"fake@mmąöî", u"mmąöî", \
                    u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî", u"mmąöî"]
        dgm_cli.dbadd(self.db, self.config, uniargs_add)

        pathgraph = os.path.join(BASEDIR, u"mmąöîgraph")
        uniargs = [u"--out="+pathgraph, u"testmmąöî"]
        dgm_cli.graphrules(self.db, self.config, uniargs)
        assert os.path.exists(pathgraph)
        with open(pathgraph) as f1:
            f1r = f1.read().decode('utf-8')
            val = compare_to_ref("test_graphrules_file_2rules", "graph")
            assert val == f1r

    def test_knowntypes(self):
        uniargs = [u"testmmąöî"]
        # The table is sent to output using logger.output()
        capturer = Capturer(self.logger)
        dgm_cli.knowntypes(self.db, self.config, uniargs)
        data = capturer.getCaptured().decode('utf-8')

        val = compare_to_ref("test_knowntypes", "table")
        assert data == val

    def test_depmake(self):
        pathdep = os.path.join(BASEDIR, u"mmąöîdep")
        pathdot = os.path.join(BASEDIR, u"mmąöîdepdot")
        uniargs = [u"testmmąöî", u"127.0.0.1", u"-o", pathdep, \
                    u"--depgraphto="+pathdot]
        dgm_cli.depmake(self.db, self.config, uniargs)
        with open(pathdep) as f1:
            with open(pathdot) as f2:
                print("F1\n%s" % f1.read()) 
                print("F2\n%s" % f2.read()) 
        #assert False 
        #TODO test with real cmd? pings... having a rule that applies to the
        # components would be good
        #TODO compare files to something

#    def test_depmake_real(self):
#        uniargs_add = [u"pings", u"cmd", u"ALL", u"ALL", \
#            u"/bin/bash -c 'ping -nq -c 1 %name > /dev/null  && echo Alive \
#            || echo Unreachable'", u"'ping -nq -c 1 %name'", u"NONE", \
#            u"NONE", u"'Parallel Ping'", u"Some Help"]



# depmake avec un depsfinder uni name
