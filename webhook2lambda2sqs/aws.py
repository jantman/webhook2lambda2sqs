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
import json
from pprint import pformat

from webhook2lambda2sqs.utils import pretty_json

logger = logging.getLogger(__name__)


class AWSInfo(object):

    # API Gateway Stage methodSetting paths
    # These have '%s' as a placeholder for the method_setting_key
    _method_setting_paths = {
        'metricsEnabled': '/%s/metrics/enabled',
        'loggingLevel': '/%s/logging/loglevel',
        'dataTraceEnabled': '/%s/logging/dataTrace',
        'throttlingBurstLimit': '/%s/throttling/burstLimit',
        'throttlingRateLimit': '/%s/throttling/rateLimit'
    }

    def __init__(self, config):
        self.config = config

    def show_cloudwatch_logs(self, count=10, grp_name=None):
        """
        Show ``count`` latest CloudWatch Logs entries for our lambda function.

        :param count: number of log entries to show
        :type count: int
        """
        if grp_name is None:
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
        :type conn: :py:class:`botocore:CloudWatchLogs.Client`
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
        :type conn: :py:class:`botocore:SQS.Client`
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
        :type conn: :py:class:`botocore:SQS.Client`
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
        :type conn: :py:class:`botocore:SQS.Client`
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
        if not delete:
            logger.warning("WARNING: Displayed messages will be invisible in "
                           "queue for 60 seconds!")
        seen_ids = []
        all_msgs = []
        empty_polls = 0
        # continue getting messages until we get 2 empty polls in a row
        while empty_polls < 2 and len(all_msgs) < count:
            logger.debug('Polling queue %s for messages (empty_polls=%d)',
                         name, empty_polls)
            msgs = conn.receive_message(
                QueueUrl=url,
                AttributeNames=['All'],
                MessageAttributeNames=['All'],
                MaxNumberOfMessages=count,
                VisibilityTimeout=60,
                WaitTimeSeconds=20
            )
            if 'Messages' in msgs and len(msgs['Messages']) > 0:
                empty_polls = 0
                logger.debug("Queue %s - got %d messages", name,
                             len(msgs['Messages']))
                for m in msgs['Messages']:
                    if m['MessageId'] in seen_ids:
                        continue
                    seen_ids.append(m['MessageId'])
                    all_msgs.append(m)
                continue
            # no messages found
            logger.debug('Queue %s - got no messages', name)
            empty_polls += 1
        logger.debug('received %d messages', len(all_msgs))
        if len(all_msgs) == 0:
            print('=> Queue \'%s\' appears empty.' % name)
            return
        print("=> Queue '%s' (%s)" % (name, url))
        if len(all_msgs) > count:
            all_msgs = all_msgs[:count]
        for m in all_msgs:
            try:
                m['Body'] = json.loads(m['Body'])
            except Exception:
                pass
            print(pretty_json(m))
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
        logger.debug('Connecting to SQS API')
        conn = client('sqs')
        if name is not None:
            queues = [name]
        else:
            queues = self._all_queue_names
        for q_name in queues:
            try:
                self._show_one_queue(conn, q_name, count, delete=delete)
            except Exception:
                logger.error("Error showing queue '%s'", q_name, exc_info=1)

    def get_api_base_url(self):
        conn = client('apigateway')
        api_id = self.get_api_id()
        return 'https://%s.execute-api.%s.amazonaws.com/%s/' % (
                api_id, conn._client_config.region_name, self.config.stage_name
            )

    def get_api_id(self):
        """
        Return the API ID.

        :return: API ID
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
        return api_id

    def set_method_settings(self):
        """
        Set the Method settings <https://docs.aws.amazon.com/apigateway/api-\
reference/resource/stage/#methodSettings> on our Deployment Stage.
        This is currently not supported by Terraform; see <https://github.com/\
jantman/webhook2lambda2sqs/issues/7> and <https://github.com/hashicorp\
/terraform/issues/6612>.

        Calls :py:meth:`~._add_method_setting` for each setting that is not
        currently correct.
        """
        settings = self.config.get('api_gateway_method_settings')
        if settings is None:
            logger.debug('api_gateway_method_settings not set in config')
            return
        logger.info('Setting API Gateway Stage methodSettings')
        api_id = self.get_api_id()
        stage_name = self.config.stage_name
        logger.debug('Connecting to AWS apigateway API')
        conn = client('apigateway')
        logger.debug('Getting Stage configuration: api_id=%s stage_name=%s',
                     api_id, stage_name)
        stage = conn.get_stage(restApiId=api_id, stageName=stage_name)
        logger.debug("Got stage config: \n%s", pformat(stage))
        # hack for stages that have had no method settings applied yet
        if '*/*' not in stage['methodSettings']:
            stage['methodSettings']['*/*'] = {}
        curr_settings = stage['methodSettings']['*/*']
        for k, v in sorted(settings.items()):
            if k in curr_settings and curr_settings[k] == v:
                logger.debug('methodSetting "%s" is correct (%s)', k, v)
                continue
            # else update the value; note that the API doesn't actually follow
            # https://tools.ietf.org/html/rfc6902#section-4 and doesn't seem
            # to actually accept 'add' for these.
            op = 'replace'
            if k not in curr_settings:
                logger.debug('Adding new methodSetting "%s" value %s', k, v)
            else:
                logger.debug('Updating methodSetting "%s" from %s to %s',
                             k, curr_settings[k], v)
            self._add_method_setting(conn, api_id, stage_name,
                                     self._method_setting_paths[k] % '*/*',
                                     k, v, op)

    def _add_method_setting(self, conn, api_id, stage_name, path, key, value,
                            op):
        """
        Update a single method setting on the specified stage. This uses the
        'add' operation to PATCH the resource.

        :param conn: APIGateway API connection
        :type conn: :py:class:`botocore:APIGateway.Client`
        :param api_id: ReST API ID
        :type api_id: str
        :param stage_name: stage name
        :type stage_name: str
        :param path: path to patch (see https://docs.aws.amazon.com/apigateway/\
api-reference/resource/stage/#methodSettings)
        :type path: str
        :param key: the dictionary key this should update
        :type key: str
        :param value: new value to set
        :param op: PATCH operation to perform, 'add' or 'replace'
        :type op: str
        """
        logger.debug('update_stage PATCH %s on %s; value=%s',
                     op, path, str(value))
        res = conn.update_stage(
            restApiId=api_id,
            stageName=stage_name,
            patchOperations=[
                {
                    'op': op,
                    'path': path,
                    'value': str(value)
                }
            ]
        )
        if res['methodSettings']['*/*'][key] != value:
            logger.error('methodSettings PATCH expected to update %s to %s,'
                         'but instead found value as %s', key, value,
                         res['methodSettings']['*/*'][key])
        else:
            logger.info('Successfully updated methodSetting %s to %s',
                        key, value)
