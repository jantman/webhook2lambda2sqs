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

from webhook2lambda2sqs.terraform_runner import TerraformRunner

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT  # noqa
else:
    from unittest.mock import patch, call, Mock, DEFAULT  # noqa

pbm = 'webhook2lambda2sqs.terraform_runner'
pb = '%s.TerraformRunner' % pbm


class TestTerraformRunner(object):

    def mock_config(self, conf={}):

        def se_get(k):
            return conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        return config

    def test_init(self):
        c = Mock()
        with patch('%s._validate' % pb, autospec=True) as mock_validate:
            cls = TerraformRunner(c, 'mypath')
        assert cls.config == c
        assert cls.tf_path == 'mypath'
        assert mock_validate.mock_calls == [call(cls)]

    def DONTtest_init_version_fail(self):

        def se_exc(*args):
            raise Exception('foo')

        c = Mock()
        with patch('%s._run_tf' % pb) as mock_run:
            mock_run.side_effect = se_exc
            with pytest.raises(Exception) as excinfo:
                TerraformRunner(c, 'mypath')
        assert excinfo.value.message == 'ERROR: executing \'mypath ' \
                                        'version\' failed; is terraform ' \
                                        'installed and is the path to it ' \
                                        '(mypath) correct?'

    def test_args_for_remote_none(self):
        conf = self.mock_config()
        with patch('%s._validate' % pb):
            cls = TerraformRunner(conf, 'tfpath')
        assert cls._args_for_remote() is None

    def test_args_for_remote(self):
        conf = self.mock_config(conf={
            'terraform_remote_state': {
                'backend': 'consul',
                'config': {
                    'path': 'consul/path',
                    'address': 'foo:1234'
                }
            }
        })
        with patch('%s._validate' % pb):
            cls = TerraformRunner(conf, 'tfpath')
        assert cls._args_for_remote() == [
            '-backend=consul',
            '-backend-config="path=consul/path"',
            '-backend-config="address=foo:1234"'
        ]

    def test_set_remote_none(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), '/path/to/terraform')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._args_for_remote' % pb, autospec=True) as mock_args:
                with patch('%s.run_cmd' % pbm, autospec=True) as mock_run:
                    mock_args.return_value = None
                    cls._set_remote()
        assert mock_args.mock_calls == [call(cls)]
        assert mock_run.mock_calls == []
        assert mock_logger.mock_calls == [
            call.debug('_args_for_remote() returned None; not configuring '
                       'terraform remote')
        ]

    def test_set_remote(self):
        expected_args = ['config', 'foo', 'bar']
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._args_for_remote' % pb, autospec=True) as mock_args:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_args.return_value = ['foo', 'bar']
                    mock_run.return_value = ('myoutput', 0)
                    cls._set_remote()
        assert mock_args.mock_calls == [call(cls)]
        assert mock_run.mock_calls == [
            call(cls, 'remote', cmd_args=expected_args, stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Setting terraform remote config: %s', 'foo bar'),
            call.info('Terraform remote configured.')
        ]

    def test_run_tf(self):
        expected_args = 'terraform plan config foo bar'
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.run_cmd' % pbm, autospec=True) as mock_run:
                mock_run.return_value = ('myoutput', 0)
                cls._run_tf('plan', cmd_args=['config', 'foo', 'bar'])
        assert mock_run.mock_calls == [
            call(expected_args, stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.info('Running terraform command: %s', expected_args)
        ]

    def test_run_tf_fail(self):
        expected_args = 'terraform-bin plan config foo bar'
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.run_cmd' % pbm, autospec=True) as mock_run:
                mock_run.return_value = ('myoutput', 5)
                with pytest.raises(Exception) as excinfo:
                    cls._run_tf('plan', cmd_args=['config', 'foo', 'bar'],
                                stream=True)
        assert excinfo.value.message == 'terraform plan failed'
        assert mock_run.mock_calls == [
            call(expected_args, stream=True)
        ]
        assert mock_logger.mock_calls == [
            call.info('Running terraform command: %s', expected_args),
            call.critical('Terraform command (%s) failed with exit code '
                          '%d:\n%s', expected_args, 5, 'myoutput')
        ]

    def test_plan(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    cls.plan()
        assert mock_set.mock_calls == [call(cls, stream=False)]
        assert mock_run.mock_calls == [
            call(cls, 'plan', cmd_args=['-input=false', '-refresh=true', '.'],
                 stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform plan: %s',
                         '-input=false -refresh=true .'),
            call.warning("Terraform plan finished successfully:\n%s", 'output')
        ]

    def test_plan_stream(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    cls.plan(stream=True)
        assert mock_set.mock_calls == [call(cls, stream=True)]
        assert mock_run.mock_calls == [
            call(cls, 'plan', cmd_args=['-input=false', '-refresh=true', '.'],
                 stream=True)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform plan: %s',
                         '-input=false -refresh=true .'),
            call.warning("Terraform plan finished successfully.")
        ]

    def test_apply(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    with patch('%s._show_outputs' % pb,
                               autospec=True) as mock_show:
                        cls.apply()
        assert mock_set.mock_calls == [call(cls, stream=False)]
        assert mock_run.mock_calls == [
            call(cls, 'apply', cmd_args=['-input=false', '-refresh=true', '.'],
                 stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform apply: %s',
                         '-input=false -refresh=true .'),
            call.warning("Terraform apply finished successfully:\n%s", 'output')
        ]
        assert mock_show.mock_calls == [call(cls)]

    def test_apply_stream(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    with patch('%s._show_outputs' % pb,
                               autospec=True) as mock_show:
                        cls.apply(stream=True)
        assert mock_set.mock_calls == [call(cls, stream=True)]
        assert mock_run.mock_calls == [
            call(cls, 'apply', cmd_args=['-input=false', '-refresh=true', '.'],
                 stream=True)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform apply: %s',
                         '-input=false -refresh=true .'),
            call.warning("Terraform apply finished successfully.")
        ]
        assert mock_show.mock_calls == [call(cls)]

    def test_show_outputs(self, capsys):
        state = {
            'version': 1,
            'serial': 1,
            'modules': [
                {
                    'path': ['root'],
                    'resources': {'foo': 'bar'},
                    'outputs': {
                        'out1': "foo\nbar",
                        'out2': "baz"
                    }
                },
                {
                    'path': ['foo']
                }
            ]
        }
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.read_json_file' % pbm, autospec=True) as mock_read:
                with patch('%s.os.path.exists' % pbm) as mock_exists:
                    mock_read.return_value = state
                    mock_exists.side_effect = [False, True]
                    cls._show_outputs()
        assert mock_read.mock_calls == [call('terraform.tfstate')]
        out, err = capsys.readouterr()
        assert err == ''
        assert out == "\n\n=> Terraform Outputs:\nout1 = foo\nbar\nout2 = baz\n"
        assert mock_logger.mock_calls == [
            call.debug('Does not exist: %s', '.terraform/terraform.tfstate'),
            call.debug('Found tfstate: %s', 'terraform.tfstate'),
            call.debug('Terraform state: %s', state)
        ]

    def test_show_outputs_exception(self, capsys):

        def se_exc(fpath):
            raise Exception('foo')

        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.read_json_file' % pbm, autospec=True) as mock_read:
                with patch('%s.os.path.exists' % pbm) as mock_exists:
                    mock_exists.return_value = True
                    mock_read.side_effect = se_exc
                    cls._show_outputs()
        assert mock_read.mock_calls == [call('.terraform/terraform.tfstate')]
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''
        assert mock_logger.mock_calls == [
            call.debug('Found tfstate: %s', '.terraform/terraform.tfstate'),
            call.error('Error showing outputs from terraform state file: %s',
                       '.terraform/terraform.tfstate', excinfo=1)
        ]

    def test_show_outputs_no_file(self, capsys):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.read_json_file' % pbm, autospec=True) as mock_read:
                with patch('%s.os.path.exists' % pbm) as mock_exists:
                    mock_exists.return_value = False
                    cls._show_outputs()
        assert mock_read.mock_calls == []
        out, err = capsys.readouterr()
        assert err == ''
        assert out == ''
        assert mock_logger.mock_calls == [
            call.debug('Does not exist: %s', '.terraform/terraform.tfstate'),
            call.debug('Does not exist: %s', 'terraform.tfstate'),
            call.error('Error: no terraform.tfstate file found; cannot show '
                       'terraform outputs.')
        ]

    def test_destroy(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    cls.destroy()
        assert mock_set.mock_calls == [call(cls, stream=False)]
        assert mock_run.mock_calls == [
            call(cls, 'destroy', cmd_args=['-refresh=true', '.'],
                 stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform destroy: %s',
                         '-refresh=true .'),
            call.warning("Terraform destroy finished successfully:\n%s",
                         'output')
        ]

    def test_destroy_stream(self):
        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
                    cls.destroy(stream=True)
        assert mock_set.mock_calls == [call(cls, stream=True)]
        assert mock_run.mock_calls == [
            call(cls, 'destroy', cmd_args=['-refresh=true', '.'],
                 stream=True)
        ]
        assert mock_logger.mock_calls == [
            call.warning('Running terraform destroy: %s',
                         '-refresh=true .'),
            call.warning("Terraform destroy finished successfully.")
        ]

    def test_validate(self):

        def se_run(*args, **kwargs):
            return

        with patch('%s._validate' % pb):
            cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s._run_tf' % pb, autospec=True) as mock_run:
            mock_run.side_effect = se_run
            cls._validate()
        assert mock_run.mock_calls == [
            call(cls, 'version'),
            call(cls, 'validate', ['.'])
        ]

    def test_validate_version_fail(self):
        def se_run(*args, **kwargs):
            if args[0] == 'version':
                raise Exception()

        # validate is called in __init__; we can't easily patch and re-call
        with patch('%s._run_tf' % pb) as mock_run:
            mock_run.side_effect = se_run
            with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                with pytest.raises(Exception) as excinfo:
                    TerraformRunner(self.mock_config(), 'terraform-bin')
        assert mock_run.mock_calls == [
            call('version')
        ]
        assert excinfo.value.message == 'ERROR: executing \'terraform-bin ' \
                                        'version\' failed; is terraform ' \
                                        'installed and is the path to it ' \
                                        '(terraform-bin) correct?'
        assert mock_logger.mock_calls == []

    def test_validate_fail(self):
        def se_run(*args, **kwargs):
            if args[0] == 'validate':
                raise Exception()

        # validate is called in __init__; we can't easily patch and re-call
        with patch('%s._run_tf' % pb) as mock_run:
            mock_run.side_effect = se_run
            with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                with pytest.raises(Exception) as excinfo:
                    TerraformRunner(self.mock_config(), 'terraform-bin')
        assert mock_run.mock_calls == [
            call('version'),
            call('validate', ['.'])
        ]
        assert excinfo.value.message == 'ERROR: Terraform config validation ' \
                                        'failed.'
        assert mock_logger.mock_calls == [
            call.critical("Terraform config validation failed. This is almost "
                          "certainly a bug in webhook2lambda2sqs; please "
                          "re-run with '-vv' and open a bug at <https://"
                          "github.com/jantman/webhook2lambda2sqs/issues>")
        ]
