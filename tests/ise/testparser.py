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
import io
import random
import string
import tempfile
import unittest

import lxml
from sequencer.ise import parser
from sequencer.ise.parser import ISE, SEQ, PAR, ACTION


class TestISEParserBasic(unittest.TestCase):
    """Check that the ISE Parser acceptes basic document."""

    def _parse(self, doc):
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.failIf(parser.ISEParser(reader) is None)

    def test_singleAction(self):
        doc = ISE(ACTION(id="SingleActionOk"))
        self._parse(doc)

    def test_SimpleSequenceWithoutDesc(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo")))
        self._parse(doc)

    def test_SimpleSequenceWithDesc(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo"),
                      desc="Dummy Description"))
        self._parse(doc)

    def test_SimpleParallelWithoutDesc(self):
        doc = ISE(PAR(ACTION("Action1", id="foo")))
        self._parse(doc)

    def test_SimpleParallelWithDesc(self):
        doc = ISE(PAR(ACTION("Action1", id="foo"),
                      desc="Dummy Description"))
        self._parse(doc)

    def test_RemoteAction(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo", remote="true")))
        self._parse(doc)

    def test_LocalAction(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo", remote="false")))
        self._parse(doc)

    def test_ActionWithForceAlways(self):
        doc = ISE(ACTION("Action1", id="foo", force='always'))
        self._parse(doc)

    def test_ActionWithForceAllowed(self):
        doc = ISE(ACTION("Action1", id="foo", force='allowed'))
        self._parse(doc)

    def test_ActionWithForceNever(self):
        doc = ISE(ACTION("Action1", id="foo", force='never'))
        self._parse(doc)

    def test_ActionWithCS(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo", component_set="dummy CS")))
        self._parse(doc)

    def test_ActionWithDesc(self):
        doc = ISE(SEQ(ACTION("Action1", id="foo", desc="dummy Description")))
        self._parse(doc)

    def test_ActionWithDepsSingle(self):
        doc = ISE(SEQ(ACTION("Action1", id="id1"),
                      PAR(ACTION("Action2", id="id2", deps="id1"))))
        self._parse(doc)

    def test_ActionWithDepsMultiple(self):
        doc = ISE(SEQ(ACTION("Action1", id="id1"),
                      PAR(ACTION("Action2", id="id2", deps="id1"),
                          ACTION("Action3", id="id3", deps="id2, id1")
                          )))
        self._parse(doc)

class TestISEParserError(unittest.TestCase):
    """Test that the ISE Parser performs check on the input correctly."""

    def test_ParseFileNotFound(self):

        self.assertRaises(ValueError, parser.ISEParser, None)

        fileName = ''.join(random.sample(string.letters, 10))
        self.assertRaises(IOError, parser.ISEParser, fileName)

    def test_EmptyFile(self):

        with tempfile.TemporaryFile() as file:
            self.assertRaises(lxml.etree.XMLSyntaxError, parser.ISEParser, file)

    def test_WrongFileContent(self):

        dummy = unicode(''.join(random.sample(string.letters, 20)))
        with io.StringIO() as writer:
            writer.write(dummy)

            with io.StringIO(writer.getvalue()) as reader:
                self.assertRaises(lxml.etree.XMLSyntaxError,
                                  parser.ISEParser,
                                  reader)

    def test_InvalidXML(self):

        with io.StringIO() as writer:
            writer.write(u"<?xml version=\"1.0\"?>\n")
            writer.write(u"<ise/>\n")

            with io.StringIO(writer.getvalue()) as reader:
                self.assertRaises(lxml.etree.DocumentInvalid,
                                  parser.ISEParser,
                                  reader)

    def test_notATree(self):

        doc = ISE(SEQ(ACTION("Action1", id="id1")),
                  PAR(ACTION("Action2", id="id1")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.assertRaises(lxml.etree.DocumentInvalid,
                              parser.ISEParser,
                              reader)

    def test_duplicateActionID(self):
        doc = ISE(SEQ(ACTION("Action1", id="id1"),
                      ACTION("Action2", id="id1")))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.assertRaises(lxml.etree.DocumentInvalid,
                              parser.ISEParser,
                              reader)

    def test_wrongForceAttribute(self):
        doc = ISE(ACTION("Action1", id="id1", force="foo"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.assertRaises(lxml.etree.DocumentInvalid,
                              parser.ISEParser,
                              reader)


    def test_emptySeq(self):
        doc = ISE(SEQ(desc="EmptySequenceForbidden"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.assertRaises(lxml.etree.DocumentInvalid,
                              parser.ISEParser,
                              reader)

    def test_emptyPar(self):
        doc = ISE(PAR(desc="EmptyParallelForbidden"))
        xml = lxml.etree.tostring(doc, pretty_print=True)
        print(xml)
        with io.StringIO(unicode(xml)) as reader:
            self.assertRaises(lxml.etree.DocumentInvalid,
                              parser.ISEParser,
                              reader)

