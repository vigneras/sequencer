#!/usr/bin/env python
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
from setuptools import setup, find_packages


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

if not os.access('bin/sequencer', os.F_OK):
    os.symlink('sequencer', 'bin/sequencer')

VERSION='1.0.0'

setup(name='sequencer',
      version=VERSION,
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      scripts=['bin/sequencer'],
      author='Pierre Vignéras',
      author_email='pierre.vigneras@bull.net',
      maintainer='Pierre Vignéras',
      maintainer_email='pierre.vigneras@bull.net',
      license='GPL v3',
      url='https://pv-bull.github.com/sequencer',
      platforms=['GNU/Linux', 'BSD', 'MacOSX'],
      keywords=['sequencer'],
      description='Sequencer library and tools',
      long_description=read('README'),
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "Environment :: Console",
          "Intended Audience :: System Administrators",
          "License :: OSI Approved :: GNU General Public License (GPL)",
          "Operating System :: MacOS :: MacOS X",
          "Operating System :: POSIX :: BSD",
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Topic :: Software Development :: Libraries :: Python Modules",
          "Topic :: System :: Clustering",
          "Topic :: System :: Distributed Computing"
      ]
     )

