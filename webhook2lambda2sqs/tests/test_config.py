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
import pytest

from webhook2lambda2sqs.config import Config

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT, mock_open  # noqa

pbm = 'webhook2lambda2sqs.config'
pb = '%s.Config' % pbm


class TestConfig(object):

    def setup(self):
        with patch('%s._load_config' % pb, autospec=True) as mock_load:
            mock_load.return_value = {'my': 'config', 'endpoints': {'a': 1}}
            self.cls = Config('confpath')

    def test_init(self):
        with patch('%s._load_config' % pb, autospec=True) as mock_load:
            mock_load.return_value = {'my': 'config', 'endpoints': {'a': 1}}
            cls = Config('mypath')
        assert cls.path == 'mypath'
        assert cls._config == {'my': 'config', 'endpoints': {'a': 1}}
        assert mock_load.mock_calls == [
            call(cls, 'mypath')
        ]

    def test_init_no_endpoints(self):
        with patch('%s._load_config' % pb, autospec=True) as mock_load:
            mock_load.return_value = {'my': 'config'}
            with pytest.raises(Exception) as excinfo:
                Config('mypath')
            assert excinfo.value.message == 'Error: configuration must have ' \
                                            'at least 1 endpoint'

    def test_load_config(self):
        with patch('%s.read_json_file' % pbm, autospec=True) as mock_read:
            with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                mock_read.return_value = {'foo': 'bar'}
                res = self.cls._load_config('/my/path')
        assert res == {'foo': 'bar'}
        assert mock_read.mock_calls == [call('/my/path')]
        assert mock_logger.mock_calls == [
            call.debug('Loading configuration from: %s', '/my/path')
        ]

    def test_example_config(self):
        with patch('%s.pretty_json' % pbm) as mock_pretty:
            with patch('%s.dedent' % pbm) as mock_dedent:
                mock_pretty.return_value = 'pretty'
                mock_dedent.return_value = 'dedent'
                res = Config.example_config()
        assert res == ('pretty', 'dedent')
        assert mock_pretty.mock_calls == [call(Config._example)]
        assert mock_dedent.mock_calls == [call(Config._example_docs)]

    def test_func_name(self):
        self.cls._config = {}
        assert self.cls.func_name == 'webhook2lambda2sqs'

    def test_func_name_suffix(self):
        self.cls._config = {'name_suffix': 'foo'}
        assert self.cls.func_name == 'webhook2lambda2sqsfoo'

    def test_get(self):
        self.cls._config = {'foo': 'bar', 'baz': {'blam': 'blarg'}}
        assert self.cls.get('foo') == 'bar'
        assert self.cls.get('baz') == {'blam': 'blarg'}
        assert self.cls.get('badkey') is None
