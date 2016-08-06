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
from webhook2lambda2sqs.json_templates import (
    request_model_mapping, response_model_mapping
)

logger = logging.getLogger(__name__)


class TerraformGenerator(object):
    """
    Generate the Terraform configs for webhook2lambda2sqs.

    All of the _generate_* methods simply add resources to the
    ``tf_config`` dict.
    """

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
            'resource': {
                'aws_api_gateway_integration': {},
                'aws_api_gateway_integration_response': {},
                'aws_api_gateway_deployment': {},
                'aws_api_gateway_method': {},
                'aws_api_gateway_method_response': {},
                'aws_api_gateway_resource': {},
                'aws_api_gateway_rest_api': {},
                'aws_iam_role': {},
                'aws_iam_role_policy': {},
                'aws_lambda_function': {},
                'template_file': {},
            },
            'output': {}
        }
        self.resource_name = config.func_name
        self.aws_account_id = None
        self.aws_region = None

    @property
    def description(self):
        return 'push webhook contents to SQS - generated and managed by ' \
               '%s v%s' % (PROJECT_URL, VERSION)

    def _generate_iam_role_policy(self):
        """
        Generate the policy for the IAM Role.

        Terraform name: aws_iam_role.lambda_role
        """
        endpoints = self.config.get('endpoints')
        queue_arns = []
        for ep in endpoints:
            for qname in endpoints[ep]['queues']:
                qarn = 'arn:aws:sqs:%s:%s:%s' % (self.aws_region,
                                                 self.aws_account_id, qname)
                if qarn not in queue_arns:
                    queue_arns.append(qarn)
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
                },
                {
                    'Effect': 'Allow',
                    'Action': [
                        'sqs:ListQueues'
                    ],
                    'Resource': '*'
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "sqs:GetQueueUrl",
                        "sqs:SendMessage"
                    ],
                    "Resource": sorted(queue_arns)
                }
            ]
        }
        self.tf_conf['resource']['aws_iam_role_policy']['role_policy'] = {
            'name': self.resource_name,
            'role': '${aws_iam_role.lambda_role.id}',
            'policy': json.dumps(pol)
        }

    def _generate_iam_invoke_role_policy(self):
        """
        Generate the policy for the IAM role used by API Gateway to invoke
        the lambda function.

        Terraform name: aws_iam_role.invoke_role
        """
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
        Generate the IAM Role needed by the Lambda function.

        Terraform name: aws_iam_role.lambda_role
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

    def _generate_iam_invoke_role(self):
        """
        Generate the IAM Role for API Gateway to use to invoke the function.

        Terraform name: aws_iam_role.invoke_role
        :return:
        """

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

    def _generate_lambda(self):
        """
        Generate the lambda function and its IAM role, and add to self.tf_conf
        """
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

    def _generate_response_models(self):
        """
        Generate API Gateway response models and add to self.tf_conf
        """
        self.tf_conf['resource']['aws_api_gateway_model'] = {
            'errormessage': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'name': 'errormessage',
                'description': 'error message JSON schema',
                'content_type': 'application/json',
                'schema': """{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "title" : "Error Schema",
  "type" : "object",
  "properties" : {
    "status" : { "type" : "string" },
    "message" : { "type" : "string" },
    "request_id" : { "type" : "string" }
  }
}
                """
            },
            'successmessage': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'name': 'successmessage',
                'description': 'success message JSON schema',
                'content_type': 'application/json',
                'schema': """{
  "$schema" : "http://json-schema.org/draft-04/schema#",
  "title" : "Success Schema",
  "type" : "object",
  "properties" : {
    "status" : { "type" : "string" },
    "message" : { "type" : "string" },
    "SQSMessageIds" : { "type" : "array" },
    "request_id" : { "type" : "string" }
  }
}
                """
            }
        }

    def _generate_api_gateway(self):
        """
        Generate the full configuration for the API Gateway, and add to
        self.tf_conf
        """
        self.tf_conf['resource']['aws_api_gateway_rest_api']['rest_api'] = {
            'name': self.resource_name,
            'description': self.description
        }
        self.tf_conf['output']['rest_api_id'] = {
            'value': '${aws_api_gateway_rest_api.rest_api.id}'
        }
        # finally, the deployment
        """
        @NOTE Currently, Terraform can't enable metrics collection,
        request logging or rate limiting on API Gateway services.

        @TODO update this when
        <https://github.com/hashicorp/terraform/issues/6612> is fixed.

        @see https://github.com/jantman/webhook2lambda2sqs/issues/7
        @see https://github.com/jantman/webhook2lambda2sqs/issues/16
        """
        self.tf_conf['output']['base_url'] = {
            'value': 'https://${aws_api_gateway_rest_api.rest_api.id}.'
                     'execute-api.%s.amazonaws.com/%s/' % (
                         self.aws_region, self.config.stage_name)
        }
        # generate the endpoint configs
        endpoints = self.config.get('endpoints')
        for ep in sorted(endpoints.keys()):
            self._generate_endpoint(ep, endpoints[ep]['method'])

    def _generate_api_gateway_deployment(self):
        """
        Generate the API Gateway Deployment/Stage, and add to self.tf_conf
        """
        # finally, the deployment
        # this resource MUST come last
        dep_on = []
        for rtype in sorted(self.tf_conf['resource'].keys()):
            for rname in sorted(self.tf_conf['resource'][rtype].keys()):
                dep_on.append('%s.%s' % (rtype, rname))
        self.tf_conf['resource']['aws_api_gateway_deployment']['depl'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'description': self.description,
            'stage_name': self.config.stage_name,
            'depends_on': dep_on
        }
        self.tf_conf['output']['deployment_id'] = {
            'value': '${aws_api_gateway_deployment.depl.id}'
        }

    def _generate_endpoint(self, ep_name, ep_method):
        """
        Generate configuration for a single endpoint (this is many resources)

        Terraform Names:

        - aws_api_gateway_resource: {ep_name}
        - aws_api_gateway_method: {ep_name}_{ep_method}

        :param ep_name: endpoint name (path component)
        :type ep_name: str
        :param ep_method: HTTP method for the endpoint
        :type ep_method: str
        """
        ep_method = ep_method.upper()
        self.tf_conf['resource']['aws_api_gateway_resource'][ep_name] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'parent_id':
                '${aws_api_gateway_rest_api.rest_api.root_resource_id}',
            'path_part': ep_name
        }
        self.tf_conf['output']['%s_path' % ep_name] = {
            'value': '${aws_api_gateway_resource.%s.path}' % ep_name
        }
        self.tf_conf['resource']['aws_api_gateway_method'][
            '%s_%s' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'authorization': 'NONE',
            # @TODO: request_models ?
            # @TODO: request_parameters_in_json ?
        }
        self.tf_conf['resource']['aws_api_gateway_method_response'][
            '%s_%s_202' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'status_code': 202,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.successmessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.%s_%s' % (ep_name, ep_method)
            ]
        }
        self.tf_conf['resource']['aws_api_gateway_method_response'][
            '%s_%s_500' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'status_code': 500,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.errormessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.%s_%s' % (ep_name, ep_method)
            ]
        }

        self.tf_conf['resource']['aws_api_gateway_integration'][
            '%s_%s_integration' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'type': 'AWS',
            'uri': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/'
                   'functions/${aws_lambda_function.lambda_func.arn}'
                   '/invocations',
            'credentials': '${aws_iam_role.invoke_role.arn}',
            'integration_http_method': 'POST',
            'request_templates': request_model_mapping
            # @TODO:
            # request_parameters_in_json
            # integrationResponses
        }

        self.tf_conf['resource']['aws_api_gateway_integration_response'][
            '%s_%s_successResponse' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'status_code': 202,
            'response_templates': response_model_mapping['success'],
            'depends_on': [
                'aws_api_gateway_method_response.%s_%s_202' % (
                    ep_name, ep_method),
                'aws_api_gateway_integration.%s_%s_integration' % (
                    ep_name, ep_method)
            ]
        }
        self.tf_conf['resource']['aws_api_gateway_integration_response'][
            '%s_%s_errorResponse' % (ep_name, ep_method)] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.%s.id}' % ep_name,
            'http_method': ep_method,
            'status_code': 500,
            'selection_pattern': '(^Failed.*)|(.*([Ee]xception|[Ee]rror).*)',
            'response_templates': response_model_mapping['error'],
            'depends_on': [
                'aws_api_gateway_method_response.%s_%s_500' % (
                    ep_name, ep_method),
                'aws_api_gateway_integration.%s_%s_integration' % (
                    ep_name, ep_method)
            ]
        }

    def _generate_saved_config(self):
        """
        In order to ease saving webhook2lambda2sqs's JSON configuration,
        we dump it in the Terraform state in the hopes that remote state
        storage is being used. Then, at least it can be retrieved from there.
        """
        self.tf_conf['resource']['template_file'][
            'webhook2lambda2sqs_config_json'] = {
            'template': '$jsonconf',
            'vars': {
                'jsonconf': json.dumps(self.config._config)
            }
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
        self._generate_iam_role_policy()
        self._generate_iam_invoke_role()
        self._generate_iam_invoke_role_policy()
        self._generate_lambda()
        self._generate_response_models()
        self._generate_api_gateway()
        self._generate_api_gateway_deployment()
        self._generate_saved_config()
        return pretty_json(self.tf_conf)

    def _write_zip(self, func_src, fpath):
        """
        Write the function source to a zip file, suitable for upload to
        Lambda.

        Note there's a bit of undocumented magic going on here; Lambda needs
        the execute bit set on the module with the handler in it (i.e. 0755
        or 0555 permissions). There doesn't seem to be *any* documentation on
        how to do this in the Python docs. The only real hint comes from the
        source code of ``zipfile.ZipInfo.from_file()``, which includes:

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
        zinfo.external_attr = 0x0755 << 16
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
