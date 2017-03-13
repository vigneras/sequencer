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
"""
Sequencer DB Management
"""
from ConfigParser import RawConfigParser, DuplicateSectionError
from os import path
from sequencer.commons import get_version, UnknownRuleSet, SequencerError, \
    replace_if_none, NONE_VALUE, DuplicateRuleError, NoSuchRuleError, \
    replace_if_none_by_uni, UnicodeConfigParser, \
    to_str_from_unicode
from sequencer.dgm.model import Rule
import hashlib
import logging
import os
import sys
import codecs

__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = logging.getLogger(__name__)


def _update_hash(checksum, rule):
    """
    Update the given checksum with all required fields of the given rule.
    """
    checksum.update(to_str_from_unicode(rule.ruleset, should_be_uni=True))
    checksum.update(to_str_from_unicode(rule.name, should_be_uni=True))
    for type_ in rule.types:
        checksum.update(to_str_from_unicode(type_, should_be_uni=True))
    # Do not take filter into account
    # ruleset_h.update(str(rule.filter))
    checksum.update(to_str_from_unicode(replace_if_none_by_uni(rule.action), \
                    should_be_uni=True))
    checksum.update(to_str_from_unicode(replace_if_none_by_uni(rule.depsfinder), \
                    should_be_uni=True))
    checksum.update(to_str_from_unicode(replace_if_none_by_uni(rule.help), \
                    should_be_uni=True))
    for dep in rule.dependson:
        checksum.update(to_str_from_unicode(replace_if_none_by_uni(dep), \
                    should_be_uni=True))
    # Do not take comment into account
    # ruleset_h.update(str(rule.comments))


def create_rule_from_strings_array(given_row):
    """
    Function that creates a Rule from a strings array
    Arguments are converted to their final model format.
    """
    row = [replace_if_none(x) for x in given_row]
    ruleset = row[0]
    name = row[1]
    # Multiple types are allowed: they are separated by symbol ','
    try:
        # Try unicode first
        types = None if row[2] is None else [unicode.strip(x)
                                             for x in row[2].split(',')]
    except TypeError:
        # Try str then
        types = None if row[2] is None else [str.strip(x)
                                             for x in row[2].split(',')]
    filter_ = row[3]
    action = row[4]
    depsfinder = row[5]
    # Multiple dependencies are allowed: they are separated by symbol ','
    try:
        # Try unicode first
        dependson = None if row[6] is None else [unicode.strip(x)
                                                 for x in row[6].split(',')]
    except TypeError:
        # Try str then.
        dependson = None if row[6] is None else [str.strip(x)
                                                 for x in row[6].split(',')]
    comments = row[7]
    help = row[8] #if row[8] is not None else unicode(None)
    return Rule(ruleset,
                name,
                types,
                filter_,
                action,
                depsfinder,
                dependson,
                comments,
                help)

class SequencerFileDB(object):
    """
    This class uses standard INI file (configuration file) to fetch rulesets.
    """

    def __init__(self, basedir):
        self.basedir = path.abspath(basedir)
        self.config_for_ruleset = self._update_rulesets()
        _LOGGER.debug("Basedir is: %s", self.basedir)

    def __str__(self):
        return self.basedir

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def _get_config_filename_for(self, ruleset):
        """
        Return the config file name related to the given ruleset.
        """
        filename = path.join(self.basedir, ruleset + '.rs')
        return filename

    def _update_rulesets(self):
        """
        Return a mapping of {ruleset_name: config} from self.basedir.
        """
        if not os.path.exists(self.basedir):
            return dict()
        _LOGGER.debug("Reading entries from %s", self.basedir)
        entries = os.listdir(self.basedir)
        result = {}
        for entry in entries:
            index = entry.rfind('.rs')
            if index == -1:
                continue
            ruleset_name = entry[:index]
            config = UnicodeConfigParser()
            
            config_file = self._get_config_filename_for(ruleset_name)
            with codecs.open(config_file, 'r', encoding='utf-8') as f:
                config.readfp(f)

            if _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug("Ruleset found: %s with rules: %s",
                              ruleset_name,
                              ", ".join(config.sections()))
            result[ruleset_name] = config
        return result

    def create_table(self):
        """
        Create the basedir path if it does not exist.
        """
        if not path.exists(self.basedir):
            _LOGGER.info("Creating db: %s", self.basedir)
            os.makedirs(self.basedir)
        elif not path.isdir(self.basedir):
            raise SequencerError("Specified basedir is " + \
                                     "not a directory: %s" % self.basedir)
        else:
            _LOGGER.warning("Path already exists: %s" % self.basedir)
        self.config_for_ruleset = self._update_rulesets()

    def drop_table(self):
        """
        Drop the sequencer table
        """
        _LOGGER.info("Dropping db: %s", self.basedir)
        for ruleset in self.config_for_ruleset:
            os.remove(self._get_config_filename_for(ruleset))
        try:
            os.rmdir(self.basedir)
        except OSError as ose:
            _LOGGER.warning("Can't remove path %s: %s" % (self.basedir, ose))

    def _commit_all_changes(self, rulesets=None):
        """
        Write all config files related to the given ruleset names
        'rulesets' to the backing store (the filesystem). If rulesets is None,
        names are taken from 'self.config_for_ruleset.keys()'.
        """
        if not os.path.exists(self.basedir):
            _LOGGER.output("Creating base directory %s", self.basedir)
            os.makedirs(self.basedir)
        if rulesets is None:
            rulesets = self.config_for_ruleset.keys()
        for ruleset in rulesets:
            if ruleset is not None:
                filename = self._get_config_filename_for(ruleset)
                config = self.config_for_ruleset[ruleset]
                if _LOGGER.isEnabledFor(logging.DEBUG):
                    _LOGGER.debug("Commiting %s to %s",
                                  ", ".join(config.sections()),
                                  filename)
                with open(filename, 'wb') as configfile:
                    config.write(configfile)

    def add_rule(self, rule, commit=True):
        """
        Create a single entry in the DB.
        """
        # NB: it is OK to remove the conversion to str because all the args used
        # to create a Rule are unicode-typed (done in the main).
        # As create_rule_from_string_array converts the string "None" to 
        # the value None, we have to convert it back.
        config = self.config_for_ruleset.setdefault(rule.ruleset,
                                                    UnicodeConfigParser())
        _LOGGER.info("Adding rule: %s to %s", rule, str(config.sections()))
        try:
            config.add_section(rule.name)
        except DuplicateSectionError as dse:
            _LOGGER.debug("DuplicateSectionError catched: %s"
                          " -> raising DuplicateRuleError", dse)
            raise DuplicateRuleError(rule.ruleset, rule.name)
        config.set(rule.name, 'types', ",".join(rule.types))

        config.set(rule.name, 'filter', replace_if_none_by_uni(rule.filter))

        # was "... str(rule.action))"
        config.set(rule.name, 'action', replace_if_none_by_uni(rule.action))

        # was "... str(rule.depsfinder))"
        config.set(rule.name, 'depsfinder', 
                    replace_if_none_by_uni(rule.depsfinder))

        config.set(rule.name, 'dependson',
                   NONE_VALUE if len(rule.dependson) == 0 else u",".join(rule.dependson))

        # was "... str(rule.comments))"
        config.set(rule.name, 'comments', replace_if_none_by_uni(rule.comments))

        # was "... str(rule.help))"
        config.set(rule.name, 'help', replace_if_none_by_uni(rule.help))

        if commit:
            self._commit_all_changes([rule.ruleset])

    def remove_rules(self, ruleset, rule_names=None, nodeps=False, commit=True):
        """
        Remove the rules from the given ruleset.  Return the set of
        rules thas has not been removed for some reasons.  Unless
        nodeps is True, any reference to the rules in the dependson
        column will also be removed.
        """
        result = set()
        rules = None
        try:
            rules = self.get_rules_for(ruleset)
        except UnknownRuleSet:
            return rule_names

        if rule_names is None:
            rule_names = rules.keys()
        for name in rule_names:
            _LOGGER.info("Removing rule: %s %s", ruleset, name)
            config = self.config_for_ruleset[ruleset]
            done = config.remove_section(name)
            if not done:
                result.add(name)
            if nodeps:
                continue
            # Remove dependencies
            if name in rules:
                del rules[name]
            for rule in rules.values():
                if name in rule.dependson:
                    _LOGGER.debug("Removing reference %s from rule %s",
                                  name, rule.name)
                    rule.dependson.remove(name)
                    deps = None if len(rule.dependson) == 0 \
                        else ",".join(rule.dependson)
                    update_set = set()
                    update_set.add(("dependson", deps))
                    self.update_rule(ruleset, rule.name,
                                     update_set, commit=False)

        if commit:
            self._commit_all_changes([ruleset])
        return result

    def update_rule(self, ruleset, name, update_set, nodeps=False, commit=True):
        """
        Update the column 'col' of the given rule ('ruleset', 'name')
        with the given value 'val'. Return true Iff the given rule has
        been successfully updated. False otherwise.
        """
        config = self.config_for_ruleset.get(ruleset)
        if config is None:
            raise UnknownRuleSet(ruleset)
        if not config.has_section(name):
            raise NoSuchRuleError(ruleset, name)

        new_ruleset = None
        new_name = None
        new_config = None
        _LOGGER.info("Updating rule (%s, %s) with %s",
                     ruleset, name, str(update_set))

        record_set = []
        # Remove ruleset and name from the record as they are not
        # present in the config file (config file name is the ruleset,
        # and section is the rule name)
        for record in update_set:
            if record[0].upper() == 'NAME':
                if not nodeps:
                    new_name = record[1]
                continue
            if record[0].upper() == 'RULESET':
                new_ruleset = record[1]
                continue
            record_set.append(record)

        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Original config: %s", str(config.items(name)))
            _LOGGER.debug("Config change: %s", str(record_set))
        section_name = new_name if new_name is not None else name
        # Copy and remove rule from previous config if a new ruleset
        # has been specified
        if new_ruleset is not None:
            new_config = self.config_for_ruleset.setdefault(new_ruleset,
                                                            UnicodeConfigParser())
            if new_config.has_section(section_name):
                raise ValueError("Cannot move (%s, %s)" % (ruleset, name) + \
                                     " to (%s, %s):" % (new_ruleset,
                                                       section_name) + \
                                     " destination already exists")
            # Copy
            _LOGGER.debug("Copying (%s, %s) section to (%s, %s)",
                          ruleset, name, new_ruleset, section_name)
            new_config.add_section(section_name)
            for (option, value) in config.items(name):
                new_config.set(section_name, option, value)
            # Remove
            _LOGGER.debug("Removing section (%s, %s)", ruleset, name)
            config.remove_section(name)

        # Copy rule to a new section if new name has been specified
        elif new_name is not None:
            items = list(config.items(name))
            # Remove
            _LOGGER.debug("Removing section (%s, %s)", ruleset, name)
            config.remove_section(name)
            # Copy
            if config.has_section(section_name):
                raise ValueError("Cannot move (%s, %s)" % (ruleset, name) + \
                                     " to (%s, %s):" % (ruleset,
                                                       section_name) + \
                                     " destination already exists")
            _LOGGER.debug("Copying (%s, %s) section to (%s, %s)",
                          ruleset, name, ruleset, section_name)
            config.add_section(section_name)
            for (option, value) in items:
                config.set(section_name, option, value)

        # Update
        final_config = config if new_ruleset is None else new_config
        for record in record_set:
            # Was : str(record[0]), str(record[1]). Unnecessary because all the
            # args used are unicode-typed (done in the main).
            final_config.set(section_name, record[0],
                                replace_if_none_by_uni(record[1]))

        _LOGGER.debug("Final config: %s",
                      final_config.items(section_name))

        # Update dependencies
        if not nodeps and (new_name is not None or new_ruleset is not None):
            try:
                rules = self.get_rules_for(ruleset)
                for rule in rules.values():
                    deps = rule.dependson
                    if deps is not None and name in deps:
                        deps.remove(name)
                        if new_ruleset is None:
                            deps.add(new_name)
                        update_set = set()
                        update_set.add(("dependson", ",".join(deps)))
                        _LOGGER.info("Updating deps of %s: ", rule)
                        self.update_rule(ruleset, rule.name, update_set,
                                         nodeps=False, commit=False)
            except UnknownRuleSet:
                pass
        if commit:
            self._commit_all_changes()
        return True

    def add_rules(self, rules):
        """
        Create multiple entries in the table
        """
        for rule in rules:
            self.add_rule(rule, commit=False)
        self._commit_all_changes()

    def get_rules_for(self, ruleset):
        """
        Return a {name : rule} map for the given ruleset name.
        """
        if ruleset is None:
            raise ValueError("None ruleset given!")

        try:
            config = self.config_for_ruleset[ruleset]
        except KeyError:
            raise UnknownRuleSet(ruleset)

        sections = config.sections()
        result = dict()
        for section in sections:
            _LOGGER.debug("Reading rule from %s:%s", ruleset, section)
            row = [ruleset, section]
            row.append(config.get(section, 'types'))
            row.append(config.get(section, 'filter'))
            row.append(config.get(section, 'action'))
            row.append(config.get(section, 'depsfinder'))
            row.append(config.get(section, 'dependson'))
            row.append(config.get(section, 'comments'))
            row.append(config.get(section, 'help'))
            rule = create_rule_from_strings_array(row)
            result[rule.name] = rule

        return result

    def get_rules_map(self):
        """
        Return a {ruleset: {name: rule}} map of maps of all rules
        defined in the db.
        """
        result = {}
        for ruleset in self.config_for_ruleset:
            rules = self.get_rules_for(ruleset)
            if len(rules) != 0:
                result[ruleset] = rules

        return result

    def checksum(self, ruleset):
        """
        Return a pair [ruleset_h, {name: hash}] for the given ruleset
        name.
        """
        rules = self.get_rules_for(ruleset).values()
        ruleset_h = hashlib.new('sha512')
        h_for = dict()
        for rule in sorted(rules, key=lambda r: r.name):
            h_for[rule.name] = hashlib.new('sha512')
            _update_hash(h_for[rule.name], rule)
            _update_hash(ruleset_h, rule)


        return [ruleset_h, h_for]


class SequencerSQLDB(object):
    """
    Instance of this class are independent of the underlying DB
    implementation. Any DB-API 2.0 compliant object should work. This
    allows the sequencer to perform on various DB such as postgresql
    (the actual target) or sqlite (used for unit tests).

    Note however, that the paramstyle differs between database. For
    example, sqlite uses 'qmark' whereas pgdb uses
    'format'. Therefore, the exact string should be passed to
    guarantee database independence.
    """
    def __init__(self, db):
        assert db is not None
        self.raw_db = db

    def close(self):
        """
        Close the db.
        """
        self.raw_db.close()

    def execute(self, sql, values=None, fetch=False):
        """
        Execute the given sql statement with the given values.
        If fetch is true, the result is returned.
        """
        return self.raw_db.execute(sql, values, fetch)

    def dump(self, out):
        """
        Dump the content of this instance to the given out file-type.
        """
        return self.raw_db.dump(out)

    def get_name(self):
        """
        Return the name of this database.
        """
        return self.raw_db.get_name()

    def sql_match_exp(self, column, re):
        """
        Return the matching SQL expression for the underlying database
        implementation.
        """
        return self.raw_db.sql_match_exp(column, re)


    def create_table(self):
        """
        Create the sequencer table
        """
        _LOGGER.info("Creating table: sequencer")
        sql_stmt = "CREATE TABLE sequencer " + \
            "(ruleset text NOT NULL, " + \
            "name text NOT NULL, " + \
            "types text NOT NULL, " + \
            "filter text, " + \
            "action text, " + \
            "depsfinder text, " + \
            "dependson text, " + \
            "comments text, " + \
            "help text, " + \
            "CONSTRAINT ruleset_name PRIMARY KEY (ruleset, name)," +\
            "CONSTRAINT not_empty CHECK (LENGTH(types) > 0 AND" + \
            " LENGTH(filter) > 0 AND " + \
            "(depsfinder ISNULL OR LENGTH(depsfinder) > 0)))"
        self.execute(sql_stmt)

    def drop_table(self):
        """
        Drop the sequencer table
        """
        _LOGGER.info("Dropping table: sequencer")
        self.execute("DROP TABLE sequencer")

    def add_rule(self, rule):
        """
        Create a single entry in the DB.
        """
        _LOGGER.info("Adding rule: %r", rule)
        dependson =  None if len(rule.dependson) == 0 \
            else ",".join(rule.dependson)

        # test if name and ruleset already exists
        (rowcount, rows) = self.execute("SELECT * FROM sequencer "
                                        "WHERE ruleset=? AND name=?",
                                        (rule.ruleset, rule.name),
                                        fetch=True)
        if len(rows) == 0:
            self.execute("INSERT INTO sequencer VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (rule.ruleset,
                          rule.name,
                          ",".join(rule.types),
                          rule.filter,
                          rule.action,
                          rule.depsfinder,
                          dependson,
                          rule.comments,
                          rule.help))
        else:
            raise DuplicateRuleError(rule.ruleset, rule.name)

    def remove_rules(self, ruleset, rule_names=None, nodeps=False):
        """
        Remove the rules from the given ruleset.  Return the set of
        rules thas has not been removed for some reasons.  Unless
        nodeps is True, any reference to the rules in the dependson
        column will also be removed.
        """
        result = set()
        rules = None
        try:
            rules = self.get_rules_for(ruleset)
        except UnknownRuleSet:
            return rule_names

        if rule_names is None:
            rule_names = rules.keys()
        for name in rule_names:
            _LOGGER.info("Removing rule: %s %s", ruleset, name)
            rowcount = self.execute("DELETE FROM sequencer " + \
                                        "WHERE ruleset=? AND name=?",
                                    (ruleset, name))[0]
            if rowcount != 1:
                result.add(name)
            if nodeps:
                continue
            # Remove dependencies
            if name in rules:
                del rules[name]
            for rule in rules.values():
                if name in rule.dependson:
                    _LOGGER.debug("Removing reference %s from rule %s",
                                  name, rule.name)
                    rule.dependson.remove(name)
                    deps = None if len(rule.dependson) == 0 \
                        else ",".join(rule.dependson)
                    update_set = set()
                    update_set.add(("dependson", deps))
                    self.update_rule(ruleset, rule.name, update_set)

        return result


    def update_rule(self, ruleset, name, update_set, nodeps=False):
        """
        Update the column 'col' of the given rule ('ruleset', 'name')
        with the given value 'val'. Return true Iff the given rule has
        been successfully updated. False otherwise.
        """
        debug_info = []
        set_sql = []
        params = []
        new_name = None
        for record in update_set:
            set_sql.append("%s=?" % record[0])
            new_name = record[1] if (record[0].upper() == 'NAME'
                                     and not nodeps) else None
            debug_info.append("%s=%s" % (record[0], record[1]))
            params.append(record[1])

        params.append(ruleset)
        params.append(name)

        # test if ruleset already exists
        (rowcount, rows) = self.execute("SELECT * FROM sequencer "
                                        "WHERE ruleset=?",
                                        (ruleset,),
                                        fetch=True)
        if len(rows) == 0:
            raise UnknownRuleSet(ruleset)

        # test if name already exists
        (rowcount, rows) = self.execute("SELECT * FROM sequencer "
                                        "WHERE ruleset=? AND name=?",
                                        (ruleset, name),
                                        fetch=True)
        if len(rows) == 0:
            raise NoSuchRuleError(ruleset, name)

        _LOGGER.info("Updating rule (%s %s) with %s",
                     ruleset, name, ", ".join(debug_info))
        rowcount = self.execute("UPDATE sequencer " + \
                                    "SET " + ", ".join(set_sql) +
                                " WHERE ruleset=? AND name=?",
                                tuple(params))[0]
        if rowcount == 0:
            raise ValueError("Unable to update (ruleset, name) for some "
                             "unknown reasons: %s %s" % (ruleset, name))

        if new_name is not None:
            try:
                rules = self.get_rules_for(ruleset)
                for rule in rules.values():
                    deps = rule.dependson
                    if deps is not None and name in deps:
                        deps.remove(name)
                        deps.add(new_name)
                        update_set = set()
                        update_set.add(("dependson", ",".join(deps)))
                        self.update_rule(ruleset, rule.name, update_set)
            except UnknownRuleSet:
                pass

        return rowcount == 1



    def add_rules(self, rules):
        """
        Create multiple entries in the table
        """
        for rule in rules:
            self.add_rule(rule)

    def get_rules_for(self, ruleset):
        """
        Return a {name : rule} map for the given ruleset name.
        """
        if ruleset is None:
            raise ValueError("None ruleset given!")

        query = "SELECT * FROM sequencer WHERE ruleset=?"
        (rowcount, rows) = self.execute(query, [ruleset], fetch=True)

        if not len(rows) > 0:
            raise UnknownRuleSet(ruleset)

        result = dict()
        for row in rows:
            rule = create_rule_from_strings_array(row)
            result[rule.name] = rule

        return result

    def get_rules_map(self):
        """
        Return a {ruleset: {name : rule}} map of maps of all rules
        defined in the db.
        """
        query = "SELECT * FROM sequencer"
        (rowcount, rows) = self.execute(query, fetch=True)
        result = {}
        if rows is None:
            return result
        for row in rows:
            rule = create_rule_from_strings_array(row)
            map_ = result.get(rule.ruleset, dict())
            map_[rule.name] = rule
            result[rule.ruleset] = map_

        return result

    def checksum(self, ruleset):
        """
        Return a pair [ruleset_h, {name: hash}] for the given ruleset
        name.
        """
        rules = self.get_rules_for(ruleset).values()
        ruleset_h = hashlib.new('sha512')
        h_for = dict()
        for rule in sorted(rules, key=lambda r: r.name):
            h_for[rule.name] = hashlib.new('sha512')
            _update_hash(h_for[rule.name], rule)
            _update_hash(ruleset_h, rule)


        return [ruleset_h, h_for]

