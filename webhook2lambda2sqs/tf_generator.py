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
import json
import zipfile

from webhook2lambda2sqs.version import VERSION, PROJECT_URL
from webhook2lambda2sqs.utils import pretty_json

logger = logging.getLogger(__name__)


class TerraformGenerator(object):

    def __init__(self, config):
        """
        Initialize the Terraform config generator.

        :param config: program configuration
        :type config: :py:class:`~.Config`
        """
        self.config = config
        self.tf_conf = {
            'provider': {
                'aws': {}
            },
            'resource': {},
            'outputs': {}
        }
        self.resource_name = 'webhook2lambda2sqs'
        if config.get('name_suffix') is not None:
            self.resource_name += config.get('name_suffix')

    def _get_tags(self):
        """
        Return a dict of tags to apply to AWS resources.

        :return: dict of tags to apply to AWS resources
        :rtype: dict
        """
        tags = self.config.get('aws_tags')
        if tags is None:
            tags = {}
        if 'Name' not in tags:
            tags['Name'] = self.resource_name
        tags['created_by'] = 'webhook2lambda2sqs v%s <%s>' % (
            VERSION, PROJECT_URL)
        logger.debug('AWS Tags: %s', tags)
        return tags

    def _generate_iam_role_policy(self):
        """
        Generate the policy for the IAM Role. Used by
        :py:meth:`~._generate_iam_role`.
        :return: IAM role policy JSON string
        :rtype: str
        """
        # from:
        # http://docs.aws.amazon.com/lambda/latest/dg/policy-templates.html
        pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:region:accountId:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:region:accountId:log-group:"
                        "[[logGroups]]:*"
                    ]
                }
            ]
        }
        # from:
        # https://www.terraform.io/docs/providers/aws/r/lambda_function.html
        pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                },
                {

                }
            ]
        }
        return json.dumps(pol)

    def _generate_iam_role(self):
        """
        Generate the IAM Role needed by the Lambda function and add to
        self.tf_conf
        """
        if 'aws_iam_role' not in self.tf_conf['resource']:
            self.tf_conf['resource']['aws_iam_role'] = {}
        self.tf_conf['resource']['aws_iam_role']['lambda_role'] = {
            'name': self.resource_name,
            'assume_role_policy': self._generate_iam_role_policy(),
        }
        self.tf_conf['outputs']['iam_role_arn'] = {
            'value': '${aws_iam_role.lambda_role.arn}'
        }
        self.tf_conf['outputs']['iam_role_unique_id'] = {
            'value': '${aws_iam_role.lambda_role.unique_id}'
        }

    def _generate_lambda(self, func_src):
        """
        Generate the lambda function and its IAM role, and add to self.tf_conf
        """
        if 'aws_lambda_function' not in self.tf_conf['resource']:
            self.tf_conf['resource']['aws_lambda_function'] = {}
        self.tf_conf['resource']['aws_lambda_function']['lambda_func'] = {
            'filename': 'webhook2lambda2sqs_func.zip',
            'function_name': self.resource_name,
            'role': '${aws_iam_role.lambda_role.arn}',
            'handler': 'webhook2lambda2sqs_func.webhook2lambda2sqs_handler',
            'source_code_hash': '${base64sha256(file('
                                '"webhook2lambda2sqs_func.zip"))}',
            'description': 'push webhook contents to SQS - generated and '
                           'managed by %s v%s' % (PROJECT_URL, VERSION),
            'runtime': 'python2.7',
            'timeout': 120
        }
        self.tf_conf['outputs']['lambda_func_arn'] = {
            'value': '${aws_lambda_function.lambda_func.arn}'
        }

    def _get_config(self, func_src):
        """
        Return the full terraform configuration as a JSON string

        :param func_src: lambda function source
        :type func_src: str
        :return: terraform configuration
        :rtype: str
        """
        self._generate_iam_role()
        self._generate_lambda(func_src)
        return pretty_json(self.tf_conf)

    def _write_zip(self, func_src, fpath):
        """
        Write the function source to a zip file, suitable for upload to
        Lambda.

        :param func_src: lambda function source
        :type func_src: str
        :param fpath: path to write the zip file at
        :type fpath: str
        """
        with zipfile.ZipFile(fpath, 'w') as z:
            z.writestr('webhook2lambda2sqs_func.py', func_src)

    def generate(self, func_src):
        """
        Generate TF config and write to ./webhook2lambda2sqs.tf.json;
        write the lambda function to ./webhook2lambda2sqs_func.py

        :param func_src: lambda function source
        :type func_src: str
        """
        # write function source for reference
        logger.warning('Writing lambda function source to: '
                       './webhook2lambda2sqs_func.py')
        with open('./webhook2lambda2sqs_func.py', 'w') as fh:
            fh.write(func_src)
        logger.debug('lambda function written')
        # write upload zip
        logger.warning('Writing lambda function source zip file to: '
                       './webhook2lambda2sqs_func.zip')
        self._write_zip(func_src, './webhook2lambda2sqs_func.zip')
        logger.debug('lambda zip written')
        # write terraform
        logger.warning('Writing terraform configuration JSON to: '
                       './webhook2lambda2sqs.tf.json')
        with open('./webhook2lambda2sqs.tf.json', 'w') as fh:
            fh.write(self._get_config(func_src))
        logger.debug('terraform configuration written')
        logger.warning('Completed writing lambda function and TF config.')
