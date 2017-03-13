#!/usr/bin/python
# -*- coding: utf-8 -*-
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
# Instructions Sequence Executor stage.

if len(sys.argv) != 4:
    print("Usage: " + sys.argv[0] + " rc msg_std msg_err")
    # From /usr/include/sysexits.h
    sys.exit(os.EX_USAGE)

rc = int(sys.argv[1])
msg_std = sys.argv[2]
msg_err = sys.argv[3]

msg_std = (''.join(msg_std)).strip()
msg_err = (''.join(msg_err)).strip()

if msg_std: sys.stdout.write(msg_std + "\n")
if msg_err: sys.stderr.write(msg_err + "\n")

sys.exit(rc)

