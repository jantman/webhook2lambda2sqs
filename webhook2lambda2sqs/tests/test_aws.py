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

import sys

from webhook2lambda2sqs.aws import AWSInfo

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT  # noqa

pbm = 'webhook2lambda2sqs.aws'
pb = '%s.AWSInfo' % pbm


class TestAWSInfo(object):

    def setup(self):
        self.conf = {}

        def se_get(k):
            return self.conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        type(config).func_name = 'myfname'
        self.cls = AWSInfo(config)

    def test_init(self):
        c = Mock()
        cls = AWSInfo(c)
        assert cls.config == c

    def test_show_cloudwatch_logs(self, capsys):
        resp = {
            'logStreams': [
                {'logStreamName': 's1'},
                {'logStreamName': 's2'},
                {'logStreamName': 's3'}
            ]
        }
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_conn:
                with patch('%s._show_log_stream' % pb, autospec=True) as sls:
                    mock_conn.return_value.describe_log_streams.return_value = \
                        resp
                    sls.side_effect = [1, 10]
                    self.cls.show_cloudwatch_logs(5)
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''
        assert mock_conn.mock_calls == [
            call('logs'),
            call().describe_log_streams(descending=True, limit=5,
                                        logGroupName='/aws/lambda/myfname',
                                        orderBy='LastEventTime')
        ]
        assert sls.mock_calls == [
            call(self.cls,
                 mock_conn.return_value, '/aws/lambda/myfname', 's1', 5),
            call(self.cls,
                 mock_conn.return_value, '/aws/lambda/myfname', 's2', 4),
        ]
        assert mock_logger.mock_calls == [
            call.debug('Log Group Name: %s', '/aws/lambda/myfname'),
            call.debug('Connecting to AWS Logs API'),
            call.debug('Getting log streams'),
            call.debug('Found %d log streams', 3)
        ]
