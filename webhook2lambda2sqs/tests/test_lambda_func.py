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

from webhook2lambda2sqs.lambda_func import webhook2lambda2sqs_handler

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


class TestLambdaFunc(object):

    def test_basic(self):
        ep = {'foo': 'bar'}
        evt = {u'key3': u'value3', u'key2': u'value2', u'key1': u'value1'}
        context = Mock(
            aws_request_id='myreqid',
            log_stream_name='LogStreamName',
            invoked_function_arn='myarn',
            client_context=None,
            log_group_name='/aws/lambda/fname',
            function_name='fname',
            function_version='$LATEST',
            identity=Mock(),
            memory_limit_in_mb='128'
        )
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.endpoints' % pbm, ep):
                webhook2lambda2sqs_handler(evt, context)
        assert mock_logger.mock_calls == [
            call.debug('Endpoint Config: %s', {'foo': 'bar'}),
            call.debug('Event: %s', evt),
            call.debug('Context: %s', vars(context))
        ]

    def test_basic_no_context(self):
        ep = {'foo': 'bar'}
        evt = {u'key3': u'value3', u'key2': u'value2', u'key1': u'value1'}
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.endpoints' % pbm, ep):
                webhook2lambda2sqs_handler(evt, None)
        assert mock_logger.mock_calls == [
            call.debug('Endpoint Config: %s', {'foo': 'bar'}),
            call.debug('Event: %s', evt),
            call.info('Error dumping context vars', excinfo=1)
        ]
