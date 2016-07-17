"""
Main application entry point / runner for webhook2lambda2sqs.

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
import argparse
import logging

from webhook2lambda2sqs.version import PROJECT_URL, VERSION
from webhook2lambda2sqs.config import Config
from webhook2lambda2sqs.terraform_runner import TerraformRunner
from webhook2lambda2sqs.tf_generator import TerraformGenerator
from webhook2lambda2sqs.func_generator import LambdaFuncGenerator

FORMAT = "[%(asctime)s %(levelname)s] %(message)s"
logging.basicConfig(level=logging.WARNING, format=FORMAT)
logger = logging.getLogger()

# suppress boto3 internal logging below WARNING level
boto3_log = logging.getLogger("boto3")
boto3_log.setLevel(logging.WARNING)
boto3_log.propagate = True

# suppress botocore internal logging below WARNING level
botocore_log = logging.getLogger("botocore")
botocore_log.setLevel(logging.WARNING)
botocore_log.propagate = True


def parse_args(argv):
    """
    Use Argparse to parse command-line arguments.

    :param argv: list of arguments to parse (``sys.argv[1:]``)
    :type argv: list
    :return: parsed arguments
    :rtype: :py:class:`argparse.Namespace`
    """
    p = argparse.ArgumentParser(
        description='webhook2lambda2sqs - Generate code and manage '
                    'infrastructure for receiving webhooks with AWS API '
                    'Gateway and pushing to SQS via Lambda - <%s>' % PROJECT_URL
    )
    p.add_argument('-c', '--config', dest='config', type=str,
                   action='store', default='config.json',
                   help='path to config.json (default: ./config.json)')
    p.add_argument('-v', '--verbose', dest='verbose', action='count',
                   default=0,
                   help='verbose output. specify twice for debug-level output.')
    p.add_argument('-t', '--terraform-path', dest='tf_path', action='store',
                   type=str, help='path to terraform binary, if not in PATH',
                   default='terraform')
    p.add_argument('-s', '--stream-tf', dest='stream_tf', action='store_true',
                   default=False, help='stream Terraform output to STDOUT ('
                                       'combined) in realtime')
    p.add_argument('-V', '--version', action='version',
                   version='webhook2lambda2sqs v%s <%s>' % (
                       VERSION, PROJECT_URL
                   ))
    subparsers = p.add_subparsers(title='Action', dest='action')
    subparsers.add_parser(
        'generate', help='generate lambda function and terraform configs in ./'
    )
    subparsers.add_parser('genapply', help='generate function and terraform '
                                           'configs in ./, then run terraform '
                                           'apply')
    subparsers.add_parser('plan', help='run terraform plan to show changes '
                                       'which will be made')
    subparsers.add_parser('apply', help='run terraform apply to apply changes/'
                                        'create infrastructure')
    subparsers.add_parser('destroy', help='run terraform destroy to completely'
                                          ' destroy infrastructure')
    subparsers.add_parser(
        'example-config', help='write example config to STDOUT and description '
                               'of it to STDERR, then exit'
    )
    return p.parse_args(argv)


def set_log_info():
    """set logger level to INFO"""
    set_log_level_format(logging.INFO,
                         '%(asctime)s %(levelname)s:%(name)s:%(message)s')


def set_log_debug():
    """set logger level to DEBUG, and debug-level output format"""
    set_log_level_format(
        logging.DEBUG,
        "%(asctime)s [%(levelname)s %(filename)s:%(lineno)s - "
        "%(name)s.%(funcName)s() ] %(message)s"
    )


def set_log_level_format(level, format):
    """
    Set logger level and format.

    :param level: logging level; see the :py:mod:`logging` constants.
    :type level: int
    :param format: logging formatter format string
    :type format: str
    """
    formatter = logging.Formatter(fmt=format)
    logger.handlers[0].setFormatter(formatter)
    logger.setLevel(level)


def main(args=None):
    """
    Main entry point
    """
    # parse args
    if args is None:
        args = parse_args(sys.argv[1:])

    # dump example config if that action
    if args.action == 'example-config':
        conf, doc = Config.example_config()
        print(conf)
        sys.stderr.write(doc + "\n")
        return

    # set logging level
    if args.verbose > 1:
        set_log_debug()
    elif args.verbose == 1:
        set_log_info()

    # get our config
    config = Config(args.config)

    # if generate or genapply, generate the configs
    if args.action == 'generate' or args.action == 'genapply':
        func_gen = LambdaFuncGenerator(config)
        func_src = func_gen.generate()
        # @TODO: also write func_source to disk
        tf_gen = TerraformGenerator(config)
        tf_gen.generate(func_src)

    # if only generate, exit now
    if args.action == 'generate':
        return

    # else setup a Terraform action
    runner = TerraformRunner(config, args.tf_path)
    # run the terraform action
    if args.action == 'apply' or args.action == 'genapply':
        runner.apply(args.stream_tf)
    elif args.action == 'plan':
        runner.plan(args.stream_tf)
    else:  # destroy
        runner.destroy(args.stream_tf)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
