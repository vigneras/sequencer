#!/bin/bash
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

# This shell script creates a ruleset designed to test the following use case:
# a#doubledep@soft -> (b#leaf@soft, c#singledep@soft)
# d#doubledep@soft -> (e#leaf@soft, f#singledep@soft)
# c#singledep@soft -> e#leaf@soft
# f#singledep@soft -> b#leaf@soft

# Note that actions are just echo with a sleep.  If you want to
# display the dependency graph graphically, do not use special
# characters in rules column (especially ':' and '"' have special
# meaning in the DOT graph format which make them unusable in
# actions).

# The rules are *added* to the sequencer. In particular, if the same
# script is run twice, on the same ruleset, errors will happened
# because rules with same name are forbidden in a given
# ruleset. Remove the ruleset beforehand, or use another ruleset.
# Note also that the sequencer table must exist beforehand. Use
# 'dbm-sequencer create_table' if required.

# Let suppose a db is available as cdbpv:
# The following command:
# $ dbm-sequencer -b cdbpv remove test
# Remove all rules from the 'test' ruleset in the cdbpv database
# Then:
# $ /usr/share/doc/sequencer/example.makerules.sh -b cdbpv test
# Insert rules into the database. Watch them with:
# $ dbm-sequencer -b cdbpv show
# Finally, you can run an execution on (virtual) components: 'a' and 'd':
# $ sequencer  test -b cdbpv a#doubledep@soft d#doubledep@soft

# Different ordering algorithms are available: use the option --algo
# along with the --stats to see that different algorithms provide
# different results.

# The 'seq' algorithm will give a speedup of around 1.00. It is
# sequential.

# The 'mixed' algorithm will give a speedup of around 1.55. It mixex
# sequential and parallel instructions.

# The 'par' algorithm (default when chaining) will give a speedup of
# around 2.00. By nature, 'par' produces only parallel instructions
# with explicit dependencies.

# In the example above, a will be executed as soon as b and c have
# finished with the 'par' algorithm, hence 3 seconds after the
# start. While in the 'mixed' case, a will have to wait for both f and
# c so, 5 seconds after the start.

# Note however that action 'f' will return a WARNING code
# (=75). Therefore, action that depends on it (action d actually) will
# not be executed unless option '--Force' is given on execution. This
# is to show the error management of the sequencer.


# get command basename and parameters
program=$(basename $0)

usage() {
    echo "Usage: $(basename $0) ruleset"
    exit 1
}

# parse options
while getopts 'h:' opts
do
    case $opts in
        h) usage; break ;;
    esac
done

if test $# -lt 1; then
    echo "Missing argument: ruleset" >&2
    usage
fi


ruleset=$1

echo "Adding rules to ruleset: $ruleset"
sequencer  dbadd $ruleset R0be leaf@soft ALL "echo component: %name; sleep 1" NONE NONE "Rule for leaves b and e"
sequencer  dbadd $ruleset R1c singledep@soft "bash -c '[[ %id =~ ^c#.* ]]'" "echo type: %type;sleep 2;" "echo e#leaf@soft" R0be  "Filter using a script (bash builtin here)"
sequencer  dbadd $ruleset R1f singledep@soft "%name =~ f" "echo ruleset: %ruleset;sleep 4;exit 75" "echo b#leaf@soft" R0be  "Returns a WARNING code (=75)"
sequencer  dbadd $ruleset R2a doubledep@soft "%id =~ ^a#.*" "echo rulename: %rulename;sleep 4;" "echo -e 'b#leaf@soft\nc#singledep@soft'" R0be,R1c  "Depsfinder: one component per line."
sequencer  dbadd $ruleset R2d doubledep@soft "%id =~ ^d#.*" "echo id: %id;sleep 2;" "echo -e 'e#leaf@soft\nf#singledep@soft'" R0be,R1f  "Filter using regexp."



