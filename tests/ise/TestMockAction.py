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
import random
import subprocess
import unittest

from sequencer.ise.rc import ACTION_RC_OK, ACTION_RC_WARNING

from tests.ise import tools


class TestMockAction(unittest.TestCase):
    """Test that the MockAction acts correctly."""

    def test_RC(self):
        expected_rc = random.randint(ACTION_RC_OK, ACTION_RC_WARNING)
        expected_std = "Message2StdOut"
        expected_err = "Message2StdErr"
        mockActionFullPath = tools.getMockActionFullPath()
        popen = subprocess.Popen(["python",
                                  mockActionFullPath,
                                  str(expected_rc),
                                  expected_std,
                                  expected_err],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        (real_std, real_err) = popen.communicate()
        real_rc = popen.wait()
        self.assertEquals(expected_rc, real_rc)
        self.assertEquals(expected_std, real_std.strip())
        self.assertEquals(expected_err, real_err.strip())


