#!/bin/bash

# $Id: nfs_example.sh,v 1.1 2011/04/06 09:45:44 vigneras Exp $

###############################################################################
# Copyright (C) 2009  Bull S. A. S.  -  All rights reserved
# Bull, Rue Jean Jaures, B.P.68, 78340, Les Clayes-sous-Bois
# This is not Free or Open Source software.
# Please contact Bull S. A. S. for details about its license.
###############################################################################

# This shell script creates a ruleset designed to start and stop a bullx cluster

# It basically creates three set of rules:

# softstop: for stopping the cluster 'softly'
# hardstop: for stopping the cluster 'hardly'
# start: for starting the cluster

# get command basename and parameters
program=$(basename $0)

usage() {
    echo "Usage: $(basename $0) [-b db_name] install|uninstall|exist"
    exit 1
}


exist() {
    test $(dbm-sequencer show | wc -l) -gt 3
    return $?
}

install() {
    echo "NFS Example (see unpackaged/Sequencer.odp presentation for details)"
    dbm-sequencer $opt_db add example colddoorOff coldoor@soft '%name=~cd0' "echo stopping: %id" "echo -e 'c1#compute@soft\nnfs1#nfs@soft'" "nodeOff,nfs1Off,nfs2Off" ""
    dbm-sequencer $opt_db add example nodeOff 'compute@soft' '%name=~c1' "echo stopping: %id" NONE NONE ""
    dbm-sequencer $opt_db add example nfs1Off 'nfs@soft' '%name=~nfs1' "echo stopping: %id" "echo -e nfs1#nfsd@soft" "nfsd1Down" ""
    dbm-sequencer $opt_db add example nfs2Off 'nfs@soft' '%name=~nfs2' "echo stopping: %id" "echo -e nfs2#nfsd@soft" "nfsd2Down" ""
    dbm-sequencer $opt_db add example nfsd1Down 'nfsd@soft' '%name=~nfs1' "echo stopping: %id" "echo -e 'c1#unmount@soft\nnfs2#unmount@soft'" "unmount" ""
    dbm-sequencer $opt_db add example nfsd2Down 'nfsd@soft' '%name=~nfs2' "echo stopping: %id" "echo -e 'c1#unmount@soft\nnfs1#unmount@soft'" "unmount" ""
    dbm-sequencer $opt_db add example unmount 'unmount@soft' ALL "echo UNMOUNTING %id" NONE NONE ""
}

uninstall() {
    dbm-sequencer -F remove example
}


# parse options
while getopts 'hb:' opts
do
    case $opts in
        h) usage; break ;;
        b) opt_db="-b $OPTARG";shift;shift;break ;;
    esac
done

if test $# -ne 1; then
    usage
fi


case $1 in
    exist)    exist ; rc=$?;;
    install)   install; rc=$? ;;
    uninstall) uninstall; rc=$? ;;
    *) usage ;;
esac

exit $rc


