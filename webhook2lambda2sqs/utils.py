"""
The latest version of this package is available at:
<http://github.com/jantman/webhook2lambda2sqs>

################################################################################
Copyright 2016 Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>

    This file is part of webhook2lambda2sqs, also known as webhook2lambda2sqs.

    webhook2lambda2sqs is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    webhook2lambda2sqs is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with webhook2lambda2sqs.  If not, see <http://www.gnu.org/licenses/>.

The Copyright and Authors attributions contained herein may not be removed or
otherwise altered, except to add the Author attribution of a contributor to
this work. (Additional Terms pursuant to Section 7b of the AGPL v3)
################################################################################
While not legally required, I sincerely request that anyone who finds
bugs please submit them at <https://github.com/jantman/webhook2lambda2sqs> or
to me via email, and that you send any contributions or improvements
either as a pull request on GitHub, or to me via email.
################################################################################

AUTHORS:
Jason Antman <jason@jasonantman.com> <http://www.jasonantman.com>
################################################################################
"""

import json
import logging
import subprocess
import sys
import os

logger = logging.getLogger(__name__)


def read_json_file(fpath):
    """
    Read a JSON file from ``fpath``; raise an exception if it doesn't exist.

    :param fpath: path to file to read
    :type fpath: str
    :return: deserialized JSON
    :rtype: dict
    """
    if not os.path.exists(fpath):
        raise Exception('ERROR: file %s does not exist.' % fpath)
    with open(fpath, 'r') as fh:
        raw = fh.read()
    res = json.loads(raw)
    return res


def pretty_json(obj):
    """
    Given an object, return a pretty-printed JSON representation of it.

    :param obj: input object
    :type obj: object
    :return: pretty-printed JSON representation
    :rtype: str
    """
    return json.dumps(obj, sort_keys=True, indent=4)


def run_cmd(args, stream=False, shell=True):
    """
    Execute a command via :py:class:`subprocess.Popen`; return its output
    (string, combined STDOUT and STDERR) and exit code (int). If stream is True,
    also stream the output to STDOUT in realtime.

    :param args: the command to run and arguments, as a list or string
    :param stream: whether or not to stream combined OUT and ERR in realtime
    :type stream: bool
    :param shell: whether or not to execute the command through the shell
    :type shell: bool
    :return: 2-tuple of (combined output (str), return code (int))
    :rtype: tuple
    """
    s = ''
    if stream:
        s = ' and streaming output'
    logger.info('Running command%s: %s', s, args)
    outbuf = ''
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=shell)
    logger.debug('Started process; pid=%s', p.pid)
    for c in iter(lambda: p.stdout.read(1), ''):
        outbuf += c
        if stream:
            sys.stdout.write(c)
    p.poll()  # set returncode
    logger.info('Command exited with code %d', p.returncode)
    logger.debug("Command output:\n%s", outbuf)
    return outbuf, p.returncode
