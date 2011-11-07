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
This module defines various stuff for the ISE.
"""

# When an action is executed, its returned code (aka 'rc') is used for
# error management
import os
from sequencer.commons import get_version

__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()


ACTION_RC_OK = os.EX_OK
ACTION_RC_KO = 1 # Actually, any value different than OK and WARNING
                 # will be considerd KO.

ACTION_RC_UNEXECUTED = os.EX_UNAVAILABLE # An action cannot be
                                         # executed for some unknown
                                         # reasons.

ACTION_RC_WARNING = os.EX_TEMPFAIL
FORCE_ALLOWED = 'allowed'
FORCE_NEVER = 'never'
FORCE_ALWAYS = 'always'

def is_error_rc(rc):
    """
    Return true if and only if the rc code is an error code (neither
    OK nor WARNING)
    """
    return not (is_ok_rc(rc) or is_warning_rc(rc))

def is_warning_rc(rc):
    """
    Return true if the rc code is the WARNING code
    """
    return rc == ACTION_RC_WARNING

def is_ok_rc(rc):
    """
    Return true if the rc code is the OK code
    """
    return rc == ACTION_RC_OK

def should_stop(rc, force_option, force_attr):
    """
    Return true if the given rc code is an error code, or if it is a
    warning code with force == false
    """
    if rc == ACTION_RC_OK:
        return False
    if rc != ACTION_RC_WARNING or force_attr == FORCE_NEVER:
        return True
    if force_option or force_attr == FORCE_ALWAYS:
        return False
    return True


