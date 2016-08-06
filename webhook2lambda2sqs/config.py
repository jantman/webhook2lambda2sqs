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
import os
from textwrap import dedent

from webhook2lambda2sqs.utils import pretty_json, read_json_file

logger = logging.getLogger(__name__)


class InvalidConfigError(Exception):
    """Raised for configuration errors"""

    def __init__(self, message):
        msg = "Invalid Configuration File: %s" % message
        self._orig_message = message
        self.message = msg
        super(InvalidConfigError, self).__init__(msg)


class Config(object):

    _allowed_methods = ['POST', 'GET']

    _example = {
        'name_suffix': 'something',
        'endpoints': {
            'some_resource_path': {
                'method': 'POST',
                'queues': ['queueName1', 'queueName2']
            },
            'other_resource_path': {
                'method': 'GET',
                'queues': ['queueName2', 'queueName3']
            }
        },
        'terraform_remote_state': {
            'backend': 'backend_name',
            'config': {
                'option_name': 'option_value'
            }
        }
    }

    _example_docs = """
    Configuration description:

    endpoints - dict describing each webhook endpoint to setup in API Gateway.
      - key is the API Gateway resource name (final component of the URL)
      - value is a dict with the following keys:
        - 'method' - HTTP method for API Gateway resource
        - 'queues' - list of SQS queue names to push request content to
    name_suffix - by default, all AWS resources will be named
      "webhook2lambda2sqs"; specify a suffix to add to that name here.
    terraform_remote_state - dict of Terraform remote state options. If
      specified, will call 'terraform remote config' before every terraform
      command to setup remote state storage. See:
      https://www.terraform.io/docs/state/remote/index.html

      Dict keys:
      - 'backend' - name of the terraform remote state backend to configure
      - 'config' - dict of backend configuration option name/value pairs
    """

    def __init__(self, path):
        """
        Initialize configuration.

        :param path: path to configuration file on disk
        :type path: str
        """
        self.path = path
        self._config = self._load_config(path)
        self._validate_config()

    def _validate_config(self):
        """
        Validate configuration file.
        :raises: RuntimeError
        """
        # while set().issubset() is easier, we want to tell the user the names
        # of any invalid keys
        bad_keys = []
        for k in self._config.keys():
            if k not in self._example.keys():
                bad_keys.append(k)
        if len(bad_keys) > 0:
            raise InvalidConfigError('Invalid keys: %s' % bad_keys)
        # endpoints
        if 'endpoints' not in self._config or len(
                self._config['endpoints']) < 1:
            raise InvalidConfigError('configuration must have '
                                     'at least one endpoint')
        for ep in self._config['endpoints']:
            if sorted(
                    self._config['endpoints'][ep].keys()
            ) != ['method', 'queues']:
                raise InvalidConfigError('Endpoint %s configuration keys must '
                                         'be "method" and "queues".' % ep)
            meth = self._config['endpoints'][ep]['method']
            if meth not in self._allowed_methods:
                raise InvalidConfigError('Endpoint %s method %s not allowed '
                                         '(allowed methods: %s'
                                         ')' % (ep, meth,
                                                self._allowed_methods))

    def get(self, key):
        """
        Get the value of the specified configuration key. Return None if the
        key does not exist in the configuration.

        :param key: name of config key
        :type key: str
        :return: configuration value at specified key
        :rtype: object
        """
        return self._config.get(key, None)

    def _load_config(self, path):
        """
        Load configuration from JSON

        :param path: path to the JSON config file
        :type path: str
        :return: config dictionary
        :rtype: dict
        """
        p = os.path.abspath(os.path.expanduser(path))
        logger.debug('Loading configuration from: %s', p)
        return read_json_file(p)

    @property
    def func_name(self):
        """
        Return what we will name our lambda function.

        :return: lambda function name
        :rtype: str
        """
        name = 'webhook2lambda2sqs'
        if self.get('name_suffix') is not None:
            name += self.get('name_suffix')
        return name

    @staticmethod
    def example_config():
        """
        Return a 2-tuple of example configuration file as a pretty-printed
        JSON string and documentation about it as a string.

        :rtype: tuple
        :returns: 2-tuple of (example config file as pretty-printed JSON string,
          documentation about it (str))
        """
        ex = pretty_json(Config._example)
        return ex, dedent(Config._example_docs)
