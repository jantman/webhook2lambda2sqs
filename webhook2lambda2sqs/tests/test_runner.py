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
from requests.models import Response
from pprint import pformat
from freezegun import freeze_time

from webhook2lambda2sqs.runner import (main, parse_args, set_log_info,
                                       set_log_debug, set_log_level_format,
                                       get_base_url, run_test, get_api_id)
from webhook2lambda2sqs.version import PROJECT_URL, VERSION

from webhook2lambda2sqs.tests.support import exc_msg

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
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
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
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['get_api_id'].mock_calls == []
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
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
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
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['get_api_id'].mock_calls == []
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
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
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
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['get_api_id'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_genapply_log_debug(self):
        """
        test main function
        """

        def se_get(name):
            return None

        mock_args = Mock(verbose=2, action='genapply', config='cpath',
                         stream_tf=True, tf_path='terraform')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                mocks['Config'].return_value.get.side_effect = se_get
                mocks['LambdaFuncGenerator'
                      ''].return_value.generate.return_value = 'myfunc'
                main(mock_args)
        assert mocks['Config'].mock_calls == [
            call('cpath'),
            call().get('api_gateway_method_settings')
        ]
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
            call().apply(True)
        ]
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['get_api_id'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_apply(self):
        """
        test main function
        """

        def se_get(name):
            return {'foo': 'bar'}

        mock_args = Mock(verbose=0, action='apply', config='cpath',
                         stream_tf=False, tf_path='terraform')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                mocks['Config'].get.side_effect = se_get
                mocks['LambdaFuncGenerator'
                      ''].return_value.generate.return_value = 'myfunc'
                main(mock_args)
        assert mocks['Config'].mock_calls == [
            call('cpath'),
            call().get('api_gateway_method_settings')
        ]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == [
            call(mocks['Config'].return_value, 'terraform'),
            call().apply(False)
        ]
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == [
            call(mocks['Config'].return_value),
            call().set_method_settings()
        ]
        assert mocks['get_api_id'].mock_calls == []
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
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
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
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['get_api_id'].mock_calls == []
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
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
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
        assert mocks['get_api_id'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_logs(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='logs', config='cpath',
                         log_count=4)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == [
            call(mocks['Config'].return_value),
            call().show_cloudwatch_logs(count=4)
        ]
        assert mocks['get_api_id'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_apilogs(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='apilogs', config='cpath',
                         log_count=6)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                type(mocks['Config'].return_value).func_name = 'myfname'
                type(mocks['Config'].return_value).stage_name = 'mysname'
                mocks['get_api_id'].return_value = 'did'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == [
            call(mocks['Config'].return_value),
            call().show_cloudwatch_logs(
                count=6,
                grp_name='API-Gateway-Execution-Logs_did/mysname'
            )
        ]
        assert mocks['get_api_id'].mock_calls == [
            call(mocks['Config'].return_value, mock_args)
        ]
        assert mocklogger.mock_calls == []

    def test_main_queuepeek(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='queuepeek', config='cpath',
                         queue_name='foo', queue_delete=True, msg_count=2)
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == [
            call(mocks['Config'].return_value),
            call().show_queue(name='foo', delete=True, count=2)
        ]
        assert mocks['get_api_id'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_main_test(self):
        """
        test main function
        """

        mock_args = Mock(verbose=0, action='test', config='cpath')
        with patch('%s.logger' % pbm, autospec=True) as mocklogger:
            with patch.multiple(
                pbm,
                Config=DEFAULT,
                AWSInfo=DEFAULT,
                set_log_info=DEFAULT,
                set_log_debug=DEFAULT,
                LambdaFuncGenerator=DEFAULT,
                TerraformGenerator=DEFAULT,
                TerraformRunner=DEFAULT,
                parse_args=DEFAULT,
                run_test=DEFAULT,
                get_api_id=DEFAULT,
            ) as mocks:
                mocks['Config'].example_config.return_value = 'config-ex'
                main(mock_args)
        assert mocks['Config'].mock_calls == [call('cpath')]
        assert mocks['set_log_info'].mock_calls == []
        assert mocks['set_log_debug'].mock_calls == []
        assert mocks['LambdaFuncGenerator'].mock_calls == []
        assert mocks['TerraformGenerator'].mock_calls == []
        assert mocks['TerraformRunner'].mock_calls == []
        assert mocks['parse_args'].mock_calls == []
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['run_test'].mock_calls == [
            call(mocks['Config'].return_value, mock_args)
        ]
        assert mocks['get_api_id'].mock_calls == []
        assert mocklogger.mock_calls == []

    def test_parse_args_no_action(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args([])
        assert excinfo.value.code == 2
        out, err = capsys.readouterr()
        assert 'too few arguments' in err
        assert out == ''

    def test_parse_args_None_action_py27(self, capsys):
        """this just exists to get coverage to pass on py27"""
        m_args = Mock(action=None)
        with pytest.raises(SystemExit) as excinfo:
            with patch('%s.argparse.ArgumentParser' % pbm) as mock_parser:
                mock_parser.return_value.parse_args.return_value = m_args
                parse_args([])
        out, err = capsys.readouterr()
        assert out == ''
        assert err == "ERROR: too few arguments\n"
        assert excinfo.value.code == 2

    def test_parse_args_actions(self):
        for action in ['generate', 'example-config', 'logs', 'queuepeek',
                       'test', 'apilogs']:
            res = parse_args([action])
            assert res.action == action
            assert res.verbose == 0

    def test_parse_args_tf_actions_default(self):
        for action in ['genapply', 'apply', 'plan', 'destroy']:
            res = parse_args([action])
            assert res.action == action
            assert res.verbose == 0
            assert res.tf_path == 'terraform'
            assert res.stream_tf is True

    def test_parse_args_tf_actions_non_default(self):
        for action in ['genapply', 'apply', 'plan', 'destroy']:
            res = parse_args([action, '--terraform-path=/path/to/tf', '-S'])
            assert res.action == action
            assert res.verbose == 0
            assert res.tf_path == '/path/to/tf'
            assert res.stream_tf is False

    def test_parse_args_apilogs(self):
        res = parse_args(['apilogs'])
        assert res.action == 'apilogs'
        assert res.log_count == 10

    def test_parse_args_apilogs_count(self):
        res = parse_args(['apilogs', '-c', '3'])
        assert res.action == 'apilogs'
        assert res.log_count == 3

    def test_parse_args_logs(self):
        res = parse_args(['logs'])
        assert res.action == 'logs'
        assert res.log_count == 10

    def test_parse_args_logs_count(self):
        res = parse_args(['logs', '-c', '3'])
        assert res.action == 'logs'
        assert res.log_count == 3

    def test_parse_args_queuepeek(self):
        res = parse_args(['queuepeek'])
        assert res.action == 'queuepeek'
        assert res.queue_name is None
        assert res.queue_delete is False
        assert res.msg_count == 10

    def test_parse_args_queuepeek_non_default(self):
        res = parse_args(['queuepeek', '--name=foo', '-d', '-c', '5'])
        assert res.action == 'queuepeek'
        assert res.queue_name == 'foo'
        assert res.queue_delete is True
        assert res.msg_count == 5

    def test_parse_args_test(self):
        res = parse_args(['test'])
        assert res.action == 'test'
        assert res.endpoint_name is None

    def test_parse_args_test_name(self):
        res = parse_args(['test', '-n', 'foo'])
        assert res.action == 'test'
        assert res.endpoint_name == 'foo'

    def test_parse_args_config(self):
        res = parse_args(['--config=foo', 'plan'])
        assert res.config == 'foo'

    def test_parse_args_verbose1(self):
        res = parse_args(['-v', 'plan'])
        assert res.verbose == 1

    def test_parse_args_verbose2(self):
        res = parse_args(['-vv', 'plan'])
        assert res.verbose == 2

    def test_parse_args_version(self, capsys):
        with pytest.raises(SystemExit) as excinfo:
            parse_args(['-V'])
        assert excinfo.value.code == 0
        expected = "webhook2lambda2sqs v%s <%s>\n" % (
            VERSION, PROJECT_URL
        )
        out, err = capsys.readouterr()
        if (sys.version_info[0] < 3 or
                (sys.version_info[0] == 3 and sys.version_info[1] < 4)):
            assert out == ''
            assert err == expected
        else:
            assert out == expected
            assert err == ''

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

    def test_get_base_url_tf(self):
        conf = Mock()
        args = Mock(tf_path='tfpath')
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            TerraformRunner=DEFAULT,
            AWSInfo=DEFAULT
        ) as mocks:
            mocks['TerraformRunner'].return_value._get_outputs.return_value = {
                'base_url': 'mytfbase'
            }
            res = get_base_url(conf, args)
        assert res == 'mytfbase/'
        assert mocks['TerraformRunner'].mock_calls == [
            call(conf, 'tfpath'),
            call()._get_outputs()
        ]
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['logger'].mock_calls == [
            call.debug('Trying to get Terraform base_url output'),
            call.debug('Terraform base_url output: \'%s\'', 'mytfbase')
        ]

    def test_get_base_url_aws(self):

        def se_exc(*args, **kwargs):
            raise Exception()

        conf = Mock()
        args = Mock(tf_path='tfpath')
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            TerraformRunner=DEFAULT,
            AWSInfo=DEFAULT
        ) as mocks:
            mocks['TerraformRunner'].return_value._get_outputs.side_effect = \
                se_exc
            mocks['AWSInfo'].return_value.get_api_base_url.return_value = 'au/'
            res = get_base_url(conf, args)
        assert res == 'au/'
        assert mocks['TerraformRunner'].mock_calls == [
            call(conf, 'tfpath'),
            call()._get_outputs()
        ]
        assert mocks['AWSInfo'].mock_calls == [
            call(conf),
            call().get_api_base_url()
        ]
        assert mocks['logger'].mock_calls == [
            call.debug('Trying to get Terraform base_url output'),
            call.info('Unable to find API base_url from Terraform state; '
                      'querying AWS.', exc_info=1),
            call.debug('AWS api_base_url: \'%s\'', 'au/')
        ]

    def test_get_api_id_tf(self):
        conf = Mock()
        args = Mock(tf_path='tfpath')
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            TerraformRunner=DEFAULT,
            AWSInfo=DEFAULT
        ) as mocks:
            mocks['TerraformRunner'].return_value._get_outputs.return_value = {
                'base_url': 'mytfbase',
                'rest_api_id': 'myid'
            }
            res = get_api_id(conf, args)
        assert res == 'myid'
        assert mocks['TerraformRunner'].mock_calls == [
            call(conf, 'tfpath'),
            call()._get_outputs()
        ]
        assert mocks['AWSInfo'].mock_calls == []
        assert mocks['logger'].mock_calls == [
            call.debug('Trying to get Terraform rest_api_id output'),
            call.debug('Terraform rest_api_id output: \'%s\'', 'myid')
        ]

    def test_get_api_id_aws(self):

        def se_exc(*args, **kwargs):
            raise Exception()

        conf = Mock()
        args = Mock(tf_path='tfpath')
        with patch.multiple(
            pbm,
            autospec=True,
            logger=DEFAULT,
            TerraformRunner=DEFAULT,
            AWSInfo=DEFAULT
        ) as mocks:
            mocks['TerraformRunner'].return_value._get_outputs.side_effect = \
                se_exc
            mocks['AWSInfo'].return_value.get_api_id.return_value = 'myaid'
            res = get_api_id(conf, args)
        assert res == 'myaid'
        assert mocks['TerraformRunner'].mock_calls == [
            call(conf, 'tfpath'),
            call()._get_outputs()
        ]
        assert mocks['AWSInfo'].mock_calls == [
            call(conf),
            call().get_api_id()
        ]
        assert mocks['logger'].mock_calls == [
            call.debug('Trying to get Terraform rest_api_id output'),
            call.info('Unable to find API rest_api_id from Terraform state; '
                      'querying AWS.', exc_info=1),
            call.debug('AWS API ID: \'%s\'', 'myaid')
        ]

    @freeze_time("2016-07-01 02:03:04")
    def test_run_test(self, capsys):
        conf = Mock()
        conf.get.return_value = {
            'ep1': {'method': 'GET'},
            'ep2': {'method': 'POST'}
        }
        args = Mock(endpoint_name=None)
        res1 = Mock(spec_set=Response)
        type(res1).status_code = 200
        type(res1).content = 'res1content'
        type(res1).headers = {
            'h1': 'h1val',
            'hz': 'hzval'
        }
        res2 = Mock(spec_set=Response)
        type(res2).status_code = 503
        type(res2).content = 'res2content'
        type(res2).headers = {
            'h21': 'h21val',
            'h2z': 'h2zval'
        }

        req_data = {
            'message': 'testing via webhook2lambda2sqs CLI',
            'version': VERSION,
            'host': 'mynode',
            'datetime': '2016-07-01T02:03:04.000000'
        }

        with patch.multiple(
            pbm,
            autospec=True,
            requests=DEFAULT,
            logger=DEFAULT,
            get_base_url=DEFAULT,
            node=DEFAULT
        ) as mocks:
            mocks['get_base_url'].return_value = 'mybase/'
            mocks['node'].return_value = 'mynode'
            mocks['requests'].get.return_value = res1
            mocks['requests'].post.return_value = res2
            run_test(conf, args)
        out, err = capsys.readouterr()
        assert err == ''
        expected_out = "=> Testing endpoint mybase/ep1/ with GET: "
        expected_out += pformat(req_data) + "\n"
        expected_out += "RESULT: HTTP 200\n"
        expected_out += "h1: h1val\n"
        expected_out += "hz: hzval\n"
        expected_out += "\nres1content\n\n"
        expected_out += "=> Testing endpoint mybase/ep2/ with POST: "
        expected_out += pformat(req_data) + "\n"
        expected_out += "RESULT: HTTP 503\n"
        expected_out += "h21: h21val\n"
        expected_out += "h2z: h2zval\n"
        expected_out += "\nres2content\n\n"
        assert out == expected_out
        assert conf.mock_calls == [call.get('endpoints')]
        assert mocks['get_base_url'].mock_calls == [call(conf, args)]
        assert mocks['logger'].mock_calls == [
            call.debug('API base url: %s', 'mybase/')
        ]
        assert mocks['requests'].mock_calls == [
            call.get('mybase/ep1/', params={
                'message': 'testing via webhook2lambda2sqs CLI',
                'version': '0.1.0',
                'host': 'mynode',
                'datetime': '2016-07-01T02:03:04.000000'
            }),
            call.post('mybase/ep2/', json={
                'message': 'testing via webhook2lambda2sqs CLI',
                'version': '0.1.0',
                'host': 'mynode',
                'datetime': '2016-07-01T02:03:04.000000'
            })
        ]
        assert mocks['node'].mock_calls == [call()]

    @freeze_time("2016-07-01 02:03:04")
    def test_run_test_one(self, capsys):
        conf = Mock()
        conf.get.return_value = {
            'ep1': {'method': 'GET'}
        }
        args = Mock(endpoint_name='ep1')
        res1 = Mock(spec_set=Response)
        type(res1).status_code = 200
        type(res1).content = 'res1content'
        type(res1).headers = {
            'h1': 'h1val',
            'hz': 'hzval'
        }

        req_data = {
            'message': 'testing via webhook2lambda2sqs CLI',
            'version': VERSION,
            'host': 'mynode',
            'datetime': '2016-07-01T02:03:04.000000'
        }

        with patch.multiple(
            pbm,
            autospec=True,
            requests=DEFAULT,
            logger=DEFAULT,
            get_base_url=DEFAULT,
            node=DEFAULT
        ) as mocks:
            mocks['get_base_url'].return_value = 'mybase/'
            mocks['node'].return_value = 'mynode'
            mocks['requests'].get.return_value = res1
            run_test(conf, args)
        out, err = capsys.readouterr()
        assert err == ''
        expected_out = "=> Testing endpoint mybase/ep1/ with GET: "
        expected_out += pformat(req_data) + "\n"
        expected_out += "RESULT: HTTP 200\n"
        expected_out += "h1: h1val\n"
        expected_out += "hz: hzval\n"
        expected_out += "\nres1content\n\n"
        assert out == expected_out
        assert conf.mock_calls == [call.get('endpoints')]
        assert mocks['get_base_url'].mock_calls == [call(conf, args)]
        assert mocks['logger'].mock_calls == [
            call.debug('API base url: %s', 'mybase/')
        ]
        assert mocks['requests'].mock_calls == [
            call.get('mybase/ep1/', params={
                'message': 'testing via webhook2lambda2sqs CLI',
                'version': '0.1.0',
                'host': 'mynode',
                'datetime': '2016-07-01T02:03:04.000000'
            })
        ]
        assert mocks['node'].mock_calls == [call()]

    @freeze_time("2016-07-01 02:03:04")
    def test_run_test_bad_method(self, capsys):
        conf = Mock()
        conf.get.return_value = {
            'ep1': {'method': 'FOO'}
        }
        args = Mock(endpoint_name='ep1')
        res1 = Mock(spec_set=Response)
        type(res1).status_code = 200
        type(res1).content = 'res1content'
        type(res1).headers = {
            'h1': 'h1val',
            'hz': 'hzval'
        }

        with patch.multiple(
            pbm,
            autospec=True,
            requests=DEFAULT,
            logger=DEFAULT,
            get_base_url=DEFAULT,
            node=DEFAULT
        ) as mocks:
            mocks['get_base_url'].return_value = 'mybase/'
            mocks['node'].return_value = 'mynode'
            mocks['requests'].get.return_value = res1
            with pytest.raises(Exception) as excinfo:
                run_test(conf, args)
        assert exc_msg(excinfo.value) == 'Unimplemented method: FOO'
