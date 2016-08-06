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
import json
from freezegun import freeze_time
from zipfile import ZipInfo
from copy import deepcopy

from webhook2lambda2sqs.tf_generator import TerraformGenerator
from webhook2lambda2sqs.version import VERSION, PROJECT_URL
from webhook2lambda2sqs.config import Config

# https://code.google.com/p/mock/issues/detail?id=249
# py>=3.4 should use unittest.mock not the mock package on pypi
if (
        sys.version_info[0] < 3 or
        sys.version_info[0] == 3 and sys.version_info[1] < 4
):
    from mock import patch, call, Mock, DEFAULT, mock_open, PropertyMock  # noqa
else:
    from unittest.mock import (patch, call, Mock, DEFAULT,  # noqa
                               mock_open, PropertyMock)  # noqa

pbm = 'webhook2lambda2sqs.tf_generator'
pb = '%s.TerraformGenerator' % pbm


class TestTerraformGenerator(object):

    def setup(self):
        self.conf = deepcopy(Config._example)
        if 'terraform_remote_state' in self.conf:
            del self.conf['terraform_remote_state']

        def se_get(k):
            return self.conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        type(config).func_name = 'myFuncName'
        type(config).stage_name = 'mystagename'
        self.cls = TerraformGenerator(config)
        self.cls.aws_region = 'myregion'
        self.cls.aws_account_id = '1234'
        self.base_tf_conf = {
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

    def test_init(self):
        conf = {}

        def se_get(k):
            return conf.get(k, None)

        config = Mock()
        config.get.side_effect = se_get
        type(config).func_name = 'foobar'
        cls = TerraformGenerator(config)
        assert cls.config == config
        assert cls.resource_name == 'foobar'
        assert cls.aws_account_id is None
        assert cls.aws_region is None
        assert cls.tf_conf == self.base_tf_conf

    def test_description(self):
        assert self.cls.description == 'push webhook contents to SQS - ' \
                                       'generated and managed by %s ' \
                                       'v%s' % (PROJECT_URL, VERSION)

    def test_generate_iam_role_policy(self):
        self.cls._generate_iam_role_policy()
        expected_pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "logs:CreateLogGroup",
                    "Resource": "arn:aws:logs:myregion:1234:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": [
                        "arn:aws:logs:myregion:1234:log-group:"
                        "/aws/lambda/myFuncName:*"
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
                    "Resource": [
                        "arn:aws:sqs:myregion:1234:queueName1",
                        "arn:aws:sqs:myregion:1234:queueName2",
                        "arn:aws:sqs:myregion:1234:queueName3"
                    ]
                }
            ]
        }
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_iam_role_policy']['role_policy'] = {
            'name': 'myFuncName',
            'role': '${aws_iam_role.lambda_role.id}',
            'policy': json.dumps(expected_pol)
        }
        assert self.cls.tf_conf == expected_conf

    def test_generate_iam_invoke_role_policy(self):
        self.cls._generate_iam_invoke_role_policy()
        expected_pol = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Resource": ["*"],
                    "Action": ["lambda:InvokeFunction"]
                }
            ]
        }
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_iam_role_policy']['invoke_policy'] = {
            'name': 'myFuncName-invoke',
            'role': '${aws_iam_role.invoke_role.id}',
            'policy': json.dumps(expected_pol)
        }
        assert self.cls.tf_conf == expected_conf

    def test_generate_iam_role(self):
        self.cls._generate_iam_role()
        expected_pol = {
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
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_iam_role']['lambda_role'] = {
            'name': 'myFuncName',
            'assume_role_policy': json.dumps(expected_pol)
        }
        expected_conf['output']['iam_role_arn'] = {
            'value': '${aws_iam_role.lambda_role.arn}'
        }
        expected_conf['output']['iam_role_unique_id'] = {
            'value': '${aws_iam_role.lambda_role.unique_id}'
        }
        assert self.cls.tf_conf == expected_conf

    def test_generate_iam_invoke_role(self):
        self.cls._generate_iam_invoke_role()
        expected_pol = {
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
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_iam_role']['invoke_role'] = {
            'name': 'myFuncName-invoke',
            'assume_role_policy': json.dumps(expected_pol)
        }
        expected_conf['output']['iam_invoke_role_arn'] = {
            'value': '${aws_iam_role.invoke_role.arn}'
        }
        expected_conf['output']['iam_invoke_role_unique_id'] = {
            'value': '${aws_iam_role.invoke_role.unique_id}'
        }
        assert self.cls.tf_conf == expected_conf

    def test_generate_lambda(self):
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_lambda_function']['lambda_func'] = {
            'filename': 'webhook2lambda2sqs_func.zip',
            'function_name': 'myFuncName',
            'role': '${aws_iam_role.lambda_role.arn}',
            'handler': 'webhook2lambda2sqs_func.webhook2lambda2sqs_handler',
            'source_code_hash': '${base64sha256(file('
                                '"webhook2lambda2sqs_func.zip"))}',
            'description': 'mydesc',
            'runtime': 'python2.7',
            'timeout': 120
        }
        expected_conf['output']['lambda_func_arn'] = {
            'value': '${aws_lambda_function.lambda_func.arn}'
        }
        with patch('%s.description' % pb, new_callable=PropertyMock) as m_d:
            m_d.return_value = 'mydesc'
            self.cls._generate_lambda()
        assert self.cls.tf_conf == expected_conf

    def test_set_account_info_env_default(self):
        self.cls.aws_account_id = None
        self.cls.aws_region = None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict(
                        '%s.os.environ' % pbm,
                        {'AWS_DEFAULT_REGION': 'adr'},
                        clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam', region_name='adr'),
            call().get_user(),
            call('lambda', region_name='adr')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM with region_name=%s', 'adr'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    def test_set_account_info_env(self):
        self.cls.aws_account_id = None
        self.cls.aws_region = None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict(
                        '%s.os.environ' % pbm,
                        {'AWS_REGION': 'ar'},
                        clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam', region_name='ar'),
            call().get_user(),
            call('lambda', region_name='ar')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM with region_name=%s', 'ar'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    def test_set_account_info_no_env(self):
        self.cls.aws_account_id = None
        self.cls.aws_region = None
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s.client' % pbm, autospec=True) as mock_client:
                mock_client.return_value.get_user.return_value = {
                    'User': {'Arn': 'arn:aws:iam::123456789:user/foo'}
                }
                type(mock_client.return_value)._client_config = Mock(
                    region_name='myregion')
                with patch.dict('%s.os.environ' % pbm, {}, clear=True):
                    self.cls._set_account_info()
        assert self.cls.aws_account_id == '123456789'
        assert self.cls.aws_region == 'myregion'
        assert mock_client.mock_calls == [
            call('iam'),
            call().get_user(),
            call('lambda')
        ]
        assert mock_logger.mock_calls == [
            call.debug('Connecting to IAM without specified region'),
            call.info('Found AWS account ID as %s; region: %s',
                      '123456789', 'myregion')
        ]

    def test_generate_response_models(self):
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_api_gateway_model'] = {
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
        self.cls._generate_response_models()
        assert self.cls.tf_conf == expected_conf

    def test_generate_api_gateway(self):
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_api_gateway_rest_api'] = {
            'rest_api': {
                'name': 'myFuncName',
                'description': 'mydesc'
            }
        }
        expected_conf['output']['rest_api_id'] = {
            'value': '${aws_api_gateway_rest_api.rest_api.id}'
        }
        expected_conf['output']['base_url'] = {
            'value': 'https://${aws_api_gateway_rest_api.rest_api.id}.'
                     'execute-api.%s.amazonaws.com/%s/' % ('myregion',
                                                           'mystagename')
        }
        with patch('%s._generate_endpoint' % pb, autospec=True) as mock_ge:
            with patch('%s.description' % pb, new_callable=PropertyMock) as m_d:
                m_d.return_value = 'mydesc'
                self.cls._generate_api_gateway()
        assert self.cls.tf_conf == expected_conf
        assert mock_ge.mock_calls == [
            call(self.cls, 'other_resource_path', 'GET'),
            call(self.cls, 'some_resource_path', 'POST')
        ]

    def test_generate_api_gateway_deployment(self):
        self.cls.tf_conf['resource']['aws_api_gateway_integration'] = {
            'foo': 1,
            'bar': 2
        }
        self.cls.tf_conf['resource']['baz'] = {
            'blam': 3,
            'blarg': 4
        }
        self.cls.tf_conf['resource']['aws_api_gateway_rest_api'] = {
            'rest_api': 5
        }
        expected_conf = self.base_tf_conf
        expected_conf['resource']['baz'] = self.cls.tf_conf['resource']['baz']
        expected_conf['resource']['aws_api_gateway_rest_api'] =\
            self.cls.tf_conf['resource']['aws_api_gateway_rest_api']
        expected_conf['resource']['aws_api_gateway_integration'] = {
            'foo': 1,
            'bar': 2
        }
        expected_conf['resource']['aws_api_gateway_deployment'] = {
            'depl': {
                'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
                'depends_on': [
                    'aws_api_gateway_integration.bar',
                    'aws_api_gateway_integration.foo',
                    'aws_api_gateway_rest_api.rest_api',
                    'baz.blam',
                    'baz.blarg'
                ],
                'description': 'mydesc',
                'stage_name': 'mystagename'
            }
        }
        expected_conf['output'] = {
            'deployment_id': {'value': '${aws_api_gateway_deployment.depl.id}'}
        }
        with patch('%s.description' % pb, new_callable=PropertyMock) as m_d:
            m_d.return_value = 'mydesc'
            self.cls._generate_api_gateway_deployment()
        assert self.cls.tf_conf == expected_conf

    def test_generate_endpoint_post(self):
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_api_gateway_resource']['rname'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'parent_id':
                '${aws_api_gateway_rest_api.rest_api.root_resource_id}',
            'path_part': 'rname'
        }
        expected_conf['output']['rname_path'] = {
            'value': '${aws_api_gateway_resource.rname.path}'
        }
        expected_conf['resource']['aws_api_gateway_method']['rname_POST'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'authorization': 'NONE',
        }

        expected_conf['resource']['aws_api_gateway_method_response'][
            'rname_POST_202'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'status_code': 202,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.successmessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.rname_POST'
            ]
        }
        expected_conf['resource']['aws_api_gateway_method_response'][
            'rname_POST_500'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'status_code': 500,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.errormessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.rname_POST'
            ]
        }

        expected_conf['resource']['aws_api_gateway_integration_response'][
            'rname_POST_successResponse'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'status_code': 202,
            'response_templates': {'sbaz': 'sblam'},
            'depends_on': [
                'aws_api_gateway_method_response.rname_POST_202',
                'aws_api_gateway_integration.rname_POST_integration'
            ]
        }
        expected_conf['resource']['aws_api_gateway_integration_response'][
            'rname_POST_errorResponse'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'status_code': 500,
            'response_templates': {'ebaz': 'eblam'},
            'selection_pattern': '(^Failed.*)|(.*([Ee]xception|[Ee]rror).*)',
            'depends_on': [
                'aws_api_gateway_method_response.rname_POST_500',
                'aws_api_gateway_integration.rname_POST_integration'
            ]
        }

        expected_conf['resource']['aws_api_gateway_integration'][
            'rname_POST_integration'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.rname.id}',
            'http_method': 'POST',
            'type': 'AWS',
            'uri': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/'
                   'functions/${aws_lambda_function.lambda_func.arn}'
                   '/invocations',
            'credentials': '${aws_iam_role.invoke_role.arn}',
            'integration_http_method': 'POST',
            'request_templates': {'foo': 'bar'}
            # @TODO:
            # request_parameters_in_json
            # integrationResponses
        }
        with patch('%s.request_model_mapping' % pbm, {'foo': 'bar'}):
            with patch('%s.response_model_mapping' % pbm, {
                'success': {'sbaz': 'sblam'},
                'error': {'ebaz': 'eblam'}
            }):
                self.cls._generate_endpoint('rname', 'post')
        assert self.cls.tf_conf == expected_conf

    def test_generate_endpoint_get(self):
        expected_conf = self.base_tf_conf
        expected_conf['resource']['aws_api_gateway_resource']['myname'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'parent_id':
                '${aws_api_gateway_rest_api.rest_api.root_resource_id}',
            'path_part': 'myname'
        }
        expected_conf['output']['myname_path'] = {
            'value': '${aws_api_gateway_resource.myname.path}'
        }
        expected_conf['resource']['aws_api_gateway_method']['myname_GET'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'authorization': 'NONE',
        }

        expected_conf['resource']['aws_api_gateway_method_response'][
            'myname_GET_202'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'status_code': 202,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.successmessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.myname_GET'
            ]
        }
        expected_conf['resource']['aws_api_gateway_method_response'][
            'myname_GET_500'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'status_code': 500,
            'response_models': {
                'application/json':
                    '${aws_api_gateway_model.errormessage.name}',
            },
            'depends_on': [
                'aws_api_gateway_method.myname_GET'
            ]
        }

        expected_conf['resource']['aws_api_gateway_integration_response'][
            'myname_GET_successResponse'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'status_code': 202,
            'response_templates': {'sbaz': 'sblam'},
            'depends_on': [
                'aws_api_gateway_method_response.myname_GET_202',
                'aws_api_gateway_integration.myname_GET_integration'
            ]
        }
        expected_conf['resource']['aws_api_gateway_integration_response'][
            'myname_GET_errorResponse'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'status_code': 500,
            'response_templates': {'ebaz': 'eblam'},
            'selection_pattern': '(^Failed.*)|(.*([Ee]xception|[Ee]rror).*)',
            'depends_on': [
                'aws_api_gateway_method_response.myname_GET_500',
                'aws_api_gateway_integration.myname_GET_integration'
            ]
        }

        expected_conf['resource']['aws_api_gateway_integration'][
            'myname_GET_integration'] = {
            'rest_api_id': '${aws_api_gateway_rest_api.rest_api.id}',
            'resource_id': '${aws_api_gateway_resource.myname.id}',
            'http_method': 'GET',
            'type': 'AWS',
            'uri': 'arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/'
                   'functions/${aws_lambda_function.lambda_func.arn}'
                   '/invocations',
            'credentials': '${aws_iam_role.invoke_role.arn}',
            'integration_http_method': 'POST',
            'request_templates': {'foo': 'bar'}
            # @TODO:
            # request_parameters_in_json
            # integrationResponses
        }
        with patch('%s.request_model_mapping' % pbm, {'foo': 'bar'}):
            with patch('%s.response_model_mapping' % pbm, {
                'success': {'sbaz': 'sblam'},
                'error': {'ebaz': 'eblam'}
            }):
                self.cls._generate_endpoint('myname', 'GET')
        assert self.cls.tf_conf == expected_conf

    def test_generate_saved_config(self):
        type(self.cls.config)._config = {'foo': 'bar', 'baz': 2}
        expected_conf = self.base_tf_conf
        expected_conf['resource']['template_file'][
            'webhook2lambda2sqs_config_json'] = {
            'template': '$jsonconf',
            'vars': {
                'jsonconf': json.dumps({'foo': 'bar', 'baz': 2})
            }
        }
        self.cls._generate_saved_config()
        assert self.cls.tf_conf == expected_conf

    def test_get_config(self):
        with patch('%s.pretty_json' % pbm, autospec=True) as mock_json:
            with patch.multiple(
                pb,
                autospec=True,
                _generate_lambda=DEFAULT,
                _generate_iam_role=DEFAULT,
                _generate_iam_invoke_role=DEFAULT,
                _set_account_info=DEFAULT,
                _generate_response_models=DEFAULT,
                _generate_api_gateway=DEFAULT,
                _generate_iam_role_policy=DEFAULT,
                _generate_iam_invoke_role_policy=DEFAULT,
                _generate_api_gateway_deployment=DEFAULT,
                _generate_saved_config=DEFAULT,
            ) as mocks:
                mock_json.return_value = 'my_json_str'
                res = self.cls._get_config('funcsrc')
        assert mock_json.mock_calls == [call(self.base_tf_conf)]
        for m in mocks:
            if m.startswith('_generate'):
                assert mocks[m].mock_calls == [call(self.cls)]
        assert mocks['_set_account_info'].mock_calls == [call(self.cls)]
        assert res == 'my_json_str'

    @freeze_time("2016-07-01 02:03:04")
    def test_write_zip(self):
        with patch('%s.zipfile.ZipFile' % pbm, autospec=True) as mock_zf:
            with patch('%s.logger' % pbm, autospec=True) as mock_logger:
                self.cls._write_zip('myfsrc', 'mypath.zip')
        # the only way I can find to capture attributes being set on the ZipInfo
        # is to not mock it, but use a real ZipInfo object. Unfortunately, that
        # makes assertin on calls a bit more difficult...
        assert len(mock_zf.mock_calls) == 4
        assert mock_zf.mock_calls[0] == call('mypath.zip', 'w')
        assert mock_zf.mock_calls[1] == call().__enter__()
        assert mock_zf.mock_calls[3] == call().__exit__(None, None, None)
        # ok, now handle the second call, which should have the ZipInfo
        # as its first argument...
        # test that it's the right chained method call
        assert mock_zf.mock_calls[2][0] == '().__enter__().writestr'
        # test its arguments
        arg_tup = mock_zf.mock_calls[2][1]
        assert isinstance(arg_tup[0], ZipInfo)
        assert arg_tup[0].filename == 'webhook2lambda2sqs_func.py'
        assert arg_tup[0].date_time == (2016, 7, 1, 2, 3, 4)
        assert arg_tup[0].external_attr == 0x0755 << 16
        assert arg_tup[1] == 'myfsrc'
        assert mock_logger.mock_calls == [
            call.debug('setting zipinfo date to: %s', (2016, 7, 1, 2, 3, 4)),
            call.debug('setting zipinfo file mode to: %s', (0x0755 << 16)),
            call.debug('writing zip file at: %s', 'mypath.zip')
        ]

    def test_generate(self):
        with patch('%s.logger' % pbm, autospec=True) as mock_logger:
            with patch('%s._get_config' % pb, autospec=True) as mock_get:
                with patch('%s.open' % pbm, mock_open(), create=True) as m_open:
                    with patch('%s._write_zip' % pb, autospec=True) as mock_zip:
                        mock_get.return_value = 'myjson'
                        self.cls.generate('myfunc')
        assert mock_get.mock_calls == [call(self.cls, 'myfunc')]
        assert m_open.mock_calls == [
            call('./webhook2lambda2sqs_func.py', 'w'),
            call().__enter__(),
            call().write('myfunc'),
            call().__exit__(None, None, None),
            call('./webhook2lambda2sqs.tf.json', 'w'),
            call().__enter__(),
            call().write('myjson'),
            call().__exit__(None, None, None)
        ]
        assert mock_zip.mock_calls == [
            call(self.cls, 'myfunc', './webhook2lambda2sqs_func.zip')
        ]
        assert mock_logger.mock_calls == [
            call.warning('Writing lambda function source to: '
                         './webhook2lambda2sqs_func.py'),
            call.debug('lambda function written'),
            call.warning('Writing lambda function source zip file to: '
                         './webhook2lambda2sqs_func.zip'),
            call.debug('lambda zip written'),
            call.warning('Writing terraform configuration JSON to: '
                         './webhook2lambda2sqs.tf.json'),
            call.debug('terraform configuration written'),
            call.warning('Completed writing lambda function and TF config.')
        ]
