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
This package defines exceptions specific to the ISE.

Note that exceptions from the standard python library can still be thrown.
"""

from sequencer.commons import SequencerError, get_version

__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

class BadDepError(SequencerError):
    """
    Raised when an explicit dependency is already defined as an
    implicit one (in a seq).
    """
    def __init__(self, bad_dep):
        self.bad_dep = bad_dep
        msg = "Explicit dependency" + \
            " %s is already implicit (in a sequence)" % bad_dep
        SequencerError.__init__(self, msg)


class UnknownDepsError(SequencerError):
    """
    Raised when some explicit dependencies refer to unknown id.
    """
    def __init__(self, unknown_deps):
        self.unknown_deps = unknown_deps
        msg = "Unknown explicit dependencies: %s " % unknown_deps
        SequencerError.__init__(self, msg)
