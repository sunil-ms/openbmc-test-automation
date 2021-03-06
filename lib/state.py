#!/usr/bin/env python

r"""
This module contains functions having to do with machine state: get_state,
check_state, wait_state, etc.

The 'State' is a composite of many pieces of data.  Therefore, the functions
in this module define state as an ordered dictionary.  Here is an example of
some test output showing machine state:

default_state:
  default_state[chassis]:                         On
  default_state[boot_progress]:                   FW Progress, Starting OS
  default_state[host]:                            Running
  default_state[os_ping]:                         1
  default_state[os_login]:                        1
  default_state[os_run_cmd]:                      1

Different users may very well have different needs when inquiring about
state.  Support for new pieces of state information may be added to this
module as needed.

By using the wait_state function, a caller can start a boot and then wait for
a precisely defined state to indicate that the boot has succeeded.  If
the boot fails, they can see exactly why by looking at the current state as
compared with the expected state.
"""

import gen_print as gp
import gen_robot_print as grp
import gen_valid as gv
import gen_robot_utils as gru
import gen_cmd as gc

import commands
from robot.libraries.BuiltIn import BuiltIn
from robot.utils import DotDict

import re
import os

# We need utils.robot to get keywords like "Get Chassis Power State".
gru.my_import_resource("utils.robot")
gru.my_import_resource("state_manager.robot")

# The BMC code has recently been changed as far as what states are defined and
# what the state values can be.  This module now has a means of processing both
# the old style state (i.e. OBMC_STATES_VERSION = 0) and the new style (i.e.
# OBMC_STATES_VERSION = 1).
# The caller can set environment variable OBMC_STATES_VERSION to dictate
# whether we're processing old or new style states.  If OBMC_STATES_VERSION is
# not set it will default to 1.

# As of the present moment, OBMC_STATES_VERSION of 0 is for cold that is so old
# that it is no longer worthwhile to maintain.  The OBMC_STATES_VERSION 0 code
# is being removed but the OBMC_STATES_VERSION value will stay for now in the
# event that it is needed in the future.

OBMC_STATES_VERSION = int(os.environ.get('OBMC_STATES_VERSION', 1))

# When a user calls get_state w/o specifying req_states, default_req_states
# is used as its value.
default_req_states = ['rest',
                      'chassis',
                      'bmc',
                      'boot_progress',
                      'host',
                      'os_ping',
                      'os_login',
                      'os_run_cmd']

# valid_req_states is a list of sub states supported by the get_state function.
# valid_req_states, default_req_states and master_os_up_match are used by the
# get_state function.
valid_req_states = ['ping',
                    'packet_loss',
                    'uptime',
                    'epoch_seconds',
                    'rest',
                    'chassis',
                    'bmc',
                    'boot_progress',
                    'host',
                    'os_ping',
                    'os_login',
                    'os_run_cmd']

# valid_os_req_states and default_os_req_states are used by the os_get_state
# function.
# valid_os_req_states is a list of state information supported by the
# get_os_state function.
valid_os_req_states = ['os_ping',
                       'os_login',
                       'os_run_cmd']
# When a user calls get_os_state w/o specifying req_states,
# default_os_req_states is used as its value.
default_os_req_states = ['os_ping',
                         'os_login',
                         'os_run_cmd']

# Presently, some BMCs appear to not keep time very well.  This environment
# variable directs the get_state function to use either the BMC's epoch time
# or the local epoch time.
USE_BMC_EPOCH_TIME = int(os.environ.get('USE_BMC_EPOCH_TIME', 0))

# Useful state constant definition(s).
# A match state for checking that the system is at "standby".
standby_match_state = DotDict([('rest', '^1$'),
                               ('chassis', '^Off$'),
                               ('bmc', '^Ready$'),
                               ('boot_progress', ''),
                               ('host', '')])

# default_state is an initial value which may be of use to callers.
default_state = DotDict([('rest', '1'),
                         ('chassis', 'On'),
                         ('bmc', 'Ready'),
                         ('boot_progress', 'FW Progress, Starting OS'),
                         ('host', 'Running'),
                         ('os_ping', '1'),
                         ('os_login', '1'),
                         ('os_run_cmd', '1')])

# A master dictionary to determine whether the os may be up.
master_os_up_match = DotDict([('chassis', '^On$'),
                              ('bmc', '^Ready$'),
                              ('boot_progress',
                               'FW Progress, Starting OS'),
                              ('host', '^Running$')])


###############################################################################
def return_default_state():

    r"""
    Return default state dictionary.

    default_state is an initial value which may be of use to callers.
    """

    return default_state

###############################################################################


valid_state_constants = ['default', 'standby_match_state']


###############################################################################
def return_state_constant(state_name='default'):

    r"""
    Return default state dictionary.

    default_state is an initial value which may be of use to callers.
    """

    error_message = gv.svalid_value(state_name, var_name='state_name',
                                    valid_values=valid_state_constants)
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if state_name == 'default':
        return default_state
    elif state_name == 'standby_match_state':
        return standby_match_state

###############################################################################


###############################################################################
def anchor_state(state):

    r"""
    Add regular expression anchors ("^" and "$") to the beginning and end of
    each item in the state dictionary passed in.  Return the resulting
    dictionary.

    Description of Arguments:
    state    A dictionary such as the one returned by the get_state()
             function.
    """

    anchored_state = state.copy()
    for key, match_state_value in anchored_state.items():
        anchored_state[key] = "^" + str(anchored_state[key]) + "$"

    return anchored_state

###############################################################################


###############################################################################
def strip_anchor_state(state):

    r"""
    Strip regular expression anchors ("^" and "$") from the beginning and end
    of each item in the state dictionary passed in.  Return the resulting
    dictionary.

    Description of Arguments:
    state    A dictionary such as the one returned by the get_state()
             function.
    """

    stripped_state = state.copy()
    for key, match_state_value in stripped_state.items():
        stripped_state[key] = stripped_state[key].strip("^$")

    return stripped_state

###############################################################################


###############################################################################
def compare_states(state,
                   match_state):

    r"""
    Compare 2 state dictionaries.  Return True if they match and False if they
    don't.  Note that the match_state dictionary does not need to have an entry
    corresponding to each entry in the state dictionary.  But for each entry
    that it does have, the corresponding state entry will be checked for a
    match.

    Description of arguments:
    state           A state dictionary such as the one returned by the
                    get_state function.
    match_state     A dictionary whose key/value pairs are "state field"/
                    "state value".  The state value is interpreted as a
                    regular expression.  Every value in this dictionary is
                    considered.  If each and every one matches, the 2
                    dictionaries are considered to be matching.
    """

    match = True
    for key, match_state_value in match_state.items():
        # Blank match_state_value means "don't care".
        if match_state_value == "":
            continue
        try:
            if not re.match(match_state_value, str(state[key])):
                match = False
                break
        except KeyError:
            match = False
            break

    return match

###############################################################################


###############################################################################
def get_os_state(os_host="",
                 os_username="",
                 os_password="",
                 req_states=default_os_req_states,
                 os_up=True,
                 quiet=None):

    r"""
    Get component states for the operating system such as ping, login,
    etc, put them into a dictionary and return them to the caller.

    Note that all substate values are strings.

    Description of arguments:
    os_host      The DNS name or IP address of the operating system.
                 This defaults to global ${OS_HOST}.
    os_username  The username to be used to login to the OS.
                 This defaults to global ${OS_USERNAME}.
    os_password  The password to be used to login to the OS.
                 This defaults to global ${OS_PASSWORD}.
    req_states   This is a list of states whose values are being requested by
                 the caller.
    os_up        If the caller knows that the os can't possibly be up, it can
                 improve performance by passing os_up=False.  This function
                 will then simply return default values for all requested os
                 sub states.
    quiet        Indicates whether status details (e.g. curl commands) should
                 be written to the console.
                 Defaults to either global value of ${QUIET} or to 1.
    """

    quiet = int(gp.get_var_value(quiet, 0))

    # Set parm defaults where necessary and validate all parms.
    if os_host == "":
        os_host = BuiltIn().get_variable_value("${OS_HOST}")
    error_message = gv.svalid_value(os_host, var_name="os_host",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if os_username == "":
        os_username = BuiltIn().get_variable_value("${OS_USERNAME}")
    error_message = gv.svalid_value(os_username, var_name="os_username",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if os_password == "":
        os_password = BuiltIn().get_variable_value("${OS_PASSWORD}")
    error_message = gv.svalid_value(os_password, var_name="os_password",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    invalid_req_states = [sub_state for sub_state in req_states
                          if sub_state not in valid_os_req_states]
    if len(invalid_req_states) > 0:
        error_message = "The following req_states are not supported:\n" +\
            gp.sprint_var(invalid_req_states)
        BuiltIn().fail(gp.sprint_error(error_message))

    # Initialize all substate values supported by this function.
    os_ping = 0
    os_login = 0
    os_run_cmd = 0

    if os_up:
        if 'os_ping' in req_states:
            # See if the OS pings.
            cmd_buf = "ping -c 1 -w 2 " + os_host
            if not quiet:
                gp.pissuing(cmd_buf)
            rc, out_buf = commands.getstatusoutput(cmd_buf)
            if rc == 0:
                os_ping = 1

        # Programming note: All attributes which do not require an ssh login
        # should have been processed by this point.
        master_req_login = ['os_login', 'os_run_cmd']
        req_login = [sub_state for sub_state in req_states if sub_state in
                     master_req_login]
        must_login = (len(req_login) > 0)

        if must_login:
            # Open SSH connection to OS.  Note that this doesn't fail even when
            # the OS is not up.
            cmd_buf = ["SSHLibrary.Open Connection", os_host]
            if not quiet:
                grp.rpissuing_keyword(cmd_buf)
            ix = BuiltIn().run_keyword(*cmd_buf)

            # Login to OS.
            cmd_buf = ["Login", os_username, os_password]
            if not quiet:
                grp.rpissuing_keyword(cmd_buf)
            status, ret_values = \
                BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
            if status == "PASS":
                os_login = 1
            else:
                gp.dprint_var(status)
                gp.dprint_var(ret_values)

            if os_login:
                if 'os_run_cmd' in req_states:
                    # Try running a simple command (uptime) on the OS.
                    cmd_buf = ["Execute Command", "uptime",
                               "return_stderr=True", "return_rc=True"]
                    if not quiet:
                        grp.rpissuing_keyword(cmd_buf)
                    # Note that in spite of its name, there are occasions
                    # where run_keyword_and_ignore_error can fail.
                    status, ret_values = \
                        BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
                    if status == "PASS":
                        stdout, stderr, rc = ret_values
                        if rc == 0 and stderr == "":
                            os_run_cmd = 1
                        else:
                            gp.dprint_var(status)
                            gp.dprint_var(stdout)
                            gp.dprint_var(stderr)
                            gp.dprint_var(rc)
                    else:
                        gp.dprint_var(status)
                        gp.dprint_var(ret_values)

    os_state = DotDict()
    for sub_state in req_states:
        cmd_buf = "os_state['" + sub_state + "'] = str(" + sub_state + ")"
        exec(cmd_buf)

    return os_state

###############################################################################


###############################################################################
def get_state(openbmc_host="",
              openbmc_username="",
              openbmc_password="",
              os_host="",
              os_username="",
              os_password="",
              req_states=default_req_states,
              quiet=None):

    r"""
    Get component states such as chassis state, bmc state, etc, put them into a
    dictionary and return them to the caller.

    Note that all substate values are strings.

    Description of arguments:
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    req_states        This is a list of states whose values are being requested
                      by the caller.
    quiet             Indicates whether status details (e.g. curl commands)
                      should be written to the console.
                      Defaults to either global value of ${QUIET} or to 1.
    """

    quiet = int(gp.get_var_value(quiet, 0))

    # Set parm defaults where necessary and validate all parms.
    if openbmc_host == "":
        openbmc_host = BuiltIn().get_variable_value("${OPENBMC_HOST}")
    error_message = gv.svalid_value(openbmc_host,
                                    var_name="openbmc_host",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if openbmc_username == "":
        openbmc_username = BuiltIn().get_variable_value("${OPENBMC_USERNAME}")
    error_message = gv.svalid_value(openbmc_username,
                                    var_name="openbmc_username",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    if openbmc_password == "":
        openbmc_password = BuiltIn().get_variable_value("${OPENBMC_PASSWORD}")
    error_message = gv.svalid_value(openbmc_password,
                                    var_name="openbmc_password",
                                    invalid_values=[None, ""])
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    # NOTE: OS parms are optional.
    if os_host == "":
        os_host = BuiltIn().get_variable_value("${OS_HOST}")
        if os_host is None:
            os_host = ""

    if os_username is "":
        os_username = BuiltIn().get_variable_value("${OS_USERNAME}")
        if os_username is None:
            os_username = ""

    if os_password is "":
        os_password = BuiltIn().get_variable_value("${OS_PASSWORD}")
        if os_password is None:
            os_password = ""

    invalid_req_states = [sub_state for sub_state in req_states
                          if sub_state not in valid_req_states]
    if len(invalid_req_states) > 0:
        error_message = "The following req_states are not supported:\n" +\
            gp.sprint_var(invalid_req_states)
        BuiltIn().fail(gp.sprint_error(error_message))

    # Initialize all substate values supported by this function.
    ping = 0
    packet_loss = ''
    uptime = ''
    epoch_seconds = ''
    rest = '1'
    chassis = ''
    bmc = ''
    boot_progress = ''
    host = ''

    # Get the component states.
    if 'ping' in req_states:
        # See if the OS pings.
        cmd_buf = "ping -c 1 -w 2 " + openbmc_host
        if not quiet:
            gp.pissuing(cmd_buf)
        rc, out_buf = commands.getstatusoutput(cmd_buf)
        if rc == 0:
            ping = 1

    if 'packet_loss' in req_states:
        # See if the OS pings.
        cmd_buf = "ping -c 5 -w 5 " + openbmc_host +\
            " | egrep 'packet loss' | sed -re 's/.* ([0-9]+)%.*/\\1/g'"
        if not quiet:
            gp.pissuing(cmd_buf)
        rc, out_buf = commands.getstatusoutput(cmd_buf)
        if rc == 0:
            packet_loss = out_buf.rstrip("\n")

    master_req_login = ['uptime', 'epoch_seconds']
    req_login = [sub_state for sub_state in req_states if sub_state in
                 master_req_login]
    must_login = (len(req_login) > 0)

    bmc_login = 0
    if must_login:
        cmd_buf = ["Open Connection And Log In"]
        if not quiet:
            grp.rpissuing_keyword(cmd_buf)
        status, ret_values = \
            BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
        if status == "PASS":
            bmc_login = 1
        else:
            if re.match('^Authentication failed for user', ret_values):
                # An authentication failure is worth failing on.
                BuiltIn().fail(gp.sprint_error(ret_values))

    if 'uptime' in req_states and bmc_login:
        cmd_buf = ["Execute Command", "cat /proc/uptime | cut -f 1 -d ' '",
                   "return_stderr=True", "return_rc=True"]
        if not quiet:
            grp.rpissuing_keyword(cmd_buf)
        status, ret_values = \
            BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
        if status == "PASS":
            stdout, stderr, rc = ret_values
            if rc == 0 and stderr == "":
                uptime = stdout

    if 'epoch_seconds' in req_states and bmc_login:
        date_cmd_buf = "date -u +%s"
        if USE_BMC_EPOCH_TIME:
            cmd_buf = ["Execute Command", date_cmd_buf, "return_stderr=True",
                       "return_rc=True"]
            if not quiet:
                grp.rpissuing_keyword(cmd_buf)
            status, ret_values = \
                BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
            if status == "PASS":
                stdout, stderr, rc = ret_values
                if rc == 0 and stderr == "":
                    epoch_seconds = stdout.rstrip("\n")
        else:
            shell_rc, out_buf = gc.cmd_fnc_u(date_cmd_buf,
                                             quiet=1,
                                             print_output=0)
            if shell_rc == 0:
                epoch_seconds = out_buf.rstrip("\n")

    master_req_rest = ['rest', 'chassis', 'bmc', 'boot_progress',
                       'host']
    req_rest = [sub_state for sub_state in req_states if sub_state in
                master_req_rest]
    need_rest = (len(req_rest) > 0)

    # Though we could try to determine 'rest' state on any of several calls,
    # for simplicity, we'll use 'chassis' to figure it out (even if the caller
    # hasn't explicitly asked for 'chassis').
    if 'chassis' in req_states or need_rest:
        cmd_buf = ["Get Chassis Power State", "quiet=${" + str(quiet) + "}"]
        grp.rdpissuing_keyword(cmd_buf)
        status, ret_values = \
            BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
        if status == "PASS":
            chassis = ret_values
            chassis = re.sub(r'.*\.', "", chassis)
            rest = '1'
        else:
            rest = ret_values

    if rest == '1':
        if 'bmc' in req_states:
            if OBMC_STATES_VERSION == 0:
                qualifier = "utils"
            else:
                # This will not be supported much longer.
                qualifier = "state_manager"
            cmd_buf = [qualifier + ".Get BMC State",
                       "quiet=${" + str(quiet) + "}"]
            grp.rdpissuing_keyword(cmd_buf)
            status, ret_values = \
                BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
            if status == "PASS":
                bmc = ret_values

        if 'boot_progress' in req_states:
            cmd_buf = ["Get Boot Progress", "quiet=${" + str(quiet) + "}"]
            grp.rdpissuing_keyword(cmd_buf)
            status, ret_values = \
                BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
            if status == "PASS":
                boot_progress = ret_values

        if 'host' in req_states:
            if OBMC_STATES_VERSION > 0:
                cmd_buf = ["Get Host State", "quiet=${" + str(quiet) + "}"]
                grp.rdpissuing_keyword(cmd_buf)
                status, ret_values = \
                    BuiltIn().run_keyword_and_ignore_error(*cmd_buf)
                if status == "PASS":
                    host = ret_values
                    # Strip everything up to the final period.
                    host = re.sub(r'.*\.', "", host)

    state = DotDict()
    for sub_state in req_states:
        if sub_state.startswith("os_"):
            # We pass "os_" requests on to get_os_state.
            continue
        cmd_buf = "state['" + sub_state + "'] = str(" + sub_state + ")"
        exec(cmd_buf)

    if os_host == "":
        # The caller has not specified an os_host so as far as we're concerned,
        # it doesn't exist.
        return state

    os_req_states = [sub_state for sub_state in req_states
                     if sub_state.startswith('os_')]

    if len(os_req_states) > 0:
        # The caller has specified an os_host and they have requested
        # information on os substates.

        # Based on the information gathered on bmc, we'll try to make a
        # determination of whether the os is even up.  We'll pass the result
        # of that assessment to get_os_state to enhance performance.
        os_up_match = DotDict()
        for sub_state in master_os_up_match:
            if sub_state in req_states:
                os_up_match[sub_state] = master_os_up_match[sub_state]
        os_up = compare_states(state, os_up_match)
        os_state = get_os_state(os_host=os_host,
                                os_username=os_username,
                                os_password=os_password,
                                req_states=os_req_states,
                                os_up=os_up,
                                quiet=quiet)
        # Append os_state dictionary to ours.
        state.update(os_state)

    return state

###############################################################################


###############################################################################
def check_state(match_state,
                invert=0,
                print_string="",
                openbmc_host="",
                openbmc_username="",
                openbmc_password="",
                os_host="",
                os_username="",
                os_password="",
                quiet=None):

    r"""
    Check that the Open BMC machine's composite state matches the specified
    state.  On success, this keyword returns the machine's composite state as a
    dictionary.

    Description of arguments:
    match_state       A dictionary whose key/value pairs are "state field"/
                      "state value".  The state value is interpreted as a
                      regular expression.  Example call from robot:
                      ${match_state}=  Create Dictionary  chassis=^On$
                      ...  bmc=^Ready$
                      ...  boot_progress=^FW Progress, Starting OS$
                      ${state}=  Check State  &{match_state}
    invert            If this flag is set, this function will succeed if the
                      states do NOT match.
    print_string      This function will print this string to the console prior
                      to getting the state.
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    quiet             Indicates whether status details should be written to the
                      console.  Defaults to either global value of ${QUIET} or
                      to 1.
    """

    quiet = int(gp.get_var_value(quiet, 0))

    grp.rprint(print_string)

    req_states = match_state.keys()
    # Initialize state.
    state = get_state(openbmc_host=openbmc_host,
                      openbmc_username=openbmc_username,
                      openbmc_password=openbmc_password,
                      os_host=os_host,
                      os_username=os_username,
                      os_password=os_password,
                      req_states=req_states,
                      quiet=quiet)
    if not quiet:
        gp.print_var(state)

    match = compare_states(state, match_state)

    if invert and match:
        fail_msg = "The current state of the machine matches the match" +\
                   " state:\n" + gp.sprint_varx("state", state)
        BuiltIn().fail("\n" + gp.sprint_error(fail_msg))
    elif not invert and not match:
        fail_msg = "The current state of the machine does NOT match the" +\
                   " match state:\n" +\
                   gp.sprint_varx("state", state)
        BuiltIn().fail("\n" + gp.sprint_error(fail_msg))

    return state

###############################################################################


###############################################################################
def wait_state(match_state=(),
               wait_time="1 min",
               interval="1 second",
               invert=0,
               openbmc_host="",
               openbmc_username="",
               openbmc_password="",
               os_host="",
               os_username="",
               os_password="",
               quiet=None):

    r"""
    Wait for the Open BMC machine's composite state to match the specified
    state.  On success, this keyword returns the machine's composite state as
    a dictionary.

    Description of arguments:
    match_state       A dictionary whose key/value pairs are "state field"/
                      "state value".  See check_state (above) for details.
                      This value may also be any string accepted by
                      return_state_constant (e.g. "standby_match_state").
                      In such a case this function will call
                      return_state_constant to convert it to a proper
                      dictionary as described above.
    wait_time         The total amount of time to wait for the desired state.
                      This value may be expressed in Robot Framework's time
                      format (e.g. 1 minute, 2 min 3 s, 4.5).
    interval          The amount of time between state checks.
                      This value may be expressed in Robot Framework's time
                      format (e.g. 1 minute, 2 min 3 s, 4.5).
    invert            If this flag is set, this function will for the state of
                      the machine to cease to match the match state.
    openbmc_host      The DNS name or IP address of the BMC.
                      This defaults to global ${OPENBMC_HOST}.
    openbmc_username  The username to be used to login to the BMC.
                      This defaults to global ${OPENBMC_USERNAME}.
    openbmc_password  The password to be used to login to the BMC.
                      This defaults to global ${OPENBMC_PASSWORD}.
    os_host           The DNS name or IP address of the operating system.
                      This defaults to global ${OS_HOST}.
    os_username       The username to be used to login to the OS.
                      This defaults to global ${OS_USERNAME}.
    os_password       The password to be used to login to the OS.
                      This defaults to global ${OS_PASSWORD}.
    quiet             Indicates whether status details should be written to the
                      console.  Defaults to either global value of ${QUIET} or
                      to 1.
    """

    quiet = int(gp.get_var_value(quiet, 0))

    if type(match_state) in (str, unicode):
        match_state = return_state_constant(match_state)

    if not quiet:
        if invert:
            alt_text = "cease to "
        else:
            alt_text = ""
        gp.print_timen("Checking every " + str(interval) + " for up to " +
                       str(wait_time) + " for the state of the machine to " +
                       alt_text + "match the state shown below.")
        gp.print_var(match_state)

    if quiet:
        print_string = ""
    else:
        print_string = "#"

    debug = int(BuiltIn().get_variable_value("${debug}", "0"))
    if debug:
        # In debug we print state so no need to print the "#".
        print_string = ""
    check_state_quiet = 1 - debug
    cmd_buf = ["Check State", match_state, "invert=${" + str(invert) + "}",
               "print_string=" + print_string, "openbmc_host=" + openbmc_host,
               "openbmc_username=" + openbmc_username,
               "openbmc_password=" + openbmc_password, "os_host=" + os_host,
               "os_username=" + os_username, "os_password=" + os_password,
               "quiet=${" + str(check_state_quiet) + "}"]
    grp.rdpissuing_keyword(cmd_buf)
    try:
        state = BuiltIn().wait_until_keyword_succeeds(wait_time, interval,
                                                      *cmd_buf)
    except AssertionError as my_assertion_error:
        gp.printn()
        message = my_assertion_error.args[0]
        BuiltIn().fail(message)

    if not quiet:
        gp.printn()
        if invert:
            gp.print_timen("The states no longer match:")
        else:
            gp.print_timen("The states match:")
        gp.print_var(state)

    return state

###############################################################################


###############################################################################
def wait_for_comm_cycle(start_boot_seconds,
                        quiet=None):

    r"""
    Wait for communications to the BMC to stop working and then resume working.
    This function is useful when you have initiated some kind of reboot.

    Description of arguments:
    start_boot_seconds  The time that the boot test started.  The format is the
                        epoch time in seconds, i.e. the number of seconds since
                        1970-01-01 00:00:00 UTC.  This value should be obtained
                        from the BMC so that it is not dependent on any kind of
                        synchronization between this machine and the target BMC
                        This will allow this program to work correctly even in
                        a simulated environment.  This value should be obtained
                        by the caller prior to initiating a reboot.  It can be
                        obtained as follows:
                        state = st.get_state(req_states=['epoch_seconds'])
    """

    quiet = int(gp.get_var_value(quiet, 0))

    # Validate parms.
    error_message = gv.svalid_integer(start_boot_seconds,
                                      var_name="start_boot_seconds")
    if error_message != "":
        BuiltIn().fail(gp.sprint_error(error_message))

    match_state = anchor_state(DotDict([('packet_loss', '100')]))
    # Wait for 100% packet loss trying to ping machine.
    wait_state(match_state, wait_time="8 mins", interval="0 seconds")

    match_state['packet_loss'] = '^0$'
    # Wait for 0% packet loss trying to ping machine.
    wait_state(match_state, wait_time="8 mins", interval="0 seconds")

    # Get the uptime and epoch seconds for comparisons.  We want to be sure
    # that the uptime is less than the elapsed boot time.  Further proof that
    # a reboot has indeed occurred (vs random network instability giving a
    # false positive.
    state = get_state(req_states=['uptime', 'epoch_seconds'], quiet=quiet)

    elapsed_boot_time = int(state['epoch_seconds']) - start_boot_seconds
    gp.qprint_var(elapsed_boot_time)
    if int(float(state['uptime'])) < elapsed_boot_time:
        uptime = state['uptime']
        gp.qprint_var(uptime)
        gp.qprint_timen("The uptime is less than the elapsed boot time," +
                        " as expected.")
    else:
        error_message = "The uptime is greater than the elapsed boot time," +\
                        " which is unexpected:\n" +\
                        gp.sprint_var(start_boot_seconds) +\
                        gp.sprint_var(state)
        BuiltIn().fail(gp.sprint_error(error_message))

    gp.qprint_timen("Verifying that REST API interface is working.")
    match_state = DotDict([('rest', '^1$')])
    state = wait_state(match_state, wait_time="5 mins", interval="2 seconds")

###############################################################################
