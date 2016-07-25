"""
This tests the skeleton of the generated lambda function.

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
import sys
from copy import deepcopy
import pytest
import json

from webhook2lambda2sqs.lambda_func import (
    webhook2lambda2sqs_handler, handle_event, serializable_dict,
    try_enqueue, queues_for_endpoint, msg_body_for_event
)
from webhook2lambda2sqs.tests.support import exc_msg

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 'webhook2lambda2sqs.lambda_func'


class MockContext(object):
    aws_request_id = 'fcf275fa-51fe-11e6-9058-c9225d69789a'
    client_context = None
    function_name = 'webhook2lambda2sqsintegrtest'
    function_version = '$LATEST'
    invoked_function_arn = 'arn:aws:lambda:us-east-1:423319072129:' \
                           'function:webhook2lambda2sqsintegrtest'
    log_group_name = '/aws/lambda/webhook2lambda2sqsintegrtest'
    log_stream_name = '2016/07/25/[$LATEST]a8187b7fecbc4c3bbb8b60c43bfafc5a'
    memory_limit_in_mb = '128'


class TestLambdaFunc(object):

    def setup(self):
        self.mock_context = MockContext()
        self.mock_event = {
            'body-json': {},
            'context': {
                'account-id': '',
                'api-id': 'f8f89f3f',
                'api-key': '',
                'authorizer-principal-id': '',
                'caller': '',
                'cognito-authentication-provider': '',
                'cognito-authentication-type': '',
                'cognito-identity-id': '',
                'cognito-identity-pool-id': '',
                'http-method': 'GET',
                'request-id': 'fce66768-51fe-11e6-8a66-ffd96137a54e',
                'resource-id': 'h8tfr6',
                'resource-path': '/foo',
                'source-ip': '24.98.0.0',
                'stage': 'webhook2lambda2sqs',
                'user': '',
                'user-agent': 'python-requests/2.10.0',
                'user-arn': ''
            },
            'params': {
                'header': {
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'CloudFront-Forwarded-Proto': 'https',
                    'CloudFront-Is-Desktop-Viewer': 'true',
                    'CloudFront-Is-Mobile-Viewer': 'false',
                    'CloudFront-Is-SmartTV-Viewer': 'false',
                    'CloudFront-Is-Tablet-Viewer': 'false',
                    'CloudFront-Viewer-Country': 'US',
                    'Host': '8u398f3.execute-api.us-east-1.amazonaws.com',
                    'User-Agent': 'python-requests/2.10.0',
                    'Via': '1.1 b4462bd98dd9186cca8c54d37f70d629.'
                           'cloudfront.net (CloudFront)',
                    'X-Amz-Cf-Id': 'iWHI2ekmJcWJd_5j3bgms1oP8YcqUdD3'
                                   'qMgjXZ7HLWSDH7lPPqp-mw==',
                    'X-Forwarded-For': '24.98.0.0, 54.239.0.0',
                    'X-Forwarded-Port': '443',
                    'X-Forwarded-Proto': 'https'
                },
                'path': {},
                'querystring': {
                    'method': 'foo',
                    'run_id': '98765'
                }
            },
            'stage-variables': {}
        }
        self.endpoints = {
            'foo': {
                'method': 'GET',
                'queues': ['q1']
            },
            'bar': {
                'method': 'POST',
                'queues': ['q2']
            },
            'fail': {
                'method': 'POST',
                'queues': ['q3']
            }
        }

    def test_webhook2lambda2sqs_handler(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.handle_event' % pbm, autospec=True) as mock_handle:
                mock_handle.return_value = {
                    'foo': 'bar',
                    'SQSMessageIds': [1, 2]
                }
                with patch('%s.endpoints' % pbm, self.endpoints):
                    res = webhook2lambda2sqs_handler(self.mock_event,
                                                     self.mock_context)
        assert res == {'foo': 'bar', 'SQSMessageIds': [1, 2]}
        assert mock_handle.mock_calls == [
            call(self.mock_event, self.mock_context)
        ]
        assert mock_logger.mock_calls == [
            call.debug('handle_event() result: %s',
                       {'foo': 'bar', 'SQSMessageIds': [1, 2]})
        ]

    def test_webhook2lambda2sqs_handler_no_updates(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.handle_event' % pbm, autospec=True) as mock_handle:
                mock_handle.return_value = {
                    'foo': 'bar',
                    'SQSMessageIds': []
                }
                with patch('%s.endpoints' % pbm, self.endpoints):
                    with pytest.raises(Exception) as excinfo:
                        webhook2lambda2sqs_handler(self.mock_event,
                                                   self.mock_context)
        assert exc_msg(excinfo.value) == 'Failed enqueueing all messages'
        assert mock_handle.mock_calls == [
            call(self.mock_event, self.mock_context)
        ]
        assert mock_logger.mock_calls == [
            call.debug('handle_event() result: %s',
                       {'foo': 'bar', 'SQSMessageIds': []})
        ]

    def test_webhook2lambda2sqs_handler_exception(self):

        def se_exc(*args):
            raise Exception('foo')

        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.handle_event' % pbm, autospec=True) as mock_handle:
                mock_handle.side_effect = se_exc
                with patch('%s.endpoints' % pbm, self.endpoints):
                    with pytest.raises(Exception) as excinfo:
                        webhook2lambda2sqs_handler(self.mock_event,
                                                   self.mock_context)
        assert exc_msg(excinfo.value) == 'foo'
        assert mock_handle.mock_calls == [
            call(self.mock_event, self.mock_context)
        ]
        assert mock_logger.mock_calls == [
            call.error('Error handling event; event=%s context=%s',
                       self.mock_event, vars(self.mock_context), exc_info=1)
        ]

    def test_queues_for_endpoint(self):
        with patch('%s.endpoints' % pbm, self.endpoints):
            res = queues_for_endpoint(self.mock_event)
        assert res == ['q1']

    def test_queues_for_endpoint_exception(self):
        self.mock_event['context']['resource-path'] = '/wrong'
        with patch('%s.endpoints' % pbm, self.endpoints):
            with pytest.raises(Exception) as excinfo:
                queues_for_endpoint(self.mock_event)
        assert exc_msg(excinfo.value) == 'Endpoint not in configuration: /wrong'

    def test_msg_body_for_event_GET(self):
        self.mock_event['context']['http-method'] = 'GET'
        self.mock_event['params']['querystring'] = {
            'method': 'foo',
            'run_id': '98765'
        }
        res = msg_body_for_event(self.mock_event, self.mock_context)
        assert res == json.dumps({
            'data': {
                'method': 'foo',
                'run_id': '98765'
            },
            'event': self.mock_event,
            'context': vars(self.mock_context)
        }, sort_keys=True)

    def test_msg_body_for_event_POST(self):
        self.mock_event['context']['http-method'] = 'POST'
        self.mock_event['params']['querystring'] = {}
        self.mock_event['body-json'] = {
            'method': 'foo',
            'run_id': '98765'
        }
        res = msg_body_for_event(self.mock_event, self.mock_context)
        assert res == json.dumps({
            'data': {
                'method': 'foo',
                'run_id': '98765'
            },
            'event': self.mock_event,
            'context': vars(self.mock_context)
        }, sort_keys=True)

    def test_handle_event(self):

        def se_enqueue(conn, qname, msg):
            if qname == 'q1':
                return 'msgid1'
            if qname == 'q2':
                raise Exception('foo')
            if qname == 'q3':
                return 'msgid3'
            return 'othermsgid'

        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            queues_for_endpoint=DEFAULT,
            msg_body_for_event=DEFAULT,
            boto3=DEFAULT,
            try_enqueue=DEFAULT
        ) as mocks:
            mocks['queues_for_endpoint'].return_value = ['q1', 'q2', 'q3']
            mocks['msg_body_for_event'].return_value = 'mybody'
            mocks['try_enqueue'].side_effect = se_enqueue
            res = handle_event(self.mock_event, self.mock_context)
        assert res == {
            'status': 'partial',
            'message': 'enqueued 2 messages; 1 failed',
            'SQSMessageIds': ['msgid1', 'msgid3']
        }
        assert mocks['queues_for_endpoint'].mock_calls == [
            call(self.mock_event)
        ]
        assert mocks['msg_body_for_event'].mock_calls == [
            call(self.mock_event, self.mock_context)
        ]
        assert mocks['try_enqueue'].mock_calls == [
            call(mocks['boto3'].client.return_value, 'q1', 'mybody'),
            call(mocks['boto3'].client.return_value, 'q2', 'mybody'),
            call(mocks['boto3'].client.return_value, 'q3', 'mybody'),
        ]
        assert mocks['boto3'].mock_calls == [
            call.client('sqs')
        ]
        assert mocks['logger'].mock_calls == [
            call.error('Failed enqueueing message in %s:', 'q2', exc_info=1)
        ]

    def test_handle_event_success(self):
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            queues_for_endpoint=DEFAULT,
            msg_body_for_event=DEFAULT,
            boto3=DEFAULT,
            try_enqueue=DEFAULT
        ) as mocks:
            mocks['queues_for_endpoint'].return_value = ['q1']
            mocks['msg_body_for_event'].return_value = 'mybody'
            mocks['try_enqueue'].return_value = 'msgid'
            res = handle_event(self.mock_event, self.mock_context)
        assert res == {
            'status': 'success',
            'message': 'enqueued 1 messages',
            'SQSMessageIds': ['msgid']
        }
        assert mocks['queues_for_endpoint'].mock_calls == [
            call(self.mock_event)
        ]
        assert mocks['msg_body_for_event'].mock_calls == [
            call(self.mock_event, self.mock_context)
        ]
        assert mocks['try_enqueue'].mock_calls == [
            call(mocks['boto3'].client.return_value, 'q1', 'mybody')
        ]
        assert mocks['boto3'].mock_calls == [
            call.client('sqs')
        ]
        assert mocks['logger'].mock_calls == []

    def test_try_enqueue(self):
        mock_conn = Mock()
        mock_conn.get_queue_url.return_value = {'QueueUrl': 'qurl'}
        mock_conn.send_message.return_value = {'MessageId': '123abc'}
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            res = try_enqueue(mock_conn, 'qname', 'foo bar')
        assert res == '123abc'
        assert mock_conn.mock_calls == [
            call.get_queue_url(QueueName='qname'),
            call.send_message(QueueUrl='qurl', MessageBody='foo bar',
                              DelaySeconds=0)
        ]
        assert mock_logger.mock_calls == [
            call.debug('Getting Queue URL for queue %s', 'qname'),
            call.debug('Sending message to queue at: %s', 'qurl'),
            call.debug('Enqueued message in %s with ID %s', 'qname', '123abc')
        ]

    def test_serializable_dict(self):
        expected_dict = {
            'one': 1,
            'two': 'two',
            'four': {'five': 5, 'six': [1, 2, "three"]}
        }
        in_dict = deepcopy(expected_dict)
        in_dict['three'] = Mock()
        in_dict['four']['seven'] = Mock()
        assert serializable_dict(in_dict) == expected_dict
