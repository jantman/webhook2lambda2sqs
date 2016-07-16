"""
Tests for runner.py

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
import logging
import pytest

from webhook2lambda2sqs.runner import (main, parse_args, set_log_info,
                                       set_log_debug, set_log_level_format)
from webhook2lambda2sqs.version import PROJECT_URL, VERSION

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT  # noqa

pbm = 'webhook2lambda2sqs.runner'


class TestRunner(object):

    def test_main_example_config_no_args(self):
        mock_args = Mock(verbose=0, action='example-config', config='cpath',
                         stream_tf=False)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                autospec=True,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = (
                    'config-ex', 'config-docs')
                mocks['parse_args'].return_value = mock_args
                with patch.object(sys, 'argv', ['foo', 'example-config']):
                    main()
        assert mocks['Config'].mock_calls == [call.example_config()]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == [call(['example-config'])]
        assert mocklogger.mock_calls == []

    def test_main_example_config(self, capsys):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='example-config', config='cpath',
                         stream_tf=False)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                autospec=True,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = (
                    'config-ex', 'config-docs')
                main(mock_args)
        assert mocks['Config'].mock_calls == [call.example_config()]
        out, err = capsys.readouterr()
        assert out == "config-ex\n"
        assert err == "config-docs\n"
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_generate_log_info(self):
        """
        test main function
        """

        mock_args = Mock(verbose=1, action='generate', config='cpath',
                         stream_tf=False)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                mocks['LambdaFuncGenerator'
                      ''].return_value.generate.return_value = 'myfunc'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == [call()]
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == [
            call(mocks['Config'].return_value),
            call().generate()
        ]
        assert mocks['TerraformGenerator'].mock_calls == [
            call(mocks['Config'].return_value),
            call().generate('myfunc')
        ]
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_genapply_log_debug(self):
        """
        test main function
        """

        mock_args = Mock(verbose=2, action='genapply', config='cpath',
                         stream_tf=False, tf_path='terraform')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                mocks['LambdaFuncGenerator'
                      ''].return_value.generate.return_value = 'myfunc'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == [call()]
        assert mocks['LambdaFuncGenerator'].mock_calls == [
            call(mocks['Config'].return_value),
            call().generate()
        ]
        assert mocks['TerraformGenerator'].mock_calls == [
            call(mocks['Config'].return_value),
            call().generate('myfunc')
        ]
        assert mocks['TerraformRunner'].mock_calls == [
            call(mocks['Config'].return_value, 'terraform'),
            call().apply(False)
        ]
        assert mocks['parse_args'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_plan(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='plan', config='cpath',
                         stream_tf=True, tf_path='terraform')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == [
            call(mocks['Config'].return_value, 'terraform'),
            call().plan(True)
        ]
        assert mocks['parse_args'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_destroy(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='destroy', config='cpath',
                         stream_tf=False, tf_path='/some/other/path')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == [
            call(mocks['Config'].return_value, '/some/other/path'),
            call().destroy(False)
        ]
        assert mocks['parse_args'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_parse_args_no_action(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args([])
        assert excinfo.value.code == 2
        out, err = capsys.readouterr()
        assert 'too few arguments' in err
        assert out == ''

    def test_parse_args_actions(self):
        for action in ['generate', 'plan', 'genapply',
                       'apply', 'destroy', 'example-config']:
            res = parse_args([action])
            assert res.action == action
            assert res.verbose == 0

    def test_parse_args_config(self):
        res = parse_args(['--config=foo', 'plan'])
        assert res.config == 'foo'

    def test_parse_args_verbose1(self):
        res = parse_args(['-v', 'plan'])
        assert res.verbose == 1

    def test_parse_args_verbose2(self):
        res = parse_args(['-vv', 'plan'])
        assert res.verbose == 2

    def test_parse_args_tf_path(self):
        res = parse_args(['-t', 'bar', 'plan'])
        assert res.tf_path == 'bar'
        assert res.stream_tf is False

    def test_parse_args_stream_tf(self):
        res = parse_args(['-s', 'plan'])
        assert res.stream_tf is True
        assert res.tf_path == 'terraform'

    def test_parse_args_version(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args(['-V'])
        assert excinfo.value.code == 0
        out, err = capsys.readouterr()
        assert out == ''
        assert err == "webhook2lambda2sqs v%s <%s>\n" % (
            VERSION, PROJECT_URL
        )

    def test_set_log_info(self):
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_info()
        assert mock_set.mock_calls == [
            call(logging.INFO, '%(asctime)s %(levelname)s:%(name)s:%(message)s')
        ]

    def test_set_log_debug(self):
        with patch('%s.set_log_level_format' % pbm) as mock_set:
            set_log_debug()
        assert mock_set.mock_calls == [
            call(logging.DEBUG,
                 "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
                 "%(name)s.%(funcName)s() ] %(message)s")
        ]

    def test_set_log_level_format(self):
        mock_handler = Mock(spec_set=logging.Handler)
        with patch('%s.logger' % pbm) as mock_logger:
            with patch('%s.logging.Formatter' % pbm) as mock_formatter:
                type(mock_logger).handlers = [mock_handler]
                set_log_level_format(5, 'foo')
        assert mock_formatter.mock_calls == [
            call(fmt='foo')
        ]
        assert mock_handler.mock_calls == [
            call.setFormatter(mock_formatter.return_value)
        ]
        assert mock_logger.mock_calls == [
            call.setLevel(5)
        ]
