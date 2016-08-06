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
from platform import node
from datetime import datetime
import requests
from pprint import pformat

from webhook2lambda2sqs.version import PROJECT_URL, VERSION
from webhook2lambda2sqs.config import Config
from webhook2lambda2sqs.terraform_runner import TerraformRunner
from webhook2lambda2sqs.tf_generator import TerraformGenerator
from webhook2lambda2sqs.func_generator import LambdaFuncGenerator
from webhook2lambda2sqs.aws import AWSInfo

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

# suppress requests internal logging below WARNING level
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
requests_log.propagate = True


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
    p.add_argument('-V', '--version', action='version',
                   version='webhook2lambda2sqs v%s <%s>' % (
                       VERSION, PROJECT_URL
                   ))
    subparsers = p.add_subparsers(title='Action (Subcommand)', dest='action',
                                  metavar='ACTION', description='Action to '
                                  'perform; each action may take further '
                                  'parameters. Use ACTION -h for subcommand-'
                                  'specific options and arguments.')
    subparsers.add_parser(
        'generate', help='generate lambda function and terraform configs in ./'
    )
    tf_parsers = [
        ('genapply', 'generate function and terraform configs in ./, then run '
                     'terraform apply'),
        ('plan', 'run terraform plan to show changes which will be made'),
        ('apply', 'run terraform apply to apply changes/create infrastructure'),
        ('destroy',
         'run terraform destroy to completely destroy infrastructure')
    ]
    tf_p_objs = {}
    for cname, chelp in tf_parsers:
        tf_p_objs[cname] = subparsers.add_parser(cname, help=chelp)
        tf_p_objs[cname].add_argument('-t', '--terraform-path', dest='tf_path',
                                      action='store', default='terraform',
                                      type=str, help='path to terraform '
                                                     'binary, if not in PATH')
        tf_p_objs[cname].add_argument('-S', '--no-stream-tf', dest='stream_tf',
                                      action='store_false', default=True,
                                      help='DO NOT stream Terraform output to '
                                           'STDOUT (combined) in realtime')
    apilogparser = subparsers.add_parser('apilogs', help='show last 10 '
                                         'CloudWatch Logs entries for the '
                                         'API Gateway')
    apilogparser.add_argument('-c', '--count', dest='log_count', type=int,
                              default=10, help='number of log entries to show '
                              '(default 10')
    logparser = subparsers.add_parser('logs', help='show last 10 CloudWatch '
                                      'Logs entries for the function')
    logparser.add_argument('-c', '--count', dest='log_count', type=int,
                           default=10, help='number of log entries to show '
                                            '(default 10')
    queueparser = subparsers.add_parser('queuepeek', help='show messages from '
                                        'one or all of the SQS queues')
    queueparser.add_argument('-n', '--name', type=str, dest='queue_name',
                             default=None, help='queue name to read (defaults '
                                                'to None to read all)')
    queueparser.add_argument('-d', '--delete', action='store_true',
                             dest='queue_delete', default=False,
                             help='delete messages after reading')
    queueparser.add_argument('-c', '--count', dest='msg_count', type=int,
                             default=10, help='number of messages to read from '
                                              'each queue (default 10)')
    testparser = subparsers.add_parser('test', help='send test message to '
                                                    'one or more endpoints')
    testparser.add_argument('-t', '--terraform-path', dest='tf_path',
                            action='store', default='terraform',
                            type=str, help='path to terraform '
                            'binary, if not in PATH')
    testparser.add_argument('-n', '--endpoint-name', dest='endpoint_name',
                            type=str, default=None,
                            help='endpoint name (default: None, to send to '
                                 'all endpoints)')
    subparsers.add_parser(
        'example-config', help='write example config to STDOUT and description '
                               'of it to STDERR, then exit'
    )
    args = p.parse_args(argv)
    if args.action is None:
        # for py3, which doesn't raise on this
        sys.stderr.write("ERROR: too few arguments\n")
        raise SystemExit(2)
    return args


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


def get_base_url(config, args):
    """
    Get the API base url. Try Terraform state first, then
    :py:class:`~.AWSInfo`.

    :param config: configuration
    :type config: :py:class:`~.Config`
    :param args: command line arguments
    :type args: :py:class:`argparse.Namespace`
    :return: API base URL
    :rtype: str
    """
    try:
        logger.debug('Trying to get Terraform base_url output')
        runner = TerraformRunner(config, args.tf_path)
        outputs = runner._get_outputs()
        base_url = outputs['base_url']
        logger.debug("Terraform base_url output: '%s'", base_url)
    except Exception:
        logger.info('Unable to find API base_url from Terraform state; '
                    'querying AWS.', exc_info=1)
        aws = AWSInfo(config)
        base_url = aws.get_api_base_url()
        logger.debug("AWS api_base_url: '%s'", base_url)
    if not base_url.endswith('/'):
        base_url += '/'
    return base_url


def get_api_id(config, args):
    """
    Get the API ID from Terraform, or from AWS if that fails.

    :param config: configuration
    :type config: :py:class:`~.Config`
    :param args: command line arguments
    :type args: :py:class:`argparse.Namespace`
    :return: API Gateway ID
    :rtype: str
    """
    try:
        logger.debug('Trying to get Terraform rest_api_id output')
        runner = TerraformRunner(config, args.tf_path)
        outputs = runner._get_outputs()
        depl_id = outputs['rest_api_id']
        logger.debug("Terraform rest_api_id output: '%s'", depl_id)
    except Exception:
        logger.info('Unable to find API rest_api_id from Terraform state;'
                    ' querying AWS.', exc_info=1)
        aws = AWSInfo(config)
        depl_id = aws.get_api_id()
        logger.debug("AWS API ID: '%s'", depl_id)
    return depl_id


def run_test(config, args):
    """
    Run the 'test' subcommand

    :param config: configuration
    :type config: :py:class:`~.Config`
    :param args: command line arguments
    :type args: :py:class:`argparse.Namespace`
    """
    base_url = get_base_url(config, args)
    logger.debug('API base url: %s', base_url)
    endpoints = config.get('endpoints')
    if args.endpoint_name is not None:
        endpoints = {
            args.endpoint_name: endpoints[args.endpoint_name]
        }
    dt = datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
    data = {
        'message': 'testing via webhook2lambda2sqs CLI',
        'version': VERSION,
        'host': node(),
        'datetime': dt
    }
    for ep in sorted(endpoints):
        url = base_url + ep + '/'
        print('=> Testing endpoint %s with %s: %s' % (
            url, endpoints[ep]['method'], pformat(data))
        )
        if endpoints[ep]['method'] == 'POST':
            res = requests.post(url, json=data)
        elif endpoints[ep]['method'] == 'GET':
            res = requests.get(url, params=data)
        else:
            raise Exception('Unimplemented method: %s'
                            '' % endpoints[ep]['method'])
        print('RESULT: HTTP %d' % res.status_code)
        for h in sorted(res.headers):
            print('%s: %s' % (h, res.headers[h]))
        print("\n%s\n" % res.content)


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

    if args.action == 'logs':
        aws = AWSInfo(config)
        aws.show_cloudwatch_logs(count=args.log_count)
        return

    if args.action == 'apilogs':
        api_id = get_api_id(config, args)
        aws = AWSInfo(config)
        aws.show_cloudwatch_logs(
            count=args.log_count,
            grp_name='API-Gateway-Execution-Logs_%s/%s' % (
                api_id, config.stage_name
            )
        )
        return

    if args.action == 'queuepeek':
        aws = AWSInfo(config)
        aws.show_queue(name=args.queue_name, delete=args.queue_delete,
                       count=args.msg_count)
        return

    if args.action == 'test':
        run_test(config, args)
        return

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
        # conditionally set API Gateway Method settings
        if config.get('api_gateway_method_settings') is not None:
            aws = AWSInfo(config)
            aws.set_method_settings()
    elif args.action == 'plan':
        runner.plan(args.stream_tf)
    else:  # destroy
        runner.destroy(args.stream_tf)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(args)
