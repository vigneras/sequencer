#!/usr/bin/python
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
from sequencer import commons
from sequencer.commons import smart_display, REMOVE_UNSPECIFIED_COLUMNS, \
    FILL_EMPTY_ENTRY
import logging
import re
import sys
import unittest

"""Test the smart_display() routine."""


class SmartDisplayTest(unittest.TestCase):

    def testBadArg(self):
        self.assertRaises(AssertionError, smart_display, None, ['foo'])
        self.assertRaises(AssertionError, smart_display, [], ['foo'])
        self.assertRaises(AssertionError, smart_display, ['dummy'], None)
        self.assertRaises(AssertionError,
                          smart_display, ['dummy'], ['foo'], hsep=None)
        self.assertRaises(AssertionError,
                          smart_display, ['dummy'], ['foo'], vsep=None)
        # justify should have the same length than header when specified.
        self.assertRaises(AssertionError,
                          smart_display, ['dummy'], ['foo'], justify=[])


#    def testLengthHeaderDataDiffers(self):
#        # Each data row should have the same length than the header
#        self.assertRaises(AssertionError, smart_display, ['bar', 'foo'], [['data1']])
#        self.assertRaises(AssertionError, smart_display, ['bar'], [['data1', 'data2']])

    def testSimpleOutput(self):
        output = smart_display([u"Title"], [[u"data1"], [u"data2"]])
        self.assertIsNotNone(re.search(r'^.*Title.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*data1.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*data2.*$', output,
                                       flags=re.MULTILINE),
                             output)

    def testRemoveAllColumns(self):
        # Removing single column -> no output at all!!
        output = smart_display([u"Title"], [[u"data1"], [u"data2"]],
                               columns_max={'Title':0})
        self.assertIsNone(re.search(r'^.*Title.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNone(re.search(r'^.*data.*$', output,
                                    flags=re.MULTILINE),
                          output)

    def testRemoveSomeColumns(self):
        # Two columns only one remain
        output = smart_display([u"T1", u"T2"],
                               [[u"d1.1", u"d2.1"],
                                [u"d1.2", u"d2.2"]],
                               columns_max={'T1':0})
        self.assertIsNone(re.search(r'^.*T1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNone(re.search(r'^.*d1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNotNone(re.search(r'^.*T2.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*d2.*$', output,
                                       flags=re.MULTILINE),
                             output)

    def testSpecifySingleColumn(self):
        output = smart_display([u"T1", u"T2"],
                               [[u"d1.1", u"d2.1"],
                                [u"d1.2", u"d2.2"]],
                               columns_max={'T2': REMOVE_UNSPECIFIED_COLUMNS})
        self.assertIsNone(re.search(r'^.*T1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNone(re.search(r'^.*d1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNotNone(re.search(r'^.*T2.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*d2.*$', output,
                                       flags=re.MULTILINE),
                             output)

    def testSpecifyMultipleColumns(self):
        output = smart_display([u"T1", u"T2", u"T3"],
                               [[u"d1.1", u"d2.1", u"d3.1"],
                                [u"d1.2", u"d2.2", u"d3.2"]],
                               columns_max={u'T2': REMOVE_UNSPECIFIED_COLUMNS,
                                            u'T3': REMOVE_UNSPECIFIED_COLUMNS})
        self.assertIsNone(re.search(r'^.*T1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNone(re.search(r'^.*d1.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNotNone(re.search(r'^.*T2.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*d2.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*T3.*$', output,
                                    flags=re.MULTILINE),
                          output)
        self.assertIsNotNone(re.search(r'^.*d3.*$', output,
                                    flags=re.MULTILINE),
                          output)

    def testFILLERSpecified(self):
        output = smart_display([u"T1", u"T2"],
                               [[u"d1.1", u"d2.1"],
                                [FILL_EMPTY_ENTRY, u"d2.2"]])
        self.assertIsNotNone(re.search(r'^.*T1.*$', output,
                                       flags=re.MULTILINE),
                          output)
        self.assertIsNotNone(re.search(r'^.*d1.*$', output,
                                       flags=re.MULTILINE),
                          output)
        # Here a faked sample of what we are looking for:
        match = re.search(r'^-+ +| +d2.2 $', '------- | d2.2',
                          flags=re.MULTILINE)
        print("Faked matching at: %s" % match.string[match.start():match.end()])
        assert match is not None
        # Now, doing the same on the actual output
        match = re.search(r'^-+ +| +d2.2 $', output, flags=re.MULTILINE)
        self.assertIsNotNone(match, output)
        print(output)
        print("Matching at: %s" % match.string[match.start():match.end()])
        self.assertIsNotNone(re.search(r'^.*T2.*$', output,
                                       flags=re.MULTILINE),
                             output)
        self.assertIsNotNone(re.search(r'^.*d2.*$', output,
                                       flags=re.MULTILINE),
                             output)



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(commons.__name__).setLevel(logging.DEBUG)
    unittest.main()
