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
import subprocess
import shlex
from setuptools import setup, find_packages

VERSION = '1.0.0.snapshot'
META_FILE = 'lib/sequencer/.metainfo'


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

if not os.access('bin/sequencer', os.F_OK):
    os.symlink('sequencer', 'bin/sequencer')

# Generate the .version file that contains the version and the last
# commit
last_commit_cmd_raw = "git show --pretty=format:'%H %aN %aE %ci'  -1"
last_commit_cmd = shlex.split(last_commit_cmd_raw)
last_commit = subprocess.check_output(last_commit_cmd)
with open(META_FILE, 'w') as f:
    # Do not change those names unless you also change in commons.py
    f.write("sequencer.version = %s\n" % VERSION)
    f.write("sequencer.lastcommit = %s\n" % last_commit)

setup(name='sequencer',
      version=VERSION,
      package_dir={'': 'lib'},
      packages=find_packages('lib'),
      package_data={'': ['.metainfo', 'ise/ise.xsd']},
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
      requires=('ClusterShell(>=1.5)', 'pygraph(>=1.7.0)', 'pydot', 'lxml(>=2.2.3)', 'graphviz(>=2.26)'),
      provides='sequencer',
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

