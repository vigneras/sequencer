#!/usr/bin/python
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
import os
import time
import sys


# This script is used for unit testing of the Bull clusterctrl
# engine. It displays string DELAY_REACHED_MSG only after the given
# ok_after_delay delay has passed since the given timestamp. Othewise,
# it displays DELAY_NOT_REACHED_MSG.
# In both cases, it exits with the given returned_code.

DELAY_REACHED_MSG = "Delay reached."
DELAY_NOT_REACHED_MSG = "Delay not reached."


def main():


    if len(sys.argv) != 4:
        print("Usage: " + sys.argv[0] + \
                  " started_timestamp ok_after_delay returned_code")
        # From /usr/include/sysexits.h
        sys.exit(os.EX_USAGE)

    started_timestamp = float(sys.argv[1])
    ok_after_delay = float(sys.argv[2])
    returned_code = int(sys.argv[3])

    now = time.time()
    diff = now - started_timestamp
    if diff > ok_after_delay:
        print(DELAY_REACHED_MSG)
    else:
        print(DELAY_NOT_REACHED_MSG)

    return returned_code

if __name__ == "__main__":
    rc = int(main())
    sys.exit(rc)
