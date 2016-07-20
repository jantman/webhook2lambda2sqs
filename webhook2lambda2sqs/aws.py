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
from pprint import pprint

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
            if shown >= max_count:
                break
            shown += 1
            dt = datetime.fromtimestamp(evt['timestamp'] / 1000.0)
            print("%s => %s" % (dt, evt['message'].strip()))
        logger.debug('displayed %d events from stream', shown)
        return shown

    def _url_for_queue(self, conn, name):
        """
        Given a queue name, return the URL for it.

        :param conn: SQS API connection
        :type conn: botocore.client.SQS
        :param name: queue name, or None for all queues in config.
        :type name: str
        :return: queue URL
        :rtype: str
        """
        res = conn.get_queue_url(QueueName=name)
        return res['QueueUrl']

    def _delete_msg(self, conn, queue_url, receipt_handle):
        """
        Delete the message specified by ``receipt_handle`` in the queue
        specified by ``queue_url``.

        :param conn: SQS API connection
        :type conn: botocore.client.SQS
        :param queue_url: queue URL to delete the message from
        :type queue_url: str
        :param receipt_handle: message receipt handle
        :type receipt_handle: str
        """
        resp = conn.delete_message(QueueUrl=queue_url,
                                   ReceiptHandle=receipt_handle)
        if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
            logger.error('Error: message with receipt handle %s in queue %s '
                         'was not successfully deleted (HTTP %s)',
                         receipt_handle, queue_url,
                         resp['ResponseMetadata']['HTTPStatusCode'])
            return
        logger.info('Message with receipt handle %s deleted from queue %s',
                    receipt_handle, queue_url)

    def _show_one_queue(self, conn, name, count, delete=False):
        """
        Show ``count`` messages from the specified SQS queue.

        :param conn: SQS API connection
        :type conn: botocore.client.SQS
        :param name: queue name, or None for all queues in config.
        :type name: str
        :param count: maximum number of messages to get from queue
        :type count: int
        :param delete: whether or not to delete messages after receipt
        :type delete: bool
        """
        url = self._url_for_queue(conn, name)
        logger.debug("Queue '%s' url: %s", name, url)
        logger.warning('Receiving %d messages from queue\'%s\'; this may take '
                       'up to 20 seconds.', count, name)
        msgs = conn.receive_message(
            QueueUrl=url,
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=count,
            WaitTimeSeconds=20
        )
        if 'Messages' not in msgs:
            logger.debug('received no messages')
            print('=> Queue \'%s\' appears empty.' % name)
            return
        logger.debug('received %d messages', len(msgs['Messages']))
        print('=> Queue \'%s\' (%s)' % (name, url))
        if len(msgs['Messages']) > count:
            msgs['Messages'] = msgs['Messages'][:count]
        for m in msgs['Messages']:
            pprint(m)
            if delete:
                self._delete_msg(conn, url, m['ReceiptHandle'])

    @property
    def _all_queue_names(self):
        """
        Return a list of all unique queue names in our config.

        :return: list of all queue names (str)
        :rtype: list
        """
        queues = set()
        endpoints = self.config.get('endpoints')
        for e in endpoints:
            for q in endpoints[e]['queues']:
                queues.add(q)
        return sorted(queues)

    def show_queue(self, name=None, count=10, delete=False):
        """
        Show up to ``count`` messages from the queue named ``name``. If ``name``
        is None, show for each queue in our config. If ``delete`` is True,
        delete the messages after showing them.

        :param name: queue name, or None for all queues in config.
        :type name: str
        :param count: maximum number of messages to get from queue
        :type count: int
        :param delete: whether or not to delete messages after receipt
        :type delete: bool
        """
        if count > 10:
            raise Exception('Error: currently this script only supports '
                            'receiving 10 or fewer messages per queue.')
        logger.debug('Connecting to SQS API')
        conn = client('sqs')
        if name is not None:
            self._show_one_queue(conn, name, count, delete=delete)
            return
        for q_name in self._all_queue_names:
            self._show_one_queue(conn, q_name, count, delete=delete)

    def get_api_base_url(self):
        """
        Return the base URL to the API.

        :return: API base url
        :rtype: str
        """
        logger.debug('Connecting to AWS apigateway API')
        conn = client('apigateway')
        apis = conn.get_rest_apis()
        api_id = None
        for api in apis['items']:
            if api['name'] == self.config.func_name:
                api_id = api['id']
                logger.debug('Found API id: %s', api_id)
                break
        if api_id is None:
            raise Exception('Unable to find ReST API named %s' %
                            self.config.func_name)
        return 'https://%s.execute-api.%s.amazonaws.com/%s/' % (
            api_id, conn._client_config.region_name, 'webhook2lambda2sqs'
        )
