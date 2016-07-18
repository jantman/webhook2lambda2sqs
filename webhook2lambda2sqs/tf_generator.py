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
from boto3 import client
from datetime import datetime
import os

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
            'output': {}
        }
        self.resource_name = config.func_name
        self.aws_account_id = None
        self.aws_region = None

    @property
    def description(self):
        return 'push webhook contents to SQS - generated and managed by ' \
               '%s v%s' % (PROJECT_URL, VERSION)

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
        """
        pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:%s:%s:*" % (
                        self.aws_region, self.aws_account_id
                    )
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:%s:%s:log-group:%s:*" % (
                            self.aws_region, self.aws_account_id,
                            '/aws/lambda/%s' % self.resource_name
                        )
                    ]
                }
            ]
        }
        self.tf_conf['resource']['aws_iam_role_policy'] = {}
        self.tf_conf['resource']['aws_iam_role_policy']['role_policy'] = {
            'name': self.resource_name,
            'role': '${aws_iam_role.lambda_role.id}',
            'policy': json.dumps(pol)
        }
        invoke_pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Resource": ["*"],
                    "Action": ["lambda:InvokeFunction"]
                }
            ]
        }
        self.tf_conf['resource']['aws_iam_role_policy']['invoke_policy'] = {
            'name': self.resource_name + '-invoke',
            'role': '${aws_iam_role.invoke_role.id}',
            'policy': json.dumps(invoke_pol)
        }

    def _generate_iam_role(self):
        """
        Generate the IAM Role needed by the Lambda function and add to
        self.tf_conf
        """
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
                }
            ]
        }

        self.tf_conf['resource']['aws_iam_role'] = {}
        self.tf_conf['resource']['aws_iam_role']['lambda_role'] = {
            'name': self.resource_name,
            'assume_role_policy': json.dumps(pol),
        }
        self.tf_conf['output']['iam_role_arn'] = {
            'value': '${aws_iam_role.lambda_role.arn}'
        }
        self.tf_conf['output']['iam_role_unique_id'] = {
            'value': '${aws_iam_role.lambda_role.unique_id}'
        }

        invoke_assume = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "apigateway.amazonaws.com"
                    },
                    "Effect": "Allow",
                    "Sid": ""
                }
            ]
        }
        self.tf_conf['resource']['aws_iam_role']['invoke_role'] = {
            'name': self.resource_name + '-invoke',
            'assume_role_policy': json.dumps(invoke_assume),
        }
        self.tf_conf['output']['iam_invoke_role_arn'] = {
            'value': '${aws_iam_role.invoke_role.arn}'
        }
        self.tf_conf['output']['iam_invoke_role_unique_id'] = {
            'value': '${aws_iam_role.invoke_role.unique_id}'
        }
        self._generate_iam_role_policy()

    def _generate_lambda(self):
        """
        Generate the lambda function and its IAM role, and add to self.tf_conf
        """
        self.tf_conf['resource']['aws_lambda_function'] = {}
        self.tf_conf['resource']['aws_lambda_function']['lambda_func'] = {
            'filename': 'webhook2lambda2sqs_func.zip',
            'function_name': self.resource_name,
            'role': '${aws_iam_role.lambda_role.arn}',
            'handler': 'webhook2lambda2sqs_func.webhook2lambda2sqs_handler',
            'source_code_hash': '${base64sha256(file('
                                '"webhook2lambda2sqs_func.zip"))}',
            'description': self.description,
            'runtime': 'python2.7',
            'timeout': 120
        }
        self.tf_conf['output']['lambda_func_arn'] = {
            'value': '${aws_lambda_function.lambda_func.arn}'
        }

    def _set_account_info(self):
        """
        Connect to the AWS IAM API via boto3 and run the GetUser operation
        on the current user. Use this to set ``self.aws_account_id`` and
        ``self.aws_region``.
        """
        if 'AWS_DEFAULT_REGION' in os.environ:
            logger.debug('Connecting to IAM with region_name=%s',
                         os.environ['AWS_DEFAULT_REGION'])
            kwargs = {'region_name': os.environ['AWS_DEFAULT_REGION']}
        elif 'AWS_REGION' in os.environ:
            logger.debug('Connecting to IAM with region_name=%s',
                         os.environ['AWS_REGION'])
            kwargs = {'region_name': os.environ['AWS_REGION']}
        else:
            logger.debug('Connecting to IAM without specified region')
            kwargs = {}
        conn = client('iam', **kwargs)
        self.aws_account_id = conn.get_user()['User']['Arn'].split(':')[4]
        # region
        conn = client('lambda', **kwargs)
        self.aws_region = conn._client_config.region_name
        logger.info('Found AWS account ID as %s; region: %s',
                    self.aws_account_id, self.aws_region)

    def _generate_api_gateway(self):
        """
        Generate the full configuration for the API Gateway, and add to
        self.tf_conf
        """
        self.tf_conf['resource']['aws_api_gateway_rest_api'] = {
            'rest_api': {
                'name': self.resource_name,
                'description': self.description
            }
        }
        self.tf_conf['output']['rest_api_id'] = {
            'value': '${aws_api_gateway_rest_api.rest_api.id}'
        }
        # @TODO - these should be per-endpoint
        self.tf_conf['resource']['aws_api_gateway_resource'] = {
            'res1': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'parent_id':
                    '${aws_api_gateway_rest_api.rest_api.root_resource_id}',
                'path_part': 'foo'
            }
        }
        self.tf_conf['output']['res1_path'] = {
            'value': '${aws_api_gateway_resource.res1.path}'
        }
        self.tf_conf['resource']['aws_api_gateway_method'] = {
            'res1meth1': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'resource_id': '${aws_api_gateway_resource.res1.id}',
                'http_method': 'POST',
                'authorization': 'NONE',
                # request_models
                # request_parameters_in_json
            }
        }
        # https://www.terraform.io/docs/providers/aws/r/api_gateway_integration.html
        self.tf_conf['resource']['aws_api_gateway_integration'] = {
            'res1int1': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'resource_id': '${aws_api_gateway_resource.res1.id}',
                'http_method':
                    '${aws_api_gateway_method.res1meth1.http_method}',
                'type': 'AWS',
                'uri': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/'
                       'functions/${aws_lambda_function.lambda_func.arn}'
                       '/invocations',
                'credentials': self.tf_conf['output'][
                    'iam_invoke_role_arn']['value'],
                'integration_http_method':
                    '${aws_api_gateway_method.res1meth1.http_method}',
                # request_templates
                # request_parameters_in_json
                # integrationResponses
            }
        }

        # finally, the deployment
        stage_name = 'webhook2lambda2sqs'
        self.tf_conf['resource']['aws_api_gateway_deployment'] = {
            'depl': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'depends_on': ['aws_api_gateway_rest_api.rest_api'],
                'description': self.description,
                'stage_name': stage_name
            }
        }
        """
        @TODO - how to enable cloudwatch logs and metrics?
        it looks like TF doesn't support this. When we enable them via the
        Console:

        $ aws apigateway get-stages --rest-api-id qn6agayon8
        {
            "item": [
                {
                    "stageName": "webhook2lambda2sqs",
                    "cacheClusterSize": "0.5",
                    "variables": {},
                    "cacheClusterEnabled": false,
                    "cacheClusterStatus": "NOT_AVAILABLE",
                    "deploymentId": "za7cha",
                    "lastUpdatedDate": 1468865370,
                    "createdDate": 1468864980,
                    "methodSettings": {
                        "*/*": {
                            "cacheTtlInSeconds": 300,
                            "loggingLevel": "INFO",
                            "dataTraceEnabled": true,
                            "metricsEnabled": true,
                            "unauthorizedCacheControlHeaderStrategy":
                                "SUCCEED_WITH_RESPONSE_HEADER",
                            "throttlingRateLimit": 500.0,
                            "cacheDataEncrypted": false,
                            "cachingEnabled": false,
                            "throttlingBurstLimit": 1000,
                            "requireAuthorizationForCacheControl": true
                        }
                    }
                }
            ]
        }

        But TF doesn't have a 'methodSettings' parameter... and it appears
        ( see
        https://docs.aws.amazon.com/apigateway/api-reference/resource/stage/
        and
        https://docs.aws.amazon.com/apigateway/api-reference/link-relation/stage-create/
        )
        that the actual AWS API supports updating these values, but not
        specifying them at creation time.
        """
        self.tf_conf['output']['base_url'] = {
            'value': 'https://${aws_api_gateway_rest_api.rest_api.id}.'
                     'execute-api.%s.amazonaws.com/%s/' % (
                self.aws_region, stage_name
            )
        }

    def _get_config(self, func_src):
        """
        Return the full terraform configuration as a JSON string

        :param func_src: lambda function source
        :type func_src: str
        :return: terraform configuration
        :rtype: str
        """
        self._set_account_info()
        self._generate_iam_role()
        self._generate_lambda()
        self._generate_api_gateway()
        return pretty_json(self.tf_conf)

    def _write_zip(self, func_src, fpath):
        """
        Write the function source to a zip file, suitable for upload to
        Lambda.

        Note there's a bit of undocumented magic going on here; Lambda needs
        the execute bit set on the module with the handler in it (i.e. 0755
        or 0555 permissions). There doesn't seem to be *any* documentation on
        how to do this in the Python docs. The only real hint comes from the
        source code of :py:meth:`zipfile.ZipInfo.from_file`, which includes:

            st = os.stat(filename)
            ...
            zinfo.external_attr = (st.st_mode & 0xFFFF) << 16  # Unix attributes

        :param func_src: lambda function source
        :type func_src: str
        :param fpath: path to write the zip file at
        :type fpath: str
        """
        # get timestamp for file
        now = datetime.now()
        zi_tup = (now.year, now.month, now.day, now.hour, now.minute,
                  now.second)
        logger.debug('setting zipinfo date to: %s', zi_tup)
        # create a ZipInfo so we can set file attributes/mode
        zinfo = zipfile.ZipInfo('webhook2lambda2sqs_func.py', zi_tup)
        # set file mode
        zinfo.external_attr = 0755 << 16
        logger.debug('setting zipinfo file mode to: %s', zinfo.external_attr)
        logger.debug('writing zip file at: %s', fpath)
        with zipfile.ZipFile(fpath, 'w') as z:
            z.writestr(zinfo, func_src)

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
