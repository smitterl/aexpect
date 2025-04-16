# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.

"""Some shared functions"""

import os
import fcntl
import termios
import logging
import threading

LOG = logging.getLogger(__name__)
BASE_DIR = os.environ.get('TMPDIR', '/tmp')


def get_lock_fd(filename):
    """Lock a file"""
    LOG.debug("SM - get_lock_fd")
    LOG.debug(f"(pid, thread) ({os.getpid()},{threading.get_ident()})")
    if not os.path.exists(filename):
        LOG.debug(f"(pid, thread) ({os.getpid()},{threading.get_ident()})")
        LOG.debug(f"SM - will create {filename}")
        with open(filename, "w", encoding="utf-8"):
            pass
    LOG.debug(f"SM - try open file {filename}")
    lock_fd = os.open(filename, os.O_RDWR)
    LOG.debug("SM - try get exclusive lock")
    fcntl.lockf(lock_fd, fcntl.LOCK_EX)
    LOG.debug("SM - Lock obtained, return")
    return lock_fd


def unlock_fd(lock_fd):
    """Unlock a file"""
    LOG.debug("SM - try unlock")
    LOG.debug(f"(pid, thread) ({os.getpid()},{threading.get_ident()})")
    fcntl.lockf(lock_fd, fcntl.LOCK_UN)
    LOG.debug("SM - close fd")
    os.close(lock_fd)
    LOG.debug("SM - closed - return")


def is_file_locked(filename):
    """Check whether file is currently locked"""
    try:
        lock_fd = os.open(filename, os.O_RDWR)
    except OSError:
        return False
    try:
        fcntl.lockf(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        os.close(lock_fd)
        return True
    fcntl.lockf(lock_fd, fcntl.LOCK_UN)
    os.close(lock_fd)
    return False


def wait_for_lock(filename):
    """Wait until lock can be acquired, then release it"""
    lock_fd = get_lock_fd(filename)
    unlock_fd(lock_fd)


def makeraw(shell_fd):
    """Turn console into 'raw' format"""
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~(termios.IGNBRK | termios.BRKINT | termios.PARMRK |
                 termios.ISTRIP | termios.INLCR | termios.IGNCR |
                 termios.ICRNL | termios.IXON)
    attr[1] &= ~termios.OPOST
    attr[2] &= ~(termios.CSIZE | termios.PARENB)
    attr[2] |= termios.CS8
    attr[3] &= ~(termios.ECHO | termios.ECHONL | termios.ICANON |
                 termios.ISIG | termios.IEXTEN)
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def makestandard(shell_fd, echo):
    """Turn console into 'normal' mode"""
    attr = termios.tcgetattr(shell_fd)
    attr[0] &= ~termios.INLCR
    attr[0] &= ~termios.ICRNL
    attr[0] &= ~termios.IGNCR
    attr[1] &= ~termios.OPOST
    if echo:
        attr[3] |= termios.ECHO
    else:
        attr[3] &= ~termios.ECHO
    termios.tcsetattr(shell_fd, termios.TCSANOW, attr)


def get_filenames(base_dir):
    """Get paths to files produced by aexpect in it's working dir"""
    files = ("shell-pid", "status", "output", "inpipe", "ctrlpipe",
             "lock-server-running", "lock-client-starting",
             "server-log")
    return [os.path.join(base_dir, s) for s in files]


def get_reader_filename(base_dir, reader):
    """Return path to pipe of the associated reader"""
    return os.path.join(base_dir, f"outpipe-{reader}")
