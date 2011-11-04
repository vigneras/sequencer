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
ISE Parser implementation.
"""
import os
from logging import getLogger

from clmsequencer.commons import get_version
from clmsequencer.ise.rc import FORCE_ALLOWED
from lxml import etree
from lxml.builder import ElementMaker # lxml only !


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = getLogger(__name__)

ISE_NAMESPACE = "http://www.xml.bcm.bull/clmsequencer/ise"
NSMAP = {None : ISE_NAMESPACE} # the default namespace (no prefix)

E = ElementMaker(namespace=ISE_NAMESPACE, nsmap=NSMAP)

ISE = E.instructions
SEQ = E.seq
PAR = E.par
ACTION = E.action

_ISE_XML_HEADER = u"""<ise:instructions
   xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"
   xsi:schemaLocation=\"http://www.xml.bcm.bull/clmsequencer/ise
		       /usr/share/clmsequencer/ise.xsd\"
   xmlns:ise=\"http://www.xml.bcm.bull/clmsequencer/ise\">\n"""


NS_ISE = "{%s}" % ISE_NAMESPACE

_RESOURCE_DIR = os.path.dirname(__file__)
_ISE_XSD_FILENAME = u"ise.xsd"

DESC_ATTR = "desc"
DEFAULT_DESC = ""
ID_ATTR = "id"
COMPONENT_SET_ATTR = "component_set"
DEFAULT_COMPONENT_SET = "localhost#type@cat"
REMOTE_ATTR = "remote"
FORCE_ATTR = "force"
DEFAULT_FORCE = FORCE_ALLOWED
DEPS_ATTR = "deps"

SEQ_TAG = "seq"
PAR_TAG = "par"
ACTION_TAG = "action"
INSTRUCTIONS_TAG = "instructions"

NS_SEQ_TAG = NS_ISE + SEQ_TAG
NS_PAR_TAG = NS_ISE + PAR_TAG
NS_ACTION_TAG = NS_ISE + ACTION_TAG
NS_INSTRUCTIONS_TAG = NS_ISE + INSTRUCTIONS_TAG

class ISEParser(object):
    """
    This class represents the parser of the ISE.
    """
    def __init__(self, afile):
        if (afile is None):
            raise ValueError("Invalid Argument: None")

        self.file = afile

        parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
        tree = etree.parse(afile, parser)
        self.root = tree.getroot()
        xsd_doc = etree.parse(os.path.join(_RESOURCE_DIR,
                                           _ISE_XSD_FILENAME))
        xsd = etree.XMLSchema(xsd_doc)
        xsd.assertValid(self.root)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


