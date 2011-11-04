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
"""
ISE API implementation
"""
import logging
import time
from datetime import datetime as dt

from ClusterShell.Task import EventHandler, task_self
from clmsequencer.commons import get_nodes_from, get_version
from clmsequencer.ise import parser, model
from clmsequencer.ise.rc import should_stop, is_error_rc, is_warning_rc, \
    ACTION_RC_OK, ACTION_RC_WARNING, ACTION_RC_UNEXECUTED


__author__ = "Pierre Vigneras"
__copyright__ = "Copyright (c) 2010 Bull S.A.S."
__credits__ = ["Pierre Vigneras"]
__version__ = get_version()

_LOGGER = logging.getLogger(__name__)

class ProgressReporter(EventHandler):
    """
    This EventHandler is just used to report progress of the given execution
    """

    def __init__(self, execution):
        EventHandler.__init__(self)
        self.execution = execution

    def ev_timer(self, timer):
        """
        Called when the timer expires.
        """
        self.execution.report_progress()


class ActionUpdater(EventHandler):
    """
    This EventHandler updates executed action as soon as possible
    """

    def __init__(self, action, execution):
        EventHandler.__init__(self)
        self.action = action
        self.execution = execution
        self.execution.running = self.execution.running + 1
        self.execution.best_fanout = max(self.execution.best_fanout,
                                         self.execution.running)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)

    def ev_start(self, worker):
        """
        Called when the action starts its execution.
        """
        _LOGGER.info("Executing action %s: %s",
                     self.action.id, self.action.description)
        self.action.started_time = time.time()

    def ev_read(self, worker):
        """
        Called when an action outputs something.
        """
        if self.action.remote:
            # Worker SSH
            node, buf = worker.last_read()
            _LOGGER.output("%s: [node=%s] %s",
                           self.action.id, node, buf)
        else:
            # Worker Popen
            buf = worker.last_read()
            _LOGGER.output("%s: %s", self.action.id, buf)

    def ev_error(self, worker):
        """
        Called when an action outputs something on its standard error.
        """
        if self.action.remote:
            # Worker SSH
            node, err = worker.last_error()
            _LOGGER.warning("%s: [node=%s] %s",
                            self.action.id, node, err)
        else:
            # Worker Popen
            err = worker.last_error()
            _LOGGER.warning("%s: %s", self.action.id, err)

    def _update_remote_action(self, ssh_worker):
        """
        Update the fields of the related remote action
        """
        # Worker SSH
        overall_rc = ACTION_RC_OK
        overall_stdout = ""
        overall_stderr = ""
        for rc, nodes in ssh_worker.iter_retcodes():
            for buf, nodes in ssh_worker.iter_buffers(nodes):
                overall_stdout += "%s: %s" % (nodes, buf)
            for error, nodes in ssh_worker.iter_errors(nodes):
                overall_stderr += "%s: %s" % (nodes, error)
            if is_error_rc(rc):
                overall_rc = rc
                break
            if is_warning_rc(rc):
                overall_rc = rc
        self.action.rc = overall_rc
        self.action.stdout = overall_stdout
        self.action.stderr = overall_stderr

    def _update_local_action(self, popen_worker):
        """
        Update the fields of the related local action
        """
        self.action.rc = popen_worker.retcode()
        self.action.stdout = popen_worker.read()
        self.action.stderr = popen_worker.error()

    def ev_close(self, worker):
        """
        Called when an action completes.
        """
        self.action.ended_time = time.time()
        if (self.action.remote):
            self._update_remote_action(worker)
        else:
            self._update_local_action(worker)

        self.execution.executed_actions[self.action.id] = self.action
        self.execution.running = self.execution.running - 1
        if should_stop(self.action.rc,
                       self.execution.force,
                       self.action.force):
            errmsg = "[No output on stderr]" if self.action.stderr is None \
                else self.action.stderr
            _LOGGER.error("%s: [rc=%s] %s",
                          self.action.id, self.action.rc, errmsg)
            self.execution.error_actions[self.action.id] = self.action
            return

        for next_id in self.action.next():
            self.execution.schedule_action(next_id)


def execute(a_file, force=False, doexec=True, progress=0.0, fanout=64):
    """
    Execute the instructions sequence specified in the model described
    in the given XML file
    """
    return execute_model(model.Model(parser.ISEParser(a_file).root),
                         force,
                         doexec,
                         progress,
                         fanout)

def execute_model(a_model, force=False, doexec=True, progress=0.0, fanout=64):
    """
    Execute the instructions sequence specified in the given model
    """
    return Execution(a_model, force, doexec, progress, fanout)


class Execution(object):
    """
    execution.executed_actions[actionId] : action that has been
    executed execution.error_actions[actionId] : action that returned
    an error code
    """

    def __init__(self, a_model, force=False,
                 doexec=True, progress=0.0, fanout=64):
        """
        force defines how warning should be handled. When set to false,
        warning == error.
        """
        self.force = force
        self.model = a_model
        self.executed_actions = {}
        self.error_actions = {}
        self.running = 0
        self.best_fanout = 0
        self.fanout = fanout
        self.start_time = dt.fromtimestamp(time.time())
        if not doexec:
            _LOGGER.output("No execution (doexec is false)")
        else:
            self.schedule_all()
            if progress is not None and progress >= 0.0:
                task_self().timer(fire=progress,
                                  handler=ProgressReporter(self),
                                  interval=progress,
                                  autoclose=True)

            # ClusterShell does not use the Python logging API: it
            # uses print statement instead. By the way, our _LOGGER
            # default to NOTSET, so ConsoleHandler and FileHandler can
            # do their stuff with different levels.  Therefore,
            # _LOGGER.isEnabledFor(DEBUG) is always True since

            # NOTSET = 0 < DEBUG

            # and getEffectiveLevel() is always NOTSET by default.
            # Therefore, the following condition is useless.
            # Either task_self.debug is always true or is never.
            # For the moment, we remove this feature completely
            #if _LOGGER.getEffectiveLevel() != NOTSET and _LOGGER.isEnabledFor(DEBUG):
            #   task_self().set_info('debug', True)
            task_self().set_info("fanout", self.fanout)
            task_self().resume() # Start and block
        self.rc = self._compute_returned_code()


    def _compute_returned_code(self):
        """
        Compute the returned code that this Execution instance should returned.
        This method is used internally, it is not normally called by the client.

        The actual execution *should* have completed
        (task_self().resume() or task_self().join())
        """
        returned_rc = ACTION_RC_OK
        for action in self.executed_actions.values():
            current_rc = action.rc
            # We reach an error, we will return an error
            if is_error_rc(current_rc):
                return current_rc
            if is_warning_rc(current_rc):
                returned_rc = ACTION_RC_WARNING
                continue

        return returned_rc

    def report_progress(self):
        """
        Output a progress report.
        """
        current_time = dt.fromtimestamp(time.time())
        delta_time = current_time - self.start_time
        total = len(self.model.actions)
        done = len(self.executed_actions)
        done_percent = (float(done) / total) * 100
        errors = len(self.error_actions)
        errors_percent = (float(errors) / total) * 100
        pending_percent = (float(self.running) / self.fanout) * 100
        _LOGGER.output("Progress: %s (%s) %d/%d done (%2.1f %%)," + \
                           " %d errors (%2.1f %%)," + \
                           " %d pending (%2.1f %% of fanout)",
                       current_time,
                       delta_time,
                       done, total, done_percent,
                       errors, errors_percent,
                       self.running,
                       pending_percent)

    def __repr__(self):
        return "%s(%r)" % (self.__class__, self.__dict__)


    def schedule_all(self):
        """
        Schedule the execution of the instructions set
        """
        for id_ in self.model.actions.keys():
            # Schedule each action.
            self.schedule_action(id_)

    def schedule_action(self, id_):
        """
        Schedule the action with the given id_.
        Dependencies are checked before.
        """
        action = self.model.actions[id_]
        all_deps = action.all_deps()
        for dep in all_deps:
            if (not dep in self.executed_actions) \
                   or (dep in self.error_actions):

                _LOGGER.debug("Can't currently execute %s because of %s",
                              id_, dep)
                return

        _LOGGER.debug("Submitting execution of %s, all deps satisfied: %s",
                      id_, ', '.join(all_deps))
        try:
            self._submit(action)
        except Exception as exception:
            msg = "Exception raised while submitting" + \
                " action: %s: %r" % (action.id, exception) + \
                ". This action will appear both as an error " + \
                "(rc=%d) " % ACTION_RC_UNEXECUTED + \
                "and as unexecuted."
            _LOGGER.error(msg)
            action.rc = ACTION_RC_UNEXECUTED
            action.stdout = ""
            action.stderr = msg
            self.error_actions[action.id] = action

    def _submit(self, action, task=task_self()):
        """
        Submit the execution of the given action to the underlying engine (ClusterShell)
        """
        event_handler = ActionUpdater(action, self)
        action.submitted_time = time.time()
        if action.remote:
            nodes = get_nodes_from(action.component_set)
            action.worker = task.shell(action.command,
                                       nodes=nodes,
                                       stderr='enable_stderr',
                                       handler=event_handler)
        else:
            action.worker = task.shell(action.command,
                                       key=action.component_set,
                                       stderr='enable_stderr',
                                       handler=event_handler)

        return action






