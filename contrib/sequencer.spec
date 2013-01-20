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

#TODO: define your package name
%define name sequencer

# For versionning policy, please see wiki:
# TODO: define
%define version 1.0.0

# Using the .snapshot suffix helps tagging process.
# Tagging process is defined here:
# TODO: define
%define release 0%{?dist}.snapshot

%define src_dir %{name}-%{version}
%define src_tarall %{src_dir}.tar.gz

%define src_conf_dir conf
%define src_bin_dir bin
%define src_lib_dir lib
%define src_doc_dir doc
%define src_depsfinder_dir lib/depsfinder
%define src_filter_dir lib/filter
%define src_setup_dir setup

%define target_conf_dir /etc/sequencer
%define target_share_dir /usr/share/%{name}
%define target_bin_dir /usr/bin
%define target_sbin_dir /usr/sbin
%define target_man_dir %{_mandir}
%define target_lib_dir /usr/lib/python2.6/site-packages
%define target_doc_dir /usr/share/doc/%{name}
%define target_depsfinder_dir /usr/lib/sequencer/depsfinder
%define target_filter_dir /usr/lib/sequencer/filter
%define target_action_dir /usr/lib/sequencer/action
%define target_tools_dir /usr/lib/sequencer/tools

# TODO: Give your summary
Summary:	Sequencer
Name:		%{name}
Version:	%{version}
Release:	%{release}
Source:		%{src_tarall}
# Perform a 'cat /usr/share/doc/rpm-*/GROUPS' to get a list of available
# groups.
# TODO: Specify the category your software belongs to
Group:		Applications/System
BuildRoot:	%{_tmppath}/%{name}-root
Packager:	Pierre Vignéras <pierre.vigneras@bull.net>
# TODO: Check here
Distribution:	Fedora

Vendor:         Bull
License:        GPLv3 Copyright (C) 2009 Bull S.A.S.
BuildArch:	noarch
# TODO: Define here
URL:	 	http://forge.frec.bull.fr

#TODO: What do you provide
Provides: sequencer
#Conflicts:
#TODO: What do you require
Requires: clustershell >= 1.3.3, python-graph >= 1.7.0-Bull.1, pydot >= 1.0.2, python-lxml >= 2.2.3, graphviz >= 2.26

#TODO: Give a description (seen by rpm -qi) (No more than 80 characters)
%description
Sequencer starts/stops hard/soft components taking dependencies into account.

###############################################################################
# Prepare the files to be compiled
%prep
#%setup -q -n %{name}
%setup

###############################################################################
# The current directory is the one main directory of the tar
# Order of upgrade is:
#%pretrans new
#%pre new
#install new
#%post new
#%preun old
#delete old
#%postun old
#%posttrans new

%install
rm -rf $RPM_BUILD_ROOT

# Use install to install components from the tar file to the target system
# Notice the use of the $RPM_BUILD_ROOT environment variable.

# Install configuration files
install -m 644 -D %{src_conf_dir}/sequencer.conf $RPM_BUILD_ROOT/%{target_conf_dir}/config
# Do not allow read access to others since this file contains SNMP community.
mkdir -p $RPM_BUILD_ROOT/%{target_conf_dir}/filter

# Install commands
install -m 755 -D %{src_bin_dir}/sequencer $RPM_BUILD_ROOT/%{target_sbin_dir}/sequencer

# Install Misc stuff (ChangeLog, examples, ...)
install -m 644 -D %{src_doc_dir}/ChangeLog $RPM_BUILD_ROOT/%{target_doc_dir}/ChangeLog
install -m 755 -D %{src_doc_dir}/example.makerules.sh $RPM_BUILD_ROOT/%{target_doc_dir}/example.makerules.sh
install -m 644 -D %{src_doc_dir}/example.seqmake.xml $RPM_BUILD_ROOT/%{target_doc_dir}/example.seqmake.xml
install -m 644 -D %{src_doc_dir}/example.seqexec.xml $RPM_BUILD_ROOT/%{target_doc_dir}/example.seqexec.xml
install -m 644 -D %{src_doc_dir}/hello_world.seqexec.xml $RPM_BUILD_ROOT/%{target_doc_dir}/hello_world.seqexec.xml

# Install man pages
install -m 644 -D %{src_doc_dir}/sequencer.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.dgmdb.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.dgmdb.1.gz
install -m 644 -D %{src_doc_dir}/dgmdb.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/dgmdb.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.graphrules.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.graphrules.1.gz
install -m 644 -D %{src_doc_dir}/graphrules.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/graphrules.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.knowntypes.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.knowntypes.1.gz
install -m 644 -D %{src_doc_dir}/knowntypes.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/knowntypes.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.depmake.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.depmake.1.gz
install -m 644 -D %{src_doc_dir}/depmake.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/depmake.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.seqmake.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.seqmake.1.gz
install -m 644 -D %{src_doc_dir}/seqmake.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/seqmake.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.seqmake.5.gz $RPM_BUILD_ROOT/%{target_man_dir}/man5/sequencer.seqmake.5.gz
install -m 644 -D %{src_doc_dir}/seqmake.5.gz $RPM_BUILD_ROOT/%{target_man_dir}/man5/seqmake.5.gz
install -m 644 -D %{src_doc_dir}/sequencer.seqexec.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.seqexec.1.gz
install -m 644 -D %{src_doc_dir}/seqexec.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/seqexec.1.gz
install -m 644 -D %{src_doc_dir}/sequencer.seqexec.5.gz $RPM_BUILD_ROOT/%{target_man_dir}/man5/sequencer.seqexec.5.gz
install -m 644 -D %{src_doc_dir}/seqexec.5.gz $RPM_BUILD_ROOT/%{target_man_dir}/man5/seqexec.5.gz
install -m 644 -D %{src_doc_dir}/sequencer.chain.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/sequencer.chain.1.gz
install -m 644 -D %{src_doc_dir}/chain.1.gz $RPM_BUILD_ROOT/%{target_man_dir}/man1/chain.1.gz


# Install libs
mkdir -p $RPM_BUILD_ROOT/%{target_lib_dir}/sequencer
rsync --recursive --specials --links --exclude "*rpmnew" --exclude ".cvsignore" --exclude "*.pyc" %{src_lib_dir}/sequencer $RPM_BUILD_ROOT/%{target_lib_dir}/

# Install DepsFinders

# Install Filters

# Install actions

# Install tools
mkdir -p $RPM_BUILD_ROOT/%{target_tools_dir}/
install -m 755 %{src_bin_dir}/db2files $RPM_BUILD_ROOT/%{target_tools_dir}/db2files

%pre
%post
if [ "$1" = "1" ];
then
     # Actions specific to new install (not to upgrade)
     echo "Nothing to do" > /dev/null
fi
if [ "$1" = "2" ];
then
     # Actions specific to upgrade
     echo "Nothing to do" > /dev/null
fi

%preun
%postun
if [ "$1" = "0" ]; then
     # Actions specific to uninstall (not to upgrade)
    echo "Nothing to do" > /dev/null
fi

if [ "$1" = "1" ]; then
    # Actions specific to upgrade
     echo "Nothing to do" > /dev/null
fi

%clean
rm -rf $RPM_BUILD_ROOT

###############################################################################
# Specify files to be placed into the package
%files
%defattr(-,root,root)

%config(noreplace) %{target_conf_dir}/config
%config %{target_conf_dir}/filter

# Misc Stuff
#%doc %{target_doc_dir}/README
# Changelog is automatically generated (see Makefile)
%doc %{target_doc_dir}/ChangeLog
%doc %{target_doc_dir}/example.makerules.sh
%doc %{target_doc_dir}/example.seqexec.xml
%doc %{target_doc_dir}/example.seqmake.xml
%doc %{target_doc_dir}/hello_world.seqexec.xml

# Man pages
%doc %{target_man_dir}/man1/sequencer.1.gz
%doc %{target_man_dir}/man1/sequencer.dgmdb.1.gz
%doc %{target_man_dir}/man1/dgmdb.1.gz
%doc %{target_man_dir}/man1/sequencer.graphrules.1.gz
%doc %{target_man_dir}/man1/graphrules.1.gz
%doc %{target_man_dir}/man1/sequencer.knowntypes.1.gz
%doc %{target_man_dir}/man1/knowntypes.1.gz
%doc %{target_man_dir}/man1/sequencer.depmake.1.gz
%doc %{target_man_dir}/man1/depmake.1.gz
%doc %{target_man_dir}/man1/sequencer.seqmake.1.gz
%doc %{target_man_dir}/man1/seqmake.1.gz
%doc %{target_man_dir}/man5/sequencer.seqmake.5.gz
%doc %{target_man_dir}/man5/seqmake.5.gz
%doc %{target_man_dir}/man1/sequencer.seqexec.1.gz
%doc %{target_man_dir}/man1/seqexec.1.gz
%doc %{target_man_dir}/man5/sequencer.seqexec.5.gz
%doc %{target_man_dir}/man5/seqexec.5.gz
%doc %{target_man_dir}/man1/sequencer.chain.1.gz
%doc %{target_man_dir}/man1/chain.1.gz

# Binary stuff
%{target_sbin_dir}/sequencer

# lib
%{target_lib_dir}/sequencer/.version
%{target_lib_dir}/sequencer/__init__.py
%{target_lib_dir}/sequencer/commons.py
%{target_lib_dir}/sequencer/tracer.py
%{target_lib_dir}/sequencer/dgm/__init__.py
%{target_lib_dir}/sequencer/dgm/db.py
%{target_lib_dir}/sequencer/dgm/model.py
%{target_lib_dir}/sequencer/dgm/cli.py
%{target_lib_dir}/sequencer/dgm/errors.py

%{target_lib_dir}/sequencer/ism/__init__.py
%{target_lib_dir}/sequencer/ism/algo.py
%{target_lib_dir}/sequencer/ism/cli.py

%{target_lib_dir}/sequencer/ise/__init__.py
%{target_lib_dir}/sequencer/ise/api.py
%{target_lib_dir}/sequencer/ise/rc.py
%{target_lib_dir}/sequencer/ise/ise.xsd
%{target_lib_dir}/sequencer/ise/model.py
%{target_lib_dir}/sequencer/ise/parser.py
%{target_lib_dir}/sequencer/ise/cli.py
%{target_lib_dir}/sequencer/ise/errors.py

%{target_lib_dir}/sequencer/chain/__init__.py
%{target_lib_dir}/sequencer/chain/cli.py

# DepsFinders

# Filters

# Actions

# Tools
%{target_tools_dir}/db2files


# %changelog is automatically generated by 'make log' (see the Makefile)
##################### WARNING ####################
## Do not add anything after the following line!
##################################################
%changelog

