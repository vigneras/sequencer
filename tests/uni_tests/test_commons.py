#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sequencer
import sequencer.commons as lib
import os, sys

from commons import BaseTest
from sequencer.dgm import cli as dgm_cli
from sequencer.dgm.db import SequencerFileDB

class AbstractTest(BaseTest):

    def setUp(self):
        pass
    
    def tearDown(self):
        pass
    
class CommonsUniTest(AbstractTest):

    def test_to_unicode(self):
        nonascii = "mmąöî"
        uni = lib.to_unicode(nonascii)
        assert type(nonascii) == str
        assert len(nonascii) != 5
        assert type(uni) == unicode
        assert len(uni) == 5
        assert uni == u"mmąöî"
    
    def test_to_str_from_unicode(self):
        uni = u"mmąöî"
        nonascii = lib.to_str_from_unicode(uni, should_be_uni=True)
        assert type(uni) == unicode
        assert len(uni) == 5
        assert type(nonascii) == str
        assert len(nonascii) != 5
        assert nonascii == "mmąöî"
    
    def test_replace_if_none_by_uni(self):
        noneval = None
        noneuni = lib.replace_if_none_by_uni(noneval)
        assert type(noneuni) == unicode
        assert noneuni == u"None"
    
    def test_get_basedir_nobase(self):
        ret = lib.get_basedir()
        cmdstr = lib.to_unicode(os.path.basename(sys.argv[0]))
        assert type(ret) == unicode
        assert ret == u"/etc/" + cmdstr
    
    def test_get_basedir_base(self):
        ret = lib.get_basedir(u"mmąöî")
        cmdstr = lib.to_unicode(os.path.basename(sys.argv[0]))
        assert type(ret) == unicode
        assert ret == u"/etc/" + cmdstr + u"/mmąöî"
    
    def test_confirm(self):
        pass
        
        
        
        
        
        
