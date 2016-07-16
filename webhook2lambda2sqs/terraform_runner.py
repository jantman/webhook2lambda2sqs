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

import logging
from webhook2lambda2sqs.utils import run_cmd

logger = logging.getLogger(__name__)

TF_CONFIG_NAME = 'webhook2lambda2sqs.tf.json'


class TerraformRunner(object):

    def __init__(self, config, tf_path):
        """
        Initialize the Terraform command runner.

        :param config: program configuration
        :type config: :py:class:`~.Config`
        :param tf_path: path to terraform binary
        :type tf_path: str
        """
        self.config = config
        self.tf_path = tf_path

    def _args_for_remote(self):
        """
        Generate arguments for 'terraform remote config'. Return None if
        not present in configuration.

        :return: list of args for 'terraform remote config' or None
        :rtype: list or None
        """
        conf = self.config.get('terraform_remote_state')
        if conf is None:
            return None
        args = ['-backend=%s' % conf['backend']]
        for k, v in conf['config'].items():
            args.append('-backend-config="%s=%s"' % (k, v))
        return args

    def _set_remote(self, stream=False):
        """
        Call :py:meth:`~._args_for_remote`; if the return value is not None,
        execute 'terraform remote config' with those argumants and ensure it
        exits 0.

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        args = self._args_for_remote()
        if args is None:
            logger.debug('_args_for_remote() returned None; not configuring '
                         'terraform remote')
            return
        logger.warning('Setting terraform remote config: %s', ' '.join(args))
        args = ['config'] + args
        self._run_tf('remote', cmd_args=args, stream=stream)
        logger.info('Terraform remote configured.')

    def _run_tf(self, cmd, cmd_args=[], stream=False):
        """
        Run a single terraform command; raise exception on non-zero exit status.

        :param cmd: terraform command to run
        :type cmd: str
        :param cmd_args: arguments to command
        :type cmd_args: list

        :return: command output
        :rtype: str
        :raises: Exception on non-zero exit
        """
        args = [self.tf_path, cmd] + cmd_args
        logger.info('Running terraform command: %s', ' '.join(args))
        out, retcode = run_cmd(args, stream=stream)
        if retcode != 0:
            logger.critical('Terraform command (%s) failed with exit code '
                            '%d:\n%s', ' '.join(args), retcode, out)
            raise Exception('terraform %s failed' % cmd)
        return out

    def plan(self, stream=False):
        """
        Run a 'terraform plan'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._set_remote(stream=stream)
        args = ['-input=false', '-refresh=true', '.']
        logger.warning('Running terraform plan: %s', ' '.join(args))
        out = self._run_tf('plan', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform plan finished successfully.')
        else:
            logger.warning("Terraform plan finished successfully:\n%s", out)

    def apply(self, stream=False):
        """
        Run a 'terraform apply'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._set_remote(stream=stream)
        args = ['-input=false', '-refresh=true', '.']
        logger.warning('Running terraform apply: %s', ' '.join(args))
        out = self._run_tf('apply', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform apply finished successfully.')
        else:
            logger.warning("Terraform apply finished successfully:\n%s", out)

    def destroy(self, stream=False):
        """
        Run a 'terraform destroy'

        :param stream: whether or not to stream TF output in realtime
        :type stream: bool
        """
        self._set_remote(stream=stream)
        args = ['-refresh=true', '.']
        logger.warning('Running terraform destroy: %s', ' '.join(args))
        out = self._run_tf('destroy', cmd_args=args, stream=stream)
        if stream:
            logger.warning('Terraform destroy finished successfully.')
        else:
            logger.warning("Terraform destroy finished successfully:\n%s", out)
