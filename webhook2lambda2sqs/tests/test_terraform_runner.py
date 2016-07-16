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
        cls = TerraformRunner(c, 'mypath')
        assert cls.config == c
        assert cls.tf_path == 'mypath'

    def test_args_for_remote_none(self):
        conf = self.mock_config()
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
        cls = TerraformRunner(conf, 'tfpath')
        assert cls._args_for_remote() == [
            '-backend=consul',
            '-backend-config="path=consul/path"',
            '-backend-config="address=foo:1234"'
        ]

    def test_set_remote_none(self):
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
        expected_args = ['terraform', 'remote', 'config', 'foo', 'bar']
        cls = TerraformRunner(self.mock_config(), 'terraform')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.run_cmd' % pbm, autospec=True) as mock_run:
                mock_run.return_value = ('myoutput', 0)
                cls._run_tf('remote', cmd_args=['config', 'foo', 'bar'])
        assert mock_run.mock_calls == [
            call(expected_args, stream=False)
        ]
        assert mock_logger.mock_calls == [
            call.info('Running terraform command: %s', ' '.join(expected_args))
        ]

    def test_run_tf_fail(self):
        expected_args = ['terraform-bin', 'plan', 'config', 'foo', 'bar']
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
            call.info('Running terraform command: %s', ' '.join(expected_args)),
            call.critical('Terraform command (%s) failed with exit code '
                          '%d:\n%s', ' '.join(expected_args), 5, 'myoutput')
        ]

    def test_plan(self):
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
        cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
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

    def test_apply_stream(self):
        cls = TerraformRunner(self.mock_config(), 'terraform-bin')
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._set_remote' % pb, autospec=True) as mock_set:
                with patch('%s._run_tf' % pb, autospec=True) as mock_run:
                    mock_run.return_value = 'output'
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

    def test_destroy(self):
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
