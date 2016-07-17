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

import logging
from boto3 import client
from datetime import datetime

logger = logging.getLogger(__name__)


class AWSInfo(object):

    def __init__(self, config):
        self.config = config

    def show_cloudwatch_logs(self, count=10):
        """
        Show ``count`` latest CloudWatch Logs entries for our lambda function.

        :param count: number of log entries to show
        :type count: int
        """
        grp_name = '/aws/lambda/%s' % self.config.func_name
        logger.debug('Log Group Name: %s', grp_name)
        logger.debug('Connecting to AWS Logs API')
        conn = client('logs')
        logger.debug('Getting log streams')
        streams = conn.describe_log_streams(
            logGroupName=grp_name,
            orderBy='LastEventTime',
            descending=True,
            limit=count  # at worst, we have 1 event per stream
        )
        logger.debug('Found %d log streams', len(streams['logStreams']))
        shown = 0
        for stream in streams['logStreams']:
            if (count - shown) < 1:
                break
            shown += self._show_log_stream(conn, grp_name,
                                           stream['logStreamName'],
                                           (count - shown))

    def _show_log_stream(self, conn, grp_name, stream_name, max_count=10):
        """
        Show up to ``max`` events from a specified log stream; return the
        number of events shown.

        :param conn: AWS Logs API connection
        :type conn: botocore.client.CloudWatchLogs
        :param grp_name: log group name
        :type grp_name: str
        :param stream_name: log stream name
        :type stream_name: str
        :param max_count: maximum number of events to show
        :type max_count: int
        :return: count of events shown
        :rtype: int
        """
        logger.debug('Showing up to %d events from stream %s',
                     max_count, stream_name)
        events = conn.get_log_events(
            logGroupName=grp_name,
            logStreamName=stream_name,
            limit=max_count,
            startFromHead=False
        )
        if len(events['events']) > 0:
            print('## Log Group \'%s\'; Log Stream \'%s\'' % (
                grp_name, stream_name))
        shown = 0
        for evt in events['events']:
            shown += 1
            dt = datetime.fromtimestamp(evt['timestamp'] / 1000.0)
            print("%s => %s" % (dt, evt['message'].strip()))
        logger.debug('displayed %d events from stream', shown)
        return shown

    def show_queue(self, name=None, count=10, delete=False):
        pass
