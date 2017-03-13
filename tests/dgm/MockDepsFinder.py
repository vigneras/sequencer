# -*- coding: utf-8 -*-
#!/usr/bin/python
###############################################################################
# Copyright (C) Bull S.A.S (2010, 2011)
# Contributor: Pierre Vignéras <pierre.vigneras@gmail.com>
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
import os
import sys


# This script is used for unit testing of the Bull sequencer
# Dependency Graph Maker stage.

if len(sys.argv) == 1:
    print("Usage: " + sys.argv[0] + " dep1#type1 dep2#type2 ... depN#typeN")
    # From /usr/include/sysexits.h
    sys.exit(os.EX_USAGE)

deps = sys.argv[1:]
for dep in deps:
    print(dep)

sys.exit(os.EX_OK)

