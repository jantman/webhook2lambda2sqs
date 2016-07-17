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

from webhook2lambda2sqs.tf_generator import TerraformGenerator
from webhook2lambda2sqs.version import VERSION, PROJECT_URL

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 'webhook2lambda2sqs.tf_generator'
pb = '%s.TerraformGenerator' % pbm


class TestTerraformGenerator(object):

    def setup(self):
        self.conf = {}

        def se_get(k):
            return self.conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        self.cls = TerraformGenerator(config)

    def test_init(self):
        conf = {}

        def se_get(k):
            return conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        cls = TerraformGenerator(config)
        assert cls.config == config
        assert cls.tf_conf == {
            'provider': {
                'aws': {}
            },
            'resource': {},
            'outputs': {}
        }
        assert cls.resource_name == 'webhook2lambda2sqs'

    def test_init_suffix(self):
        conf = {'name_suffix': '-foo'}

        def se_get(k):
            return conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        cls = TerraformGenerator(config)
        assert cls.config == config
        assert cls.tf_conf == {
            'provider': {
                'aws': {}
            },
            'resource': {},
            'outputs': {}
        }
        assert cls.resource_name == 'webhook2lambda2sqs-foo'

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
            ) as mocks:
                mock_json.return_value = 'my_json_str'
                res = self.cls._get_config('funcsrc')
        assert mock_json.mock_calls == [call({'foo': 'bar'})]
        assert mocks['_generate_lambda'].mock_calls == [
            call(self.cls, 'funcsrc')
        ]
        assert mocks['_generate_iam_role'].mock_calls == [call(self.cls)]
        assert res == 'my_json_str'
