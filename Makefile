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
current_makefile := $(lastword $(MAKEFILE_LIST))
rpm_topdir	:= $(shell rpm --eval="%_topdir")
rpmdir		:= $(shell rpm --eval="%_rpmdir")
srcrpmdir	:= $(shell rpm --eval="%_srcrpmdir")
sourcedir	:= $(shell rpm --eval="%_sourcedir")

# TODO: specify your spec file here
specfile=clmsequencer.spec

# For release target (rt_)
# TODO: you may change that. See Bullforge files for examples.
rt_project=clustmngt
rt_package=Sequencer
rt_release=$(name)

# TODO: Here, you list all the files and directories you want to include
# with your release. When a directory is specified, all its content is
# taken into account recursively.
files=$(specfile) conf bin lib doc

#TODO: add the file you want to auto tag here. Default is the
#whole current directory recursively. but you can adapt it to
#your own need. In particular, you can specify a file
#list. This is usefull if you have multiple .spec and Makefile
#in your source directory.
files_list_to_tag=.
#files_list_to_tag=$(files) $(current_makefile)

man_files_core=clmsequencer.dgmdb.1 dgmdb.1 clmsequencer.1 clmsequencer.graphrules.1 clmsequencer.knowntypes.1 clmsequencer.depmake.1 clmsequencer.seqmake.1 clmsequencer.seqmake.5 clmsequencer.seqexec.1 clmsequencer.seqexec.5 clmsequencer.chain.1
man_alias=graphrules.1 knowntypes.1 depmake.1 seqmake.1 seqmake.5 seqexec.1 seqexec.5 chain.1
man_files=$(man_files_core) $(man_alias)


name=$(shell awk '/^%define name/ {print $$NF}' $(specfile))
version=$(shell awk '/^%define version/ {print $$NF}' $(specfile))
raw_release=$(shell awk '/^%define release/ {print $$NF}' $(specfile))
srelease=$(shell rpm --define='dist %{nil}' --eval=$(raw_release))
release=$(shell rpm --eval=$(raw_release))
arch=$(shell awk '/^BuildArch/ {print $$NF}' $(specfile))
pkg_dir= $(name)-$(version)
tarall= $(pkg_dir).tar.gz
spackage_name=$(pkg_dir)-$(srelease)
package_name=$(pkg_dir)-$(release)
srpm= $(srcrpmdir)/$(spackage_name).src.rpm
rpm= $(rpmdir)/$(arch)/$(package_name).$(arch).rpm
cvs_logfile= /tmp/$(name)-$(version)-$(release).cvslog

# Default target: erase only produced files.
clean:
	rm -f *~ archives/$(tarall) archives/$(shell basename $(rpm)) archives/$(shell basename $(srpm))
	rm -rf /tmp/$(USER)/$(pkg_dir)/*


# Use this target to print out the version that will be produce
showversion:
	@version_from_spec $(specfile)

# Use this target to get information gathered by this Makefile.
# 'make config'
config:
	@echo "name:		$(name)"
	@echo "version:		$(version)"
	@echo "release:		$(release)"
	@echo "pkg_dir:		$(pkg_dir)"
	@echo "tarall:		$(tarall)"
	@echo "srpm:		$(srpm)"
	@echo "rpm:		$(rpm)"
	@echo "rt_project:	$(rt_project)"
	@echo "rt_package:	$(rt_package)"
	@echo "rt_release:	$(rt_release)"
	@echo "INFO: config OK"
        @echo "tarall: $(tarall)"

# Copy required source files to a temporary directory. This directory
# will be tarred. The tar file will then be used by the rpmbuild
# command.
mkdir: config
	mkdir -p archives
	mkdir -p /tmp/$(USER)
	@mkdir -pv /tmp/$(USER)/$(pkg_dir)

copy: mkdir doc
	cp -r $(files) /tmp/$(USER)/$(pkg_dir)

# Create the ChangeLog file and add changelog entries to the RPM .spec file.
# This step requires the 'cvschangelogbuilder' tool.
# It is available here: http://cvschangelogb.sourceforge.net/
log: mkdir
	git --no-pager log --format="%ai %aN %n%n%x09* %s%d%n" > /tmp/$(USER)/$(pkg_dir)/doc/ChangeLog

version: mkdir
	@echo "$(name).version = $(version).$(release)" > /tmp/$(USER)/$(pkg_dir)/lib/clmsequencer/.version

man: copy
	@for i in $(man_files);do \
		gzip -c doc/$$i > /tmp/$(USER)/$(pkg_dir)/doc/$$i.gz; \
	done

pdfman:
	@echo pdf man pages are generated in /tmp
	@for i in $(man_files_core);do \
		groff -Tps -man doc/$$i |ps2pdf - /tmp/$$i.pdf ; \
	done

tar: version man
	tar --exclude CVS --exclude '*~' --exclude '#*#' -C /tmp/$(USER) --owner=root --group=root -cvzf archives/$(tarall) $(pkg_dir)
	@echo "INFO: tar OK"


generate_rpm:
	@rpmbuild -v -ts --define='dist %{nil}' archives/$(tarall)
	@echo "INFO: rpmbuild -v -ts  --define='dist %{nil}' archives/$(tarall) OK"
	@cp $(srpm) archives
	@echo "####################################################"
	@echo "INFO: Source rpm successfully created in archives!!!"
	@echo "####################################################"
	@echo "TARALL: $(tarall)"
	@rpmbuild -v -tb archives/$(tarall)
	@echo "INFO: rpmbuild -v -tb archives/$(tarall) OK"
	@cp $(rpm) archives
	@echo "####################################################"
	@echo "INFO: Binary rpm successfully created in archives!!!"
	@echo "####################################################"

devrpm:  copy tar generate_rpm

rpm: copy log tar generate_rpm

# auto_tag2 should be in your PATH
# This target is for tagging your software in the CVS tree.
# See DEV_PROCESS.readme for details.
tag: clean
	@echo -n "Launching the test suite? (y/N)"
	@read SURE; if test -n "$${SURE}" -a "$${SURE}" = "y";then make test;fi
	@if type auto_tag2; then\
		auto_tag2 $(specfile) $(files_list_to_tag);\
	else\
		echo ;echo ;\
		echo "*************************************************";\
		echo "The script auto_tag2 cannot be found in your path!";\
		echo "Please install it!";\
		echo "For that purpose, I suggest you do something like:";\
		echo ;\
		echo "mkdir ~/bull-exc-cvs ~/bin";\
		echo "cd ~/bull-exc-cvs";\
		echo "cvs -d :ext:username@forge.frec.bull.fr:/cvsroot/clustmngt checkout devtools";\
		echo "ln -sf ~/bull-exc-cvs/devtools/bin/* ~/bin/";\
		echo "export PATH=~/bin:\$PATH";\
		echo ;\
		echo "Enjoy! ;-)";\
		exit 1;\
	fi;


test:
	@echo "*****************************************************************************"
	@echo "*****************************************************************************"
	@echo "*** Test requires some configuration to work! Please see the README file. ***"
	@echo "*****************************************************************************"
	@echo "*****************************************************************************"
	@nosetests

coverage:
	@nosetests --with-coverage --cover-html --cover-html-dir=unpackaged/tests-report/ --cover-package=clmsequencer

pylint:
	@PYTHONPATH=${PYTHONPATH}:lib pylint -i y -r n -f colorized --rcfile=unpackaged/pylint.rc clmsequencer bin/clmsequencer bin/clmguesser bin/dbm-sequencer bin/clmcomptype bin/clusterctrl bin/gen_ise_input

sloc:
	@sloccount --wide  lib tests bin


release: tag
	@if type ask4release2; then\
		ask4release2 $(current_makefile) $(specfile) $(rt_project) $(rt_package) $(rt_release);\
	else\
		echo ;echo ;\
		echo "*************************************************";\
		echo "The script ask4release2 cannot be found in your path!";\
		echo "Please install it!";\
		echo "For that purpose, I suggest you do something like:";\
		echo ;\
		echo "mkdir ~/bull-exc-cvs ~/bin;";\
		echo "cd ~/bull-exc-cvs;";\
		echo "cvs -d :ext:username@forge.frec.bull.fr:/cvsroot/clustmngt checkout devtools";\
		echo "ln -sf ~/bull-exc-cvs/devtools/bin/* ~/bin/";\
		echo "export PATH=~/bin:\$PATH";\
		echo ;\
		echo "Enjoy! ;-)";\
		exit 1;\
	fi;
