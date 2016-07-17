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
import json
from freezegun import freeze_time
from zipfile import ZipInfo

from webhook2lambda2sqs.tf_generator import TerraformGenerator
from webhook2lambda2sqs.version import VERSION, PROJECT_URL

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open, PropertyMock  # noqa
else:
    from unittest.mock import (patch, call, Mock, DEFAULT,  # noqa
                               mock_open, PropertyMock)  # noqa

pbm = 'webhook2lambda2sqs.tf_generator'
pb = '%s.TerraformGenerator' % pbm


class TestTerraformGenerator(object):

    def setup(self):
        self.conf = {}

        def se_get(k):
            return self.conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        type(config).func_name = 'webhook2lambda2sqs'
        self.cls = TerraformGenerator(config)

    def test_init(self):
        conf = {}

        def se_get(k):
            return conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        type(config).func_name = 'foobar'
        cls = TerraformGenerator(config)
        assert cls.config == config
        assert cls.tf_conf == {
            'provider': {
                'aws': {}
            },
            'resource': {},
            'output': {}
        }
        assert cls.resource_name == 'foobar'

    def test_get_tags_none(self):
        res = self.cls._get_tags()
        assert res == {
            'Name': 'webhook2lambda2sqs',
            'created_by': 'webhook2lambda2sqs v%s <%s>' % (VERSION, PROJECT_URL)
        }

    def test_get_tags(self):
        self.conf = {
            'aws_tags': {
                'Name': 'myname',
                'other': 'otherval',
                'foo': 'bar'
            }
        }
        res = self.cls._get_tags()
        assert res == {
            'Name': 'myname',
            'other': 'otherval',
            'foo': 'bar',
            'created_by': 'webhook2lambda2sqs v%s <%s>' % (VERSION, PROJECT_URL)
        }

    def test_generate_iam_role_policy(self):
        self.cls.aws_region = 'myregion'
        self.cls.aws_account_id = '1234'
        self.cls.resource_name = 'abc'
        assert self.cls.tf_conf['resource'] == {}
        self.cls._generate_iam_role_policy()
        assert 'aws_iam_role_policy' in self.cls.tf_conf['resource']
        assert 'role_policy' in self.cls.tf_conf['resource'][
            'aws_iam_role_policy']
        pol = self.cls.tf_conf['resource']['aws_iam_role_policy']['role_policy']
        assert sorted(pol.keys()) == ['name', 'policy', 'role']
        assert pol['name'] == 'abc'
        assert pol['role'] == '${aws_iam_role.lambda_role.id}'
        expected_pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:myregion:1234:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:myregion:1234:log-group:/aws/lambda/abc:*"
                    ]
                }
            ]
        }
        assert json.loads(pol['policy']) == expected_pol

    def test_generate_iam_role(self):
        assert self.cls.tf_conf['resource'] == {}
        self.cls.resource_name = 'abc'
        with patch('%s._generate_iam_role_policy' % pb, autospec=True) as mrp:
            self.cls._generate_iam_role()
        assert 'aws_iam_role' in self.cls.tf_conf['resource']
        assert 'lambda_role' in self.cls.tf_conf['resource']['aws_iam_role']
        role = self.cls.tf_conf['resource']['aws_iam_role']['lambda_role']
        assert sorted(role.keys()) == ['assume_role_policy', 'name']
        assert role['name'] == 'abc'
        assert json.loads(role['assume_role_policy']) == {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }
        assert self.cls.tf_conf['output']['iam_role_arn'] == {
            'value': '${aws_iam_role.lambda_role.arn}'
        }
        assert self.cls.tf_conf['output']['iam_role_unique_id'] == {
            'value': '${aws_iam_role.lambda_role.unique_id}'
        }
        assert mrp.mock_calls == [call(self.cls)]

    def test_generate_lambda(self):
        assert self.cls.tf_conf['resource'] == {}
        self.cls.resource_name = 'abc'
        self.cls._generate_lambda()
        f = self.cls.tf_conf['resource']['aws_lambda_function']['lambda_func']
        assert f == {
            'filename': 'webhook2lambda2sqs_func.zip',
            'function_name': 'abc',
            'role': '${aws_iam_role.lambda_role.arn}',
            'handler': 'webhook2lambda2sqs_func.webhook2lambda2sqs_handler',
            'source_code_hash': '${base64sha256(file('
                                '"webhook2lambda2sqs_func.zip"))}',
            'description': 'push webhook contents to SQS - generated and '
                           'managed by %s v%s' % (PROJECT_URL, VERSION),
            'runtime': 'python2.7',
            'timeout': 120
        }
        assert self.cls.tf_conf['output']['lambda_func_arn'] == {
            'value': '${aws_lambda_function.lambda_func.arn}'
        }

    def test_set_account_info_env_default(self):
        assert self.cls.aws_account_id is None
        assert self.cls.aws_region is None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict(
                        '%s.os.environ' % pbm,
                        {'AWS_DEFAULT_REGION': 'adr'},
                        clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam', region_name='adr'),
            call().get_user(),
            call('lambda', region_name='adr')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM with region_name=%s', 'adr'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    def test_set_account_info_env(self):
        assert self.cls.aws_account_id is None
        assert self.cls.aws_region is None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict(
                        '%s.os.environ' % pbm,
                        {'AWS_REGION': 'ar'},
                        clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam', region_name='ar'),
            call().get_user(),
            call('lambda', region_name='ar')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM with region_name=%s', 'ar'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    def test_set_account_info_no_env(self):
        assert self.cls.aws_account_id is None
        assert self.cls.aws_region is None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict('%s.os.environ' % pbm, {}, clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam'),
            call().get_user(),
            call('lambda')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM without specified region'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    @freeze_time("2016-07-01 02:03:04")
    def test_write_zip(self):
        with patch('%s.zipfile.ZipFile' % pbm, autospec=True) as mock_zf:
            with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                self.cls._write_zip('myfsrc', 'mypath.zip')
        # the only way I can find to capture attributes being set on the ZipInfo
        # is to not mock it, but use a real ZipInfo object. Unfortunately, that
        # makes assertin on calls a bit more difficult...
        assert len(mock_zf.mock_calls) == 4
        assert mock_zf.mock_calls[0] == call('mypath.zip', 'w')
        assert mock_zf.mock_calls[1] == call().__enter__()
        assert mock_zf.mock_calls[3] == call().__exit__(None, None, None)
        # ok, now handle the second call, which should have the ZipInfo
        # as its first argument...
        # test that it's the right chained method call
        assert mock_zf.mock_calls[2][0] == '().__enter__().writestr'
        # test its arguments
        arg_tup = mock_zf.mock_calls[2][1]
        assert isinstance(arg_tup[0], ZipInfo)
        assert arg_tup[0].filename == 'webhook2lambda2sqs_func.py'
        assert arg_tup[0].date_time == (2016, 7, 1, 2, 3, 4)
        assert arg_tup[0].external_attr == 0755 << 16
        assert arg_tup[1] == 'myfsrc'
        assert mock_logger.mock_calls == [
            call.debug('setting zipinfo date to: %s', (2016, 7, 1, 2, 3, 4)),
            call.debug('setting zipinfo file mode to: %s', (0755 << 16)),
            call.debug('writing zip file at: %s', 'mypath.zip')
        ]

    def test_generate(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._get_config' % pb, autospec=True) as mock_get:
                with patch('%s.open' % pbm, mock_open(), create=True) as m_open:
                    with patch('%s._write_zip' % pb, autospec=True) as mock_zip:
                        mock_get.return_value = 'myjson'
                        self.cls.generate('myfunc')
        assert mock_get.mock_calls == [call(self.cls, 'myfunc')]
        assert m_open.mock_calls == [
            call('./webhook2lambda2sqs_func.py', 'w'),
            call().__enter__(),
            call().write('myfunc'),
            call().__exit__(None, None, None),
            call('./webhook2lambda2sqs.tf.json', 'w'),
            call().__enter__(),
            call().write('myjson'),
            call().__exit__(None, None, None)
        ]
        assert mock_zip.mock_calls == [
            call(self.cls, 'myfunc', './webhook2lambda2sqs_func.zip')
        ]
        assert mock_logger.mock_calls == [
            call.warning('Writing lambda function source to: '
                         './webhook2lambda2sqs_func.py'),
            call.debug('lambda function written'),
            call.warning('Writing lambda function source zip file to: '
                         './webhook2lambda2sqs_func.zip'),
            call.debug('lambda zip written'),
            call.warning('Writing terraform configuration JSON to: '
                         './webhook2lambda2sqs.tf.json'),
            call.debug('terraform configuration written'),
            call.warning('Completed writing lambda function and TF config.')
        ]

    def test_get_config(self):
        self.cls.tf_conf = {'foo': 'bar'}
        with patch('%s.pretty_json' % pbm, autospec=True) as mock_json:
            with patch.multiple(
                pb,
                autospec=True,
                _generate_lambda=DEFAULT,
                _generate_iam_role=DEFAULT,
                _set_account_info=DEFAULT,
            ) as mocks:
                mock_json.return_value = 'my_json_str'
                res = self.cls._get_config('funcsrc')
        assert mock_json.mock_calls == [call({'foo': 'bar'})]
        assert mocks['_generate_lambda'].mock_calls == [call(self.cls)]
        assert mocks['_generate_iam_role'].mock_calls == [call(self.cls)]
        assert mocks['_set_account_info'].mock_calls == [call(self.cls)]
        assert res == 'my_json_str'
